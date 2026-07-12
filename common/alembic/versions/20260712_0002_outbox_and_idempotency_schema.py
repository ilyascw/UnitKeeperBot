"""add outbox and idempotency schema

Revision ID: 20260712_0002
Revises: 20260315_0001
Create Date: 2026-07-12 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260712_0002"
down_revision: Union[str, Sequence[str], None] = "20260315_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notification_event_type_enum = postgresql.ENUM(
    "task_approval_requested",
    "task_approved",
    "task_rejected",
    "sprint_closed",
    "reminder",
    name="notification_event_type_enum",
    create_type=False,
)
notification_outbox_status_enum = postgresql.ENUM(
    "pending",
    "delivered",
    "dead_letter",
    name="notification_outbox_status_enum",
    create_type=False,
)
notification_delivery_attempt_status_enum = postgresql.ENUM(
    "acknowledged",
    "failed",
    name="notification_delivery_attempt_status_enum",
    create_type=False,
)
idempotency_status_enum = postgresql.ENUM(
    "processing",
    "completed",
    "failed",
    name="idempotency_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    notification_event_type_enum.create(bind, checkfirst=True)
    notification_outbox_status_enum.create(bind, checkfirst=True)
    notification_delivery_attempt_status_enum.create(bind, checkfirst=True)
    idempotency_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "notification_outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", notification_event_type_enum, nullable=False),
        sa.Column("recipient_user_id", sa.BigInteger(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("deep_link_path", sa.String(length=512), nullable=True),
        sa.Column("status", notification_outbox_status_enum, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("attempt_count >= 0", name=op.f("ck_notification_outbox_events_attempt_count_nonnegative")),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
            name=op.f("fk_notification_outbox_events_group_id_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"],
            ["users.id"],
            name=op.f("fk_notification_outbox_events_recipient_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification_outbox_events")),
    )
    op.create_index(
        op.f("ix_notification_outbox_events_group_id"),
        "notification_outbox_events",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_outbox_events_pending_delivery",
        "notification_outbox_events",
        ["status", "next_attempt_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "ix_notification_outbox_events_recipient_created_at",
        "notification_outbox_events",
        ["recipient_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_outbox_events_recipient_user_id"),
        "notification_outbox_events",
        ["recipient_user_id"],
        unique=False,
    )

    op.create_table(
        "notification_delivery_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", notification_delivery_attempt_status_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "attempt_number > 0",
            name=op.f("ck_notification_delivery_attempts_attempt_number_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["notification_outbox_events.id"],
            name=op.f("fk_notification_delivery_attempts_event_id_notification_outbox_events"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification_delivery_attempts")),
        sa.UniqueConstraint(
            "event_id",
            "attempt_number",
            name=op.f("uq_notification_delivery_attempts_event_id_attempt_number"),
        ),
    )
    op.create_index(
        "ix_notification_delivery_attempts_event_id_created_at",
        "notification_delivery_attempts",
        ["event_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_delivery_attempts_event_id"),
        "notification_delivery_attempts",
        ["event_id"],
        unique=False,
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(length=128), nullable=False),
        sa.Column("actor_key", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("status", idempotency_status_enum, server_default=sa.text("'processing'"), nullable=False),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_idempotency_keys")),
        sa.UniqueConstraint("scope", "actor_key", "key", name=op.f("uq_idempotency_keys_scope_actor_key_key")),
    )
    op.create_index("ix_idempotency_keys_expires_at", "idempotency_keys", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_expires_at", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_index(op.f("ix_notification_delivery_attempts_event_id"), table_name="notification_delivery_attempts")
    op.drop_index("ix_notification_delivery_attempts_event_id_created_at", table_name="notification_delivery_attempts")
    op.drop_table("notification_delivery_attempts")
    op.drop_index(op.f("ix_notification_outbox_events_recipient_user_id"), table_name="notification_outbox_events")
    op.drop_index("ix_notification_outbox_events_recipient_created_at", table_name="notification_outbox_events")
    op.drop_index("ix_notification_outbox_events_pending_delivery", table_name="notification_outbox_events")
    op.drop_index(op.f("ix_notification_outbox_events_group_id"), table_name="notification_outbox_events")
    op.drop_table("notification_outbox_events")

    bind = op.get_bind()
    idempotency_status_enum.drop(bind, checkfirst=True)
    notification_delivery_attempt_status_enum.drop(bind, checkfirst=True)
    notification_outbox_status_enum.drop(bind, checkfirst=True)
    notification_event_type_enum.drop(bind, checkfirst=True)
