from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_subscription import DailySubscription
from app.repositories.daily_subscription_repository import (
    DailySubscriptionRepository,
)
from app.services.setting_service import SettingService
from app.utils.datetime import utc_now


class DailySubscriptionService:

    def __init__(self, session: AsyncSession):

        self.daily_subscription_repository = (
            DailySubscriptionRepository(session)
        )

        self.setting_service = SettingService(
            session
        )

    async def get_active_subscription(
        self,
        user_id: int,
    ) -> DailySubscription | None:

        return await (
            self.daily_subscription_repository
            .get_active_by_user(user_id)
        )

    async def get_pending_subscriptions(
        self,
        user_id: int,
    ) -> list[DailySubscription]:

        return await (
            self.daily_subscription_repository
            .get_pending_by_user(user_id)
        )

    async def get_subscription_history(
        self,
        user_id: int,
    ) -> list[DailySubscription]:
        return await (
            self.daily_subscription_repository
            .get_all_by_user(user_id)
        )

    async def get_all_pending_subscriptions(
        self,
    ) -> list[DailySubscription]:

        return await (
            self.daily_subscription_repository
            .get_all_pending()
        )

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[DailySubscription]:

        return await (
            self.daily_subscription_repository
            .get_all_active_for_expiry_check()
        )

    async def calculate_price(
        self,
        duration_days: int,
    ) -> int:

        return await self.setting_service.calculate_price(
            duration_days
        )

    async def create_subscription(
        self,
        user_id: int,
        duration_days: int,
    ) -> DailySubscription:

        if duration_days <= 0:
            raise ValueError(
                "Daily subscription duration must be greater than zero."
            )

        price = await self.calculate_price(
            duration_days
        )

        return await (
            self.daily_subscription_repository.create(
                user_id=user_id,
                duration_days=duration_days,
                price=price,
                start_date=None,
                end_date=None,
                status="pending",
            )
        )

    async def activate_subscription(
        self,
        daily_subscription: DailySubscription,
        start_date: datetime | None = None,
    ) -> DailySubscription:

        if daily_subscription.status != "pending":
            raise ValueError(
                "Only pending daily subscriptions can be activated."
            )

        start = start_date or utc_now()

        daily_subscription.start_date = start
        daily_subscription.end_date = start + timedelta(
            days=daily_subscription.duration_days
        )
        daily_subscription.status = "active"

        return await (
            self.daily_subscription_repository.update(
                daily_subscription
            )
        )