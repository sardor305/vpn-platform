"""remove user bonus valid_until and use strict queue FIFO

Revision ID: 8c4d6e1f2a30
Revises: 7b3c5d9e1a20
Create Date: 2026-09-13 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c4d6e1f2a30"
down_revision: Union[str, Sequence[str], None] = "7b3c5d9e1a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove the obsolete UserBonus validity field."""
    op.drop_index(
        op.f("ix_user_bonuses_valid_until"),
        table_name="user_bonuses",
    )
    op.drop_column(
        "user_bonuses",
        "valid_until",
    )


def downgrade() -> None:
    """Restore the obsolete UserBonus validity field."""
    op.add_column(
        "user_bonuses",
        sa.Column(
            "valid_until",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_user_bonuses_valid_until"),
        "user_bonuses",
        ["valid_until"],
        unique=False,
    )
