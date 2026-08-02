from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService

router = Router()


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):

    async with async_session() as session:

        user_service = UserService(session)
        subscription_service = SubscriptionService(session)

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

    status = (
        "🟢 Faol"
        if subscription.status == "active"
        else "🔴 Faol emas"
    )

    await message.answer(
        f"👤 Mening obunam\n\n"
        f"📦 Tarif: {subscription.plan.name}\n"
        f"💰 Narxi: {subscription.plan.price} ₽\n\n"
        f"📅 Boshlangan sana:\n"
        f"{subscription.start_date.strftime('%d.%m.%Y')}\n\n"
        f"⏳ Tugash sanasi:\n"
        f"{subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        f"{status}"
    )