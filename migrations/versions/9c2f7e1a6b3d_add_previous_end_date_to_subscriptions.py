"""add previous end date to subscriptions

Revision ID: 9c2f7e1a6b3d
Revises: baf78ff5c84f
Create Date: 2026-09-06 16:37:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c2f7e1a6b3d"
down_revision: Union[str, Sequence[str], None] = "baf78ff5c84f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "subscriptions",
        sa.Column(
            "previous_end_date",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "subscriptions",
        "previous_end_date",
    )