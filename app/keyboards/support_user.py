from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def user_ticket_keyboard(
    ticket_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Murojaatni ochish",
                    callback_data=f"user_ticket_view:{ticket_id}",
                ),
            ],
        ],
    )


def user_ticket_reply_keyboard(
    ticket_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Javob berish",
                    callback_data=f"user_ticket_reply:{ticket_id}",
                ),
            ],
        ],
    )


def user_tickets_list_keyboard(
    ticket_ids: list[int],
) -> InlineKeyboardMarkup:

    keyboard = []

    for ticket_id in ticket_ids:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📩 Murojaat #{ticket_id}",
                    callback_data=f"user_ticket_view:{ticket_id}",
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )