from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Javob berish",
                    callback_data=f"ticket_reply:{ticket_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Yechilgan",
                    callback_data=f"ticket_close:{ticket_id}",
                ),
                InlineKeyboardButton(
                    text="🗑 O‘chirish",
                    callback_data=f"ticket_delete:{ticket_id}",
                ),
            ],
        ],
    )


def ticket_list_keyboard(
    ticket_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📩 Murojaat #{ticket_id}",
                    callback_data=f"ticket_view:{ticket_id}",
                ),
            ],
        ],
    )