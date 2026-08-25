from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.database import async_session
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService


router = Router()


@router.callback_query(F.data.startswith("daily_buy:"))
async def buy_daily_subscription(
    callback: CallbackQuery,
):

    await callback.answer()

    duration_days = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)
        purchase_service = PurchaseService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            language_code=callback.from_user.language_code,
        )

        result = await purchase_service.purchase_daily(
            user_id=user.id,
            duration_days=duration_days,
        )

        if result.success:
            await session.commit()
        else:
            await session.rollback()

    if not result.success:

        await callback.message.answer(
            result.message,
        )

        return

    daily_subscription = result.daily_subscription

    text = (
        "🎉 <b>VPN muvaffaqiyatli yaratildi!</b>\n\n"
        "📅 <b>Obuna turi:</b> Kunlik\n"
        f"⏳ <b>Muddat:</b> "
        f"{daily_subscription.duration_days} kun\n"
        f"💰 <b>Narxi:</b> "
        f"{daily_subscription.price} ₽\n"
        f"📅 <b>Amal qilish muddati:</b> "
        f"{daily_subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        "🔗 <b>VLESS havola:</b>\n"
        f"<code>{result.vpn_link}</code>\n\n"
        "🔄 <b>Subscription:</b>\n"
        f"<code>{result.subscription_url}</code>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
    )