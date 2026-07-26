from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.menu import main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Assalomu alaykum!\n\nVPN Platformaga xush kelibsiz.",
        reply_markup=main_menu,
    )