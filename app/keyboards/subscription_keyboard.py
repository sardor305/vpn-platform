from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(
    subscription_url: str,
    vpn_link: str,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📥 Subscription",
        url=subscription_url,
    )

    builder.button(
        text="🔗 VLESS",
        url=vpn_link,
    )

    builder.adjust(1)

    return builder.as_markup()