from html import escape

from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.services.referral_service import ReferralService
from app.services.user_service import UserService


router = Router()


@router.message(F.text == "👥 Do‘stlarni taklif qilish")
async def referral_menu(message: Message):
    async with async_session() as session:
        try:
            user_service = UserService(session)

            user = await user_service.get_by_telegram_id(
                telegram_id=message.from_user.id
            )

            if user is None:
                await message.answer(
                    "❌ Foydalanuvchi topilmadi."
                )
                return

            referral_service = ReferralService(session)

            rewarded_count = (
                await referral_service.referral_repository
                .count_rewarded_by_inviter(
                    inviter_user_id=user.id
                )
            )

            next_referral_number = (
                await referral_service
                .get_referral_number_for_next_reward(
                    inviter_user_id=user.id
                )
            )

            bot_info = await message.bot.get_me()

            if not bot_info.username:
                await message.answer(
                    "❌ Referral havolasini yaratib bo‘lmadi: "
                    "bot username mavjud emas."
                )
                return

            referral_link = (
                f"https://t.me/{bot_info.username}"
                f"?start=ref_{message.from_user.id}"
            )

        except Exception:
            await session.rollback()
            raise

    if next_referral_number % 5 == 0:
        next_reward_days = 7
    else:
        next_reward_days = 3

    await message.answer(
        "👥 <b>DO‘STLARNI TAKLIF QILISH</b>\n\n"
        "Do‘stingizni shu havola orqali botga taklif qiling:\n\n"
        f"🔗 <code>{escape(referral_link)}</code>\n\n"
        "🎁 <b>Bonus qoidasi:</b>\n"
        "Do‘stingiz botga kirib, birinchi marta "
        "oylik Pullik obuna sotib olsa, sizga bonus beriladi.\n\n"
        f"👤 Takliflar bo‘yicha olingan bonuslar: "
        f"<b>{rewarded_count} ta</b>\n"
        f"🎯 Keyingi bonus: <b>{next_reward_days} kun</b>\n"
        f"🔢 Keyingi referral raqami: <b>{next_referral_number}</b>\n\n"
        "ℹ️ Har bir taklif qilingan foydalanuvchi faqat "
        "bir marta hisoblanadi.\n"
        "⭐ 5-, 10-, 15-, 20-... referral uchun <b>7 kun</b>, "
        "qolganlari uchun <b>3 kun</b> bonus beriladi.",
        parse_mode="HTML",
    )
