from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.menu import main_menu, main_menu_with_welcome
from app.keyboards.welcome_bonus import (
    welcome_bonus_confirm_keyboard,
)
from app.services.user_service import UserService
from app.services.welcome_bonus_service import WelcomeBonusService


router = Router()


def _bonus_status_text(status: str) -> str:
    if status == "active":
        return "🟢 Faol"

    if status == "pending":
        return "⏳ Navbatda"

    if status == "expired":
        return "🔴 Muddati tugagan"

    if status == "revoked":
        return "⚪ Bekor qilingan"

    return f"⚪ {status}"


@router.message(F.text == "🎁 Bonusni olish")
async def welcome_bonus_handler(
    message: Message,
):
    async with async_session() as session:
        user_service = UserService(
            session
        )

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if user is None:
            await message.answer(
                "❌ Foydalanuvchi topilmadi."
            )
            return

        welcome_bonus_service = WelcomeBonusService(
            session
        )

        existing = (
            await welcome_bonus_service.get_existing_welcome(
                user_id=user.id
            )
        )

    if existing is not None:
        await message.answer(
            "🎁 <b>Welcome Bonus</b>\n\n"
            "Siz bu bonusni avval olgansiz.\n\n"
            f"📅 Muddat: <b>{existing.duration_days} kun</b>\n"
            "📦 Trafik: <b>3 GB jami</b>\n"
            f"📌 Holati: <b>{_bonus_status_text(existing.status)}</b>",
            parse_mode="HTML",
            reply_markup=main_menu,
        )
        return

    await message.answer(
        "🎁 <b>Welcome Bonus</b>\n\n"
        "Yangi foydalanuvchilar uchun maxsus bonus:\n\n"
        "⏳ <b>3 kun</b> xizmat muddati\n"
        "📦 <b>3 GB</b> jami trafik\n\n"
        "⚠️ 3 GB trafik kunlik emas — bonus davomida "
        "jami 3 GB beriladi.\n\n"
        "Bonusni olishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=welcome_bonus_confirm_keyboard(),
    )


@router.callback_query(
    F.data == "welcome_bonus:cancel"
)
async def welcome_bonus_cancel(
    callback: CallbackQuery,
):
    await callback.answer(
        "Bonus olish bekor qilindi."
    )

    await callback.message.edit_text(
        "🎁 Welcome Bonus olish bekor qilindi.\n\n"
        "Istasangiz, keyinroq yana <b>🎁 Bonusni olish</b> "
        "tugmasi orqali urinib ko‘rishingiz mumkin.",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu_with_welcome,
    )


@router.callback_query(
    F.data == "welcome_bonus:claim"
)
async def welcome_bonus_claim(
    callback: CallbackQuery,
):
    async with async_session() as session:
        user_service = UserService(
            session
        )

        user = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        welcome_bonus_service = WelcomeBonusService(
            session
        )

        result = await welcome_bonus_service.claim(
            user_id=user.id
        )

        if not result.success:
            await session.rollback()

            await callback.answer(
                result.message,
                show_alert=True,
            )
            return

        await session.commit()

        bonus = result.bonus

    await callback.answer(
        "Welcome Bonus olindi! 🎁"
    )

    if bonus is None:
        await callback.message.edit_text(
            "❌ Bonus ma’lumotlarini olishda xatolik yuz berdi.",
            parse_mode="HTML",
        )
        return

    if bonus.status == "active":
        status_text = (
            "🟢 Bonus hozir faol."
        )
    else:
        status_text = (
            "⏳ Bonus navbatga qo‘shildi va "
            "o‘z navbati kelganda avtomatik faollashadi."
        )

    await callback.message.edit_text(
        "🎉 <b>Welcome Bonus muvaffaqiyatli olindi!</b>\n\n"
        "⏳ Muddat: <b>3 kun</b>\n"
        "📦 Trafik: <b>3 GB jami</b>\n\n"
        f"{status_text}\n\n"
        "ℹ️ Bonusning aniq holati va navbatini "
        "👤 <b>Mening obunam</b> bo‘limidan ko‘rishingiz mumkin.",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )
