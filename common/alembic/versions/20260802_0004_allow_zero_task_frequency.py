"""allow zero task frequency

Revision ID: 20260802_0004
Revises: 20260712_0003
Create Date: 2026-08-02 15:10:00

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260802_0004"
down_revision: Union[str, Sequence[str], None] = "20260712_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_tasks_tasks_frequency_positive"),
        "tasks",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_tasks_tasks_frequency_nonnegative"),
        "tasks",
        "frequency_per_sprint >= 0",
    )


def downgrade() -> None:
    op.execute("UPDATE tasks SET frequency_per_sprint = 1 WHERE frequency_per_sprint = 0")
    op.drop_constraint(
        op.f("ck_tasks_tasks_frequency_nonnegative"),
        "tasks",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_tasks_tasks_frequency_positive"),
        "tasks",
        "frequency_per_sprint > 0",
    )
