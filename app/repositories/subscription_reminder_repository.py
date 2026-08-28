from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription_reminder import SubscriptionReminder
from app.utils.datetime import utc_now


class SubscriptionReminderRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_subscription_and_type(
        self,
        subscription_id: int,
        reminder_type: str,
    ) -> SubscriptionReminder | None:

        stmt = (
            select(SubscriptionReminder)
            .where(
                SubscriptionReminder.subscription_id
                == subscription_id,
                SubscriptionReminder.reminder_type
                == reminder_type,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
        self,
        subscription_id: int,
        reminder_type: str,
    ) -> SubscriptionReminder:

        reminder = SubscriptionReminder(
            subscription_id=subscription_id,
            reminder_type=reminder_type,
            sent_at=utc_now(),
        )

        self.session.add(reminder)

        await self.session.flush()

        await self.session.refresh(reminder)

        return reminder