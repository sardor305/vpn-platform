"""add referrals

Revision ID: 4e7a9b2c1d5f
Revises: 1f8b6c2d4a90
Create Date: 2026-09-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4e7a9b2c1d5f"
down_revision: Union[str, Sequence[str], None] = "1f8b6c2d4a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "referrals",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "inviter_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "invited_user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "first_paid_subscription_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "rewarded_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["inviter_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["invited_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["first_paid_subscription_id"],
            ["subscriptions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invited_user_id",
            name="uq_referrals_invited_user_id",
        ),
        sa.UniqueConstraint(
            "inviter_user_id",
            "invited_user_id",
            name="uq_referrals_inviter_invited",
        ),
    )

    op.create_index(
        op.f("ix_referrals_inviter_user_id"),
        "referrals",
        ["inviter_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_referrals_invited_user_id"),
        "referrals",
        ["invited_user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_referrals_status"),
        "referrals",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_referrals_first_paid_subscription_id"),
        "referrals",
        ["first_paid_subscription_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_referrals_first_paid_subscription_id"),
        table_name="referrals",
    )

    op.drop_index(
        op.f("ix_referrals_status"),
        table_name="referrals",
    )

    op.drop_index(
        op.f("ix_referrals_invited_user_id"),
        table_name="referrals",
    )

    op.drop_index(
        op.f("ix_referrals_inviter_user_id"),
        table_name="referrals",
    )

    op.drop_table("referrals")
