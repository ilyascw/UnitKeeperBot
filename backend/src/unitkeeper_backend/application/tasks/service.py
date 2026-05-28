from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from db.enums import TaskLogStatus
from unitkeeper_backend.application.models import TaskInfo, TaskLogInfo
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.domain.errors import AuthorizationError, BusinessRuleViolation, NotFoundError, ValidationError
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
        self._validate_task_payload(title=title, frequency_per_sprint=frequency_per_sprint, unit_cost=unit_cost)
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
        if frequency_per_sprint is not None and frequency_per_sprint <= 0:
            raise ValidationError("Task frequency must be a positive integer")
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
        if new_frequency <= 0:
            raise ValidationError("Task frequency must remain a positive integer")
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

    async def mark_done(self, *, group_id: int, performer_user_id: int, task_id: int) -> TaskLogInfo:
        if await self._uow.groups.get_active_membership_in_group(group_id=group_id, user_id=performer_user_id) is None:
            raise AuthorizationError("Performer is not an active group member")
        task = await self.get_task(group_id=group_id, task_id=task_id)
        if not task.is_active:
            raise BusinessRuleViolation("Soft-deleted tasks cannot be completed")

        window = await self._current_window(group_id)
        completed_count = await self._uow.tasks.count_completed_in_window(
            task_id=task_id,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        if completed_count >= task.frequency_per_sprint:
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
        await self._uow.commit()
        return log

    async def approve(self, *, group_id: int, approver_user_id: int, log_id: int) -> TaskLogInfo:
        log = await self._require_pending_log(group_id=group_id, log_id=log_id)
        memberships = await self._uow.groups.list_active_memberships(group_id)
        if len(memberships) > 1 and approver_user_id == log.performer_user_id:
            raise AuthorizationError("Performer cannot self-approve in a multi-member group")
        if await self._uow.groups.get_active_membership_in_group(group_id=group_id, user_id=approver_user_id) is None:
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
        if await self._uow.groups.get_active_membership_in_group(group_id=group_id, user_id=approver_user_id) is None:
            raise AuthorizationError("Rejector is not an active group member")
        updated = await self._uow.tasks.reject_task_log(
            log_id=log_id,
            approver_user_id=approver_user_id,
            decided_at=self._clock.now(),
            rejection_reason=rejection_reason.strip(),
        )
        await self._uow.commit()
        return updated

    async def _attach_remaining_counts(self, *, group_id: int, tasks: list[TaskInfo]) -> list[TaskInfo]:
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
            updated.append(
                TaskInfo(
                    id=task.id,
                    group_id=task.group_id,
                    title=task.title,
                    frequency_per_sprint=task.frequency_per_sprint,
                    unit_cost=task.unit_cost,
                    deleted_at=task.deleted_at,
                    completed_in_sprint=completed,
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
        )

    async def _require_pending_log(self, *, group_id: int, log_id: int) -> TaskLogInfo:
        log = await self._uow.tasks.get_task_log(log_id=log_id)
        if log is None or log.group_id != group_id:
            raise NotFoundError("Task log was not found")
        if log.status is not TaskLogStatus.PENDING:
            raise BusinessRuleViolation("Only pending task logs can be reviewed")
        return log

    @staticmethod
    def _validate_task_payload(*, title: str, frequency_per_sprint: int, unit_cost: Decimal) -> None:
        if not title.strip():
            raise ValidationError("Task title is required")
        if frequency_per_sprint <= 0:
            raise ValidationError("Task frequency must be a positive integer")
        if unit_cost < Decimal("0"):
            raise ValidationError("Task unit cost must be non-negative")

    @staticmethod
    def _validate_import_row(item: TaskImportItem) -> list[tuple[str, str]]:
        errors: list[tuple[str, str]] = []
        if not isinstance(item.title, str) or not item.title.strip():
            errors.append(("title", "Title is required"))
        elif len(item.title.strip()) > 255:
            errors.append(("title", "Title must be at most 255 characters"))
        if not isinstance(item.frequency_per_sprint, int) or isinstance(item.frequency_per_sprint, bool):
            errors.append(("frequency_per_sprint", "Frequency must be an integer"))
        elif item.frequency_per_sprint <= 0:
            errors.append(("frequency_per_sprint", "Frequency must be a positive integer"))
        try:
            cost = Decimal(item.unit_cost)
        except (InvalidOperation, TypeError, ValueError):
            errors.append(("unit_cost", "Unit cost must be a decimal number"))
        else:
            if cost < Decimal("0"):
                errors.append(("unit_cost", "Unit cost must be non-negative"))
        return errors
