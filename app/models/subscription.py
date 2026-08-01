from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id"),
        nullable=False
    )

    start_date: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False
    )

    end_date: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="subscriptions"
    )

    plan: Mapped["Plan"] = relationship(
        back_populates="subscriptions"
    )