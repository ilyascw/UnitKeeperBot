from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from db.enums import (
    BalanceTransactionType,
    NotificationDeliveryAttemptStatus,
    NotificationEventType,
    NotificationOutboxStatus,
    SprintRunStatus,
    TaskLogStatus,
    Weekday,
)


@dataclass(slots=True)
class UserProfile:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_bot: bool


@dataclass(slots=True)
class MembershipInfo:
    id: int
    group_id: int
    user_id: int
    left_at: datetime | None
    weight_percent: Decimal | None

    @property
    def is_active(self) -> bool:
        return self.left_at is None


@dataclass(slots=True)
class GroupInfo:
    id: int
    name: str
    join_secret: str
    owner_user_id: int
    sprint_start_weekday: Weekday
    sprint_duration_days: int
    timezone: str
    balance: Decimal
    active_members: list[MembershipInfo] = field(default_factory=list)


@dataclass(slots=True)
class CurrentContext:
    user: UserProfile
    membership: MembershipInfo | None
    group: GroupInfo | None


@dataclass(slots=True)
class MemberCardInfo:
    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    weight_percent: Decimal
    balance: Decimal
    is_owner: bool


@dataclass(slots=True)
class GroupCardInfo:
    id: int
    name: str
    owner_user_id: int
    sprint_start_weekday: Weekday
    sprint_duration_days: int
    timezone: str
    group_balance: Decimal
    sprint_period_start: date
    sprint_period_end: date
    sprint_ends_at: datetime
    members: list[MemberCardInfo]
    join_secret: str | None = None


@dataclass(slots=True)
class TaskInfo:
    id: int
    group_id: int
    title: str
    frequency_per_sprint: int
    unit_cost: Decimal
    deleted_at: datetime | None
    completed_in_sprint: int = 0
    pending_in_sprint: int = 0

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None

    @property
    def remaining_in_sprint(self) -> int:
        return max(self.frequency_per_sprint - self.completed_in_sprint, 0)

    @property
    def available_in_sprint(self) -> int:
        """Slots still open to be marked: cap minus confirmed and pending holds."""
        return max(self.frequency_per_sprint - self.completed_in_sprint - self.pending_in_sprint, 0)


@dataclass(slots=True)
class TaskLogInfo:
    id: int
    group_id: int
    task_id: int
    performer_user_id: int
    status: TaskLogStatus
    approver_user_id: int | None
    decided_at: datetime | None
    rejection_reason: str | None
    created_at: datetime


@dataclass(slots=True)
class TaskLogView:
    id: int
    group_id: int
    task_id: int
    task_title: str
    unit_cost: Decimal
    task_is_active: bool
    status: TaskLogStatus
    performer: UserProfile
    approver: UserProfile | None
    decided_at: datetime | None
    rejection_reason: str | None
    created_at: datetime


@dataclass(slots=True)
class TaskLogPage:
    items: list[TaskLogView]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


@dataclass(slots=True)
class BalanceInfo:
    group_id: int
    user_id: int
    current_balance: Decimal


@dataclass(slots=True)
class TransferCandidateInfo:
    user: UserProfile
    current_balance: Decimal


@dataclass(slots=True)
class BalanceTransferInfo:
    group_id: int
    sender_user_id: int
    recipient_user_id: int
    amount: Decimal
    sender_balance: Decimal
    recipient_balance: Decimal


@dataclass(slots=True)
class BalanceTransactionInfo:
    id: int
    group_id: int
    user_id: int
    transaction_type: BalanceTransactionType
    amount_delta: Decimal
    counterparty_user_id: int | None
    description: str | None
    created_at: datetime


@dataclass(slots=True)
class BalanceTransactionPage:
    items: list[BalanceTransactionInfo]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total


@dataclass(slots=True)
class CompletedTaskBreakdownItem:
    task_id: int
    title: str
    completed_count: int
    completed_units: Decimal


@dataclass(slots=True)
class TempResults:
    period_start: date
    period_end: date
    planned_units: Decimal
    completed_units: Decimal
    progress_percent: Decimal
    breakdown: list[CompletedTaskBreakdownItem]


@dataclass(slots=True)
class SprintMemberResultInfo:
    user_id: int
    planned_units: Decimal
    completed_units: Decimal
    efficiency_percent: Decimal
    bonus_units: Decimal
    balance_delta: Decimal
    balance_after: Decimal


@dataclass(slots=True)
class SprintRunInfo:
    id: int
    group_id: int
    period_start: date
    period_end: date
    status: SprintRunStatus
    total_planned_units: Decimal
    total_completed_units: Decimal
    bonus_units: Decimal
    balance_delta: Decimal
    closed_at: datetime | None
    member_results: list[SprintMemberResultInfo] = field(default_factory=list)


@dataclass(slots=True)
class SessionInfo:
    access_token: str
    expires_at: datetime
    context: CurrentContext


@dataclass(slots=True)
class TelegramIdentity:
    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_bot: bool


@dataclass(slots=True)
class NotificationOutboxEventInfo:
    id: UUID
    event_type: NotificationEventType
    recipient_user_id: int
    group_id: int | None
    payload: dict[str, object]
    deep_link_path: str | None
    correlation_id: str | None
    status: NotificationOutboxStatus
    attempt_count: int
    next_attempt_at: datetime | None
    delivered_at: datetime | None
    last_error: str | None
    created_at: datetime


@dataclass(slots=True)
class NotificationDeliveryAttemptInfo:
    event_id: UUID
    attempt_number: int
    status: NotificationDeliveryAttemptStatus
    error_message: str | None
    acknowledged_at: datetime | None
