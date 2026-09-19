from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard
from app.services.user_service import UserService


router = Router()


@router.message(F.text == "📞 Yordam")
async def help_handler(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

    if user is None:
        return

    if user.phone_number:

        text = (
            "📞 <b>Yordam</b>\n\n"
            "Sizning telefon raqamingiz akkauntga "
            "allaqachon ulangan. ✅\n\n"
            "Agar sizga yordam kerak bo'lsa, "
            "qo'llab-quvvatlash xizmatiga murojaat qilishingiz mumkin."
        )

    else:

        text = (
            "📞 <b>Yordam</b>\n\n"
            "Telefon raqamingiz hali akkauntingizga "
            "ulanmagan.\n\n"
            "📱 Telefon raqamingizni akkauntingizga "
            "ulash orqali xizmatdan foydalanishni "
            "qulay boshqarishingiz mumkin.\n\n"
            "🔒 Raqamingiz boshqa foydalanuvchilarga "
            "ko'rsatilmaydi.\n\n"
            "Agar xohlasangiz, hozir ulashing."
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="help_back",
        ),
    )


@router.message(F.text == "⬅️ Asosiy menyu")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )


@router.callback_query(F.data == "help_back")
async def help_back(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏠 <b>ASOSIY MENYU</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )
