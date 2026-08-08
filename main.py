import asyncio

from aiogram import Bot, Dispatcher

from app.config.config import config
from app.database.database import check_db_connection

from app.handlers.start import router as start_router
from app.handlers.phone import router as phone_router
from app.handlers.help import router as help_router
from app.handlers.buy import router as buy_router
from app.handlers.tariff_selection import router as tariff_selection_router
from app.handlers.my_subscription import router as my_subscription_router
from app.handlers.admin import router as admin_router


bot = Bot(
    token=config.BOT_TOKEN
)

dp = Dispatcher()


dp.include_router(start_router)
dp.include_router(phone_router)
dp.include_router(help_router)
dp.include_router(buy_router)
dp.include_router(tariff_selection_router)
dp.include_router(my_subscription_router)
dp.include_router(admin_router)


async def main():

    print("1. main() boshlandi")

    await check_db_connection()

    print("2. DB tekshirildi")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())