from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from db.enums import NotificationEventType, TaskLogStatus

from unitkeeper_backend.application.models import TaskInfo, TaskLogInfo, TaskLogPage, TaskLogView
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.domain.errors import (
    AuthorizationError,
    BusinessRuleViolation,
    NotFoundError,
    ValidationError,
)
from unitkeeper_backend.domain.services.sprint_math import SprintWindow, current_sprint_window


@dataclass(slots=True)
class TaskImportItem:
    title: str
    frequency_per_sprint: int
    unit_cost: Decimal


class TaskService:
    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def create_task(
        self,
        *,
        group_id: int,
        title: str,
        frequency_per_sprint: int,
        unit_cost: Decimal,
    ) -> TaskInfo:
        self._validate_task_payload(
            title=title, frequency_per_sprint=frequency_per_sprint, unit_cost=unit_cost
        )
        task = await self._uow.tasks.create_task(
            group_id=group_id,
            title=title.strip(),
            frequency_per_sprint=frequency_per_sprint,
            unit_cost=unit_cost,
        )
        await self._uow.commit()
        return task

    async def list_tasks(self, *, group_id: int, include_deleted: bool = False) -> list[TaskInfo]:
        tasks = await self._uow.tasks.list_tasks(group_id=group_id, active_only=not include_deleted)
        return await self._attach_remaining_counts(group_id=group_id, tasks=tasks)

    async def get_task(self, *, group_id: int, task_id: int) -> TaskInfo:
        task = await self._uow.tasks.get_task(group_id=group_id, task_id=task_id)
        if task is None:
            raise NotFoundError("Task was not found")
        return (await self._attach_remaining_counts(group_id=group_id, tasks=[task]))[0]

    async def update_task(
        self,
        *,
        group_id: int,
        task_id: int,
        title: str | None,
        frequency_per_sprint: int | None,
        unit_cost: Decimal | None,
    ) -> TaskInfo:
        if title is not None and not title.strip():
            raise ValidationError("Task title is required")
        if frequency_per_sprint is not None and frequency_per_sprint < 0:
            raise ValidationError("Task frequency must be a non-negative integer")
        if unit_cost is not None and unit_cost < Decimal("0"):
            raise ValidationError("Task unit cost must be non-negative")
        task = await self._uow.tasks.update_task(
            group_id=group_id,
            task_id=task_id,
            title=title.strip() if title is not None else None,
            frequency_per_sprint=frequency_per_sprint,
            unit_cost=unit_cost,
        )
        await self._uow.commit()
        return await self.get_task(group_id=group_id, task_id=task.id)

    async def import_tasks(self, *, group_id: int, items: list[TaskImportItem]) -> list[TaskInfo]:
        if not items:
            raise ValidationError("Import payload is empty")

        errors: list[dict[str, object]] = []
        normalized: list[TaskImportItem] = []
        for index, item in enumerate(items):
            row_errors = self._validate_import_row(item)
            if row_errors:
                for field, message in row_errors:
                    errors.append({"index": index, "field": field, "message": message})
                continue
            normalized.append(
                TaskImportItem(
                    title=item.title.strip(),
                    frequency_per_sprint=item.frequency_per_sprint,
                    unit_cost=item.unit_cost,
                )
            )

        if errors:
            raise ValidationError("Task import contains invalid rows", details={"errors": errors})

        created: list[TaskInfo] = []
        for item in normalized:
            task = await self._uow.tasks.create_task(
                group_id=group_id,
                title=item.title,
                frequency_per_sprint=item.frequency_per_sprint,
                unit_cost=item.unit_cost,
            )
            created.append(task)
        await self._uow.commit()
        return await self._attach_remaining_counts(group_id=group_id, tasks=created)

    async def adjust_frequency(self, *, group_id: int, task_id: int, delta: int) -> TaskInfo:
        if delta == 0:
            raise ValidationError("Frequency adjustment delta must be non-zero")
        task = await self.get_task(group_id=group_id, task_id=task_id)
        if not task.is_active:
            raise BusinessRuleViolation("Soft-deleted tasks cannot change frequency")
        new_frequency = task.frequency_per_sprint + delta
        if new_frequency < 0:
            raise ValidationError("Task frequency must remain a non-negative integer")
        return await self.update_task(
            group_id=group_id,
            task_id=task_id,
            title=None,
            frequency_per_sprint=new_frequency,
            unit_cost=None,
        )

    async def delete_task(self, *, group_id: int, task_id: int) -> None:
        await self.get_task(group_id=group_id, task_id=task_id)
        await self._uow.tasks.soft_delete_task(
            group_id=group_id,
            task_id=task_id,
            deleted_at=self._clock.now(),
        )
        await self._uow.commit()

    async def mark_done(
        self, *, group_id: int, performer_user_id: int, task_id: int
    ) -> TaskLogInfo:
        if (
            await self._uow.groups.get_active_membership_in_group(
                group_id=group_id, user_id=performer_user_id
            )
            is None
        ):
            raise AuthorizationError("Performer is not an active group member")
        task = await self.get_task(group_id=group_id, task_id=task_id)
        if not task.is_active:
            raise BusinessRuleViolation("Soft-deleted tasks cannot be completed")

        # Lock the task row so concurrent completions cannot both slip past the
        # sprint cap. Every open completion — confirmed or still pending —
        # consumes a slot, so you can mark a task only as many times as remain
        # available this sprint.
        await self._uow.tasks.lock_task(group_id=group_id, task_id=task_id)
        window = await self._current_window(group_id)
        completed_count = await self._uow.tasks.count_completed_in_window(
            task_id=task_id,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        pending_count = await self._uow.tasks.count_pending_in_window(
            task_id=task_id,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        if completed_count + pending_count >= task.frequency_per_sprint:
            raise BusinessRuleViolation("Task frequency limit for the current sprint is exhausted")

        memberships = await self._uow.groups.list_active_memberships(group_id)
        status = TaskLogStatus.COMPLETED if len(memberships) == 1 else TaskLogStatus.PENDING
        approver_user_id = performer_user_id if status is TaskLogStatus.COMPLETED else None
        decided_at = self._clock.now() if status is TaskLogStatus.COMPLETED else None
        log = await self._uow.tasks.create_task_log(
            group_id=group_id,
            task_id=task_id,
            performer_user_id=performer_user_id,
            status=status,
            created_at=self._clock.now(),
            approver_user_id=approver_user_id,
            decided_at=decided_at,
        )
        if status is TaskLogStatus.PENDING:
            for membership in memberships:
                if membership.user_id == performer_user_id:
                    continue
                await self._uow.notifications.enqueue(
                    event_type=NotificationEventType.TASK_APPROVAL_REQUESTED,
                    recipient_user_id=membership.user_id,
                    group_id=group_id,
                    payload={
                        "task_log_id": log.id,
                        "task_title": task.title,
                        "performer_user_id": performer_user_id,
                    },
                    deep_link_path=f"/tasks/history?task_log_id={log.id}",
                )
        await self._uow.commit()
        return log

    async def approve(self, *, group_id: int, approver_user_id: int, log_id: int) -> TaskLogInfo:
        log = await self._require_pending_log(group_id=group_id, log_id=log_id)
        memberships = await self._uow.groups.list_active_memberships(group_id)
        if len(memberships) > 1 and approver_user_id == log.performer_user_id:
            raise AuthorizationError("Performer cannot self-approve in a multi-member group")
        if (
            await self._uow.groups.get_active_membership_in_group(
                group_id=group_id, user_id=approver_user_id
            )
            is None
        ):
            raise AuthorizationError("Approver is not an active group member")

        task = await self.get_task(group_id=group_id, task_id=log.task_id)
        window = await self._current_window(group_id)
        completed_count = await self._uow.tasks.count_completed_in_window(
            task_id=task.id,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        if completed_count >= task.frequency_per_sprint:
            raise BusinessRuleViolation("Task frequency limit for the current sprint is exhausted")

        updated = await self._uow.tasks.approve_task_log(
            log_id=log_id,
            approver_user_id=approver_user_id,
            decided_at=self._clock.now(),
        )
        await self._uow.notifications.enqueue(
            event_type=NotificationEventType.TASK_APPROVED,
            recipient_user_id=updated.performer_user_id,
            group_id=group_id,
            payload={
                "task_log_id": updated.id,
                "task_title": task.title,
                "approver_user_id": approver_user_id,
            },
            deep_link_path=f"/tasks/history?task_log_id={updated.id}",
        )
        await self._uow.commit()
        return updated

    async def reject(
        self,
        *,
        group_id: int,
        approver_user_id: int,
        log_id: int,
        rejection_reason: str,
    ) -> TaskLogInfo:
        if not rejection_reason.strip():
            raise ValidationError("Rejection reason is required")
        log = await self._require_pending_log(group_id=group_id, log_id=log_id)
        memberships = await self._uow.groups.list_active_memberships(group_id)
        if len(memberships) > 1 and approver_user_id == log.performer_user_id:
            raise AuthorizationError("Performer cannot self-reject in a multi-member group")
        if (
            await self._uow.groups.get_active_membership_in_group(
                group_id=group_id, user_id=approver_user_id
            )
            is None
        ):
            raise AuthorizationError("Rejector is not an active group member")
        updated = await self._uow.tasks.reject_task_log(
            log_id=log_id,
            approver_user_id=approver_user_id,
            decided_at=self._clock.now(),
            rejection_reason=rejection_reason.strip(),
        )
        task = await self.get_task(group_id=group_id, task_id=updated.task_id)
        await self._uow.notifications.enqueue(
            event_type=NotificationEventType.TASK_REJECTED,
            recipient_user_id=updated.performer_user_id,
            group_id=group_id,
            payload={
                "task_log_id": updated.id,
                "task_title": task.title,
                "approver_user_id": approver_user_id,
                "rejection_reason": updated.rejection_reason or "",
            },
            deep_link_path=f"/tasks/history?task_log_id={updated.id}",
        )
        await self._uow.commit()
        return updated

    async def list_pending_approvals(
        self,
        *,
        group_id: int,
        user_id: int,
        limit: int,
        offset: int,
    ) -> TaskLogPage:
        """Return pending logs this member may review, never their own logs."""
        await self._require_active_member(group_id=group_id, user_id=user_id)
        return await self._list_log_page(
            group_id=group_id,
            exclude_performer_user_id=user_id,
            statuses=[TaskLogStatus.PENDING],
            limit=limit,
            offset=offset,
        )

    async def list_my_task_logs(
        self,
        *,
        group_id: int,
        user_id: int,
        task_id: int | None,
        statuses: list[TaskLogStatus] | None,
        limit: int,
        offset: int,
    ) -> TaskLogPage:
        await self._require_active_member(group_id=group_id, user_id=user_id)
        return await self._list_log_page(
            group_id=group_id,
            performer_user_id=user_id,
            task_id=task_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )

    async def list_group_task_logs(
        self,
        *,
        group_id: int,
        user_id: int,
        performer_user_id: int | None,
        task_id: int | None,
        statuses: list[TaskLogStatus] | None,
        limit: int,
        offset: int,
    ) -> TaskLogPage:
        await self._require_active_member(group_id=group_id, user_id=user_id)
        return await self._list_log_page(
            group_id=group_id,
            performer_user_id=performer_user_id,
            task_id=task_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )

    async def get_task_log_view(self, *, group_id: int, user_id: int, log_id: int) -> TaskLogView:
        await self._require_active_member(group_id=group_id, user_id=user_id)
        log = await self._uow.tasks.get_task_log(log_id=log_id)
        if log is None or log.group_id != group_id:
            raise NotFoundError("Task log was not found")
        return (await self._build_log_views([log]))[0]

    async def _list_log_page(
        self,
        *,
        group_id: int,
        limit: int,
        offset: int,
        performer_user_id: int | None = None,
        exclude_performer_user_id: int | None = None,
        task_id: int | None = None,
        statuses: list[TaskLogStatus] | None = None,
    ) -> TaskLogPage:
        logs = await self._uow.tasks.list_task_logs(
            group_id=group_id,
            performer_user_id=performer_user_id,
            exclude_performer_user_id=exclude_performer_user_id,
            task_id=task_id,
            statuses=statuses,
            limit=limit,
            offset=offset,
        )
        total = await self._uow.tasks.count_task_logs(
            group_id=group_id,
            performer_user_id=performer_user_id,
            exclude_performer_user_id=exclude_performer_user_id,
            task_id=task_id,
            statuses=statuses,
        )
        return TaskLogPage(
            items=await self._build_log_views(logs),
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _build_log_views(self, logs: Sequence[TaskLogInfo]) -> list[TaskLogView]:
        log_list = list(logs)
        if not log_list:
            return []
        task_ids = {log.task_id for log in log_list}
        user_ids = {log.performer_user_id for log in log_list}
        user_ids.update(
            log.approver_user_id for log in log_list if log.approver_user_id is not None
        )
        group_id = log_list[0].group_id
        tasks = await self._uow.tasks.list_tasks_by_ids(group_id=group_id, task_ids=tuple(task_ids))
        users = await self._uow.users.list_by_ids(tuple(user_ids))
        tasks_by_id = {task.id: task for task in tasks}
        users_by_id = {user.id: user for user in users}
        views: list[TaskLogView] = []
        for log in log_list:
            task = tasks_by_id.get(log.task_id)
            performer = users_by_id.get(log.performer_user_id)
            if task is None or performer is None:
                raise NotFoundError("Task log references missing data")
            views.append(
                TaskLogView(
                    id=log.id,
                    group_id=log.group_id,
                    task_id=task.id,
                    task_title=task.title,
                    unit_cost=task.unit_cost,
                    task_is_active=task.is_active,
                    status=log.status,
                    performer=performer,
                    approver=users_by_id.get(log.approver_user_id)
                    if log.approver_user_id is not None
                    else None,
                    decided_at=log.decided_at,
                    rejection_reason=log.rejection_reason,
                    created_at=log.created_at,
                )
            )
        return views

    async def _require_active_member(self, *, group_id: int, user_id: int) -> None:
        if (
            await self._uow.groups.get_active_membership_in_group(
                group_id=group_id, user_id=user_id
            )
            is None
        ):
            raise AuthorizationError("User is not an active group member")

    async def _attach_remaining_counts(
        self, *, group_id: int, tasks: list[TaskInfo]
    ) -> list[TaskInfo]:
        if not tasks:
            return tasks
        window = await self._current_window(group_id)
        updated: list[TaskInfo] = []
        for task in tasks:
            completed = await self._uow.tasks.count_completed_in_window(
                task_id=task.id,
                window_start=window.starts_at,
                window_end_exclusive=window.ends_before,
            )
            pending = await self._uow.tasks.count_pending_in_window(
                task_id=task.id,
                window_start=window.starts_at,
                window_end_exclusive=window.ends_before,
            )
            updated.append(
                TaskInfo(
                    id=task.id,
                    group_id=task.group_id,
                    title=task.title,
                    frequency_per_sprint=task.frequency_per_sprint,
                    unit_cost=task.unit_cost,
                    deleted_at=task.deleted_at,
                    completed_in_sprint=completed,
                    pending_in_sprint=pending,
                )
            )
        return updated

    async def _current_window(self, group_id: int) -> SprintWindow:
        group = await self._uow.groups.get_by_id(group_id)
        if group is None:
            raise NotFoundError("Group was not found")
        return current_sprint_window(
            today=self._clock.today(),
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
            anchor=group.created_at,
        )

    async def _require_pending_log(self, *, group_id: int, log_id: int) -> TaskLogInfo:
        log = await self._uow.tasks.get_task_log(log_id=log_id)
        if log is None or log.group_id != group_id:
            raise NotFoundError("Task log was not found")
        if log.status is not TaskLogStatus.PENDING:
            raise BusinessRuleViolation("Only pending task logs can be reviewed")
        return log

    @staticmethod
    def _validate_task_payload(
        *, title: str, frequency_per_sprint: int, unit_cost: Decimal
    ) -> None:
        if not title.strip():
            raise ValidationError("Task title is required")
        if frequency_per_sprint < 0:
            raise ValidationError("Task frequency must be a non-negative integer")
        if unit_cost < Decimal("0"):
            raise ValidationError("Task unit cost must be non-negative")

    @staticmethod
    def _validate_import_row(item: TaskImportItem) -> list[tuple[str, str]]:
        errors: list[tuple[str, str]] = []
        if not isinstance(item.title, str) or not item.title.strip():
            errors.append(("title", "Title is required"))
        elif len(item.title.strip()) > 255:
            errors.append(("title", "Title must be at most 255 characters"))
        if not isinstance(item.frequency_per_sprint, int) or isinstance(
            item.frequency_per_sprint, bool
        ):
            errors.append(("frequency_per_sprint", "Frequency must be an integer"))
        elif item.frequency_per_sprint < 0:
            errors.append(("frequency_per_sprint", "Frequency must be a non-negative integer"))
        try:
            cost = Decimal(item.unit_cost)
        except (InvalidOperation, TypeError, ValueError):
            errors.append(("unit_cost", "Unit cost must be a decimal number"))
        else:
            if cost < Decimal("0"):
                errors.append(("unit_cost", "Unit cost must be non-negative"))
        return errors
