from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription


class SubscriptionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user(
        self,
        user_id: int
    ) -> Subscription | None:

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        plan_id: int,
        start_date,
        end_date,
        status: str = "active",
    ) -> Subscription:

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

        self.session.add(subscription)

        await self.session.flush()

        await self.session.refresh(subscription)

        return subscription

    async def update(
        self,
        subscription: Subscription,
    ) -> Subscription:

        await self.session.flush()

        await self.session.refresh(subscription)

        return subscription