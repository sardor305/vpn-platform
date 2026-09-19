from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard
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
                await message.answer("❌ Foydalanuvchi topilmadi.")
                return

            referral_service = ReferralService(session)
            rewarded_count = (
                await referral_service.referral_repository
                .count_rewarded_by_inviter(inviter_user_id=user.id)
            )
            next_referral_number = (
                await referral_service.get_referral_number_for_next_reward(
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

    next_reward_days = 7 if next_referral_number % 5 == 0 else 3

    text = (
        "👥 <b>DO‘STLARNI TAKLIF QILISH</b>\n\n"
        "Do‘stingizni shu havola orqali botga taklif qiling:\n\n"
        f"🔗 <code>{escape(referral_link)}</code>\n\n"
        "🎁 <b>Bonus qoidasi:</b>\n"
        "Do‘stingiz botga kirib, birinchi marta "
        "oylik Pullik obuna sotib olsa, sizga bonus beriladi.\n\n"
        f"👤 Takliflar bo‘yicha olingan bonuslar: <b>{rewarded_count} ta</b>\n"
        f"🎯 Keyingi bonus: <b>{next_reward_days} kun</b>\n"
        f"🔢 Keyingi referral raqami: <b>{next_referral_number}</b>\n\n"
        "ℹ️ Har bir taklif qilingan foydalanuvchi faqat bir marta hisoblanadi.\n"
        "⭐ 5-, 10-, 15-, 20-... referral uchun <b>7 kun</b>, "
        "qolganlari uchun <b>3 kun</b> bonus beriladi."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="referral_back",
        ),
    )


@router.callback_query(F.data == "referral_back")
async def referral_back(callback: CallbackQuery):
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
