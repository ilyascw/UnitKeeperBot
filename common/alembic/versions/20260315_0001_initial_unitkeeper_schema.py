"""initial unitkeeper schema

Revision ID: 20260315_0001
Revises:
Create Date: 2026-03-15 23:59:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260315_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


weekday_enum = postgresql.ENUM(
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    name="weekday_enum",
    create_type=False,
)
task_log_status_enum = postgresql.ENUM(
    "pending",
    "completed",
    "rejected",
    name="task_log_status_enum",
    create_type=False,
)
sprint_run_status_enum = postgresql.ENUM(
    "open",
    "closed",
    name="sprint_run_status_enum",
    create_type=False,
)
balance_transaction_type_enum = postgresql.ENUM(
    "transfer",
    "sprint_settlement",
    "sprint_bonus",
    "manual_adjustment",
    name="balance_transaction_type_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    weekday_enum.create(bind, checkfirst=True)
    task_log_status_enum.create(bind, checkfirst=True)
    sprint_run_status_enum.create(bind, checkfirst=True)
    balance_transaction_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("is_bot", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("join_secret", sa.String(length=255), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("sprint_start_weekday", weekday_enum, nullable=False),
        sa.Column("sprint_duration_days", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=64), server_default=sa.text("'UTC'"), nullable=False),
        sa.Column("balance", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("mod(sprint_duration_days, 7) = 0", name=op.f("ck_groups_groups_sprint_duration_multiple_of_7")),
        sa.CheckConstraint("sprint_duration_days > 0", name=op.f("ck_groups_groups_sprint_duration_positive")),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name=op.f("fk_groups_owner_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_groups")),
        sa.UniqueConstraint("name", name=op.f("uq_groups_name")),
    )
    op.create_index(op.f("ix_groups_owner_user_id"), "groups", ["owner_user_id"], unique=False)

    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_group_memberships_group_id_groups"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_group_memberships_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_memberships")),
    )
    op.create_index(op.f("ix_group_memberships_group_id"), "group_memberships", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_memberships_user_id"), "group_memberships", ["user_id"], unique=False)
    op.create_index(
        "ix_group_memberships_active_user",
        "group_memberships",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("left_at IS NULL"),
    )
    op.create_index(
        "ix_group_memberships_active_group_user",
        "group_memberships",
        ["group_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("left_at IS NULL"),
    )

    op.create_table(
        "group_member_weights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("weight_percent", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "weight_percent >= 0 AND weight_percent <= 100",
            name=op.f("ck_group_member_weights_group_member_weights_percent_range"),
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["group_memberships.id"],
            name=op.f("fk_group_member_weights_membership_id_group_memberships"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group_member_weights")),
        sa.UniqueConstraint("membership_id", name=op.f("uq_group_member_weights_membership_id")),
    )
    op.create_index(op.f("ix_group_member_weights_membership_id"), "group_member_weights", ["membership_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("frequency_per_sprint", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("frequency_per_sprint > 0", name=op.f("ck_tasks_tasks_frequency_positive")),
        sa.CheckConstraint("unit_cost >= 0", name=op.f("ck_tasks_tasks_unit_cost_nonnegative")),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_tasks_group_id_groups"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(op.f("ix_tasks_group_id"), "tasks", ["group_id"], unique=False)
    op.create_index(
        "ix_tasks_group_active",
        "tasks",
        ["group_id"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("current_balance", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_balances_group_id_groups"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_balances_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_balances")),
        sa.UniqueConstraint("group_id", "user_id", name=op.f("uq_balances_group_id_user_id")),
    )
    op.create_index(op.f("ix_balances_group_id"), "balances", ["group_id"], unique=False)
    op.create_index(op.f("ix_balances_user_id"), "balances", ["user_id"], unique=False)

    op.create_table(
        "sprint_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sprint_run_status_enum, server_default=sa.text("'open'"), nullable=False),
        sa.Column("total_planned_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("total_completed_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("bonus_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("balance_delta", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("period_end >= period_start", name=op.f("ck_sprint_runs_sprint_runs_period_bounds")),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_sprint_runs_group_id_groups"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sprint_runs")),
        sa.UniqueConstraint("group_id", "period_start", "period_end", name=op.f("uq_sprint_runs_group_id_period_start_period_end")),
    )
    op.create_index(op.f("ix_sprint_runs_group_id"), "sprint_runs", ["group_id"], unique=False)

    op.create_table(
        "task_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("performer_user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", task_log_status_enum, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("approver_user_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name=op.f("ck_task_logs_task_logs_rejection_reason_required"),
        ),
        sa.ForeignKeyConstraint(["approver_user_id"], ["users.id"], name=op.f("fk_task_logs_approver_user_id_users")),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_task_logs_group_id_groups"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performer_user_id"], ["users.id"], name=op.f("fk_task_logs_performer_user_id_users")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], name=op.f("fk_task_logs_task_id_tasks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_logs")),
    )
    op.create_index(op.f("ix_task_logs_group_id"), "task_logs", ["group_id"], unique=False)
    op.create_index(op.f("ix_task_logs_performer_user_id"), "task_logs", ["performer_user_id"], unique=False)
    op.create_index(op.f("ix_task_logs_task_id"), "task_logs", ["task_id"], unique=False)
    op.create_index(
        "ix_task_logs_group_status_created_at",
        "task_logs",
        ["group_id", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_task_logs_task_performer_created_at",
        "task_logs",
        ["task_id", "performer_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "sprint_member_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sprint_run_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("planned_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("completed_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("efficiency_percent", sa.Numeric(precision=7, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("bonus_units", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("balance_delta", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sprint_run_id"], ["sprint_runs.id"], name=op.f("fk_sprint_member_results_sprint_run_id_sprint_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sprint_member_results_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sprint_member_results")),
        sa.UniqueConstraint("sprint_run_id", "user_id", name=op.f("uq_sprint_member_results_sprint_run_id_user_id")),
    )
    op.create_index(op.f("ix_sprint_member_results_sprint_run_id"), "sprint_member_results", ["sprint_run_id"], unique=False)
    op.create_index(op.f("ix_sprint_member_results_user_id"), "sprint_member_results", ["user_id"], unique=False)

    op.create_table(
        "balance_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_type", balance_transaction_type_enum, nullable=False),
        sa.Column("amount_delta", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("counterparty_user_id", sa.BigInteger(), nullable=True),
        sa.Column("sprint_run_id", sa.Integer(), nullable=True),
        sa.Column("task_log_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_delta <> 0", name=op.f("ck_balance_transactions_balance_transactions_amount_nonzero")),
        sa.ForeignKeyConstraint(["counterparty_user_id"], ["users.id"], name=op.f("fk_balance_transactions_counterparty_user_id_users")),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], name=op.f("fk_balance_transactions_group_id_groups"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sprint_run_id"], ["sprint_runs.id"], name=op.f("fk_balance_transactions_sprint_run_id_sprint_runs"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_log_id"], ["task_logs.id"], name=op.f("fk_balance_transactions_task_log_id_task_logs"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_balance_transactions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_balance_transactions")),
    )
    op.create_index(op.f("ix_balance_transactions_group_id"), "balance_transactions", ["group_id"], unique=False)
    op.create_index(op.f("ix_balance_transactions_user_id"), "balance_transactions", ["user_id"], unique=False)
    op.create_index(
        "ix_balance_transactions_group_user_created_at",
        "balance_transactions",
        ["group_id", "user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_balance_transactions_group_user_created_at", table_name="balance_transactions")
    op.drop_index(op.f("ix_balance_transactions_user_id"), table_name="balance_transactions")
    op.drop_index(op.f("ix_balance_transactions_group_id"), table_name="balance_transactions")
    op.drop_table("balance_transactions")

    op.drop_index(op.f("ix_sprint_member_results_user_id"), table_name="sprint_member_results")
    op.drop_index(op.f("ix_sprint_member_results_sprint_run_id"), table_name="sprint_member_results")
    op.drop_table("sprint_member_results")

    op.drop_index("ix_task_logs_task_performer_created_at", table_name="task_logs")
    op.drop_index("ix_task_logs_group_status_created_at", table_name="task_logs")
    op.drop_index(op.f("ix_task_logs_task_id"), table_name="task_logs")
    op.drop_index(op.f("ix_task_logs_performer_user_id"), table_name="task_logs")
    op.drop_index(op.f("ix_task_logs_group_id"), table_name="task_logs")
    op.drop_table("task_logs")

    op.drop_index(op.f("ix_sprint_runs_group_id"), table_name="sprint_runs")
    op.drop_table("sprint_runs")

    op.drop_index(op.f("ix_balances_user_id"), table_name="balances")
    op.drop_index(op.f("ix_balances_group_id"), table_name="balances")
    op.drop_table("balances")

    op.drop_index("ix_tasks_group_active", table_name="tasks")
    op.drop_index(op.f("ix_tasks_group_id"), table_name="tasks")
    op.drop_table("tasks")

    op.drop_index(op.f("ix_group_member_weights_membership_id"), table_name="group_member_weights")
    op.drop_table("group_member_weights")

    op.drop_index("ix_group_memberships_active_group_user", table_name="group_memberships")
    op.drop_index("ix_group_memberships_active_user", table_name="group_memberships")
    op.drop_index(op.f("ix_group_memberships_user_id"), table_name="group_memberships")
    op.drop_index(op.f("ix_group_memberships_group_id"), table_name="group_memberships")
    op.drop_table("group_memberships")

    op.drop_index(op.f("ix_groups_owner_user_id"), table_name="groups")
    op.drop_table("groups")

    op.drop_table("users")

    bind = op.get_bind()
    balance_transaction_type_enum.drop(bind, checkfirst=True)
    sprint_run_status_enum.drop(bind, checkfirst=True)
    task_log_status_enum.drop(bind, checkfirst=True)
    weekday_enum.drop(bind, checkfirst=True)
