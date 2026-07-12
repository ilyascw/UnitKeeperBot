"""initial unitkeeper schema

Revision ID: 20260315_0001
Revises: 20260315_0000
Create Date: 2026-03-15 23:59:00

"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260315_0001"
down_revision: Union[str, Sequence[str], None] = "20260315_0000"
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
balance_transaction_account_type_enum = postgresql.ENUM(
    "user",
    "group_pool",
    name="balance_transaction_account_type_enum",
    create_type=False,
)


LEGACY_TABLES = ("groups", "users", "tasks", "logs", "balances")


def _has_legacy_schema(bind: sa.engine.Connection) -> bool:
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())
    if not set(LEGACY_TABLES).issubset(table_names):
        return False

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    group_columns = {column["name"] for column in inspector.get_columns("groups")}
    task_columns = {column["name"] for column in inspector.get_columns("tasks")}
    return (
        "group_id" in user_columns
        and "password" in group_columns
        and "start_day" in group_columns
        and "frequency" in task_columns
        and "cost" in task_columns
    )


def _rename_legacy_tables(bind: sa.engine.Connection) -> bool:
    if context.is_offline_mode():
        for table_name in LEGACY_TABLES:
            op.rename_table(table_name, f"legacy_{table_name}")
        return True

    if not _has_legacy_schema(bind):
        return False

    for table_name in LEGACY_TABLES:
        op.rename_table(table_name, f"legacy_{table_name}")
    return True


def _migrate_legacy_data() -> None:
    op.execute(
        """
        INSERT INTO users (id, username, first_name, last_name, language_code, is_bot, created_at, updated_at)
        SELECT DISTINCT source.user_id, NULL, NULL, NULL, NULL, false, now(), now()
        FROM (
            SELECT id::bigint AS user_id FROM legacy_users WHERE id IS NOT NULL
            UNION
            SELECT owner_id::bigint AS user_id FROM legacy_groups WHERE owner_id IS NOT NULL
            UNION
            SELECT user_id::bigint AS user_id FROM legacy_logs WHERE user_id IS NOT NULL
            UNION
            SELECT user_id::bigint AS user_id FROM legacy_balances WHERE user_id IS NOT NULL
            UNION
            SELECT (-1000000000000::bigint - id::bigint) AS user_id
            FROM legacy_groups g
            WHERE g.owner_id IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM legacy_users u WHERE u.group_id = g.id
              )
        ) AS source
        WHERE source.user_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO groups (
            id,
            name,
            join_secret,
            owner_user_id,
            sprint_start_weekday,
            sprint_duration_days,
            timezone,
            balance,
            created_at,
            updated_at
        )
        SELECT
            g.id,
            g.name,
            COALESCE(g.password, ''),
            COALESCE(
                g.owner_id::bigint,
                (SELECT MIN(u.id)::bigint FROM legacy_users u WHERE u.group_id = g.id),
                -1000000000000::bigint - g.id::bigint
            ),
            CASE lower(g.start_day)
                WHEN 'понедельник' THEN 'monday'
                WHEN 'monday' THEN 'monday'
                WHEN 'вторник' THEN 'tuesday'
                WHEN 'tuesday' THEN 'tuesday'
                WHEN 'среда' THEN 'wednesday'
                WHEN 'wednesday' THEN 'wednesday'
                WHEN 'четверг' THEN 'thursday'
                WHEN 'thursday' THEN 'thursday'
                WHEN 'пятница' THEN 'friday'
                WHEN 'friday' THEN 'friday'
                WHEN 'суббота' THEN 'saturday'
                WHEN 'saturday' THEN 'saturday'
                WHEN 'воскресенье' THEN 'sunday'
                WHEN 'sunday' THEN 'sunday'
                ELSE 'monday'
            END::weekday_enum,
            CASE
                WHEN g.sprint_duration > 0 AND mod(g.sprint_duration, 7) = 0
                    THEN g.sprint_duration
                ELSE 7
            END,
            'UTC',
            COALESCE(g.group_balance, 0),
            now(),
            now()
        FROM legacy_groups g
        """
    )

    op.execute(
        """
        INSERT INTO group_memberships (id, group_id, user_id, left_at, created_at, updated_at)
        SELECT
            row_number() OVER (ORDER BY u.group_id, u.id),
            u.group_id,
            u.id::bigint,
            NULL,
            now(),
            now()
        FROM legacy_users u
        JOIN groups g ON g.id = u.group_id
        WHERE u.group_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO group_member_weights (id, membership_id, weight_percent, created_at, updated_at)
        SELECT
            row_number() OVER (ORDER BY gm.id),
            gm.id,
            CASE
                WHEN (lg.weights ->> gm.user_id::text) ~ '^-?[0-9]+(\\.[0-9]+)?$'
                    THEN LEAST(100, GREATEST(0, (lg.weights ->> gm.user_id::text)::numeric))::numeric(5, 2)
                ELSE 0
            END,
            now(),
            now()
        FROM group_memberships gm
        JOIN legacy_groups lg ON lg.id = gm.group_id
        """
    )

    op.execute(
        """
        INSERT INTO tasks (
            id,
            group_id,
            title,
            frequency_per_sprint,
            unit_cost,
            deleted_at,
            created_at,
            updated_at
        )
        SELECT
            t.id,
            t.group_id,
            t.title,
            GREATEST(1, COALESCE(round(t.frequency)::integer, 1)),
            COALESCE(t.cost, 0)::numeric(12, 2),
            CASE WHEN COALESCE(t.status, true) THEN NULL ELSE now() END,
            now(),
            now()
        FROM legacy_tasks t
        JOIN groups g ON g.id = t.group_id
        """
    )

    op.execute(
        """
        INSERT INTO task_logs (
            id,
            group_id,
            task_id,
            performer_user_id,
            status,
            approver_user_id,
            decided_at,
            rejection_reason,
            created_at,
            updated_at
        )
        SELECT
            l.id,
            l.group_id,
            l.task_id,
            l.user_id::bigint,
            CASE
                WHEN lower(l.status) = 'completed' THEN 'completed'
                ELSE 'pending'
            END::task_log_status_enum,
            NULL,
            CASE WHEN lower(l.status) = 'completed' THEN l.timestamp ELSE NULL END,
            NULL,
            COALESCE(l.timestamp, now()),
            COALESCE(l.timestamp, now())
        FROM legacy_logs l
        JOIN groups g ON g.id = l.group_id
        JOIN tasks t ON t.id = l.task_id
        JOIN users u ON u.id = l.user_id::bigint
        """
    )

    op.execute(
        """
        INSERT INTO balances (id, group_id, user_id, current_balance, created_at, updated_at)
        SELECT
            MIN(b.id),
            b.group_id,
            b.user_id::bigint,
            COALESCE(MAX(b.balance), 0)::numeric(12, 2),
            now(),
            now()
        FROM legacy_balances b
        JOIN groups g ON g.id = b.group_id
        JOIN users u ON u.id = b.user_id::bigint
        GROUP BY b.group_id, b.user_id
        """
    )

    op.execute(
        """
        INSERT INTO balance_transactions (
            id,
            group_id,
            user_id,
            transaction_type,
            amount_delta,
            counterparty_user_id,
            sprint_run_id,
            task_log_id,
            description,
            created_at,
            updated_at
        )
        SELECT
            row_number() OVER (ORDER BY b.group_id, b.user_id),
            b.group_id,
            b.user_id,
            'manual_adjustment'::balance_transaction_type_enum,
            b.current_balance,
            NULL,
            NULL,
            NULL,
            'Migrated opening balance from legacy bot database',
            now(),
            now()
        FROM balances b
        WHERE b.current_balance <> 0
        """
    )

    for table_name in (
        "groups",
        "group_memberships",
        "group_member_weights",
        "tasks",
        "task_logs",
        "balances",
        "balance_transactions",
        "sprint_runs",
        "sprint_member_results",
    ):
        op.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                (SELECT MAX(id) IS NOT NULL FROM {table_name})
            )
            """
        )

    op.execute(
        """
        DROP TABLE
            legacy_logs,
            legacy_balances,
            legacy_tasks,
            legacy_groups,
            legacy_users
        CASCADE
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    legacy_schema_was_present = _rename_legacy_tables(bind)

    weekday_enum.create(bind, checkfirst=True)
    task_log_status_enum.create(bind, checkfirst=True)
    sprint_run_status_enum.create(bind, checkfirst=True)
    balance_transaction_type_enum.create(bind, checkfirst=True)
    balance_transaction_account_type_enum.create(bind, checkfirst=True)

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
        sa.Column(
            "account_type",
            balance_transaction_account_type_enum,
            nullable=False,
            server_default=sa.text("'user'"),
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("transaction_type", balance_transaction_type_enum, nullable=False),
        sa.Column("amount_delta", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "transaction_group_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("counterparty_user_id", sa.BigInteger(), nullable=True),
        sa.Column("sprint_run_id", sa.Integer(), nullable=True),
        sa.Column("task_log_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_delta <> 0", name=op.f("ck_balance_transactions_balance_transactions_amount_nonzero")),
        sa.CheckConstraint(
            "(account_type = 'user' AND user_id IS NOT NULL) "
            "OR (account_type = 'group_pool' AND user_id IS NULL)",
            name=op.f("ck_balance_transactions_balance_transactions_account_type_user_id"),
        ),
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
    op.create_index(
        "ix_balance_transactions_transaction_group_id",
        "balance_transactions",
        ["transaction_group_id"],
        unique=False,
    )

    if legacy_schema_was_present:
        _migrate_legacy_data()


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
