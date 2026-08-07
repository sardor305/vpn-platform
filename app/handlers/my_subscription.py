from aiogram import F, Router
from aiogram.types import Message

from app.config.config import config
from app.database.database import async_session
from app.keyboards.subscription_keyboard import subscription_keyboard
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService

router = Router()


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):

    async with async_session() as session:

        user_service = UserService(session)
        subscription_service = SubscriptionService(session)
        subscription_info_service = SubscriptionInfoService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        subscription = await subscription_service.get_active_subscription(
            user.id
        )

        if subscription is None:

            await message.answer(
                "❌ Sizda faol obuna mavjud emas.\n\n"
                "🛒 \"Obuna sotib olish\" bo'limidan tarif tanlang."
            )

            return

        info = await subscription_info_service.get_info(
            subscription.id
        )

    status = (
        "🟢 Faol"
        if subscription.status == "active"
        else "🔴 Faol emas"
    )

    subscription_url = (
        f"{config.MARZBAN_PUBLIC_URL}{info.subscription_url}"
    )

    await message.answer(
        f"👤 <b>Mening obunam</b>\n\n"
        f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
        f"💰 Narxi: <b>{subscription.plan.price} ₽</b>\n\n"
        f"👤 Username:\n"
        f"<code>{info.username}</code>\n\n"
        f"📅 Boshlangan sana:\n"
        f"{subscription.start_date.strftime('%d.%m.%Y')}\n\n"
        f"⏳ Tugash sanasi:\n"
        f"{subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        f"{status}\n\n"
        f"🔗 <b>VLESS havola:</b>\n"
        f"<code>{info.vpn_link}</code>",
        parse_mode="HTML",
        reply_markup=subscription_keyboard(
            subscription_url=subscription_url,
        ),
    )