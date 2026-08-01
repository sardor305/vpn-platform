from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database.database import async_session
from app.repositories.user_repository import UserRepository

from app.keyboards.menu import main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):

    async with async_session() as session:
        user_repo = UserRepository(session)

        user = await user_repo.get_by_telegram_id(
            message.from_user.id
        )

        if user is None:
            user = await user_repo.create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
            )

            text = "🎉 Siz muvaffaqiyatli ro'yxatdan o'tdingiz!"

        else:
            text = "👋 Qaytganingizdan xursandmiz!"

    await message.answer(
        f"{text}\n\n👋 Assalomu alaykum!\n\nVPN Platformaga xush kelibsiz.",
        reply_markup=main_menu,
    )