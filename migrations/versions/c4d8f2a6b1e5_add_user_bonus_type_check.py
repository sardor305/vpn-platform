"""add user bonus type check constraint

Revision ID: c4d8f2a6b1e5
Revises: b3c7e9f1d2a4
Create Date: 2026-09-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d8f2a6b1e5"
down_revision: Union[str, Sequence[str], None] = "b3c7e9f1d2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restrict UserBonus.bonus_type to supported bonus types."""

    op.create_check_constraint(
        "ck_user_bonuses_bonus_type",
        "user_bonuses",
        "bonus_type IN ('promo', 'referral', 'admin', 'welcome')",
    )


def downgrade() -> None:
    """Remove the UserBonus.bonus_type check constraint."""

    op.drop_constraint(
        "ck_user_bonuses_bonus_type",
        "user_bonuses",
        type_="check",
    )
