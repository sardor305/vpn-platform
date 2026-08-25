from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def daily_subscription_keyboard(
    daily_price: int,
) -> InlineKeyboardMarkup:

    durations = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
    ]

    buttons = []

    for days in durations:

        price = daily_price * days

        buttons.append([
            InlineKeyboardButton(
                text=f"{days} kun — {price} ₽",
                callback_data=f"daily_buy:{days}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✏️ 7 kundan ko‘p",
            callback_data="daily_custom",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="buy_back",
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons,
    )