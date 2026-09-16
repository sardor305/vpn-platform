"""add user bonus reason

Revision ID: b3c7e9f1d2a4
Revises: a2f4c8e1d7b3
Create Date: 2026-09-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b3c7e9f1d2a4"
down_revision: Union[str, Sequence[str], None] = "a2f4c8e1d7b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_bonuses",
        sa.Column("reason", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_bonuses", "reason")
