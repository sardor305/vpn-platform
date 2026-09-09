from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_bonus import UserBonus


class BonusTraffic(Base):
    __tablename__ = "bonus_traffic"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    bonus_id: Mapped[int] = mapped_column(
        ForeignKey("user_bonuses.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    traffic_limit_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    traffic_used_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    bonus: Mapped["UserBonus"] = relationship(
        back_populates="traffic",
    )
