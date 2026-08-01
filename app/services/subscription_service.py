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