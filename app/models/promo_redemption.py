from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.promo import Promo
    from app.models.user import User
    from app.models.user_bonus import UserBonus


class PromoRedemption(Base):
    __tablename__ = "promo_redemptions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    promo_id: Mapped[int] = mapped_column(
        ForeignKey("promos.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    bonus_id: Mapped[int] = mapped_column(
        ForeignKey("user_bonuses.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    promo: Mapped["Promo"] = relationship(
        back_populates="redemptions",
    )

    user: Mapped["User"] = relationship()

    bonus: Mapped["UserBonus"] = relationship()
