"""add promos and promo redemptions

Revision ID: 7b3c5d9e1a20
Revises: 4e7a9b2c1d5f
Create Date: 2026-09-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b3c5d9e1a20"
down_revision: Union[str, Sequence[str], None] = "4e7a9b2c1d5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Promo and PromoRedemption tables."""

    op.create_table(
        "promos",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "duration_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "total_redemption_limit",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "per_user_limit",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "end_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_index(
        op.f("ix_promos_code"),
        "promos",
        ["code"],
        unique=True,
    )

    op.create_index(
        op.f("ix_promos_is_active"),
        "promos",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "promo_redemptions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "promo_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "bonus_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["promo_id"],
            ["promos.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["bonus_id"],
            ["user_bonuses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bonus_id"),
    )

    op.create_index(
        op.f("ix_promo_redemptions_promo_id"),
        "promo_redemptions",
        ["promo_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_promo_redemptions_user_id"),
        "promo_redemptions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_promo_redemptions_bonus_id"),
        "promo_redemptions",
        ["bonus_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop PromoRedemption and Promo tables."""

    op.drop_index(
        op.f("ix_promo_redemptions_bonus_id"),
        table_name="promo_redemptions",
    )

    op.drop_index(
        op.f("ix_promo_redemptions_user_id"),
        table_name="promo_redemptions",
    )

    op.drop_index(
        op.f("ix_promo_redemptions_promo_id"),
        table_name="promo_redemptions",
    )

    op.drop_table("promo_redemptions")

    op.drop_index(
        op.f("ix_promos_is_active"),
        table_name="promos",
    )

    op.drop_index(
        op.f("ix_promos_code"),
        table_name="promos",
    )

    op.drop_table("promos")
