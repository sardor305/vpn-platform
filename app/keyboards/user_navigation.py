from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def append_navigation(
    keyboard: InlineKeyboardMarkup,
    *,
    back_callback: str | None = None,
    home_callback: str = "user_main_menu",
) -> InlineKeyboardMarkup:
    """Append standard user navigation to an existing inline keyboard."""
    rows = [list(row) for row in keyboard.inline_keyboard]

    if back_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="↩ Ortga",
                callback_data=back_callback,
            )
        ])

    if home_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="🏠 Asosiy menyu",
                callback_data=home_callback,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_navigation_keyboard(
    *,
    back_callback: str | None = None,
    home_callback: str = "user_main_menu",
) -> InlineKeyboardMarkup:
    """Standard navigation: Home only, or Back + Home for child screens."""
    rows = []

    if back_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="↩ Ortga",
                callback_data=back_callback,
            )
        ])

    if home_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="🏠 Asosiy menyu",
                callback_data=home_callback,
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
