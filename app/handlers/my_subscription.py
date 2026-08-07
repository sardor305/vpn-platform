from aiogram import F, Router
from aiogram.types import Message

from app.config.config import config
from app.database.database import async_session
from app.keyboards.subscription_keyboard import subscription_keyboard
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.user_service import UserService

router = Router()


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):

    async with async_session() as session:

        user_service = UserService(session)
        subscription_info_service = SubscriptionInfoService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        info = await subscription_info_service.get_subscription_info(
            user.id
        )

    if info is None:

        await message.answer(
            "❌ Sizda faol obuna mavjud emas.\n\n"
            "🛒 \"Obuna sotib olish\" bo'limidan tarif tanlang."
        )

        return

    subscription = info["subscription"]
    vpn_account = info["vpn_account"]

    status = (
        "🟢 Faol"
        if subscription.status == "active"
        else "🔴 Faol emas"
    )

    subscription_url = (
        f"{config.MARZBAN_PUBLIC_URL}{vpn_account.subscription_url}"
    )

    await message.answer(
        f"👤 <b>Mening obunam</b>\n\n"

        f"📦 <b>Tarif:</b> {subscription.plan.name}\n"
        f"💰 <b>Narxi:</b> {subscription.plan.price} ₽\n\n"

        f"📅 <b>Boshlangan sana:</b>\n"
        f"{subscription.start_date.strftime('%d.%m.%Y')}\n\n"

        f"⏳ <b>Tugash sanasi:</b>\n"
        f"{subscription.end_date.strftime('%d.%m.%Y')}\n\n"

        f"{status}\n\n"

        f"👤 <b>VPN Username</b>\n"
        f"<code>{vpn_account.marzban_username}</code>",
        parse_mode="HTML",
        reply_markup=subscription_keyboard(
            subscription_url=subscription_url,
            vpn_link=vpn_account.vpn_link,
        ),
    )