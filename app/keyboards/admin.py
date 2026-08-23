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


def daily_price_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Narxni o‘zgartirish",
                    callback_data="daily_price:change",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data="daily_price:back",
                )
            ],
        ]
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


def admin_user_search_actions_keyboard(
    user_id: int,
    vpn_account_id: int | None = None,
) -> InlineKeyboardMarkup:

    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data=f"admin_user_refresh:{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 VPN link",
                callback_data=f"admin_user_vpn_link:{user_id}",
            ),
            InlineKeyboardButton(
                text="🔗 Subscription",
                callback_data=f"admin_user_subscription:{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📦 Obunani o‘zgartirish",
                callback_data=f"admin_user_change_plan:{user_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⏳ Muddatni uzaytirish",
                callback_data=f"admin_user_extend:{user_id}",
            ),
        ],
    ]

    if vpn_account_id is not None:

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🚫 VPNni o‘chirish",
                    callback_data=f"admin_user_delete_vpn:{vpn_account_id}",
                ),
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Admin panel",
                callback_data="admin_user_search_back",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )