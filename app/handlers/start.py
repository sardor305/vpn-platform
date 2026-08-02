from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database.database import async_session
from app.services.user_service import UserService
from app.keyboards.menu import main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):

    async with async_session() as session:

        try:
            user_service = UserService(session)

            user, created = await user_service.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    if created:
        text = "🎉 Siz muvaffaqiyatli ro'yxatdan o'tdingiz!"
    else:
        text = "👋 Qaytganingizdan xursandmiz!"

    await message.answer(
        f"{text}\n\n👋 Assalomu alaykum!\n\nVPN Platformaga xush kelibsiz.",
        reply_markup=main_menu,
    )