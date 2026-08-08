from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def help_keyboard(
    has_phone: bool,
) -> ReplyKeyboardMarkup:

    keyboard = []

    if not has_phone:
        keyboard.append(
            [
                KeyboardButton(
                    text="📱 Telefon raqamini ulashish",
                    request_contact=True,
                )
            ]
        )

    keyboard.append(
        [
            KeyboardButton(
                text="💬 Qo'llab-quvvatlash"
            )
        ]
    )

    keyboard.append(
        [
            KeyboardButton(
                text="📂 Murojaatlarim"
            )
        ]
    )

    keyboard.append(
        [
            KeyboardButton(
                text="⬅️ Asosiy menyu"
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )