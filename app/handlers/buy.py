from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.tariffs import tariffs_keyboard
from app.services.plan_service import PlanService

router = Router()


@router.message(F.text == "🛒 Obuna sotib olish")
async def buy_subscription(message: Message):

    async with async_session() as session:

        plan_service = PlanService(session)

        plans = await plan_service.get_all_active_plans()

    await message.answer(
        "📦 VPN tariflari\n\n"
        "⬇️ Tarifni tanlang:",
        reply_markup=tariffs_keyboard(plans),
    )