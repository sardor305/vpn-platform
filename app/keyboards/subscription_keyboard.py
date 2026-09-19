from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_keyboard(
    subscription_url: str | None = None,
    show_create_vpn: bool = False,
) -> InlineKeyboardMarkup:
    rows = []

    if subscription_url:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📥 Subscription",
                    url=subscription_url,
                )
            ]
        )

    if show_create_vpn:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔑 Yangi VPN olish",
                    callback_data="subscription:create_vpn",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="📜 Obunalar tarixi",
                callback_data="subscription_history",
            ),
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text="↩️ Ortga",
                callback_data="user_back",
            ),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
