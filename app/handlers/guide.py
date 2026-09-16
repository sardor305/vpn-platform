from aiogram import F, Router
from aiogram.types import Message


router = Router()


@router.message(F.text == "📖 Foydalanish qo'llanmasi")
async def guide_handler(message: Message):

    await message.answer(
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