from aiogram import F, Router
from aiogram.types import Message


router = Router()


@router.message(F.text == "ℹ️ Bot haqida")
async def about_handler(message: Message):

    await message.answer(
        "ℹ️ <b>ZevintorTunnel haqida</b>\n\n"
        "🔐 ZevintorTunnel — qulay VPN xizmatidan "
        "foydalanish uchun mo‘ljallangan platforma.\n\n"
        "🤝 Bot orqali VPN xizmatlarini sotib olish, "
        "xizmat muddatini boshqarish va mavjud imkoniyatlardan "
        "foydalanish mumkin.\n\n"
        "🎁 Yangi foydalanuvchilar uchun maxsus bonus ham mavjud."
    )