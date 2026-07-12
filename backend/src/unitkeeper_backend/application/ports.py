from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from db.enums import TaskLogStatus, Weekday
from unitkeeper_backend.application.models import (
    BalanceTransactionInfo,
    GroupInfo,
    MembershipInfo,
    SprintMemberResultInfo,
    SprintRunInfo,
    TaskInfo,
    TaskLogInfo,
    TelegramIdentity,
    UserProfile,
)


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class TelegramInitDataVerifier(Protocol):
    def verify(self, init_data: str) -> TelegramIdentity: ...


class SessionTokenManager(Protocol):
    def issue(self, *, user_id: int, issued_at: datetime) -> tuple[str, datetime]: ...

    def verify(self, token: str) -> int: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> UserProfile | None: ...

    async def list_by_ids(self, user_ids: Sequence[int]) -> list[UserProfile]: ...

    async def upsert_from_telegram(self, identity: TelegramIdentity) -> UserProfile: ...


class GroupRepository(Protocol):
    async def get_by_id(self, group_id: int) -> GroupInfo | None: ...

    async def get_by_name(self, name: str) -> GroupInfo | None: ...

    async def get_active_membership(self, user_id: int) -> MembershipInfo | None: ...

    async def get_active_membership_in_group(self, *, group_id: int, user_id: int) -> MembershipInfo | None: ...

    async def list_active_memberships(self, group_id: int) -> list[MembershipInfo]: ...

    async def create_group(
        self,
        *,
        name: str,
        join_secret: str,
        owner_user_id: int,
        sprint_start_weekday: Weekday,
        sprint_duration_days: int,
        timezone: str,
    ) -> GroupInfo: ...

    async def create_membership(self, *, group_id: int, user_id: int) -> MembershipInfo: ...

    async def ensure_balance(self, *, group_id: int, user_id: int) -> Decimal: ...

    async def set_owner(self, *, group_id: int, owner_user_id: int) -> None: ...

    async def set_group_balance(self, *, group_id: int, balance: Decimal) -> None: ...

    async def deactivate_membership(self, membership_id: int, *, left_at: datetime) -> None: ...

    async def replace_weights(self, *, group_id: int, weights_by_user_id: dict[int, Decimal]) -> None: ...

    async def update_settings(
        self,
        *,
        group_id: int,
        join_secret: str | None,
        sprint_start_weekday: Weekday | None,
        sprint_duration_days: int | None,
    ) -> GroupInfo: ...

    async def list_member_balances(self, group_id: int) -> dict[int, Decimal]: ...

    async def get_balance(self, *, group_id: int, user_id: int) -> Decimal: ...

    async def apply_balance_delta(self, *, group_id: int, user_id: int, amount_delta: Decimal) -> Decimal: ...

    async def transfer_balance(
        self,
        *,
        group_id: int,
        sender_user_id: int,
        recipient_user_id: int,
        amount: Decimal,
    ) -> tuple[Decimal, Decimal]: ...


class TaskRepository(Protocol):
    async def create_task(
        self,
        *,
        group_id: int,
        title: str,
        frequency_per_sprint: int,
        unit_cost: Decimal,
    ) -> TaskInfo: ...

    async def list_tasks(self, *, group_id: int, active_only: bool = True) -> list[TaskInfo]: ...

    async def list_tasks_by_ids(self, *, group_id: int, task_ids: Sequence[int]) -> list[TaskInfo]: ...

    async def get_task(self, *, group_id: int, task_id: int) -> TaskInfo | None: ...

    async def update_task(
        self,
        *,
        group_id: int,
        task_id: int,
        title: str | None,
        frequency_per_sprint: int | None,
        unit_cost: Decimal | None,
    ) -> TaskInfo: ...

    async def soft_delete_task(self, *, group_id: int, task_id: int, deleted_at: datetime) -> None: ...

    async def count_completed_in_window(
        self,
        *,
        task_id: int,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> int: ...

    async def count_pending_in_window(
        self,
        *,
        task_id: int,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> int: ...

    async def lock_task(self, *, group_id: int, task_id: int) -> TaskInfo: ...

    async def create_task_log(
        self,
        *,
        group_id: int,
        task_id: int,
        performer_user_id: int,
        status: object,
        created_at: datetime,
        approver_user_id: int | None = None,
        decided_at: datetime | None = None,
        rejection_reason: str | None = None,
    ) -> TaskLogInfo: ...

    async def get_task_log(self, *, log_id: int) -> TaskLogInfo | None: ...

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
    ) -> Sequence[TaskLogInfo]: ...

    async def count_task_logs(
        self,
        *,
        group_id: int,
        performer_user_id: int | None = None,
        exclude_performer_user_id: int | None = None,
        task_id: int | None = None,
        statuses: Sequence[TaskLogStatus] | None = None,
    ) -> int: ...

    async def approve_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int,
        decided_at: datetime,
    ) -> TaskLogInfo: ...

    async def reject_task_log(
        self,
        *,
        log_id: int,
        approver_user_id: int,
        decided_at: datetime,
        rejection_reason: str,
    ) -> TaskLogInfo: ...

    async def list_completed_logs_in_window(
        self,
        *,
        group_id: int,
        performer_user_id: int | None,
        window_start: datetime,
        window_end_exclusive: datetime,
    ) -> Sequence[TaskLogInfo]: ...


class SprintRepository(Protocol):
    async def get_sprint_run(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
    ) -> SprintRunInfo | None: ...

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
    ) -> SprintRunInfo: ...

    async def add_balance_transaction(
        self,
        *,
        group_id: int,
        user_id: int,
        transaction_type: object,
        amount_delta: Decimal,
        description: str,
        sprint_run_id: int | None = None,
        task_log_id: int | None = None,
        counterparty_user_id: int | None = None,
    ) -> None: ...

    async def list_balance_transactions(
        self,
        *,
        group_id: int,
        user_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[BalanceTransactionInfo], int]: ...


class UnitOfWork(Protocol):
    users: UserRepository
    groups: GroupRepository
    tasks: TaskRepository
    sprints: SprintRepository

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
