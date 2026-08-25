from sqlalchemy.ext.asyncio import AsyncSession

from app.factories.marzban_factory import create_marzban_service
from app.services.daily_subscription_service import (
    DailySubscriptionService,
)
from app.services.subscription_service import SubscriptionService
from app.services.vpn_account_service import VPNAccountService


class SubscriptionInfoService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.subscription_service = SubscriptionService(
            session
        )

        self.daily_subscription_service = (
            DailySubscriptionService(session)
        )

        self.vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=create_marzban_service(),
        )

    async def get_info(
        self,
        user_id: int,
    ):

        subscription = (
            await self.subscription_service
            .get_active_subscription(user_id)
        )

        daily_subscription = None

        if subscription is None:

            daily_subscription = (
                await self.daily_subscription_service
                .get_active_subscription(user_id)
            )

            if daily_subscription is None:
                return None

        vpn_account = (
            await self.vpn_account_service.get_existing(
                user_id=user_id,
                protocol="vless",
            )
        )

        return {
            "subscription": subscription,
            "daily_subscription": daily_subscription,
            "vpn_account": vpn_account,
        }