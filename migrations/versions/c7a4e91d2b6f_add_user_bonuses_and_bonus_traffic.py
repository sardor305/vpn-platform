"""add user bonuses and bonus traffic

Revision ID: c7a4e91d2b6f
Revises: 9c2f7e1a6b3d
Create Date: 2026-09-09 19:31:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7a4e91d2b6f"
down_revision: Union[str, Sequence[str], None] = "9c2f7e1a6b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "user_bonuses",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "bonus_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "duration_days",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "start_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "end_date",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "valid_until",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "activated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_user_bonuses_user_id"),
        "user_bonuses",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_bonuses_bonus_type"),
        "user_bonuses",
        ["bonus_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_bonuses_status"),
        "user_bonuses",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_user_bonuses_valid_until"),
        "user_bonuses",
        ["valid_until"],
        unique=False,
    )

    op.create_table(
        "bonus_traffic",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "bonus_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "traffic_limit_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "traffic_used_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bonus_id"],
            ["user_bonuses.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bonus_id"),
    )

    op.create_index(
        op.f("ix_bonus_traffic_bonus_id"),
        "bonus_traffic",
        ["bonus_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_bonus_traffic_bonus_id"),
        table_name="bonus_traffic",
    )

    op.drop_table("bonus_traffic")

    op.drop_index(
        op.f("ix_user_bonuses_valid_until"),
        table_name="user_bonuses",
    )

    op.drop_index(
        op.f("ix_user_bonuses_status"),
        table_name="user_bonuses",
    )

    op.drop_index(
        op.f("ix_user_bonuses_bonus_type"),
        table_name="user_bonuses",
    )

    op.drop_index(
        op.f("ix_user_bonuses_user_id"),
        table_name="user_bonuses",
    )

    op.drop_table("user_bonuses")
