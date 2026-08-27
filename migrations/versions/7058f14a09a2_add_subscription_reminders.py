"""add subscription reminders

Revision ID: 7058f14a09a2
Revises: b3343269c01b
Create Date: 2026-08-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7058f14a09a2"
down_revision: Union[str, Sequence[str], None] = "b3343269c01b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "subscription_reminders",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "reminder_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscription_id",
            "reminder_type",
            name="uq_subscription_reminder",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("subscription_reminders")