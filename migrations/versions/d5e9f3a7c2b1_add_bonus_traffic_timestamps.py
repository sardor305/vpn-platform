"""add bonus traffic timestamps

Revision ID: d5e9f3a7c2b1
Revises: c4d8f2a6b1e5
Create Date: 2026-09-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e9f3a7c2b1"
down_revision: Union[str, Sequence[str], None] = "c4d8f2a6b1e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timestamps required by the BonusTraffic model."""
    timestamp = sa.text("CURRENT_TIMESTAMP")

    op.add_column(
        "bonus_traffic",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=timestamp,
        ),
    )

    op.add_column(
        "bonus_traffic",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=timestamp,
        ),
    )

    op.alter_column(
        "bonus_traffic",
        "created_at",
        server_default=None,
    )

    op.alter_column(
        "bonus_traffic",
        "updated_at",
        server_default=None,
    )


def downgrade() -> None:
    """Remove BonusTraffic timestamps."""
    op.drop_column("bonus_traffic", "updated_at")
    op.drop_column("bonus_traffic", "created_at")
