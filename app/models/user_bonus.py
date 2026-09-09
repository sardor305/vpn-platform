from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.bonus_traffic import BonusTraffic


class UserBonus(Base):
    __tablename__ = "user_bonuses"

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

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="bonuses",
    )

    traffic: Mapped["BonusTraffic | None"] = relationship(
        back_populates="bonus",
        uselist=False,
        cascade="all, delete-orphan",
    )
