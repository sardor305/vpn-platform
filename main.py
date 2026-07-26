import asyncio

from aiogram import Bot, Dispatcher

from app.config.config import config
from app.handlers.start import router as start_router
from app.handlers.buy import router as buy_router
from app.handlers.tariff_selection import router as tariff_selection_router

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(buy_router)
dp.include_router(tariff_selection_router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())