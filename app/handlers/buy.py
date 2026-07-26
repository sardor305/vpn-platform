from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.tariffs import tariffs_keyboard

router = Router()


@router.message(F.text == "🛒 Obuna sotib olish")
async def buy_subscription(message: Message):
    await message.answer(
        "📦 VPN tariflari\n\n"
        "⬇️ Tarifni tanlang:",
        reply_markup=tariffs_keyboard(),
    )