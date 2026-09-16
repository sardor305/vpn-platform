"""add permanent user bonus numbers

Revision ID: 9d5e7f1a2b3c
Revises: 8c4d6e1f2a30
Create Date: 2026-09-13 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d5e7f1a2b3c"
down_revision: Union[str, Sequence[str], None] = "8c4d6e1f2a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add permanent per-user/per-type bonus numbering.

    Existing Promo and Referral bonuses are numbered in their historical
    creation order. Welcome bonuses remain unnumbered because Welcome is a
    special one-time bonus, not part of the numbered bonus history.
    """

    op.add_column(
        "user_bonuses",
        sa.Column("bonus_number", sa.Integer(), nullable=True),
    )

    # Backfill Promo and Referral numbers independently, preserving the
    # historical creation order. PostgreSQL's ROW_NUMBER() gives us a stable
    # sequence when created_at values are equal by using id as a tiebreaker.
    op.execute(sa.text("""
        WITH numbered AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY user_id, bonus_type
                    ORDER BY created_at ASC, id ASC
                ) AS number
            FROM user_bonuses
            WHERE bonus_type IN ('promo', 'referral', 'admin')
        )
        UPDATE user_bonuses AS ub
        SET bonus_number = numbered.number
        FROM numbered
        WHERE ub.id = numbered.id
    """))

    op.create_index(
        op.f("ix_user_bonuses_bonus_number"),
        "user_bonuses",
        ["bonus_number"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_user_bonuses_user_type_number",
        "user_bonuses",
        ["user_id", "bonus_type", "bonus_number"],
    )


def downgrade() -> None:
    """Remove permanent user bonus numbering."""

    op.drop_constraint(
        "uq_user_bonuses_user_type_number",
        "user_bonuses",
        type_="unique",
    )

    op.drop_index(
        op.f("ix_user_bonuses_bonus_number"),
        table_name="user_bonuses",
    )

    op.drop_column(
        "user_bonuses",
        "bonus_number",
    )
