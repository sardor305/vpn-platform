from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def welcome_bonus_confirm_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Bonusni olish",
                    callback_data="welcome_bonus:claim",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="welcome_bonus:cancel",
                ),
            ],
        ]
    )
