from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.phone import phone_keyboard
from app.services.user_service import UserService


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

        await message.answer(
            "🎉 Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
            "👋 Assalomu alaykum!\n\n"
            "VPN Platformaga xush kelibsiz.\n\n"
            "📱 <b>Telefon raqamingiz</b>\n\n"
            "Telefon raqamingiz sizni botdagi akkauntingiz "
            "bilan bog‘lash va xizmatdan foydalanishingizni "
            "qulay boshqarish uchun kerak.\n\n"
            "🔒 Raqamingiz boshqa foydalanuvchilarga "
            "ko‘rsatilmaydi.\n\n"
            "Telefon raqamingizni ulashishni xohlamasangiz, "
            "bu bosqichni o'tkazib yuborishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=phone_keyboard,
        )

        return

    await message.answer(
        "👋 Qaytganingizdan xursandmiz!\n\n"
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )