from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from db.enums import (
    BalanceTransactionAccountType,
    BalanceTransactionType,
    IdempotencyStatus,
    NotificationDeliveryAttemptStatus,
    NotificationEventType,
    NotificationOutboxStatus,
    SprintRunStatus,
    TaskLogStatus,
    Weekday,
)
from db.types import pg_enum


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))
    is_bot: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    owned_groups: Mapped[list["Group"]] = relationship(
        back_populates="owner",
        foreign_keys="Group.owner_user_id",
    )
    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    balances: Mapped[list["Balance"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    performed_task_logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="performer",
        foreign_keys="TaskLog.performer_user_id",
    )
    approved_task_logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="approver",
        foreign_keys="TaskLog.approver_user_id",
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="user",
        foreign_keys="BalanceTransaction.user_id",
    )
    transfer_counterparty_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="counterparty_user",
        foreign_keys="BalanceTransaction.counterparty_user_id",
    )
    sprint_results: Mapped[list["SprintMemberResult"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_events: Mapped[list["NotificationOutboxEvent"]] = relationship(
        back_populates="recipient",
        cascade="all, delete-orphan",
    )


class Group(TimestampMixin, Base):
    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint(
            "sprint_duration_days > 0",
            name="groups_sprint_duration_positive",
        ),
        CheckConstraint(
            "mod(sprint_duration_days, 7) = 0",
            name="groups_sprint_duration_multiple_of_7",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    join_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    sprint_start_weekday: Mapped[Weekday] = mapped_column(
        pg_enum(Weekday, name="weekday_enum"),
        nullable=False,
    )
    sprint_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
        server_default=text("'UTC'"),
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    owner: Mapped["User"] = relationship(
        back_populates="owned_groups",
        foreign_keys=[owner_user_id],
    )
    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    task_logs: Mapped[list["TaskLog"]] = relationship(back_populates="group")
    balances: Mapped[list["Balance"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    sprint_runs: Mapped[list["SprintRun"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    notification_events: Mapped[list["NotificationOutboxEvent"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class GroupMembership(TimestampMixin, Base):
    __tablename__ = "group_memberships"
    __table_args__ = (
        Index(
            "ix_group_memberships_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("left_at IS NULL"),
        ),
        Index(
            "ix_group_memberships_active_group_user",
            "group_id",
            "user_id",
            unique=True,
            postgresql_where=text("left_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")
    weight: Mapped["GroupMemberWeight | None"] = relationship(
        back_populates="membership",
        cascade="all, delete-orphan",
        uselist=False,
    )


class GroupMemberWeight(TimestampMixin, Base):
    __tablename__ = "group_member_weights"
    __table_args__ = (
        UniqueConstraint("membership_id"),
        CheckConstraint(
            "weight_percent >= 0 AND weight_percent <= 100",
            name="group_member_weights_percent_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("group_memberships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    membership: Mapped["GroupMembership"] = relationship(back_populates="weight")


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "frequency_per_sprint >= 0",
            name="tasks_frequency_nonnegative",
        ),
        CheckConstraint("unit_cost >= 0", name="tasks_unit_cost_nonnegative"),
        Index(
            "ix_tasks_group_active",
            "group_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency_per_sprint: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="tasks")
    logs: Mapped[list["TaskLog"]] = relationship(back_populates="task")


class TaskLog(TimestampMixin, Base):
    __tablename__ = "task_logs"
    __table_args__ = (
        CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name="task_logs_rejection_reason_required",
        ),
        Index(
            "ix_task_logs_group_status_created_at",
            "group_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_task_logs_task_performer_created_at",
            "task_id",
            "performer_user_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    performer_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[TaskLogStatus] = mapped_column(
        pg_enum(TaskLogStatus, name="task_log_status_enum"),
        nullable=False,
        default=TaskLogStatus.PENDING,
        server_default=text("'pending'"),
    )
    approver_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    group: Mapped["Group"] = relationship(back_populates="task_logs")
    task: Mapped["Task"] = relationship(back_populates="logs")
    performer: Mapped["User"] = relationship(
        back_populates="performed_task_logs",
        foreign_keys=[performer_user_id],
    )
    approver: Mapped["User | None"] = relationship(
        back_populates="approved_task_logs",
        foreign_keys=[approver_user_id],
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="task_log",
    )


class Balance(TimestampMixin, Base):
    __tablename__ = "balances"
    __table_args__ = (UniqueConstraint("group_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    group: Mapped["Group"] = relationship(back_populates="balances")
    user: Mapped["User"] = relationship(back_populates="balances")


class SprintRun(TimestampMixin, Base):
    __tablename__ = "sprint_runs"
    __table_args__ = (
        UniqueConstraint("group_id", "period_start", "period_end"),
        CheckConstraint(
            "period_end >= period_start",
            name="sprint_runs_period_bounds",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SprintRunStatus] = mapped_column(
        pg_enum(SprintRunStatus, name="sprint_run_status_enum"),
        nullable=False,
        default=SprintRunStatus.OPEN,
        server_default=text("'open'"),
    )
    total_planned_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    total_completed_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    bonus_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    balance_delta: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped["Group"] = relationship(back_populates="sprint_runs")
    member_results: Mapped[list["SprintMemberResult"]] = relationship(
        back_populates="sprint_run",
        cascade="all, delete-orphan",
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="sprint_run",
    )


class SprintMemberResult(TimestampMixin, Base):
    __tablename__ = "sprint_member_results"
    __table_args__ = (UniqueConstraint("sprint_run_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sprint_run_id: Mapped[int] = mapped_column(
        ForeignKey("sprint_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    planned_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    completed_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    efficiency_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    bonus_units: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    balance_delta: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )

    sprint_run: Mapped["SprintRun"] = relationship(back_populates="member_results")
    user: Mapped["User"] = relationship(back_populates="sprint_results")


class BalanceTransaction(TimestampMixin, Base):
    """One leg of a double-entry ledger posting.

    Every logical operation (transfer, sprint settlement, manual
    adjustment) is recorded as a set of rows sharing the same
    ``transaction_group_id`` whose ``amount_delta`` values sum to zero.
    Transfers post two USER legs (sender/recipient); sprint settlements
    post one GROUP_POOL leg (the pool funding the payout) plus one USER
    leg per member.
    """

    __tablename__ = "balance_transactions"
    __table_args__ = (
        CheckConstraint("amount_delta <> 0", name="balance_transactions_amount_nonzero"),
        CheckConstraint(
            "(account_type = 'user' AND user_id IS NOT NULL) OR (account_type = 'group_pool' AND user_id IS NULL)",
            name="balance_transactions_account_type_user_id",
        ),
        Index(
            "ix_balance_transactions_group_user_created_at",
            "group_id",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_balance_transactions_transaction_group_id",
            "transaction_group_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_type: Mapped[BalanceTransactionAccountType] = mapped_column(
        pg_enum(BalanceTransactionAccountType, name="balance_transaction_account_type_enum"),
        nullable=False,
        default=BalanceTransactionAccountType.USER,
        server_default=text("'user'"),
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    transaction_type: Mapped[BalanceTransactionType] = mapped_column(
        pg_enum(BalanceTransactionType, name="balance_transaction_type_enum"),
        nullable=False,
    )
    amount_delta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_group_id: Mapped[UUID] = mapped_column(
        nullable=False,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    counterparty_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
    )
    sprint_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("sprint_runs.id", ondelete="SET NULL"),
    )
    task_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_logs.id", ondelete="SET NULL"),
    )
    description: Mapped[str | None] = mapped_column(Text)

    group: Mapped["Group"] = relationship(back_populates="balance_transactions")
    user: Mapped["User"] = relationship(
        back_populates="balance_transactions",
        foreign_keys=[user_id],
    )
    counterparty_user: Mapped["User | None"] = relationship(
        back_populates="transfer_counterparty_transactions",
        foreign_keys=[counterparty_user_id],
    )
    sprint_run: Mapped["SprintRun | None"] = relationship(
        back_populates="balance_transactions",
    )
    task_log: Mapped["TaskLog | None"] = relationship(
        back_populates="balance_transactions",
    )


class NotificationOutboxEvent(TimestampMixin, Base):
    __tablename__ = "notification_outbox_events"
    __table_args__ = (
        UniqueConstraint("dedupe_key"),
        Index(
            "ix_notification_outbox_events_pending_delivery",
            "status",
            "next_attempt_at",
            "created_at",
            postgresql_where=text("status = 'pending'"),
        ),
        Index(
            "ix_notification_outbox_events_recipient_created_at",
            "recipient_user_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_type: Mapped[NotificationEventType] = mapped_column(
        pg_enum(NotificationEventType, name="notification_event_type_enum"),
        nullable=False,
    )
    recipient_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        index=True,
    )
    payload: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    deep_link_path: Mapped[str | None] = mapped_column(String(512))
    dedupe_key: Mapped[str | None] = mapped_column(String(255))
    correlation_id: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[NotificationOutboxStatus] = mapped_column(
        pg_enum(NotificationOutboxStatus, name="notification_outbox_status_enum"),
        nullable=False,
        default=NotificationOutboxStatus.PENDING,
        server_default=text("'pending'"),
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    recipient: Mapped["User"] = relationship(back_populates="notification_events")
    group: Mapped["Group | None"] = relationship(back_populates="notification_events")
    delivery_attempts: Mapped[list["NotificationDeliveryAttempt"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class NotificationDeliveryAttempt(Base):
    __tablename__ = "notification_delivery_attempts"
    __table_args__ = (
        UniqueConstraint("event_id", "attempt_number"),
        CheckConstraint(
            "attempt_number > 0",
            name="notification_delivery_attempts_attempt_number_positive",
        ),
        Index("ix_notification_delivery_attempts_event_id_created_at", "event_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("notification_outbox_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[NotificationDeliveryAttemptStatus] = mapped_column(
        pg_enum(
            NotificationDeliveryAttemptStatus,
            name="notification_delivery_attempt_status_enum",
        ),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["NotificationOutboxEvent"] = relationship(back_populates="delivery_attempts")


class IdempotencyKey(TimestampMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("scope", "actor_key", "key"),
        Index("ix_idempotency_keys_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_key: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[IdempotencyStatus] = mapped_column(
        pg_enum(IdempotencyStatus, name="idempotency_status_enum"),
        nullable=False,
        default=IdempotencyStatus.PROCESSING,
        server_default=text("'processing'"),
    )
    response_status_code: Mapped[int | None] = mapped_column(Integer)
    response_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = [
    "Balance",
    "BalanceTransaction",
    "Group",
    "GroupMemberWeight",
    "GroupMembership",
    "IdempotencyKey",
    "NotificationDeliveryAttempt",
    "NotificationOutboxEvent",
    "SprintMemberResult",
    "SprintRun",
    "Task",
    "TaskLog",
    "User",
]
