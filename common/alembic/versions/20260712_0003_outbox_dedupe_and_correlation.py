"""add outbox dedupe and correlation fields

Revision ID: 20260712_0003
Revises: 20260712_0002
Create Date: 2026-07-12 00:10:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260712_0003"
down_revision: Union[str, Sequence[str], None] = "20260712_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notification_outbox_events", sa.Column("dedupe_key", sa.String(length=255), nullable=True))
    op.add_column("notification_outbox_events", sa.Column("correlation_id", sa.String(length=128), nullable=True))
    op.create_unique_constraint(
        op.f("uq_notification_outbox_events_dedupe_key"),
        "notification_outbox_events",
        ["dedupe_key"],
    )
    op.create_index(
        op.f("ix_notification_outbox_events_correlation_id"),
        "notification_outbox_events",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_outbox_events_correlation_id"), table_name="notification_outbox_events")
    op.drop_constraint(op.f("uq_notification_outbox_events_dedupe_key"), "notification_outbox_events", type_="unique")
    op.drop_column("notification_outbox_events", "correlation_id")
    op.drop_column("notification_outbox_events", "dedupe_key")
