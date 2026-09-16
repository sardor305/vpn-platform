from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.user import User


class Referral(Base):
    __tablename__ = "referrals"

    __table_args__ = (
        UniqueConstraint(
            "invited_user_id",
            name="uq_referrals_invited_user_id",
        ),
        UniqueConstraint(
            "inviter_user_id",
            "invited_user_id",
            name="uq_referrals_inviter_invited",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    inviter_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    invited_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    first_paid_subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("subscriptions.id"),
        nullable=True,
        index=True,
    )

    rewarded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    inviter: Mapped["User"] = relationship(
        foreign_keys=[inviter_user_id],
        back_populates="referrals_sent",
    )

    invited_user: Mapped["User"] = relationship(
        foreign_keys=[invited_user_id],
        back_populates="referral_received",
    )

    first_paid_subscription: Mapped["Subscription | None"] = relationship(
        foreign_keys=[first_paid_subscription_id],
    )