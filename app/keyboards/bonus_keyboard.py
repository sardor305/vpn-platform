from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards.user_navigation import user_navigation_keyboard


def bonus_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📜 Bonuslar tarixi",
                    callback_data="bonus_history",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
                    callback_data="user_main_menu",
                )
            ],
        ]
    )


def bonus_history_keyboard() -> InlineKeyboardMarkup:
    return user_navigation_keyboard(
        back_callback="bonus_history_back",
    )
