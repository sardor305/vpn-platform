from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.promo import Promo
from app.models.promo_redemption import PromoRedemption


class PromoRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        promo_id: int,
    ) -> Promo | None:
        stmt = (
            select(Promo)
            .where(Promo.id == promo_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        code: str,
    ) -> Promo | None:
        normalized_code = code.strip().upper()

        stmt = (
            select(Promo)
            .where(Promo.code == normalized_code)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code_for_update(
        self,
        code: str,
    ) -> Promo | None:
        normalized_code = code.strip().upper()

        stmt = (
            select(Promo)
            .where(Promo.code == normalized_code)
            .with_for_update()
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> list[Promo]:
        stmt = (
            select(Promo)
            .order_by(Promo.id.desc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active(
        self,
    ) -> list[Promo]:
        stmt = (
            select(Promo)
            .where(Promo.is_active.is_(True))
            .order_by(Promo.id.desc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        code: str,
        duration_days: int,
        total_redemption_limit: int | None,
        per_user_limit: int,
        start_date: datetime | None,
        end_date: datetime | None,
        is_active: bool = True,
    ) -> Promo:
        promo = Promo(
            code=code.strip().upper(),
            duration_days=duration_days,
            total_redemption_limit=total_redemption_limit,
            per_user_limit=per_user_limit,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )

        self.session.add(promo)
        await self.session.flush()
        await self.session.refresh(promo)

        return promo

    async def update(
        self,
        promo: Promo,
    ) -> Promo:
        await self.session.flush()
        await self.session.refresh(promo)
        return promo

    async def count_redemptions(
        self,
        promo_id: int,
    ) -> int:
        stmt = (
            select(func.count(PromoRedemption.id))
            .where(PromoRedemption.promo_id == promo_id)
        )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def count_user_redemptions(
        self,
        promo_id: int,
        user_id: int,
    ) -> int:
        stmt = (
            select(func.count(PromoRedemption.id))
            .where(
                PromoRedemption.promo_id == promo_id,
                PromoRedemption.user_id == user_id,
            )
        )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_user_redemptions(
        self,
        user_id: int,
    ) -> list[PromoRedemption]:
        stmt = (
            select(PromoRedemption)
            .options(
                selectinload(PromoRedemption.promo),
                selectinload(PromoRedemption.bonus),
            )
            .where(PromoRedemption.user_id == user_id)
            .order_by(PromoRedemption.id.desc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_redemption_by_bonus_id(
        self,
        bonus_id: int,
    ) -> PromoRedemption | None:
        """Return the PromoRedemption that created a specific UserBonus."""

        stmt = (
            select(PromoRedemption)
            .options(
                selectinload(PromoRedemption.promo),
                selectinload(PromoRedemption.bonus),
            )
            .where(PromoRedemption.bonus_id == bonus_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_redemption(
        self,
        promo_id: int,
        user_id: int,
        bonus_id: int,
    ) -> PromoRedemption:
        redemption = PromoRedemption(
            promo_id=promo_id,
            user_id=user_id,
            bonus_id=bonus_id,
        )

        self.session.add(redemption)
        await self.session.flush()
        await self.session.refresh(redemption)

        return redemption