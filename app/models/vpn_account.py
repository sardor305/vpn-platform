from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.user import User


class VPNAccount(Base):
    __tablename__ = "vpn_accounts"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "protocol",
            name="uq_user_protocol",
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

    marzban_username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    protocol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    vpn_link: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    subscription_url: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="vpn_accounts",
    )