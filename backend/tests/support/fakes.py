from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from db.enums import BalanceTransactionType, SprintRunStatus, TaskLogStatus, Weekday
from unitkeeper_backend.application.models import (
    GroupInfo,
    MembershipInfo,
    SprintMemberResultInfo,
    SprintRunInfo,
    TaskInfo,
    TaskLogInfo,
    TelegramIdentity,
    UserProfile,
)


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.date()


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[int, UserProfile] = {}

    async def get_by_id(self, user_id: int) -> UserProfile | None:
        return self.users.get(user_id)

    async def list_by_ids(self, user_ids: Sequence[int]) -> list[UserProfile]:
        return [self.users[user_id] for user_id in user_ids if user_id in self.users]

    async def upsert_from_telegram(self, identity: TelegramIdentity) -> UserProfile:
        profile = UserProfile(
            id=identity.user_id,
            username=identity.username,
            first_name=identity.first_name,
            last_name=identity.last_name,
            language_code=identity.language_code,
            is_bot=identity.is_bot,
        )
        self.users[identity.user_id] = profile
        return profile


class InMemoryGroupRepository:
    def __init__(self) -> None:
        self.groups: dict[int, GroupInfo] = {}
        self.memberships: dict[int, MembershipInfo] = {}
        self.balances: dict[tuple[int, int], Decimal] = {}
        self._group_seq = 1
        self._membership_seq = 1

    async def get_by_id(self, group_id: int) -> GroupInfo | None:
        group = self.groups.get(group_id)
        if group is None:
            return None
        return replace(group, active_members=await self.list_active_memberships(group_id))

    async def get_by_name(self, name: str) -> GroupInfo | None:
        for group in self.groups.values():
            if group.name == name:
                return await self.get_by_id(group.id)
        return None

    async def get_active_membership(self, user_id: int) -> MembershipInfo | None:
        for membership in self.memberships.values():
            if membership.user_id == user_id and membership.left_at is None:
                return membership
        return None

    async def get_active_membership_in_group(self, *, group_id: int, user_id: int) -> MembershipInfo | None:
        for membership in self.memberships.values():
            if membership.group_id == group_id and membership.user_id == user_id and membership.left_at is None:
                return membership
        return None

    async def list_active_memberships(self, group_id: int) -> list[MembershipInfo]:
        return [
            membership
            for membership in self.memberships.values()
            if membership.group_id == group_id and membership.left_at is None
        ]

    async def create_group(
        self,
        *,
        name: str,
        join_secret: str,
        owner_user_id: int,
        sprint_start_weekday: Weekday,
        sprint_duration_days: int,
        timezone: str,
    ) -> GroupInfo:
        group = GroupInfo(
            id=self._group_seq,
            name=name,
            join_secret=join_secret,
            owner_user_id=owner_user_id,
            sprint_start_weekday=sprint_start_weekday,
            sprint_duration_days=sprint_duration_days,
            timezone=timezone,
            balance=Decimal("0.00"),
            active_members=[],
        )
        self.groups[group.id] = group
        self._group_seq += 1
        return group

    async def create_membership(self, *, group_id: int, user_id: int) -> MembershipInfo:
        membership = MembershipInfo(
            id=self._membership_seq,
            group_id=group_id,
            user_id=user_id,
            left_at=None,
            weight_percent=None,
        )
        self.memberships[membership.id] = membership
        self._membership_seq += 1
        return membership

    async def ensure_balance(self, *, group_id: int, user_id: int) -> Decimal:
        self.balances.setdefault((group_id, user_id), Decimal("0.00"))
        return self.balances[(group_id, user_id)]

    async def set_owner(self, *, group_id: int, owner_user_id: int) -> None:
        group = self.groups[group_id]
        self.groups[group_id] = replace(group, owner_user_id=owner_user_id)

    async def set_group_balance(self, *, group_id: int, balance: Decimal) -> None:
        group = self.groups[group_id]
        self.groups[group_id] = replace(group, balance=balance)

    async def deactivate_membership(self, membership_id: int, *, left_at: datetime) -> None:
        membership = self.memberships[membership_id]
        self.memberships[membership_id] = replace(membership, left_at=left_at)

    async def update_settings(
        self,
        *,
        group_id: int,
        join_secret: str | None,
        sprint_start_weekday: Weekday | None = None,
        sprint_duration_days: int | None = None,
    ) -> GroupInfo:
        group = self.groups[group_id]
        updated = replace(
            group,
            join_secret=join_secret if join_secret is not None else group.join_secret,
            sprint_start_weekday=sprint_start_weekday if sprint_start_weekday is not None else group.sprint_start_weekday,
            sprint_duration_days=sprint_duration_days if sprint_duration_days is not None else group.sprint_duration_days,
        )
        self.groups[group_id] = updated
        return await self.get_by_id(group_id)  # type: ignore[return-value]

    async def list_member_balances(self, group_id: int) -> dict[int, Decimal]:
        return {
            user_id: balance
            for (gid, user_id), balance in self.balances.items()
            if gid == group_id
        }

    async def replace_weights(self, *, group_id: int, weights_by_user_id: dict[int, Decimal]) -> None:
        for membership_id, membership in list(self.memberships.items()):
            if membership.group_id != group_id or membership.left_at is not None:
                continue
            weight = weights_by_user_id.get(membership.user_id)
            self.memberships[membership_id] = replace(membership, weight_percent=weight)

    async def get_balance(self, *, group_id: int, user_id: int) -> Decimal:
        return self.balances[(group_id, user_id)]

    async def apply_balance_delta(self, *, group_id: int, user_id: int, amount_delta: Decimal) -> Decimal:
        current = self.balances.get((group_id, user_id), Decimal("0.00"))
        updated = current + amount_delta
        self.balances[(group_id, user_id)] = updated
        return updated


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[int, TaskInfo] = {}
        self.logs: dict[int, TaskLogInfo] = {}
        self._task_seq = 1
        self._log_seq = 1

    async def create_task(
        self,
        *,
        group_id: int,
        title: str,
        frequency_per_sprint: int,
        unit_cost: Decimal,
    ) -> TaskInfo:
        task = TaskInfo(
            id=self._task_seq,
            group_id=group_id,
            title=title,
            frequency_per_sprint=frequency_per_sprint,
            unit_cost=unit_cost,
            deleted_at=None,
        )
        self.tasks[task.id] = task
        self._task_seq += 1
        return task

    async def list_tasks(self, *, group_id: int, active_only: bool = True) -> list[TaskInfo]:
        return [
            task
            for task in self.tasks.values()
            if task.group_id == group_id and (not active_only or task.deleted_at is None)
        ]

    async def get_task(self, *, group_id: int, task_id: int) -> TaskInfo | None:
        task = self.tasks.get(task_id)
        if task is None or task.group_id != group_id:
            return None
        return task

    async def update_task(
        self,
        *,
        group_id: int,
        task_id: int,
        title: str | None,
        frequency_per_sprint: int | None,
        unit_cost: Decimal | None,
    ) -> TaskInfo:
        task = self.tasks[task_id]
        updated = replace(
            task,
            title=title if title is not None else task.title,
            frequency_per_sprint=frequency_per_sprint if frequency_per_sprint is not None else task.frequency_per_sprint,
            unit_cost=unit_cost if unit_cost is not None else task.unit_cost,
        )
        self.tasks[task_id] = updated
        return updated

    async def soft_delete_task(self, *, group_id: int, task_id: int, deleted_at: datetime) -> None:
        task = self.tasks[task_id]
        self.tasks[task_id] = replace(task, deleted_at=deleted_at)

    async def count_completed_in_window(
        self,
        *,
        task_id: int,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> int:
        return len(
            [
                log
                for log in self.logs.values()
                if log.task_id == task_id
                and log.status is TaskLogStatus.COMPLETED
                and window_start <= (log.decided_at or log.created_at) < window_end_exclusive
            ]
        )

    async def create_task_log(
        self,
        *,
        group_id: int,
        task_id: int,
        performer_user_id: int,
        status,
        created_at: datetime,
        approver_user_id: int | None = None,
        decided_at: datetime | None = None,
        rejection_reason: str | None = None,
    ) -> TaskLogInfo:
        log = TaskLogInfo(
            id=self._log_seq,
            group_id=group_id,
            task_id=task_id,
            performer_user_id=performer_user_id,
            status=status,
            approver_user_id=approver_user_id,
            decided_at=decided_at,
            rejection_reason=rejection_reason,
            created_at=created_at,
        )
        self.logs[log.id] = log
        self._log_seq += 1
        return log

    async def get_task_log(self, *, log_id: int) -> TaskLogInfo | None:
        return self.logs.get(log_id)

    async def approve_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int,
        decided_at: datetime,
    ) -> TaskLogInfo:
        log = self.logs[log_id]
        updated = replace(
            log,
            status=TaskLogStatus.COMPLETED,
            approver_user_id=approver_user_id,
            decided_at=decided_at,
        )
        self.logs[log_id] = updated
        return updated

    async def reject_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int,
        decided_at: datetime,
        rejection_reason: str,
    ) -> TaskLogInfo:
        log = self.logs[log_id]
        updated = replace(
            log,
            status=TaskLogStatus.REJECTED,
            approver_user_id=approver_user_id,
            decided_at=decided_at,
            rejection_reason=rejection_reason,
        )
        self.logs[log_id] = updated
        return updated

    async def list_completed_logs_in_window(
        self,
        *,
        group_id: int,
        performer_user_id: int | None,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> Sequence[TaskLogInfo]:
        return [
            log
            for log in self.logs.values()
            if log.group_id == group_id
            and log.status is TaskLogStatus.COMPLETED
            and (performer_user_id is None or log.performer_user_id == performer_user_id)
            and window_start <= (log.decided_at or log.created_at) < window_end_exclusive
        ]


class InMemorySprintRepository:
    def __init__(self) -> None:
        self.sprint_runs: dict[tuple[int, date, date], SprintRunInfo] = {}
        self.transactions: list[tuple[int, int, BalanceTransactionType, Decimal, int | None]] = []
        self._seq = 1

    async def get_sprint_run(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
    ) -> SprintRunInfo | None:
        return self.sprint_runs.get((group_id, period_start, period_end))

    async def create_sprint_run(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
        total_planned_units: Decimal,
        total_completed_units: Decimal,
        bonus_units: Decimal,
        balance_delta: Decimal,
        closed_at: datetime,
        member_results: list[SprintMemberResultInfo],
    ) -> SprintRunInfo:
        run = SprintRunInfo(
            id=self._seq,
            group_id=group_id,
            period_start=period_start,
            period_end=period_end,
            status=SprintRunStatus.CLOSED,
            total_planned_units=total_planned_units,
            total_completed_units=total_completed_units,
            bonus_units=bonus_units,
            balance_delta=balance_delta,
            closed_at=closed_at,
            member_results=member_results,
        )
        self.sprint_runs[(group_id, period_start, period_end)] = run
        self._seq += 1
        return run

    async def add_balance_transaction(
        self,
        *,
        group_id: int,
        user_id: int,
        transaction_type,
        amount_delta: Decimal,
        description: str,
        sprint_run_id: int | None = None,
        task_log_id: int | None = None,
        counterparty_user_id: int | None = None,
    ) -> None:
        self.transactions.append((group_id, user_id, transaction_type, amount_delta, sprint_run_id))


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.users = InMemoryUserRepository()
        self.groups = InMemoryGroupRepository()
        self.tasks = InMemoryTaskRepository()
        self.sprints = InMemorySprintRepository()
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        return None


def utc_datetime(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=timezone.utc)
