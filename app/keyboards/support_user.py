from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def user_ticket_keyboard(
    ticket_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Murojaatni ko‘rish",
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
                    text="💬 Javob yozish",
                    callback_data=f"user_ticket_reply:{ticket_id}",
                ),
            ],
        ],
    )


def user_ticket_new_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🆕 Yangi murojaat",
                    callback_data="user_ticket_new",
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
                ),
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )