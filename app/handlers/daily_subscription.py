from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.buy import buy_menu_keyboard
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService
from app.states.daily_subscription import DailySubscriptionStates


router = Router()


def _format_daily_result(result) -> str:
    daily_subscription = result.daily_subscription

    if daily_subscription is None:
        return "❌ <b>Kunlik obuna ma'lumotlari topilmadi.</b>"

    if daily_subscription.status == "active" and daily_subscription.end_date is not None:
        status_text = "🟢 <b>Faol</b>"
        period_text = (
            f"📅 <b>Amal qilish muddati:</b> "
            f"{daily_subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        )
    else:
        status_text = "⏳ <b>Navbatda</b>"
        period_text = (
            "📅 <b>Amal qilish muddati:</b> "
            "Hozirgi xizmat tugagach avtomatik boshlanadi.\n\n"
        )

    if result.vpn_link:
        vpn_text = (
            "🔗 <b>VLESS havola:</b>\n"
            f"<code>{result.vpn_link}</code>\n\n"
        )
    else:
        vpn_text = (
            "🔗 <b>VLESS havola:</b>\n"
            "Faol xizmat davri boshlanganda mavjud bo‘ladi.\n\n"
        )

    if result.subscription_url:
        subscription_text = (
            "🔄 <b>Subscription:</b>\n"
            f"<code>{result.subscription_url}</code>"
        )
    else:
        subscription_text = (
            "🔄 <b>Subscription:</b>\n"
            "Faol xizmat davri boshlanganda mavjud bo‘ladi."
        )

    if daily_subscription.status == "active":
        title = "🎉 <b>VPN muvaffaqiyatli faollashtirildi!</b>"
    else:
        title = "✅ <b>Kunlik obuna muvaffaqiyatli xarid qilindi!</b>"

    return (
        f"{title}\n\n"
        "📅 <b>Obuna turi:</b> Kunlik\n"
        f"⏳ <b>Muddat:</b> {daily_subscription.duration_days} kun\n"
        f"💰 <b>Narxi:</b> {daily_subscription.price} ₽\n"
        f"{status_text}\n"
        f"{period_text}"
        f"{vpn_text}"
        f"{subscription_text}"
    )


async def _purchase_daily(*, telegram_user, duration_days: int):
    async with async_session() as session:
        user_service = UserService(session)
        purchase_service = PurchaseService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
        )

        result = await purchase_service.purchase_daily(
            user_id=user.id,
            duration_days=duration_days,
        )

        if result.success:
            await session.commit()
        else:
            await session.rollback()

        return result


@router.callback_query(F.data.startswith("daily_buy:"))
async def buy_daily_subscription(callback: CallbackQuery):
    await callback.answer()

    try:
        duration_days = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.answer("❗ Kunlik obuna muddati noto‘g‘ri.")
        return

    if duration_days <= 0:
        await callback.message.answer("❗ Kunlik obuna muddati noto‘g‘ri.")
        return

    result = await _purchase_daily(
        telegram_user=callback.from_user,
        duration_days=duration_days,
    )

    if not result.success:
        await callback.message.answer(result.message)
        return

    await callback.message.edit_text(
        _format_daily_result(result),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "daily_custom")
async def daily_custom(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.set_state(DailySubscriptionStates.waiting_for_days)

    await callback.message.edit_text(
        "✏️ <b>Kunlik obuna muddatini kiriting</b>\n\n"
        "Necha kunlik VPN kerakligini yozing.\n\n"
        "Masalan: <b>10</b>",
        parse_mode="HTML",
    )


@router.message(DailySubscriptionStates.waiting_for_days)
async def process_custom_days(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❗ Iltimos, kun sonini raqam bilan kiriting.")
        return

    try:
        duration_days = int(message.text.strip())
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
            "1–7 kunlik obuna uchun menyudagi tayyor tugmalardan foydalaning."
        )
        return

    result = await _purchase_daily(
        telegram_user=message.from_user,
        duration_days=duration_days,
    )

    await state.clear()

    if not result.success:
        await message.answer(result.message)
        return

    await message.answer(
        _format_daily_result(result),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "buy_back")
async def buy_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.clear()

    await callback.message.edit_text(
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "Kerakli obuna turini tanlang:",
        parse_mode="HTML",
        reply_markup=buy_menu_keyboard(),
    )