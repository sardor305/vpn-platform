from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.plan import Plan


def tariffs_keyboard(
    plans: list[Plan],
) -> InlineKeyboardMarkup:

    buttons = []

    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"{plan.name} — {plan.price} ₽",
                callback_data=f"buy:{plan.id}",
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )