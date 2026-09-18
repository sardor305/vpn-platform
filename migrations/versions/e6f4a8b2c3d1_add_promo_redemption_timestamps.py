"""Add timestamps to promo_redemptions.

Revision ID: e6f4a8b2c3d1
Revises: d5e9f3a7c2b1
Create Date: 2026-09-18
"""

from alembic import op
import sqlalchemy as sa


revision = "e6f4a8b2c3d1"
down_revision = "d5e9f3a7c2b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add created_at and updated_at to promo_redemptions."""
    timestamp = sa.text("CURRENT_TIMESTAMP")

    op.add_column(
        "promo_redemptions",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=timestamp,
        ),
    )
    op.add_column(
        "promo_redemptions",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=timestamp,
        ),
    )

    op.alter_column(
        "promo_redemptions",
        "created_at",
        nullable=False,
        server_default=None,
    )
    op.alter_column(
        "promo_redemptions",
        "updated_at",
        nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    """Remove created_at and updated_at from promo_redemptions."""
    op.drop_column("promo_redemptions", "updated_at")
    op.drop_column("promo_redemptions", "created_at")
