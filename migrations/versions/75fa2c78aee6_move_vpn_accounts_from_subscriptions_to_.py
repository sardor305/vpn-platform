"""Move VPN accounts from subscriptions to users

Revision ID: 75fa2c78aee6
Revises: 020eeb11d7fc
Create Date: 2026-08-19 22:22:52.120713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "75fa2c78aee6"
down_revision: Union[str, Sequence[str], None] = "020eeb11d7fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "vpn_accounts",
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE vpn_accounts
        SET user_id = subscriptions.user_id
        FROM subscriptions
        WHERE vpn_accounts.subscription_id = subscriptions.id
        """
    )

    op.alter_column(
        "vpn_accounts",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_foreign_key(
        "vpn_accounts_user_id_fkey",
        "vpn_accounts",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_index(
        "ix_vpn_accounts_user_id",
        "vpn_accounts",
        ["user_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_user_protocol",
        "vpn_accounts",
        ["user_id", "protocol"],
    )

    op.drop_constraint(
        "vpn_accounts_subscription_id_fkey",
        "vpn_accounts",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_vpn_accounts_subscription_id",
        table_name="vpn_accounts",
    )

    op.drop_column(
        "vpn_accounts",
        "subscription_id",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "vpn_accounts",
        sa.Column(
            "subscription_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE vpn_accounts
        SET subscription_id = (
            SELECT subscriptions.id
            FROM subscriptions
            WHERE subscriptions.user_id = vpn_accounts.user_id
            ORDER BY subscriptions.id DESC
            LIMIT 1
        )
        """
    )

    op.alter_column(
        "vpn_accounts",
        "subscription_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_foreign_key(
        "vpn_accounts_subscription_id_fkey",
        "vpn_accounts",
        "subscriptions",
        ["subscription_id"],
        ["id"],
    )

    op.create_index(
        "ix_vpn_accounts_subscription_id",
        "vpn_accounts",
        ["subscription_id"],
        unique=False,
    )

    op.drop_constraint(
        "uq_user_protocol",
        "vpn_accounts",
        type_="unique",
    )

    op.drop_index(
        "ix_vpn_accounts_user_id",
        table_name="vpn_accounts",
    )

    op.drop_constraint(
        "vpn_accounts_user_id_fkey",
        "vpn_accounts",
        type_="foreignkey",
    )

    op.drop_column(
        "vpn_accounts",
        "user_id",
    )