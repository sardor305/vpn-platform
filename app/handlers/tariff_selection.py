from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.database import async_session
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService

router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def select_tariff(callback: CallbackQuery):

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

    if not result.success:
        await callback.answer(
            result.message,
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"✅ {result.message}\n\n"
        f"📦 Tarif: {result.plan.name}\n"
        f"💰 Narxi: {result.plan.price} ₽\n"
        f"📅 Amal qiladi:\n"
        f"{result.subscription.end_date.strftime('%d.%m.%Y')} gacha"
    )
    
    await callback.answer()