from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.subscription_repository import SubscriptionRepository


class SubscriptionService:

    def __init__(self, session: AsyncSession):
        self.subscription_repository = SubscriptionRepository(session)

    async def get_active_subscription(
        self,
        user_id: int,
    ) -> Subscription | None:

        return await self.subscription_repository.get_active_by_user(
            user_id
        )

    async def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        duration_days: int,
    ) -> Subscription:

        start_date = datetime.now()

        end_date = start_date + timedelta(
            days=duration_days
        )

        return await self.subscription_repository.create(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
        )