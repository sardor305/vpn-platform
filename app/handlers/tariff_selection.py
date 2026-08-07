from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.database import async_session
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService

router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def select_tariff(callback: CallbackQuery):

    # Telegram callback'ni darhol yopamiz
    await callback.answer()

    plan_id = int(callback.data.split(":")[1])

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

        result = await purchase_service.purchase(
            user_id=user.id,
            plan_id=plan_id,
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

    text = (
        f"🎉 <b>VPN muvaffaqiyatli yaratildi!</b>\n\n"
        f"📦 <b>Tarif:</b> {result.plan.name}\n"
        f"💰 <b>Narxi:</b> {result.plan.price} ₽\n"
        f"📅 <b>Amal qilish muddati:</b> "
        f"{result.subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        f"🔗 <b>VLESS havola:</b>\n"
        f"<code>{result.vpn_link}</code>\n\n"
        f"🔄 <b>Subscription:</b>\n"
        f"<code>{result.subscription_url}</code>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
    )