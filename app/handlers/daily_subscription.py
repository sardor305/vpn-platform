from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.buy import buy_menu_keyboard
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService
from app.states.daily_subscription import DailySubscriptionStates


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


@router.callback_query(F.data == "daily_custom")
async def daily_custom(
    callback: CallbackQuery,
    state: FSMContext,
):

    await callback.answer()

    await state.set_state(
        DailySubscriptionStates.waiting_for_days
    )

    await callback.message.edit_text(
        "✏️ <b>Kunlik obuna muddatini kiriting</b>\n\n"
        "Necha kunlik VPN kerakligini yozing.\n\n"
        "Masalan: <b>10</b>",
        parse_mode="HTML",
    )


@router.message(
    DailySubscriptionStates.waiting_for_days
)
async def process_custom_days(
    message: Message,
    state: FSMContext,
):

    if not message.text:
        await message.answer(
            "❗ Iltimos, kun sonini raqam bilan kiriting."
        )
        return

    try:
        duration_days = int(
            message.text.strip()
        )
    except ValueError:

        await message.answer(
            "❗ Iltimos, faqat raqam kiriting.\n\n"
            "Masalan: <b>10</b>",
            parse_mode="HTML",
        )
        return

    if duration_days <= 7:

        await message.answer(
            "❗ Bu bo‘lim 7 kundan ko‘p muddat uchun.\n\n"
            "1–7 kunlik obuna uchun menyudagi "
            "tayyor tugmalardan foydalaning."
        )
        return

    async with async_session() as session:

        user_service = UserService(session)
        purchase_service = PurchaseService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        result = await purchase_service.purchase_daily(
            user_id=user.id,
            duration_days=duration_days,
        )

        if result.success:
            await session.commit()
        else:
            await session.rollback()

    await state.clear()

    if not result.success:

        await message.answer(
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

    await message.answer(
        text,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "buy_back")
async def buy_back(
    callback: CallbackQuery,
    state: FSMContext,
):

    await callback.answer()

    await state.clear()

    await callback.message.edit_text(
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "Kerakli obuna turini tanlang:",
        parse_mode="HTML",
        reply_markup=buy_menu_keyboard(),
    )