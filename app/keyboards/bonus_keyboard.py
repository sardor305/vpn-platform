from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data="bonus_history_back",
                ),
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
                    callback_data="user_main_menu",
                ),
            ]
        ]
    )
