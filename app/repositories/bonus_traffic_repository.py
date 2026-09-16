from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bonus_traffic import BonusTraffic


class BonusTrafficRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_bonus_id(
        self,
        bonus_id: int,
    ) -> BonusTraffic | None:
        stmt = (
            select(BonusTraffic)
            .where(
                BonusTraffic.bonus_id == bonus_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
        self,
        bonus_id: int,
        traffic_limit_bytes: int,
        traffic_used_bytes: int = 0,
    ) -> BonusTraffic:
        if traffic_limit_bytes <= 0:
            raise ValueError(
                "Traffic limit must be greater than zero."
            )

        if traffic_used_bytes < 0:
            raise ValueError(
                "Traffic used cannot be negative."
            )

        traffic = BonusTraffic(
            bonus_id=bonus_id,
            traffic_limit_bytes=traffic_limit_bytes,
            traffic_used_bytes=traffic_used_bytes,
            warning_500mb_sent=False,
            exhausted_notified=False,
        )

        self.session.add(traffic)

        await self.session.flush()
        await self.session.refresh(traffic)

        return traffic

    async def update(
        self,
        traffic: BonusTraffic,
    ) -> BonusTraffic:
        await self.session.flush()
        await self.session.refresh(traffic)

        return traffic