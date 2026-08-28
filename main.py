import asyncio

from aiogram import Bot, Dispatcher

from app.config.config import config
from app.database.database import check_db_connection

from app.handlers.start import router as start_router
from app.handlers.phone import router as phone_router
from app.handlers.help import router as help_router
from app.handlers.support import router as support_router
from app.handlers.support_admin import router as support_admin_router
from app.handlers.buy import router as buy_router
from app.handlers.tariff_selection import (
    router as tariff_selection_router,
)
from app.handlers.daily_subscription import (
    router as daily_subscription_router,
)
from app.handlers.my_subscription import (
    router as my_subscription_router,
)
from app.handlers.admin import router as admin_router
from app.handlers.plan_admin import (
    router as plan_admin_router,
)
from app.tasks.subscription_scheduler import (
    subscription_reminder_scheduler,
)


bot = Bot(
    token=config.BOT_TOKEN
)

dp = Dispatcher()


dp.include_router(start_router)
dp.include_router(phone_router)
dp.include_router(help_router)
dp.include_router(support_router)
dp.include_router(support_admin_router)
dp.include_router(buy_router)
dp.include_router(tariff_selection_router)
dp.include_router(daily_subscription_router)
dp.include_router(my_subscription_router)
dp.include_router(admin_router)
dp.include_router(plan_admin_router)


async def main():

    print("1. main() boshlandi")

    await check_db_connection()

    print("2. DB tekshirildi")

    scheduler_task = asyncio.create_task(
        subscription_reminder_scheduler(bot)
    )

    print("3. Subscription reminder scheduler ishga tushdi")

    try:

        await dp.start_polling(bot)

    finally:

        scheduler_task.cancel()

        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())