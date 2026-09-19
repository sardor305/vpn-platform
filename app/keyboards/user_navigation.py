from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def append_navigation(
    keyboard: InlineKeyboardMarkup,
    *,
    back_callback: str,
    close_callback: str = "user_close",
) -> InlineKeyboardMarkup:
    rows = [list(row) for row in keyboard.inline_keyboard]
    rows.append(
        [
            InlineKeyboardButton(
                text="↩️ Ortga",
                callback_data=back_callback,
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="❌ Yopish",
                callback_data=close_callback,
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_navigation_keyboard(
    *,
    back_callback: str = "user_back",
    close_callback: str = "user_close",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Ortga",
                    callback_data=back_callback,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Yopish",
                    callback_data=close_callback,
                ),
            ],
        ]
    )
