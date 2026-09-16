"""add bonus traffic notification flags

Revision ID: 1f8b6c2d4a90
Revises: c7a4e91d2b6f
Create Date: 2026-09-10 17:48:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1f8b6c2d4a90"
down_revision: Union[str, Sequence[str], None] = "c7a4e91d2b6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bonus_traffic",
        sa.Column(
            "warning_500mb_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "bonus_traffic",
        sa.Column(
            "exhausted_notified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "bonus_traffic",
        "exhausted_notified",
    )

    op.drop_column(
        "bonus_traffic",
        "warning_500mb_sent",
    )
