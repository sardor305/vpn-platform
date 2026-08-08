from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.phone import phone_keyboard
from app.services.user_service import UserService


router = Router()


@router.message(F.contact)
async def receive_phone_number(message: Message):

    contact = message.contact

    if contact is None:
        return

    if contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Iltimos, faqat o'zingizning telefon raqamingizni "
            "ulashing."
        )

        return

    async with async_session() as session:

        try:
            user_service = UserService(session)

            user = await user_service.get_by_telegram_id(
                telegram_id=message.from_user.id
            )

            if user is None:
                return

            await user_service.update_phone_number(
                user_id=user.id,
                phone_number=contact.phone_number,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    await message.answer(
        "✅ Telefon raqamingiz muvaffaqiyatli saqlandi!\n\n"
        "🏠 Endi botdan foydalanishingiz mumkin.",
        reply_markup=main_menu,
    )


@router.message(F.text == "⏭️ O‘tkazib yuborish")
async def skip_phone_number(message: Message):

    await message.answer(
        "👍 Mayli, telefon raqamingizni hozircha "
        "ulashmadingiz.\n\n"
        "🏠 Botdan foydalanishingiz mumkin.",
        reply_markup=main_menu,
    )