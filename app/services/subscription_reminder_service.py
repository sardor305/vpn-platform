from datetime import datetime, timedelta

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.subscription_reminder_repository import (
    SubscriptionReminderRepository,
)
from app.services.subscription_service import SubscriptionService
from app.utils.datetime import utc_now


class SubscriptionReminderService:

    REMINDER_TYPE = "3_days"

    def __init__(
        self,
        session: AsyncSession,
        bot: Bot,
    ):
        self.subscription_service = (
            SubscriptionService(session)
        )

        self.reminder_repository = (
            SubscriptionReminderRepository(session)
        )

        self.bot = bot

    async def send_due_reminders(self) -> int:

        subscriptions = (
            await self.subscription_service
            .get_all_active_subscriptions()
        )

        now = utc_now()

        reminder_min = now + timedelta(days=2)
        reminder_max = now + timedelta(days=3)

        sent_count = 0

        for subscription in subscriptions:

            if not (
                reminder_min
                < subscription.end_date
                <= reminder_max
            ):
                continue

            existing_reminder = (
                await self.reminder_repository
                .get_by_subscription_and_type(
                    subscription_id=subscription.id,
                    reminder_type=self.REMINDER_TYPE,
                )
            )

            if existing_reminder is not None:
                continue

            user = subscription.user

            if not user.is_active:
                continue

            message = (
                "🔔 <b>Obunangiz tugashiga 3 kun qoldi!</b>\n\n"
                f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
                f"📅 Tugash sanasi: "
                f"<b>{subscription.end_date.strftime('%d.%m.%Y')}</b>\n\n"
                "VPN'dan uzilib qolmaslik uchun "
                "obunangizni oldindan uzaytirishingiz mumkin."
            )

            try:

                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode="HTML",
                )

            except Exception as e:

                print(
                    "SUBSCRIPTION REMINDER ERROR:",
                    repr(e),
                    "user_id=",
                    user.id,
                    "subscription_id=",
                    subscription.id,
                )

                continue

            await self.reminder_repository.create(
                subscription_id=subscription.id,
                reminder_type=self.REMINDER_TYPE,
            )

            sent_count += 1

        return sent_count