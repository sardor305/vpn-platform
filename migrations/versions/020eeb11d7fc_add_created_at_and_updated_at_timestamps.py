"""Add created_at and updated_at timestamps

Revision ID: 020eeb11d7fc
Revises: 414bf7d8862e
Create Date: 2026-08-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "020eeb11d7fc"
down_revision: Union[str, Sequence[str], None] = "414bf7d8862e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    timestamp = sa.text("CURRENT_TIMESTAMP")

    # Existing tables: add created_at with a temporary
    # server default so existing rows receive a value.
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "plans",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "plans",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "subscriptions",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "subscriptions",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "vpn_accounts",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "vpn_accounts",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    # These tables already have created_at.
    op.add_column(
        "support_tickets",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    op.add_column(
        "support_messages",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=timestamp,
            nullable=False,
        ),
    )

    # Remove the database-level default after existing rows
    # have been populated. Application-level defaults are
    # defined in app.database.base.Base.
    for table in (
        "users",
        "plans",
        "subscriptions",
        "vpn_accounts",
        "support_tickets",
        "support_messages",
    ):
        op.alter_column(
            table,
            "created_at",
            server_default=None,
        ) if table in (
            "users",
            "plans",
            "subscriptions",
            "vpn_accounts",
        ) else None

        op.alter_column(
            table,
            "updated_at",
            server_default=None,
        )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "support_messages",
        "updated_at",
    )

    op.drop_column(
        "support_tickets",
        "updated_at",
    )

    op.drop_column(
        "vpn_accounts",
        "updated_at",
    )

    op.drop_column(
        "vpn_accounts",
        "created_at",
    )

    op.drop_column(
        "subscriptions",
        "updated_at",
    )

    op.drop_column(
        "subscriptions",
        "created_at",
    )

    op.drop_column(
        "plans",
        "updated_at",
    )

    op.drop_column(
        "plans",
        "created_at",
    )

    op.drop_column(
        "users",
        "updated_at",
    )

    op.drop_column(
        "users",
        "created_at",
    )