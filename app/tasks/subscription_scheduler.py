import asyncio

from aiogram import Bot

from app.database.database import async_session
from app.services.subscription_reminder_service import (
    SubscriptionReminderService,
)


async def subscription_reminder_scheduler(
    bot: Bot,
) -> None:

    while True:

        try:

            async with async_session() as session:

                reminder_service = (
                    SubscriptionReminderService(
                        session=session,
                        bot=bot,
                    )
                )

                sent_count = (
                    await reminder_service
                    .send_due_reminders()
                )

                await session.commit()

                if sent_count > 0:
                    print(
                        f"SUBSCRIPTION REMINDER: "
                        f"{sent_count} ta xabar yuborildi."
                    )

        except Exception as e:

            print(
                "SUBSCRIPTION SCHEDULER ERROR:",
                repr(e),
            )

        await asyncio.sleep(60 * 60)