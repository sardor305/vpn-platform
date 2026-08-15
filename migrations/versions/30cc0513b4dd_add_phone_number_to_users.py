"""Add phone number to users

Revision ID: 30cc0513b4dd
Revises: ac147065f8d8
Create Date: 2026-08-08 10:16:03.612828

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "30cc0513b4dd"
down_revision: Union[str, Sequence[str], None] = "ac147065f8d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "phone_number",
            sa.String(length=20),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "users",
        "phone_number",
    )
