from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SubscriptionReminder(Base):
    __tablename__ = "subscription_reminders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subscriptions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    reminder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "reminder_type",
            name="uq_subscription_reminder",
        ),
    )