from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def append_navigation(
    keyboard: InlineKeyboardMarkup,
    *,
    back_callback: str,
    close_callback: str | None = None,
) -> InlineKeyboardMarkup:
    rows = [list(row) for row in keyboard.inline_keyboard]
    rows.append([
        InlineKeyboardButton(
            text="↩️ Ortga",
            callback_data=back_callback,
        ),
    ])
    if close_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="❌ Yopish",
                callback_data=close_callback,
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_navigation_keyboard(
    *,
    back_callback: str = "user_back",
    close_callback: str | None = None,
) -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(
            text="↩️ Ortga",
            callback_data=back_callback,
        ),
    ]]
    if close_callback is not None:
        rows.append([
            InlineKeyboardButton(
                text="❌ Yopish",
                callback_data=close_callback,
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
