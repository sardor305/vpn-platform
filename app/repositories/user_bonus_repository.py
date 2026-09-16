from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_bonus import UserBonus
from app.utils.datetime import utc_now


class UserBonusRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        bonus_id: int,
    ) -> UserBonus | None:

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.id == bonus_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_active_by_user(
        self,
        user_id: int,
    ) -> UserBonus | None:

        now = utc_now()

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
                UserBonus.status == "active",
                UserBonus.start_date <= now,
                UserBonus.end_date > now,
            )
            .order_by(
                UserBonus.start_date.asc(),
                UserBonus.id.asc(),
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_expired_active_by_user(
        self,
        user_id: int,
        now: datetime,
    ) -> list[UserBonus]:
        """Return this user's active bonuses whose period has ended."""

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
                UserBonus.status == "active",
                UserBonus.end_date.is_not(None),
                UserBonus.end_date <= now,
            )
            .order_by(
                UserBonus.end_date.asc(),
                UserBonus.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_welcome_by_user(
        self,
        user_id: int,
    ) -> UserBonus | None:
        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
                UserBonus.bonus_type == "welcome",
            )
            .order_by(
                UserBonus.id.asc()
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_pending_by_user(
        self,
        user_id: int,
    ) -> list[UserBonus]:

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
                UserBonus.status == "pending",
            )
            .order_by(
                UserBonus.created_at.asc(),
                UserBonus.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_by_user(
        self,
        user_id: int,
    ) -> list[UserBonus]:

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
            )
            .order_by(
                UserBonus.id.desc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_by_user_paginated(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[UserBonus], int]:

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 5

        count_stmt = (
            select(func.count(UserBonus.id))
            .where(
                UserBonus.user_id == user_id,
            )
        )

        count_result = await self.session.execute(
            count_stmt
        )

        total = count_result.scalar_one()

        offset = (
            (page - 1) * page_size
        )

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.traffic)
            )
            .where(
                UserBonus.user_id == user_id,
            )
            .order_by(
                UserBonus.id.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(stmt)

        bonuses = list(
            result.scalars().all()
        )

        return bonuses, total

    async def get_all_active(
        self,
    ) -> list[UserBonus]:

        now = utc_now()

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.user),
                selectinload(UserBonus.traffic),
            )
            .where(
                UserBonus.status == "active",
                UserBonus.start_date <= now,
                UserBonus.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_active_welcome(
        self,
    ) -> list[UserBonus]:
        """Return only currently active Welcome Bonuses."""

        now = utc_now()

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.user),
                selectinload(UserBonus.traffic),
            )
            .where(
                UserBonus.bonus_type == "welcome",
                UserBonus.status == "active",
                UserBonus.start_date <= now,
                UserBonus.end_date > now,
            )
            .order_by(
                UserBonus.id.asc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[UserBonus]:

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.user),
                selectinload(UserBonus.traffic),
            )
            .where(
                UserBonus.status == "active",
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_pending(
        self,
    ) -> list[UserBonus]:

        stmt = (
            select(UserBonus)
            .options(
                selectinload(UserBonus.user),
                selectinload(UserBonus.traffic),
            )
            .where(
                UserBonus.status == "pending",
            )
            .order_by(
                UserBonus.created_at.asc(),
                UserBonus.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def _get_next_bonus_number(
        self,
        user_id: int,
        bonus_type: str,
    ) -> int | None:
        """Return the next permanent number for a numbered bonus type.

        The transaction-scoped advisory lock serializes bonus creation for the
        same user. This prevents two concurrent transactions from calculating
        the same MAX(bonus_number) + 1 value.
        """

        if bonus_type == "welcome":
            return None

        await self.session.execute(
            select(func.pg_advisory_xact_lock(user_id))
        )

        max_stmt = (
            select(func.max(UserBonus.bonus_number))
            .where(
                UserBonus.user_id == user_id,
                UserBonus.bonus_type == bonus_type,
            )
        )

        result = await self.session.execute(max_stmt)
        current_max = result.scalar_one_or_none()

        return (current_max or 0) + 1

    async def create(
        self,
        user_id: int,
        bonus_type: str,
        duration_days: int,
        reason: str | None = None,
        status: str = "pending",
        bonus_number: int | None = None,
        start_date=None,
        end_date=None,
        activated_at=None,
        referral_id: int | None = None,
    ) -> UserBonus:

        if bonus_number is None:
            bonus_number = await self._get_next_bonus_number(
                user_id=user_id,
                bonus_type=bonus_type,
            )
        elif bonus_number <= 0:
            raise ValueError("Bonus number must be greater than zero.")

        bonus = UserBonus(
            user_id=user_id,
            bonus_type=bonus_type,
            bonus_number=bonus_number,
            duration_days=duration_days,
            reason=reason,
            status=status,
            start_date=start_date,
            end_date=end_date,
            activated_at=activated_at,
            referral_id=referral_id,
        )

        self.session.add(bonus)

        await self.session.flush()

        await self.session.refresh(bonus)

        return bonus

    async def update(
        self,
        bonus: UserBonus,
    ) -> UserBonus:

        await self.session.flush()

        await self.session.refresh(bonus)

        return bonus