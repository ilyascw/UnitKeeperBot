from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from db.enums import TaskLogStatus
from db.models import Task, TaskLog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from unitkeeper_backend.application.models import TaskInfo, TaskLogInfo
from unitkeeper_backend.domain.errors import NotFoundError
from unitkeeper_backend.infrastructure.repositories.mappers import map_task, map_task_log


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_task(
        self,
        *,
        group_id: int,
        title: str,
        frequency_per_sprint: int,
        unit_cost: Decimal,
    ) -> TaskInfo:
        model = Task(
            group_id=group_id,
            title=title,
            frequency_per_sprint=frequency_per_sprint,
            unit_cost=unit_cost,
        )
        self._session.add(model)
        await self._session.flush()
        return map_task(model)

    async def list_tasks(self, *, group_id: int, active_only: bool = True) -> list[TaskInfo]:
        query = select(Task).where(Task.group_id == group_id)
        if active_only:
            query = query.where(Task.deleted_at.is_(None))
        query = query.order_by(Task.title.asc(), Task.id.asc())
        result = await self._session.execute(query)
        return [map_task(item) for item in result.scalars().all()]

    async def list_tasks_by_ids(self, *, group_id: int, task_ids: Sequence[int]) -> list[TaskInfo]:
        if not task_ids:
            return []
        query = select(Task).where(Task.group_id == group_id, Task.id.in_(tuple(task_ids)))
        result = await self._session.execute(query)
        return [map_task(item) for item in result.scalars().all()]

    async def get_task(self, *, group_id: int, task_id: int) -> TaskInfo | None:
        query = select(Task).where(Task.group_id == group_id, Task.id == task_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return map_task(model) if model is not None else None

    async def update_task(
        self,
        *,
        group_id: int,
        task_id: int,
        title: str | None,
        frequency_per_sprint: int | None,
        unit_cost: Decimal | None,
    ) -> TaskInfo:
        model = await self._require_task(group_id=group_id, task_id=task_id)
        if title is not None:
            model.title = title
        if frequency_per_sprint is not None:
            model.frequency_per_sprint = frequency_per_sprint
        if unit_cost is not None:
            model.unit_cost = unit_cost
        await self._session.flush()
        return map_task(model)

    async def soft_delete_task(self, *, group_id: int, task_id: int, deleted_at: datetime) -> None:
        model = await self._require_task(group_id=group_id, task_id=task_id)
        model.deleted_at = deleted_at
        await self._session.flush()

    async def count_completed_in_window(
        self,
        *,
        task_id: int,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> int:
        completed_at = func.coalesce(TaskLog.decided_at, TaskLog.created_at)
        query = select(func.count(TaskLog.id)).where(
            TaskLog.task_id == task_id,
            TaskLog.status == TaskLogStatus.COMPLETED,
            completed_at >= window_start,
            completed_at < window_end_exclusive,
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def count_pending_in_window(
        self,
        *,
        task_id: int,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> int:
        # Pending logs are not yet decided, so they are placed in the window by
        # their creation time.
        query = select(func.count(TaskLog.id)).where(
            TaskLog.task_id == task_id,
            TaskLog.status == TaskLogStatus.PENDING,
            TaskLog.created_at >= window_start,
            TaskLog.created_at < window_end_exclusive,
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def lock_task(self, *, group_id: int, task_id: int) -> TaskInfo:
        # Row-level lock to serialise concurrent completions against the sprint
        # frequency cap. A no-op on backends without SELECT ... FOR UPDATE.
        query = select(Task).where(Task.group_id == group_id, Task.id == task_id).with_for_update()
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Task was not found")
        return map_task(model)

    async def create_task_log(
        self,
        *,
        group_id: int,
        task_id: int,
        performer_user_id: int,
        status: TaskLogStatus,
        created_at: datetime,
        approver_user_id: int | None = None,
        decided_at: datetime | None = None,
        rejection_reason: str | None = None,
    ) -> TaskLogInfo:
        model = TaskLog(
            group_id=group_id,
            task_id=task_id,
            performer_user_id=performer_user_id,
            status=status,
            approver_user_id=approver_user_id,
            decided_at=decided_at,
            rejection_reason=rejection_reason,
            created_at=created_at,
            updated_at=created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return map_task_log(model)

    async def get_task_log(self, *, log_id: int) -> TaskLogInfo | None:
        model = await self._session.get(TaskLog, log_id)
        return map_task_log(model) if model is not None else None

    @staticmethod
    def _task_log_filters(
        *,
        group_id: int,
        performer_user_id: int | None,
        exclude_performer_user_id: int | None,
        task_id: int | None,
        statuses: Sequence[TaskLogStatus] | None,
    ) -> list[ColumnElement[bool]]:
        conditions = [TaskLog.group_id == group_id]
        if performer_user_id is not None:
            conditions.append(TaskLog.performer_user_id == performer_user_id)
        if exclude_performer_user_id is not None:
            conditions.append(TaskLog.performer_user_id != exclude_performer_user_id)
        if task_id is not None:
            conditions.append(TaskLog.task_id == task_id)
        if statuses:
            conditions.append(TaskLog.status.in_(tuple(statuses)))
        return conditions

    async def list_task_logs(
        self,
        *,
        group_id: int,
        performer_user_id: int | None = None,
        exclude_performer_user_id: int | None = None,
        task_id: int | None = None,
        statuses: Sequence[TaskLogStatus] | None = None,
        limit: int,
        offset: int,
    ) -> Sequence[TaskLogInfo]:
        conditions = self._task_log_filters(
            group_id=group_id,
            performer_user_id=performer_user_id,
            exclude_performer_user_id=exclude_performer_user_id,
            task_id=task_id,
            statuses=statuses,
        )
        query = (
            select(TaskLog)
            .where(*conditions)
            .order_by(TaskLog.created_at.desc(), TaskLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        return [map_task_log(item) for item in result.scalars().all()]

    async def count_task_logs(
        self,
        *,
        group_id: int,
        performer_user_id: int | None = None,
        exclude_performer_user_id: int | None = None,
        task_id: int | None = None,
        statuses: Sequence[TaskLogStatus] | None = None,
    ) -> int:
        conditions = self._task_log_filters(
            group_id=group_id,
            performer_user_id=performer_user_id,
            exclude_performer_user_id=exclude_performer_user_id,
            task_id=task_id,
            statuses=statuses,
        )
        query = select(func.count(TaskLog.id)).where(*conditions)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def approve_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int,
        decided_at: datetime,
    ) -> TaskLogInfo:
        model = await self._require_log(log_id)
        model.status = TaskLogStatus.COMPLETED
        model.approver_user_id = approver_user_id
        model.decided_at = decided_at
        await self._session.flush()
        return map_task_log(model)

    async def reject_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int | None,
        decided_at: datetime,
        rejection_reason: str,
    ) -> TaskLogInfo:
        model = await self._require_log(log_id)
        model.status = TaskLogStatus.REJECTED
        model.approver_user_id = approver_user_id
        model.decided_at = decided_at
        model.rejection_reason = rejection_reason
        await self._session.flush()
        return map_task_log(model)

    async def delete_task_log(self, *, log_id: int) -> None:
        model = await self._require_log(log_id)
        await self._session.delete(model)
        await self._session.flush()

    async def list_completed_logs_in_window(
        self,
        *,
        group_id: int,
        performer_user_id: int | None,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> Sequence[TaskLogInfo]:
        completed_at = func.coalesce(TaskLog.decided_at, TaskLog.created_at)
        query = select(TaskLog).where(
            TaskLog.group_id == group_id,
            TaskLog.status == TaskLogStatus.COMPLETED,
            completed_at >= window_start,
            completed_at < window_end_exclusive,
        )
        if performer_user_id is not None:
            query = query.where(TaskLog.performer_user_id == performer_user_id)
        query = query.order_by(TaskLog.id.asc())
        result = await self._session.execute(query)
        return [map_task_log(item) for item in result.scalars().all()]

    async def _require_task(self, *, group_id: int, task_id: int) -> Task:
        query = select(Task).where(Task.group_id == group_id, Task.id == task_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Task was not found")
        return model

    async def _require_log(self, log_id: int) -> TaskLog:
        model = await self._session.get(TaskLog, log_id)
        if model is None:
            raise NotFoundError("Task log was not found")
        return model
