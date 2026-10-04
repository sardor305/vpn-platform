from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard


router = Router()


ABOUT_TEXT = (
    "ℹ️ <b>ZEVINTORTUNNEL</b>\n\n"
    "🔐 <b>Erkin internet. Ishonchli ulanish. Qulay boshqaruv.</b>\n\n"
    "ZevintorTunnel — internetdan foydalanish tajribangizni yanada "
    "<b>qulay, xavfsiz va erkin</b> qilish uchun yaratilgan zamonaviy VPN platforma.\n\n"
    "Biz VPN'ni murakkab xizmat emas, <b>oddiy va tushunarli vosita</b> qilishga e’tibor qaratamiz.\n\n"
    "⚡ <b>NEGA ZEVINTORTUNNEL?</b>\n\n"
    "🛡️ <b>Xavfsizlik</b>\n"
    "Internetga ulanishda qo‘shimcha himoya qatlamidan foydalaning va ochiq tarmoqlarda "
    "o‘zingizni yanada xotirjam his qiling.\n\n"
    "🌍 <b>Erkinlik</b>\n"
    "Turli tarmoqlarda internetdan qulayroq foydalanish uchun zamonaviy VPN yechimidan foydalaning.\n\n"
    "🚀 <b>Qulay boshqaruv</b>\n"
    "Obuna sotib olish, ulanish ma’lumotlarini olish va xizmatni boshqarish — "
    "barchasi bitta Telegram bot ichida.\n\n"
    "💳 <b>O‘zingizga mos tarif</b>\n"
    "Kerakli muddatni tanlang va faqat o‘zingizga kerak bo‘lgan xizmatdan foydalaning.\n\n"
    "🎁 <b>KO‘PROQ IMKONIYAT</b>\n\n"
    "Do‘stlaringizni taklif qiling, bonuslardan foydalaning va ZevintorTunnel "
    "imkoniyatlaridan yanada ko‘proq foydalaning.\n\n"
    "📞 <b>Yordam doim yaqin</b>\n"
    "Savollaringiz bo‘lsa, <b>Yordam bo‘limi</b> orqali biz bilan bog‘lanishingiz mumkin.\n\n"
    "━━━━━━━━━━━━━━\n\n"
    "<b>ZevintorTunnel</b>\n\n"
    "🔐 <i>Qulaylik. Xavfsizlik. Erkinlik.</i>\n\n"
    "🚀 <b>Internet tajribangizni o‘zingiz boshqaring.</b>"
)


@router.message(F.text.in_({"ℹ️ ZevintorTunnel haqida", "ℹ ZevintorTunnel haqida", "ℹ Bot haqida", "ℹ️ Bot haqida"}))
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
