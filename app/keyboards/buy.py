from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def buy_menu_keyboard() -> InlineKeyboardMarkup:

    buttons = [
        [
            InlineKeyboardButton(
                text="📦 Tariflar",
                callback_data="buy_plans",
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Kunlik obuna",
                callback_data="buy_daily",
            )
        ],
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )