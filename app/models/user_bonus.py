from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.bonus_traffic import BonusTraffic
    from app.models.referral import Referral


class UserBonus(Base):
    __tablename__ = "user_bonuses"

    __table_args__ = (
        CheckConstraint(
            "bonus_type IN ('promo', 'referral', 'admin', 'welcome')",
            name="ck_user_bonuses_bonus_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    bonus_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Permanent sequence number within one user and one bonus type.
    # Promo, referral and admin bonuses use independent sequences.
    # Welcome is a special one-time bonus and does not need a public number.
    bonus_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    start_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="bonuses",
    )

    referral_id: Mapped[int | None] = mapped_column(
        ForeignKey("referrals.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    referral: Mapped["Referral | None"] = relationship()

    traffic: Mapped["BonusTraffic | None"] = relationship(
        back_populates="bonus",
        uselist=False,
        cascade="all, delete-orphan",
    )
