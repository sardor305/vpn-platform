from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard


router = Router()


ABOUT_TEXT = (
    "ℹ <b>ZevintorTunnel haqida</b>\n\n"
    "🔐 ZevintorTunnel — qulay VPN xizmatidan "
    "foydalanish uchun mo‘ljallangan platforma.\n\n"
    "🤝 Bot orqali VPN xizmatlarini sotib olish, "
    "xizmat muddatini boshqarish va mavjud imkoniyatlardan "
    "foydalanish mumkin.\n\n"
    "🎁 Yangi foydalanuvchilar uchun maxsus bonus ham mavjud."
)


@router.message(F.text.in_({"ℹ Bot haqida", "ℹ️ Bot haqida"}))
async def about_handler(message: Message):
    await message.answer(
        ABOUT_TEXT,
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="about_back",
        ),
    )


@router.callback_query(F.data == "about_back")
async def about_back(callback: CallbackQuery):
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
