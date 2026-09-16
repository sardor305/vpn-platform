from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.promo_redemption import PromoRedemption


class Promo(Base):
    __tablename__ = "promos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    duration_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_redemption_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    per_user_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    start_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    end_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    redemptions: Mapped[list["PromoRedemption"]] = relationship(
        back_populates="promo",
    )
