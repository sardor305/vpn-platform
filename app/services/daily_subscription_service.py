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

        start_date = utc_now()

        end_date = start_date + timedelta(
            days=duration_days
        )

        price = await self.calculate_price(
            duration_days
        )

        return await (
            self.daily_subscription_repository.create(
                user_id=user_id,
                duration_days=duration_days,
                price=price,
                start_date=start_date,
                end_date=end_date,
            )
        )