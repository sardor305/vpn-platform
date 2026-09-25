from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def append_navigation(
    keyboard: InlineKeyboardMarkup,
    *,
    back_callback: str,
    home_callback: str | None = "user_main_menu",
    close_callback: str | None = None,
) -> InlineKeyboardMarkup:
    rows = [list(row) for row in keyboard.inline_keyboard]

    if home_callback is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data=back_callback,
                ),
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
                    callback_data=home_callback,
                ),
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data=back_callback,
                ),
            ]
        )

    if close_callback is not None:
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
    home_callback: str | None = "user_main_menu",
    close_callback: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []

    if home_callback is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data=back_callback,
                ),
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
                    callback_data=home_callback,
                ),
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text="↩️ Orqaga",
                    callback_data=back_callback,
                ),
            ]
        )

    if close_callback is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text="❌ Yopish",
                    callback_data=close_callback,
                ),
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
