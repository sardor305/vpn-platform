from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.database.database import async_session
from app.keyboards.buy import buy_menu_keyboard
from app.keyboards.daily_subscription import daily_subscription_keyboard
from app.keyboards.tariffs import tariffs_keyboard
from app.keyboards.user_navigation import append_navigation
from app.services.plan_service import PlanService
from app.services.setting_service import SettingService


router = Router()


@router.message(F.text == "🛒 Obuna sotib olish")
async def buy_subscription(message: Message):
    await message.answer(
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "Kerakli obuna turini tanlang:",
        parse_mode="HTML",
        reply_markup=_buy_menu_with_back_keyboard(),
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
            reply_markup=_plans_navigation_keyboard(),
        )
        return

    await callback.message.edit_text(
        "📦 <b>VPN TARIFLARI</b>\n\n"
        "⬇️ Kerakli tarifni tanlang:",
        parse_mode="HTML",
        reply_markup=_with_navigation(
            tariffs_keyboard(plans),
            back_callback="buy_back",
        ),
    )


@router.callback_query(F.data == "buy_daily")
async def buy_daily(callback: CallbackQuery):
    await callback.answer()

    async with async_session() as session:
        setting_service = SettingService(session)
        daily_price = await setting_service.get_daily_price()

    await callback.message.edit_text(
        "📅 <b>KUNLIK OBUNA</b>\n\n"
        f"💰 1 kunlik narx: <b>{daily_price} ₽</b>\n\n"
        "Necha kun foydalanmoqchisiz?",
        parse_mode="HTML",
        reply_markup=_with_navigation(
            daily_subscription_keyboard(
                daily_price=daily_price,
            ),
            back_callback="buy_back",
        ),
    )


@router.callback_query(F.data == "buy_back")
async def buy_back(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "Kerakli obuna turini tanlang:",
        parse_mode="HTML",
        reply_markup=_buy_menu_with_back_keyboard(),
    )


def _buy_menu_with_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = buy_menu_keyboard()
    rows = [list(row) for row in keyboard.inline_keyboard]
    rows.append(
        [
            InlineKeyboardButton(
                text="↩️ Ortga",
                callback_data="user_back",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _with_navigation(
    keyboard: InlineKeyboardMarkup,
    *,
    back_callback: str,
) -> InlineKeyboardMarkup:
    return append_navigation(
        keyboard,
        back_callback=back_callback,
    )


def _plans_navigation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Ortga",
                    callback_data="buy_back",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Yopish",
                    callback_data="user_close",
                ),
            ],
        ]
    )
