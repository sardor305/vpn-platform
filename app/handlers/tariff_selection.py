from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.database import async_session
from app.services.plan_service import PlanService

router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def select_tariff(callback: CallbackQuery):

    plan_id = int(callback.data.split(":")[1])

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(plan_id)

    if plan is None:
        await callback.answer(
            "Tarif topilmadi.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"✅ Siz tanladingiz:\n\n"
        f"{plan.name}\n"
        f"💰 {plan.price} ₽\n\n"
        f"Keyingi bosqich: to'lov usulini tanlash."
    )

    await callback.answer()