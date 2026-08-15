"""Add support messages

Revision ID: 414bf7d8862e
Revises: 6995ded45d3c
Create Date: 2026-08-08 13:08:51.333232

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "414bf7d8862e"
down_revision: Union[str, Sequence[str], None] = "6995ded45d3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["support_tickets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_support_messages_sender_id"),
        "support_messages",
        ["sender_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_support_messages_ticket_id"),
        "support_messages",
        ["ticket_id"],
        unique=False,
    )

    # Mavjud murojaatlarning birinchi xabarlarini
    # support_messages jadvaliga ko'chirish.
    op.execute(
        """
        INSERT INTO support_messages (
            ticket_id,
            sender_id,
            sender_type,
            message,
            created_at
        )
        SELECT
            id,
            user_id,
            'user',
            message,
            created_at
        FROM support_tickets
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_support_messages_ticket_id"),
        table_name="support_messages",
    )

    op.drop_index(
        op.f("ix_support_messages_sender_id"),
        table_name="support_messages",
    )

    op.drop_table("support_messages")
