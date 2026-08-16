from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(
    subscription_url: str | None = None,
    show_create_vpn: bool = False,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    if subscription_url:
        builder.button(
            text="📥 Subscription",
            url=subscription_url,
        )

    if show_create_vpn:
        builder.button(
            text="🔑 Yangi VPN olish",
            callback_data="subscription:create_vpn",
        )

    builder.adjust(1)

    return builder.as_markup()