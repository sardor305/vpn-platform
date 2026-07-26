from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.tariffs import TARIFFS


def tariffs_keyboard():
    buttons = []

    for tariff in TARIFFS:
        buttons.append([
            InlineKeyboardButton(
                text=f"{tariff['name']} — {tariff['price']} ₽",
                callback_data=f"buy:{tariff['id']}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)