"""legacy bot schema baseline

Revision ID: 20260315_0000
Revises:
Create Date: 2026-03-15 23:58:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260315_0000"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("start_day", sa.String(), nullable=False),
        sa.Column("sprint_duration", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("group_balance", sa.Numeric(), nullable=True),
        sa.Column("weights", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="legacy_pk_groups"),
        sa.UniqueConstraint("name", name="legacy_uq_groups_name"),
    )
    op.create_index("legacy_ix_groups_id", "groups", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="legacy_fk_users_group_id_groups"),
        sa.PrimaryKeyConstraint("id", name="legacy_pk_users"),
    )
    op.create_index("legacy_ix_users_id", "users", ["id"], unique=False)

    op.create_foreign_key(
        "legacy_fk_groups_owner_id_users",
        "groups",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("frequency", sa.Numeric(), nullable=False),
        sa.Column("cost", sa.Numeric(), nullable=False),
        sa.Column("status", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="legacy_fk_tasks_group_id_groups"),
        sa.PrimaryKeyConstraint("id", name="legacy_pk_tasks"),
    )
    op.create_index("legacy_ix_tasks_id", "tasks", ["id"], unique=False)

    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="legacy_fk_logs_group_id_groups"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name="legacy_fk_logs_task_id_tasks"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="legacy_fk_logs_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="legacy_pk_logs"),
    )
    op.create_index("legacy_ix_logs_id", "logs", ["id"], unique=False)

    op.create_table(
        "balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name="legacy_fk_balances_group_id_groups"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="legacy_fk_balances_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="legacy_pk_balances"),
    )
    op.create_index("legacy_ix_balances_id", "balances", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("legacy_ix_balances_id", table_name="balances")
    op.drop_table("balances")

    op.drop_index("legacy_ix_logs_id", table_name="logs")
    op.drop_table("logs")

    op.drop_index("legacy_ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_constraint("legacy_fk_groups_owner_id_users", "groups", type_="foreignkey")

    op.drop_index("legacy_ix_users_id", table_name="users")
    op.drop_table("users")

    op.drop_index("legacy_ix_groups_id", table_name="groups")
    op.drop_table("groups")
