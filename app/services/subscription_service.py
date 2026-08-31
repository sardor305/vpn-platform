from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.utils.datetime import utc_now


class SubscriptionService:

    def __init__(self, session: AsyncSession):
        self.subscription_repository = (
            SubscriptionRepository(session)
        )

    async def get_active_subscription(
        self,
        user_id: int,
    ) -> Subscription | None:

        return await (
            self.subscription_repository
            .get_active_by_user(user_id)
        )

    async def get_all_active_subscriptions(
        self,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_active()
        )

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[Subscription]:

        return await (
            self.subscription_repository
            .get_all_active_for_expiry_check()
        )

    async def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        duration_days: int,
    ) -> Subscription:

        start_date = utc_now()

        end_date = start_date + timedelta(
            days=duration_days
        )

        return await self.subscription_repository.create(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
        )

    async def change_plan(
        self,
        subscription: Subscription,
        plan_id: int,
    ) -> Subscription:

        subscription.plan_id = plan_id

        return await self.subscription_repository.update(
            subscription
        )

    async def extend_subscription(
        self,
        subscription: Subscription,
        duration_days: int,
    ) -> Subscription:

        subscription.end_date = (
            subscription.end_date
            + timedelta(days=duration_days)
        )

        return await self.subscription_repository.update(
            subscription
        )