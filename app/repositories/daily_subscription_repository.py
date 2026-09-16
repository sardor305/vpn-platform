from datetime import datetime

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
                DailySubscription.start_date <= now,
                DailySubscription.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_expired_active_by_user(
        self,
        user_id: int,
        now: datetime,
    ) -> list[DailySubscription]:
        """Return this user's active Daily services whose period has ended."""
        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.user_id == user_id,
                DailySubscription.status == "active",
                DailySubscription.end_date.is_not(None),
                DailySubscription.end_date <= now,
            )
            .order_by(
                DailySubscription.end_date.asc(),
                DailySubscription.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_pending_by_user(
        self,
        user_id: int,
    ) -> list[DailySubscription]:

        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.user_id == user_id,
                DailySubscription.status == "pending",
            )
            .order_by(
                DailySubscription.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_pending(
        self,
    ) -> list[DailySubscription]:

        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.status == "pending",
            )
            .order_by(
                DailySubscription.id.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_active(
        self,
    ) -> list[DailySubscription]:
        """Return all currently active Daily subscriptions."""
        now = utc_now()
        stmt = (
            select(DailySubscription)
            .where(
                DailySubscription.status == "active",
                DailySubscription.start_date <= now,
                DailySubscription.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

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
        start_date=None,
        end_date=None,
        status: str = "pending",
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
