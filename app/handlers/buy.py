from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    Message,
)

from app.database.database import async_session
from app.keyboards.buy import buy_menu_keyboard
from app.keyboards.daily_subscription import (
    daily_subscription_keyboard,
)
from app.keyboards.tariffs import tariffs_keyboard
from app.services.plan_service import PlanService
from app.services.setting_service import SettingService


router = Router()


@router.message(F.text == "🛒 Obuna sotib olish")
async def buy_subscription(message: Message):

    await message.answer(
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "Kerakli obuna turini tanlang:",
        parse_mode="HTML",
        reply_markup=buy_menu_keyboard(),
    )


@router.callback_query(F.data == "buy_plans")
async def buy_plans(callback: CallbackQuery):

    await callback.answer()

    async with async_session() as session:

        plan_service = PlanService(session)

        plans = await plan_service.get_all_active_plans()

    if not plans:

        await callback.message.edit_text(
            "📦 <b>VPN TARIFLARI</b>\n\n"
            "Hozircha faol tariflar mavjud emas.",
            parse_mode="HTML",
        )

        return

    await callback.message.edit_text(
        "📦 <b>VPN TARIFLARI</b>\n\n"
        "⬇️ Kerakli tarifni tanlang:",
        parse_mode="HTML",
        reply_markup=tariffs_keyboard(plans),
    )


@router.callback_query(F.data == "buy_daily")
async def buy_daily(callback: CallbackQuery):

    await callback.answer()

    async with async_session() as session:

        setting_service = SettingService(session)

        daily_price = await setting_service.get_daily_price()

    await callback.message.edit_text(
        "📅 <b>KUNLIK OBUNA</b>\n\n"
        f"💰 1 kunlik narx: "
        f"<b>{daily_price} ₽</b>\n\n"
        "Necha kun foydalanmoqchisiz?",
        parse_mode="HTML",
        reply_markup=daily_subscription_keyboard(
            daily_price=daily_price,
        ),
    )