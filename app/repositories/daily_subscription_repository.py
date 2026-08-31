from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_subscription import DailySubscription
from app.utils.datetime import utc_now


class DailySubscriptionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user(
        self,
        user_id: int,
    ) -> DailySubscription | None:

        now = utc_now()

        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.user_id == user_id,
                DailySubscription.status == "active",
                DailySubscription.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[DailySubscription]:

        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.status == "active",
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        duration_days: int,
        price: int,
        start_date,
        end_date,
        status: str = "active",
    ) -> DailySubscription:

        daily_subscription = DailySubscription(
            user_id=user_id,
            duration_days=duration_days,
            price=price,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

        self.session.add(daily_subscription)

        await self.session.flush()

        await self.session.refresh(
            daily_subscription
        )

        return daily_subscription

    async def update(
        self,
        daily_subscription: DailySubscription,
    ) -> DailySubscription:

        await self.session.flush()

        await self.session.refresh(
            daily_subscription
        )

        return daily_subscription