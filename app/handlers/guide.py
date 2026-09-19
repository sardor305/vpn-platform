from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard


router = Router()


GUIDE_TEXT = (
    "📖 <b>Foydalanish qo‘llanmasi</b>\n\n"
    "1️⃣ <b>Ro‘yxatdan o‘tish</b>\n"
    "/start orqali botni ishga tushiring.\n\n"
    "2️⃣ <b>🎁 Welcome Bonus</b>\n"
    "Yangi foydalanuvchi sifatida maxsus bonusni "
    "olishingiz mumkin.\n\n"
    "3️⃣ <b>🛒 Obuna sotib olish</b>\n"
    "Kerakli tarifni tanlang va to‘lovni amalga oshiring.\n\n"
    "4️⃣ <b>👤 Mening obunam</b>\n"
    "Faol xizmatingiz, qolgan muddat va navbatdagi "
    "xizmatlar haqida ma’lumot olishingiz mumkin.\n\n"
    "5️⃣ <b>📞 Yordam</b>\n"
    "Savol yoki muammo yuzaga kelsa, yordam bo‘limidan "
    "foydalaning.\n\n"
    "ℹ️ Qo‘llanmadagi ma’lumotlar platformadagi yangi "
    "funksiyalar qo‘shilishi bilan kengaytiriladi."
)


@router.message(F.text == "📖 Foydalanish qo'llanmasi")
async def guide_handler(message: Message):
    await message.answer(
        GUIDE_TEXT,
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="guide_back",
        ),
    )


@router.callback_query(F.data == "guide_back")
async def guide_back(callback: CallbackQuery):
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
