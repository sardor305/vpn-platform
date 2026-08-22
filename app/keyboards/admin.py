from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👥 Foydalanuvchilar"),
            KeyboardButton(text="📦 Tariflar"),
        ],
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="🔑 VPN hisoblar"),
        ],
        [
            KeyboardButton(text="🔎 Qidiruv"),
        ],
        [
            KeyboardButton(text="📩 Murojaatlar"),
        ],
        [
            KeyboardButton(text="⬅️ Asosiy menyu"),
        ],
    ],
    resize_keyboard=True,
)


users_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️ Admin panel"),
        ],
    ],
    resize_keyboard=True,
)


def vpn_accounts_keyboard(
    accounts,
) -> InlineKeyboardMarkup:

    buttons = []

    for account in accounts:

        user = account.subscription.user

        full_name = user.first_name

        if user.last_name:
            full_name += f" {user.last_name}"

        status = "🟢" if account.is_active else "🔴"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} #{account.id} "
                        f"{account.protocol.upper()} — "
                        f"{full_name}"
                    ),
                    callback_data=f"vpn_account:{account.id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Admin panel",
                callback_data="vpn_accounts:back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def vpn_account_actions_keyboard(
    account_id: int,
    is_active: bool,
) -> InlineKeyboardMarkup:

    buttons = []

    if is_active:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔴 Deaktivatsiya",
                    callback_data=f"vpn_deactivate:{account_id}",
                )
            ]
        )

    else:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🟢 Faollashtirish",
                    callback_data=f"vpn_activate:{account_id}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data=f"vpn_refresh:{account_id}",
            ),
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🗑 O‘chirish",
                callback_data=f"vpn_delete:{account_id}",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ VPN hisoblar",
                callback_data="vpn_accounts:list",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )