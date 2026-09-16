"""add user bonus referral link

Revision ID: a2f4c8e1d7b3
Revises: 9d5e7f1a2b3c
Create Date: 2026-09-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2f4c8e1d7b3"
down_revision: Union[str, Sequence[str], None] = "9d5e7f1a2b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Link rewarded Referral records to their UserBonus rows."""

    op.add_column(
        "user_bonuses",
        sa.Column("referral_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_user_bonuses_referral_id_referrals",
        "user_bonuses",
        "referrals",
        ["referral_id"],
        ["id"],
    )

    op.create_index(
        op.f("ix_user_bonuses_referral_id"),
        "user_bonuses",
        ["referral_id"],
        unique=True,
    )


def downgrade() -> None:
    """Remove the UserBonus -> Referral link."""

    op.drop_index(
        op.f("ix_user_bonuses_referral_id"),
        table_name="user_bonuses",
    )

    op.drop_constraint(
        "fk_user_bonuses_referral_id_referrals",
        "user_bonuses",
        type_="foreignkey",
    )

    op.drop_column(
        "user_bonuses",
        "referral_id",
    )
