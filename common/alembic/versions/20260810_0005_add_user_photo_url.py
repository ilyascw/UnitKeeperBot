"""add user photo url

Revision ID: 20260810_0005
Revises: 20260802_0004
Create Date: 2026-08-10 00:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_0005"
down_revision: Union[str, Sequence[str], None] = "20260802_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("photo_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "photo_url")
