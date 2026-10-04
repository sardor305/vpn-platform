from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.services.user_service import UserService


router = Router()


def help_inline_keyboard(has_phone: bool) -> InlineKeyboardMarkup:
    rows = []

    if not has_phone:
        rows.append([
            InlineKeyboardButton(
                text="📱 Telefon raqamini ulashish",
                callback_data="help_phone",
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="🏠 Asosiy menyu",
            callback_data="user_main_menu",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_share_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon raqamini yuborish",
                    request_contact=True,
                )
            ],
            [
                KeyboardButton(text="↩ Ortga"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def help_text(has_phone: bool) -> str:
    if has_phone:
        return (
            "📞 <b>Yordam</b>\n\n"
            "📱 Telefon raqamingiz akkauntingizga ulangan. ✅\n\n"
            "🔒 Raqamingiz boshqa foydalanuvchilarga ko‘rsatilmaydi.\n\n"
            "Agar sizga yordam kerak bo‘lsa, qo‘llab-quvvatlash xizmatiga murojaat qilishingiz mumkin."
        )

    return (
        "📞 <b>Yordam</b>\n\n"
        "Savolingiz yoki muammoingiz bo‘lsa, biz bilan bog‘lanishingiz mumkin.\n\n"
        "🛠 Obuna, to‘lov, VPN xizmati yoki botdan foydalanish bo‘yicha "
        "yordam olish uchun <b>Telefon raqamingizni ulashish</b> tugmasini bosing.\n\n"
        "🔒 Telefon raqamingiz faqat murojaatingizni aniqlash uchun ishlatiladi "
        "va boshqa foydalanuvchilarga ko‘rsatilmaydi."
    )


async def send_help(message: Message, has_phone: bool) -> None:
    await message.edit_text(
        help_text(has_phone),
        parse_mode="HTML",
        reply_markup=help_inline_keyboard(has_phone),
    )


@router.message(F.text == "📞 Yordam")
async def help_handler(message: Message):
    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

    if user is None:
        await message.answer(
            "📞 <b>Yordam</b>\n\n"
            "Akkaunt ma’lumotlari topilmadi. Iltimos, /start orqali botni qayta ishga tushiring.",
            parse_mode="HTML",
            reply_markup=main_menu,
        )
        return

    await message.answer(
        help_text(bool(user.phone_number)),
        parse_mode="HTML",
        reply_markup=help_inline_keyboard(bool(user.phone_number)),
    )


@router.callback_query(F.data == "help_phone")
async def help_phone(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "📱 <b>Telefon raqamini ulashish</b>\n\n"
        "Pastdagi <b>Telefon raqamini yuborish</b> tugmasini bosing.\n\n"
        "Telegram faqat o‘zingizning kontaktingizni yuborishingizga ruxsat beradi.",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "📱 Telefon raqamingizni yuborish uchun pastdagi tugmani bosing.",
        reply_markup=phone_share_keyboard(),
    )


@router.message(F.text == "↩ Ortga")
async def help_phone_cancel(message: Message):
    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

    # Remove the temporary reply keyboard first, then show the Help screen
    # again with its normal inline navigation.
    await message.answer(
        "↩ <b>Yordamga qaytildi</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        help_text(bool(user and user.phone_number)),
        parse_mode="HTML",
        reply_markup=help_inline_keyboard(bool(user and user.phone_number)),
    )

