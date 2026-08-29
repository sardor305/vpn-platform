"""add timestamps to subscription reminders

Revision ID: baf78ff5c84f
Revises: 7058f14a09a2
Create Date: 2026-08-30 02:20:32.236020

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "baf78ff5c84f"
down_revision: Union[str, Sequence[str], None] = "7058f14a09a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    timestamp = sa.text("CURRENT_TIMESTAMP")

    op.add_column(
        "subscription_reminders",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "subscription_reminders",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.alter_column(
        "subscription_reminders",
        "created_at",
        server_default=None,
    )

    op.alter_column(
        "subscription_reminders",
        "updated_at",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "subscription_reminders",
        "updated_at",
    )

    op.drop_column(
        "subscription_reminders",
        "created_at",
    )