from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )

    username: Mapped[str | None] = mapped_column(
        String(64)
    )

    first_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    last_name: Mapped[str | None] = mapped_column(
        String(64)
    )

    language_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )