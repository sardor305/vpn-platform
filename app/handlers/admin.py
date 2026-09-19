from datetime import datetime, timezone
from html import escape
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.keyboards.admin import (
    admin_menu,
    users_menu,
    vpn_account_actions_keyboard,
    vpn_accounts_keyboard,
)
from app.keyboards.menu import main_menu
from app.models.daily_subscription import DailySubscription
from app.models.promo import Promo
from app.models.promo_redemption import PromoRedemption
from app.models.user_bonus import UserBonus
from app.services.plan_service import PlanService
from app.services.bonus_statistics_service import (
    BonusStatisticsService,
    BonusTypeStats,
)
from app.services.user_bonus_service import UserBonusService
from app.services.setting_service import SettingService
from app.services.statistics_service import StatisticsService
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.services.vpn_account_service import VPNAccountService
from app.utils.datetime import utc_now
from app.utils.admin_navigation import (
    admin_back_keyboard,
    delete_last_admin_message,
    remember_admin_message,
    replace_with_admin_panel,
    send_admin_panel,
)


router = Router()


class AdminSearchStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_custom_plan_days = State()
    waiting_for_custom_extend_days = State()
    waiting_for_daily_price = State()
    waiting_for_admin_bonus_days = State()
    waiting_for_admin_bonus_reason = State()


@router.callback_query(
    F.data == "daily_price:change"
)
async def daily_price_change(
    callback: CallbackQuery,
    state: FSMContext,
):

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    await callback.answer()

    await state.set_state(
        AdminSearchStates.waiting_for_daily_price
    )

    await callback.message.answer(
        "✏️ <b>KUNLIK NARXNI O‘ZGARTIRISH</b>\n\n"
        "1 kunlik narxni rublda kiriting.\n\n"
        "Masalan:\n"
        "<code>10</code>\n"
        "<code>15</code>\n"
        "<code>20</code>",
        parse_mode="HTML",
    )


@router.message(
    AdminSearchStates.waiting_for_daily_price
)
async def process_daily_price(
    message: Message,
    state: FSMContext,
):

    admin = await get_admin(
        telegram_id=message.from_user.id
    )

    if admin is None or not admin.is_admin:
        await state.clear()
        return

    value = (message.text or "").strip()

    if not value.isdigit():
        await message.answer(
            "❌ Faqat raqam kiriting.\n\n"
            "Masalan: <code>10</code>",
            parse_mode="HTML",
        )
        return

    daily_price = int(value)

    if daily_price <= 0:
        await message.answer(
            "❌ Narx 0 dan katta bo‘lishi kerak.",
            parse_mode="HTML",
        )
        return

    async with async_session() as session:

        setting_service = SettingService(
            session=session,
        )

        await setting_service.set_daily_price(
            price=daily_price
        )

        await session.commit()

    await state.clear()

    await message.answer(
        f"✅ 1 kunlik narx: <b>{daily_price} RUB</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.callback_query(F.data == "daily_price:back")
async def daily_price_back(callback: CallbackQuery):
    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()
    await _replace_callback_with_admin_panel(callback)


async def _replace_callback_with_admin_panel(
    callback: CallbackQuery,
) -> Message:
    """Delete the current inline screen and open a fresh admin panel."""
    try:
        await callback.message.delete()
    except Exception:
        pass

    sent = await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="👨‍💼 <b>ADMIN PANEL</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )
    await remember_admin_message(sent)
    return sent


async def get_admin(
    telegram_id: int,
):
    async with async_session() as session:

        user_service = UserService(session)

        return await user_service.get_by_telegram_id(
            telegram_id=telegram_id
        )


def vpn_delete_confirmation_keyboard(
    account_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Ha, o‘chirish",
                    callback_data=f"vpn_delete_confirm:{account_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"vpn_delete_cancel:{account_id}",
                ),
            ],
        ]
    )


def search_result_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Yangilash",
                    callback_data=f"search_refresh:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📋 VPN link",
                    callback_data=f"search_vpn_link:{user_id}",
                ),
                InlineKeyboardButton(
                    text="🔗 Subscription",
                    callback_data=f"search_subscription:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Obuna / tarifni boshqarish",
                    callback_data=f"search_change_plan:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📜 Obunalar tarixi",
                    callback_data=f"search_subscription_history:{user_id}:1",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Bonus statistikasi",
                    callback_data=f"search_bonus_stats:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Muddatni boshqarish",
                    callback_data=f"search_extend:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 VPNni o‘chirish",
                    callback_data=f"search_delete_vpn:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data="search_admin_panel",
                ),
            ],
        ]
    )


def search_vpn_delete_confirmation_keyboard(
    user_id: int,
    account_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Ha, o‘chirish",
                    callback_data=(
                        f"search_delete_vpn_confirm:"
                        f"{user_id}:{account_id}"
                    ),
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=(
                        f"search_delete_vpn_cancel:{user_id}"
                    ),
                ),
            ],
        ]
    )


def subscription_plans_keyboard(
    user_id: int,
    plans,
) -> InlineKeyboardMarkup:

    buttons = []

    for plan in plans:

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"📦 {plan.name} — "
                        f"{plan.price} — "
                        f"{plan.duration_days} kun"
                    ),
                    callback_data=(
                        f"search_plan:{user_id}:{plan.id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data=f"search_plan_cancel:{user_id}",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def format_datetime(
    value,
) -> str:

    if value is None:
        return "—"

    return value.strftime(
        "%d.%m.%Y %H:%M"
    )


def format_traffic(
    value,
) -> str:

    if value is None:
        return "—"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"

    if value < 1024:
        return f"{int(value)} B"

    units = [
        "KB",
        "MB",
        "GB",
        "TB",
        "PB",
    ]

    size = value

    for unit in units:

        size /= 1024

        if size < 1024:
            return f"{size:.2f} {unit}"

    return f"{size:.2f} EB"


def format_marzban_status(
    status: str | None,
) -> str:

    if not status:
        return "—"

    statuses = {
        "active": "🟢 Faol",
        "disabled": "🔴 O‘chirilgan",
        "expired": "🟠 Muddati tugagan",
        "limited": "🟠 Trafik limiti tugagan",
        "on_hold": "🟡 Kutishda",
    }

    return statuses.get(
        status,
        f"⚪ {escape(status)}",
    )


def format_marzban_expire(
    value,
) -> str:

    if value is None:
        return "—"

    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return "—"

    if timestamp == 0:
        return "♾ Cheklanmagan"

    try:
        date = datetime.fromtimestamp(
            timestamp,
            timezone.utc,
        )

        return (
            f"{date.strftime('%d.%m.%Y %H:%M')} UTC"
        )

    except (OverflowError, OSError, ValueError):
        return "—"


def format_marzban_online_at(
    value,
) -> str:

    if not value:
        return "Hozircha ulanmagan"

    if isinstance(value, datetime):

        date = value

    else:

        try:

            value = str(value)

            if value.endswith("Z"):
                value = value[:-1] + "+00:00"

            date = datetime.fromisoformat(
                value
            )

        except ValueError:
            return escape(str(value))

    if date.tzinfo is None:

        date = date.replace(
            tzinfo=timezone.utc
        )

    return (
        f"{date.astimezone(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')} UTC"
    )


def format_marzban_data_limit(
    value,
) -> str:

    if value is None:
        return "♾ Cheklanmagan"

    try:
        value = int(value)
    except (TypeError, ValueError):
        return "—"

    if value == 0:
        return "♾ Cheklanmagan"

    return format_traffic(value)


async def get_marzban_user_data(
    username: str,
):

    try:

        marzban_service = create_marzban_service()

        return await marzban_service.get_user(
            username=username,
        )

    except Exception as e:

        print(
            "MARZBAN GET USER ERROR:",
            repr(e),
        )

        return None


async def show_vpn_account_detail(
    message: Message,
    account,
):
    user = account.user

    username = (
        f"@{user.username}"
        if user.username
        else "—"
    )

    full_name = escape(
        user.first_name
    )

    if user.last_name:
        full_name += (
            f" {escape(user.last_name)}"
        )

    status = (
        "🟢 Faol"
        if account.is_active
        else "🔴 Faol emas"
    )

    text = (
        f"🔑 <b>VPN ACCOUNT #{account.id}</b>\n\n"

        "👤 <b>FOYDALANUVCHI</b>\n"
        f"├ User ID: <code>{user.id}</code>\n"
        f"├ Ism: {full_name}\n"
        f"├ Username: {escape(username)}\n"
        f"└ Telegram ID: "
        f"<code>{user.telegram_id}</code>\n\n"

        "🔐 <b>VPN</b>\n"
        f"├ Protocol: "
        f"<b>{escape(account.protocol.upper())}</b>\n"
        f"├ Marzban username: "
        f"<code>{escape(account.marzban_username)}</code>\n"
        f"└ Status: {status}"
    )

    await message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_account_actions_keyboard(
            account_id=account.id,
            is_active=account.is_active,
        ),
    )


async def show_user_search_result(
    message: Message,
    user,
):
    async with async_session() as session:

        subscription_info_service = SubscriptionInfoService(
            session=session,
        )

        info = await subscription_info_service.get_info(
            user_id=user.id
        )

    subscription = info["subscription"]
    vpn_account = info["vpn_account"]

    full_name = escape(
        user.first_name
    )

    if user.last_name:
        full_name += (
            f" {escape(user.last_name)}"
        )

    username = (
        f"@{escape(user.username)}"
        if user.username
        else "—"
    )

    phone = (
        escape(user.phone_number)
        if user.phone_number
        else "—"
    )

    user_status = (
        "🟢 Faol"
        if user.is_active
        else "🔴 Faol emas"
    )

    text = (
        "🔎 <b>QIDIRUV NATIJASI</b>\n\n"

        "👤 <b>FOYDALANUVCHI</b>\n"
        f"├ User ID: <code>{user.id}</code>\n"
        f"├ Telegram ID: <code>{user.telegram_id}</code>\n"
        f"├ Ism: {full_name}\n"
        f"├ Username: {username}\n"
        f"├ Telefon: {phone}\n"
        f"├ Til: <code>{escape(user.language_code)}</code>\n"
        f"└ Status: {user_status}\n\n"
    )

    if subscription is None:

        text += (
            "📦 <b>OBUNA</b>\n"
            "└ Faol obuna mavjud emas.\n\n"
        )

    else:

        plan = subscription.plan

        subscription_status = (
            "🟢 Faol"
            if subscription.status == "active"
            else f"🔴 {escape(subscription.status)}"
        )

        text += (
            "📦 <b>OBUNA</b>\n"
            f"├ Tarif: <b>{escape(plan.name)}</b>\n"
            f"├ Narx: <b>{plan.price}</b>\n"
            f"├ Boshlanishi: "
            f"{format_datetime(subscription.start_date)}\n"
            f"├ Tugashi: "
            f"{format_datetime(subscription.end_date)}\n"
            f"└ Status: {subscription_status}\n\n"
        )

    marzban_data = None

    if vpn_account is None:

        text += (
            "🔐 <b>VPN</b>\n"
            "└ VPN hisob mavjud emas."
        )

    else:

        vpn_status = (
            "🟢 Faol"
            if vpn_account.is_active
            else "🔴 Faol emas"
        )

        text += (
            "🔐 <b>VPN</b>\n"
            f"├ Account ID: <code>{vpn_account.id}</code>\n"
            f"├ Marzban username: "
            f"<code>{escape(vpn_account.marzban_username)}</code>\n"
            f"├ Protocol: "
            f"<b>{escape(vpn_account.protocol.upper())}</b>\n"
            f"└ DB Status: {vpn_status}\n"
        )

        marzban_data = await get_marzban_user_data(
            username=vpn_account.marzban_username,
        )

        if marzban_data is None:

            text += (
                "\n"
                "☁️ <b>MARZBAN — REAL TIME</b>\n"
                "└ ⚠️ Marzban'dan ma'lumot olib bo‘lmadi.\n"
            )

        else:

            marzban_status = (
                marzban_data.get("status")
            )

            used_traffic = (
                marzban_data.get(
                    "used_traffic"
                )
            )

            lifetime_used_traffic = (
                marzban_data.get(
                    "lifetime_used_traffic"
                )
            )

            expire = (
                marzban_data.get("expire")
            )

            online_at = (
                marzban_data.get("online_at")
            )

            data_limit = (
                marzban_data.get("data_limit")
            )

            text += (
                "\n"
                "☁️ <b>MARZBAN — REAL TIME</b>\n"
                f"├ Status: "
                f"{format_marzban_status(marzban_status)}\n"
                f"├ Traffic: "
                f"<b>{format_traffic(used_traffic)}</b>\n"
                f"├ Lifetime traffic: "
                f"<b>{format_traffic(lifetime_used_traffic)}</b>\n"
                f"├ Expire: "
                f"<b>{format_marzban_expire(expire)}</b>\n"
                f"├ Online: "
                f"{format_marzban_online_at(online_at)}\n"
                f"└ Data limit: "
                f"<b>{format_marzban_data_limit(data_limit)}</b>\n"
            )

        vpn_link = (
            marzban_data.get("links", [None])[0]
            if marzban_data
            and marzban_data.get("links")
            else vpn_account.vpn_link
        )

        subscription_url = (
            marzban_data.get("subscription_url")
            if marzban_data
            else vpn_account.subscription_url
        )

        text += "\n"

        text += (
            "🔗 <b>VPN LINK</b>\n"
            f"<code>{escape(vpn_link or '—')}</code>\n\n"

            "🔗 <b>SUBSCRIPTION URL</b>\n"
            f"<code>{escape(subscription_url or '—')}</code>"
        )

    return await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=search_result_keyboard(
            user_id=user.id,
        ),
    )


@router.message(F.text == "admin")
async def admin_panel(message: Message):
    user = await get_admin(
        telegram_id=message.from_user.id
    )
    if user is None or not user.is_admin:
        return
    await send_admin_panel(message)


@router.message(F.text == "🔎 Qidiruv")
async def search_user(
    message: Message,
    state: FSMContext,
):

    user = await get_admin(
        telegram_id=message.from_user.id
    )

    if user is None or not user.is_admin:
        return

    await delete_last_admin_message(message)

    await state.set_state(
        AdminSearchStates.waiting_for_user_id
    )

    sent = await message.answer(
        "🔎 <b>Foydalanuvchi qidirish</b>\n\n"
        "User ID yoki Telegram ID raqamini yuboring.\n\n"
        "Masalan:\n"
        "<code>7</code>\n"
        "yoki\n"
        "<code>522599954</code>",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard("search_admin_panel"),
    )
    await remember_admin_message(sent)


@router.message(
    AdminSearchStates.waiting_for_user_id
)
async def process_user_search(
    message: Message,
    state: FSMContext,
):

    user = await get_admin(
        telegram_id=message.from_user.id
    )

    if user is None or not user.is_admin:

        await state.clear()

        return

    search_value = (
        message.text or ""
    ).strip()

    if not search_value.isdigit():

        await message.answer(
            "❌ <b>Noto‘g‘ri format.</b>\n\n"
            "Iltimos, User ID yoki Telegram ID "
            "raqamini yuboring.",
            parse_mode="HTML",
        )

        return

    search_id = int(
        search_value
    )

    async with async_session() as session:

        user_service = UserService(session)

        found_user = await user_service.get_by_id(
            user_id=search_id
        )

        if found_user is None:

            found_user = (
                await user_service.get_by_telegram_id(
                    telegram_id=search_id
                )
            )

    await state.clear()
    await delete_last_admin_message(message)

    if found_user is None:

        await message.answer(
            "❌ <b>Foydalanuvchi topilmadi.</b>\n\n"
            f"Qidirilgan raqam: "
            f"<code>{search_id}</code>",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    sent = await show_user_search_result(
        message=message,
        user=found_user,
    )
    await remember_admin_message(sent)



@router.callback_query(F.data.startswith("search_bonus_stats:"))
async def search_bonus_statistics(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id,
    )
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id=user_id)
        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        service = BonusStatisticsService(session)
        stats = await service.get_user_statistics(user_id=user_id)

    welcome = stats.by_type.get("welcome", BonusTypeStats())
    promo = stats.by_type.get("promo", BonusTypeStats())
    referral = stats.by_type.get("referral", BonusTypeStats())
    admin_bonus = stats.by_type.get("admin", BonusTypeStats())
    traffic = stats.welcome_traffic
    ref = stats.referral
    promo_stats = stats.promo

    full_name = escape(user.first_name)
    if user.last_name:
        full_name += f" {escape(user.last_name)}"

    text = (
        "👤 <b>USER BONUS STATISTIKASI</b>\n\n"
        f"├ User ID: <code>{user.id}</code>\n"
        f"├ Ism: {full_name}\n"
        f"└ Telegram ID: <code>{user.telegram_id}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎁 <b>BONUSLAR</b>\n"
        f"├ Jami: <b>{stats.total}</b>\n"
        f"├ 🟢 Faol: <b>{stats.active}</b>\n"
        f"├ ⏳ Kutilmoqda: <b>{stats.pending}</b>\n"
        f"├ ⚪ Tugagan: <b>{stats.expired}</b>\n"
        f"└ 🚫 Bekor qilingan: <b>{stats.revoked}</b>\n\n"
        "🎁 <b>BONUS TURLARI</b>\n"
        f"├ 🎁 Welcome: <b>{welcome.total}</b>\n"
        f"├ 🎟 Promo: <b>{promo.total}</b>\n"
        f"├ 🤝 Referral: <b>{referral.total}</b>\n"
        f"└ 👨‍💼 Admin: <b>{admin_bonus.total}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📦 <b>WELCOME</b>\n"
        f"├ Jami: <b>{traffic.total_welcome}</b>\n"
        f"├ 🟢 Faol: <b>{traffic.active}</b>\n"
        f"├ ⏳ Navbatda: <b>{traffic.pending}</b>\n"
        f"├ ⚪ Tugagan: <b>{traffic.expired}</b>\n"
        f"├ Limit: <b>{format_traffic(traffic.total_limit_bytes)}</b>\n"
        f"├ Ishlatilgan: <b>{format_traffic(traffic.total_used_bytes)}</b>\n"
        f"└ Qolgan: <b>{format_traffic(traffic.remaining_bytes)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤝 <b>REFERRAL</b>\n"
        f"├ Taklif qilgan: <b>{ref.total}</b>\n"
        f"├ ✅ Rewardga aylangan: <b>{ref.rewarded}</b>\n"
        f"├ ⏳ Hali xarid qilmagan: <b>{ref.pending}</b>\n"
        f"├ 🎁 Referral bonuslari: <b>{referral.total}</b>\n"
        f"└ 📅 Jami bonus muddati: <b>{ref.total_reward_days} kun</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎟 <b>PROMO</b>\n"
        f"├ Redeem qilingan: <b>{promo_stats.redemptions}</b>\n"
        f"├ 🎁 Promo bonuslari: <b>{promo_stats.bonuses}</b>\n"
        f"├ 🟢 Faol: <b>{promo_stats.active}</b>\n"
        f"├ ⏳ Kutilmoqda: <b>{promo_stats.pending}</b>\n"
        f"├ ⚪ Tugagan: <b>{promo_stats.expired}</b>\n"
        f"└ 📅 Jami bonus muddati: <b>{promo_stats.total_duration_days} kun</b>"
    )

    await callback.answer()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=bonus_user_statistics_keyboard(user_id),
    )



@router.callback_query(F.data.startswith("search_bonus_history:"))
async def search_bonus_history(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id,
    )
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id=user_id)
        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        bonus_result = await session.execute(
            select(UserBonus)
            .options(selectinload(UserBonus.traffic))
            .where(UserBonus.user_id == user_id)
            .order_by(
                UserBonus.created_at.desc(),
                UserBonus.id.desc(),
            )
        )
        bonuses = list(bonus_result.scalars().all())

        promo_result = await session.execute(
            select(PromoRedemption, Promo)
            .join(Promo, Promo.id == PromoRedemption.promo_id)
            .where(PromoRedemption.user_id == user_id)
        )
        promo_by_bonus = {
            redemption.bonus_id: promo
            for redemption, promo in promo_result.all()
        }

    if not bonuses:
        text = (
            "📜 <b>BONUSLAR TARIXI</b>\n\n"
            "Hozircha bonuslar mavjud emas."
        )
    else:
        lines = [
            "📜 <b>BONUSLAR TARIXI</b>",
            "",
        ]

        type_names = {
            "welcome": "🎁 Welcome Bonus",
            "promo": "🎟 Promo Bonus",
            "referral": "🤝 Referral Bonus",
            "admin": "👨‍💼 Admin Bonus",
        }
        status_names = {
            "active": "🟢 Faol",
            "pending": "⏳ Kutilmoqda",
            "expired": "⚪ Tugagan",
            "revoked": "🚫 Bekor qilingan",
        }

        for index, bonus in enumerate(bonuses, start=1):
            name = type_names.get(
                bonus.bonus_type,
                bonus.bonus_type,
            )
            number = (
                f" #{bonus.bonus_number}"
                if bonus.bonus_number is not None
                else ""
            )
            status = status_names.get(
                bonus.status,
                f"⚪ {escape(bonus.status)}",
            )

            lines.append(f"<b>{index}.</b> {name}{number}")
            lines.append(
                f"   ⏳ Muddat: <b>{bonus.duration_days} kun</b>"
            )

            if bonus.bonus_type == "welcome" and bonus.traffic:
                limit = bonus.traffic.traffic_limit_bytes
                used = bonus.traffic.traffic_used_bytes
                remaining = max(limit - used, 0)
                lines.append(
                    f"   📦 Limit: <b>{format_traffic(limit)}</b>"
                )
                lines.append(
                    f"   📊 Ishlatilgan: <b>{format_traffic(used)}</b>"
                )
                lines.append(
                    f"   📉 Qolgan: <b>{format_traffic(remaining)}</b>"
                )
            elif bonus.bonus_type in {"promo", "referral", "admin"}:
                lines.append("   📡 Trafik: <b>Cheksiz</b>")

            if bonus.bonus_type == "promo":
                promo = promo_by_bonus.get(bonus.id)
                if promo is not None:
                    lines.append(
                        f"   🔑 Promokod: <code>{escape(promo.code)}</code>"
                    )

            if bonus.bonus_type == "admin" and bonus.reason:
                lines.append(
                    f"   📝 Sabab: {escape(bonus.reason)}"
                )

            if bonus.bonus_type == "referral" and bonus.referral_id:
                lines.append(
                    f"   🔢 Referral: <b>#{bonus.bonus_number}</b>"
                )

            lines.append(f"   {status}")
            lines.append(
                f"   📅 Yaratilgan: {format_datetime(bonus.created_at)}"
            )
            lines.append("")

        text = "\n".join(lines).rstrip()

    await callback.answer()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=bonus_user_statistics_keyboard(user_id),
    )


@router.callback_query(F.data.startswith("search_bonus_stats_back:"))
async def search_bonus_statistics_back(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id,
    )
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id=user_id)
        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

    await callback.answer()
    await show_user_search_result(
        message=callback.message,
        user=user,
    )


# ============================================================
# OBUNANI O‘ZGARTIRISH — TARIFLAR RO‘YXATI
# ============================================================

@router.callback_query(
    F.data.startswith("search_change_plan:")
)
async def search_change_plan(
    callback: CallbackQuery,
):

    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

        if user is None:

            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )

            return

        plan_service = PlanService(session)

        plans = await plan_service.get_all_active_plans()

    if not plans:

        await callback.answer(
            "Faol tariflar mavjud emas.",
            show_alert=True,
        )

        return

    await callback.answer()

    await callback.message.edit_text(
        "📦 <b>OBUNANI O‘ZGARTIRISH</b>\n\n"
        "Yangi tarifni tanlang:",
        parse_mode="HTML",
        reply_markup=subscription_plans_keyboard(
            user_id=user_id,
            plans=plans,
        ),
    )


# ============================================================
# OBUNANI O‘ZGARTIRISH — TARIFNI TANLASH
# ============================================================

@router.callback_query(
    F.data.startswith("search_plan:")
)
async def search_plan(
    callback: CallbackQuery,
):

    parts = callback.data.split(":")

    if len(parts) != 3:

        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )

        return

    user_id = int(parts[1])
    plan_id = int(parts[2])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

        if user is None:

            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )

            return

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id=plan_id
        )

        if plan is None or not plan.is_active:

            await callback.answer(
                "Tanlangan tarif mavjud emas yoki faol emas.",
                show_alert=True,
            )

            return

        subscription_service = SubscriptionService(
            session=session
        )

        subscription = (
            await subscription_service
            .get_active_subscription(
                user_id=user_id
            )
        )

        if subscription is not None:

            old_plan = subscription.plan

            await subscription_service.change_plan(
                subscription=subscription,
                plan_id=plan.id,
            )

            await session.commit()

            result_text = (
                "✅ <b>OBUNA TARIFI O‘ZGARTIRILDI</b>\n\n"
                f"👤 User ID: <code>{user_id}</code>\n"
                f"📦 Eski tarif: "
                f"<b>{escape(old_plan.name)}</b>\n"
                f"📦 Yangi tarif: "
                f"<b>{escape(plan.name)}</b>\n\n"
                "📅 Obuna muddati o‘zgartirilmadi.\n"
                f"⏳ Tugash sanasi: "
                f"<b>{format_datetime(subscription.end_date)}</b>"
            )

        else:

            subscription_info_service = (
                SubscriptionInfoService(session)
            )

            info = await subscription_info_service.get_info(
                user_id=user_id
            )

            old_subscription = (
                info["subscription"]
                if info is not None
                else None
            )

            vpn_account = (
                info["vpn_account"]
                if info is not None
                else None
            )

            subscription = (
                await subscription_service
                .create_subscription(
                    user_id=user_id,
                    plan_id=plan.id,
                    duration_days=plan.duration_days,
                )
            )

            await sync_vpn_with_subscription(
                session=session,
                user_id=user_id,
                subscription=subscription,
                vpn_account=vpn_account,
            )

            await session.commit()

            if old_subscription is not None:

                result_text = (
                    "✅ <b>YANGI OBUNA BERILDI</b>\n\n"
                    f"👤 User ID: <code>{user_id}</code>\n"
                    f"📦 Eski obuna: "
                    f"<b>{escape(old_subscription.plan.name)}</b> "
                    "🔴 Muddati tugagan\n"
                    f"📦 Yangi tarif: "
                    f"<b>{escape(plan.name)}</b>\n"
                    f"💰 Narx: <b>{plan.price} ₽</b>\n\n"
                    f"📅 Boshlangan sana: "
                    f"<b>{format_datetime(subscription.start_date)}</b>\n"
                    f"⏳ Tugash sanasi: "
                    f"<b>{format_datetime(subscription.end_date)}</b>\n\n"
                    "🟢 Obuna faollashtirildi.\n"
                    "🔐 VPN hisob ham sinxronlashtirildi."
                )

            else:

                result_text = (
                    "✅ <b>YANGI OBUNA BERILDI</b>\n\n"
                    f"👤 User ID: <code>{user_id}</code>\n"
                    f"📦 Tarif: <b>{escape(plan.name)}</b>\n"
                    f"💰 Narx: <b>{plan.price} ₽</b>\n\n"
                    f"📅 Boshlangan sana: "
                    f"<b>{format_datetime(subscription.start_date)}</b>\n"
                    f"⏳ Tugash sanasi: "
                    f"<b>{format_datetime(subscription.end_date)}</b>\n\n"
                    "🟢 Obuna faollashtirildi.\n"
                    "🔐 VPN hisob ham sinxronlashtirildi."
                )

    await callback.answer(
        "Amal muvaffaqiyatli bajarildi. ✅"
    )

    await callback.message.edit_text(
        result_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Qidiruv natijasiga qaytish",
                        callback_data=f"search_back:{user_id}",
                    )
                ],
            ]
        ),
    )


# ============================================================
# OBUNANI O‘ZGARTIRISH — BEKOR QILISH
# ============================================================

@router.callback_query(
    F.data.startswith("search_plan_cancel:")
)
async def search_plan_cancel(
    callback: CallbackQuery,
):

    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

    if user is None:

        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer(
        "Bekor qilindi."
    )

    await callback.message.edit_text(
        "🔄 <b>Ma'lumotlar yangilanmoqda...</b>",
        parse_mode="HTML",
    )

    await show_user_search_result(
        message=callback.message,
        user=user,
    )





# ============================================================
# ADMIN BONUS — BERISH
# ============================================================


def admin_bonus_duration_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 1 kun",
                    callback_data=f"admin_bonus_days:{user_id}:1",
                ),
                InlineKeyboardButton(
                    text="➕ 3 kun",
                    callback_data=f"admin_bonus_days:{user_id}:3",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ 7 kun",
                    callback_data=f"admin_bonus_days:{user_id}:7",
                ),
                InlineKeyboardButton(
                    text="➕ 30 kun",
                    callback_data=f"admin_bonus_days:{user_id}:30",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Boshqa muddat",
                    callback_data=f"admin_bonus_custom:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Bekor qilish",
                    callback_data=f"search_back:{user_id}",
                ),
            ],
        ]
    )


def admin_bonus_result_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Qidiruv natijasiga qaytish",
                    callback_data=f"search_back:{user_id}",
                ),
            ],
        ]
    )


async def _ask_admin_bonus_reason(
    callback_or_message,
    state: FSMContext,
    user_id: int,
    days: int,
):
    await state.update_data(
        admin_bonus_user_id=user_id,
        admin_bonus_days=days,
    )
    await state.set_state(
        AdminSearchStates.waiting_for_admin_bonus_reason
    )
    text = (
        "📝 <b>ADMIN BONUS SABABI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🎁 Muddat: <b>{days} kun</b>\n\n"
        "Bonus berish sababini yozing.\n"
        "Bu maydon majburiy."
    )
    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.answer()
        await callback_or_message.message.edit_text(
            text,
            parse_mode="HTML",
        )
    else:
        await callback_or_message.answer(
            text,
            parse_mode="HTML",
        )


@router.callback_query(
    F.data.startswith("admin_user_bonus:")
)
async def admin_user_bonus(
    callback: CallbackQuery,
    state: FSMContext,
):
    user_id = int(callback.data.split(":")[1])
    admin = await get_admin(telegram_id=callback.from_user.id)
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id=user_id)
    if user is None:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "🎁 <b>ADMIN BONUS BERISH</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        "Bonus muddatini tanlang:",
        parse_mode="HTML",
        reply_markup=admin_bonus_duration_keyboard(user_id),
    )


@router.callback_query(
    F.data.startswith("admin_bonus_days:")
)
async def admin_bonus_days(
    callback: CallbackQuery,
    state: FSMContext,
):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto‘g‘ri so‘rov.", show_alert=True)
        return
    user_id = int(parts[1])
    days = int(parts[2])
    admin = await get_admin(telegram_id=callback.from_user.id)
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return
    await _ask_admin_bonus_reason(callback, state, user_id, days)


@router.callback_query(
    F.data.startswith("admin_bonus_custom:")
)
async def admin_bonus_custom(
    callback: CallbackQuery,
    state: FSMContext,
):
    user_id = int(callback.data.split(":")[1])
    admin = await get_admin(telegram_id=callback.from_user.id)
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return
    await state.update_data(admin_bonus_user_id=user_id)
    await state.set_state(AdminSearchStates.waiting_for_admin_bonus_days)
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>ADMIN BONUS MUDDATI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        "Necha kun berishni kiriting.\n"
        "Faqat musbat butun son.\n\n"
        "Masalan: <code>14</code>, <code>60</code>",
        parse_mode="HTML",
    )


@router.message(
    AdminSearchStates.waiting_for_admin_bonus_days
)
async def process_admin_bonus_days(
    message: Message,
    state: FSMContext,
):
    admin = await get_admin(telegram_id=message.from_user.id)
    if admin is None or not admin.is_admin:
        await state.clear()
        return
    value = (message.text or "").strip()
    if not value.isdigit() or int(value) <= 0:
        await message.answer(
            "❌ Muddat 0 dan katta bo‘lgan butun son bo‘lishi kerak.\n\n"
            "Masalan: <code>14</code>",
            parse_mode="HTML",
        )
        return
    data = await state.get_data()
    user_id = data.get("admin_bonus_user_id")
    if user_id is None:
        await state.clear()
        await message.answer("❌ Admin Bonus sessiyasi topilmadi.", reply_markup=admin_menu)
        return
    await _ask_admin_bonus_reason(message, state, user_id, int(value))


@router.message(
    AdminSearchStates.waiting_for_admin_bonus_reason
)
async def process_admin_bonus_reason(
    message: Message,
    state: FSMContext,
):
    admin = await get_admin(telegram_id=message.from_user.id)
    if admin is None or not admin.is_admin:
        await state.clear()
        return
    reason = (message.text or "").strip()
    if not reason:
        await message.answer("❌ Sabab bo‘sh bo‘lishi mumkin emas.")
        return
    data = await state.get_data()
    user_id = data.get("admin_bonus_user_id")
    days = data.get("admin_bonus_days")
    if user_id is None or days is None:
        await state.clear()
        await message.answer("❌ Admin Bonus sessiyasi topilmadi.", reply_markup=admin_menu)
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id=user_id)
        if user is None:
            await state.clear()
            await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=admin_menu)
            return
        try:
            bonus_service = UserBonusService(session)
            bonus = await bonus_service.create_bonus(
                user_id=user_id,
                bonus_type="admin",
                duration_days=int(days),
                reason=reason,
            )
            await session.commit()
        except ValueError as e:
            await session.rollback()
            await message.answer(f"❌ {escape(str(e))}", parse_mode="HTML")
            return
        except Exception as e:
            await session.rollback()
            print("ADMIN BONUS CREATE ERROR:", repr(e))
            await message.answer("❌ Admin Bonus berishda xatolik yuz berdi.")
            return

    await state.clear()
    number = bonus.bonus_number
    await message.answer(
        "✅ <b>ADMIN BONUS BERILDI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🎁 Admin Bonus <b>#{number}</b>\n"
        f"⏳ Muddat: <b>{days} kun</b>\n"
        f"📝 Sabab: <b>{escape(reason)}</b>\n"
        "📋 Holat: <b>Kutilmoqda</b>\n\n"
        "Bonus navbatga qo‘shildi va mavjud aktiv xizmatni to‘xtatmaydi.",
        parse_mode="HTML",
        reply_markup=admin_bonus_result_keyboard(user_id),
    )

def subscription_extend_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 7 kun",
                    callback_data=f"search_extend_days:{user_id}:7",
                ),
                InlineKeyboardButton(
                    text="➕ 30 kun",
                    callback_data=f"search_extend_days:{user_id}:30",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➖ 7 kun",
                    callback_data=f"search_extend_days:{user_id}:-7",
                ),
                InlineKeyboardButton(
                    text="➖ 30 kun",
                    callback_data=f"search_extend_days:{user_id}:-30",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Boshqa muddat",
                    callback_data=f"search_extend_custom:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Darhol tugatish",
                    callback_data=f"search_extend_zero:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Bekor qilish",
                    callback_data=f"search_extend_cancel:{user_id}",
                ),
            ],
        ]
    )


def subscription_zero_confirmation_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Ha, tugatish",
                    callback_data=f"search_extend_zero_confirm:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Bekor qilish",
                    callback_data=f"search_extend_cancel:{user_id}",
                ),
            ],
        ]
    )


def subscription_extend_result_keyboard(
    user_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Qidiruv natijasiga qaytish",
                    callback_data=f"search_back:{user_id}",
                ),
            ],
        ]
    )


async def sync_vpn_with_subscription(
    session,
    user_id: int,
    subscription,
    vpn_account,
):

    marzban_service = create_marzban_service()
    vpn_account_service = VPNAccountService(
        session=session,
        marzban_service=marzban_service,
    )

    if vpn_account is None:
        return await vpn_account_service.get_or_create(
            user_id=user_id,
            end_date=subscription.end_date,
            protocol="vless",
        )

    await marzban_service.update_user_expire(
        username=vpn_account.marzban_username,
        expire=subscription.end_date,
    )

    if not vpn_account.is_active:
        await vpn_account_service.activate_account(
            account_id=vpn_account.id,
        )

    return vpn_account


# ============================================================
# MUDDATNI BOSHQARISH — ASOSIY EKRAN
# ============================================================

@router.callback_query(
    F.data.startswith("search_extend:")
)
async def search_extend(
    callback: CallbackQuery,
):

    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        subscription_info_service = SubscriptionInfoService(session)
        info = await subscription_info_service.get_info(
            user_id=user_id
        )
        subscription = info["subscription"] if info is not None else None

    if subscription is None:
        await callback.answer(
            "Foydalanuvchida obuna mavjud emas.",
            show_alert=True,
        )
        return

    await callback.answer()

    now = utc_now()
    remaining_days = max(
        0,
        int(
            (subscription.end_date - now).total_seconds()
            + 86399
        ) // 86400,
    )

    text = (
        "🛠 <b>MUDDATNI BOSHQARISH</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        f"📦 Tarif: <b>{escape(subscription.plan.name)}</b>\n"
        f"💰 Narx: <b>{subscription.plan.price} ₽</b>\n\n"
        f"📅 Boshlangan sana:\n"
        f"{format_datetime(subscription.start_date)}\n\n"
        f"⏳ Hozirgi tugash sanasi:\n"
        f"{format_datetime(subscription.end_date)}\n\n"
        f"⏱ Qolgan muddat: <b>{remaining_days} kun</b>\n\n"
        "Muddatni o‘zgartirish uchun amalni tanlang:"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=subscription_extend_keyboard(
            user_id=user_id,
        ),
    )


# ============================================================
# MUDDATNI BOSHQARISH — +N / -N
# ============================================================

@router.callback_query(
    F.data.startswith("search_extend_days:")
)
async def search_extend_days(
    callback: CallbackQuery,
):

    parts = callback.data.split(":")

    if len(parts) != 3:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    user_id = int(parts[1])
    days = int(parts[2])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        subscription_service = SubscriptionService(session)
        subscription_info_service = SubscriptionInfoService(session)
        info = await subscription_info_service.get_info(
            user_id=user_id
        )
        subscription = info["subscription"] if info is not None else None

        if subscription is None:
            await callback.answer(
                "Foydalanuvchida obuna mavjud emas.",
                show_alert=True,
            )
            return

        old_end_date = subscription.end_date

        try:
            subscription = await subscription_service.adjust_subscription_duration(
                subscription=subscription,
                days=days,
            )

            if days > 0:
                subscription.status = "active"

            subscription_info_service = SubscriptionInfoService(session)
            info = await subscription_info_service.get_info(
                user_id=user_id
            )
            vpn_account = info["vpn_account"]

            await sync_vpn_with_subscription(
                session=session,
                user_id=user_id,
                subscription=subscription,
                vpn_account=vpn_account,
            )

            await session.commit()

        except ValueError as e:
            await session.rollback()
            await callback.answer(
                str(e),
                show_alert=True,
            )
            return

        except Exception as e:
            await session.rollback()
            print(
                "SUBSCRIPTION EXTEND ERROR:",
                repr(e),
            )
            await callback.answer(
                "Obuna muddatini o‘zgartirishda xatolik yuz berdi.",
                show_alert=True,
            )
            return

    action = "qo‘shildi" if days > 0 else "ayirildi"
    sign = "+" if days > 0 else ""

    await callback.answer(
        "Muddat muvaffaqiyatli o‘zgartirildi. ✅"
    )

    await callback.message.edit_text(
        "✅ <b>OBUNA MUDDATI O‘ZGARTIRILDI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        f"⏳ Eski tugash sanasi:\n"
        f"{format_datetime(old_end_date)}\n\n"
        f"{'➕' if days > 0 else '➖'} O‘zgartirish: <b>{sign}{days} kun</b>\n"
        f"📌 {abs(days)} kun {action}.\n\n"
        f"📅 Yangi tugash sanasi:\n"
        f"<b>{format_datetime(subscription.end_date)}</b>\n\n"
        "🔐 Marzban expire ham yangilandi.",
        parse_mode="HTML",
        reply_markup=subscription_extend_result_keyboard(
            user_id=user_id,
        ),
    )


# ============================================================
# MUDDATNI BOSHQARISH — BOSHQA MUDDAT
# ============================================================

@router.callback_query(
    F.data.startswith("search_extend_custom:")
)
async def search_extend_custom(
    callback: CallbackQuery,
    state: FSMContext,
):

    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        subscription_info_service = SubscriptionInfoService(session)
        info = await subscription_info_service.get_info(
            user_id=user_id
        )
        subscription = info["subscription"] if info is not None else None

    if subscription is None:
        await callback.answer(
            "Foydalanuvchida obuna mavjud emas.",
            show_alert=True,
        )
        return

    await state.update_data(
        extend_user_id=user_id,
    )
    await state.set_state(
        AdminSearchStates.waiting_for_custom_extend_days
    )

    await callback.answer()

    await callback.message.edit_text(
        "✏️ <b>MUDDATNI O‘ZGARTIRISH</b>\n\n"
        f"⏳ Hozirgi tugash sanasi:\n"
        f"{format_datetime(subscription.end_date)}\n\n"
        "Necha kun o‘zgartirishni kiriting.\n\n"
        "➕ Qo‘shish uchun: <code>+15</code>\n"
        "➖ Ayirish uchun: <code>-15</code>\n\n"
        "Masalan: <code>+10</code>, <code>-7</code>, <code>+30</code>",
        parse_mode="HTML",
    )


@router.message(
    AdminSearchStates.waiting_for_custom_extend_days
)
async def process_custom_extend_days(
    message: Message,
    state: FSMContext,
):

    admin = await get_admin(
        telegram_id=message.from_user.id
    )

    if admin is None or not admin.is_admin:
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("extend_user_id")

    if user_id is None:
        await state.clear()
        await message.answer(
            "❌ Muddatni boshqarish sessiyasi topilmadi.",
            reply_markup=admin_menu,
        )
        return

    value = (message.text or "").strip()

    if not re.fullmatch(r"[+-]\d+", value):
        await message.answer(
            "❌ <b>Noto‘g‘ri format.</b>\n\n"
            "Kunlarni + yoki - belgisi bilan kiriting.\n\n"
            "Masalan:\n"
            "<code>+15</code>\n"
            "<code>-15</code>",
            parse_mode="HTML",
        )
        return

    days = int(value)

    if days == 0:
        await message.answer(
            "❌ 0 kiritish mumkin emas.\n\n"
            "Darhol tugatish uchun <b>❌ Darhol tugatish</b> tugmasidan foydalaning.",
            parse_mode="HTML",
        )
        return

    async with async_session() as session:
        subscription_service = SubscriptionService(session)
        subscription_info_service = SubscriptionInfoService(session)
        info = await subscription_info_service.get_info(
            user_id=user_id
        )
        subscription = info["subscription"] if info is not None else None

        if subscription is None:
            await state.clear()
            await message.answer(
                "❌ Foydalanuvchida obuna mavjud emas.",
                reply_markup=admin_menu,
            )
            return

        old_end_date = subscription.end_date

        try:
            subscription = await subscription_service.adjust_subscription_duration(
                subscription=subscription,
                days=days,
            )

            if days > 0:
                subscription.status = "active"

            subscription_info_service = SubscriptionInfoService(session)
            info = await subscription_info_service.get_info(
                user_id=user_id
            )
            vpn_account = info["vpn_account"]

            await sync_vpn_with_subscription(
                session=session,
                user_id=user_id,
                subscription=subscription,
                vpn_account=vpn_account,
            )

            await session.commit()

        except ValueError as e:
            await session.rollback()
            await message.answer(
                f"❌ {escape(str(e))}",
                parse_mode="HTML",
            )
            return

        except Exception as e:
            await session.rollback()
            print(
                "CUSTOM SUBSCRIPTION EXTEND ERROR:",
                repr(e),
            )
            await message.answer(
                "❌ Obuna muddatini o‘zgartirishda xatolik yuz berdi.",
            )
            return

    await state.clear()

    await message.answer(
        "✅ <b>OBUNA MUDDATI O‘ZGARTIRILDI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        f"⏳ Eski tugash sanasi:\n"
        f"{format_datetime(old_end_date)}\n\n"
        f"{'➕' if days > 0 else '➖'} O‘zgartirish: <b>{days:+d} kun</b>\n\n"
        f"📅 Yangi tugash sanasi:\n"
        f"<b>{format_datetime(subscription.end_date)}</b>\n\n"
        "🔐 Marzban expire ham yangilandi.",
        parse_mode="HTML",
        reply_markup=subscription_extend_result_keyboard(
            user_id=user_id,
        ),
    )


# ============================================================
# MUDDATNI BOSHQARISH — DARHOL TUGATISH
# ============================================================

@router.callback_query(
    F.data.startswith("search_extend_zero:")
)
async def search_extend_zero(
    callback: CallbackQuery,
):

    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        subscription_service = SubscriptionService(session)
        subscription = await subscription_service.get_active_subscription(
            user_id=user_id
        )

    if subscription is None:
        await callback.answer(
            "Foydalanuvchida faol obuna mavjud emas.",
            show_alert=True,
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "⚠️ <b>OBUNANI DARHOL TUGATISH</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        f"📦 Tarif: <b>{escape(subscription.plan.name)}</b>\n"
        f"💰 Narx: <b>{subscription.plan.price} ₽</b>\n\n"
        f"⏳ Hozirgi tugash sanasi:\n"
        f"{format_datetime(subscription.end_date)}\n\n"
        "❗ <b>DIQQAT!</b>\n\n"
        "• Obuna darhol tugaydi\n"
        "• VPN hisob deaktivatsiya qilinadi\n"
        "• Marzban hisob disabled holatiga o‘tadi\n"
        "• Obuna tarixi saqlanib qoladi\n\n"
        "Bu amalni davom ettirasizmi?",
        parse_mode="HTML",
        reply_markup=subscription_zero_confirmation_keyboard(
            user_id=user_id,
        ),
    )


@router.callback_query(
    F.data.startswith("search_extend_zero_confirm:")
)
async def search_extend_zero_confirm(
    callback: CallbackQuery,
):

    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        subscription_service = SubscriptionService(session)
        subscription = await subscription_service.get_active_subscription(
            user_id=user_id
        )

        if subscription is None:
            await callback.answer(
                "Foydalanuvchida faol obuna mavjud emas.",
                show_alert=True,
            )
            return

        old_end_date = subscription.end_date
        now = utc_now()

        try:
            subscription.previous_end_date = old_end_date
            subscription.end_date = now
            subscription.status = "expired"

            subscription_info_service = SubscriptionInfoService(session)
            info = await subscription_info_service.get_info(
                user_id=user_id
            )
            vpn_account = info["vpn_account"]

            if vpn_account is not None:
                marzban_service = create_marzban_service()
                vpn_account_service = VPNAccountService(
                    session=session,
                    marzban_service=marzban_service,
                )

                await marzban_service.update_user_expire(
                    username=vpn_account.marzban_username,
                    expire=now,
                )

                await marzban_service.deactivate_user(
                    username=vpn_account.marzban_username,
                )

                if vpn_account.is_active:
                    await vpn_account_service.deactivate_account(
                        account_id=vpn_account.id,
                    )

            await session.commit()

        except Exception as e:
            await session.rollback()
            print(
                "SUBSCRIPTION ZERO ERROR:",
                repr(e),
            )
            await callback.answer(
                "Obunani tugatishda xatolik yuz berdi.",
                show_alert=True,
            )
            return

    await callback.answer(
        "Obuna darhol tugatildi. 🔴"
    )

    await callback.message.edit_text(
        "🔴 <b>OBUNA YAKUNLANDI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n\n"
        f"⏳ Eski tugash sanasi:\n"
        f"{format_datetime(old_end_date)}\n\n"
        f"📅 Yakunlangan vaqt:\n"
        f"{format_datetime(now)}\n\n"
        "🔐 VPN hisob deaktivatsiya qilindi.\n"
        "☁️ Marzban hisob disabled holatiga o‘tkazildi.",
        parse_mode="HTML",
        reply_markup=subscription_extend_result_keyboard(
            user_id=user_id,
        ),
    )


# ============================================================
# MUDDATNI BOSHQARISH — BEKOR QILISH
# ============================================================

@router.callback_query(
    F.data.startswith("search_extend_cancel:")
)
async def search_extend_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):

    user_id = int(callback.data.split(":")[1])

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await state.clear()

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(
            user_id=user_id
        )

    if user is None:
        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "Bekor qilindi."
    )

    await callback.message.edit_text(
        "🔄 <b>Ma'lumotlar yangilanmoqda...</b>",
        parse_mode="HTML",
    )

    await show_user_search_result(
        message=callback.message,
        user=user,
    )

# ============================================================
# VPN LINK
# ============================================================

@router.callback_query(
    F.data.startswith("search_vpn_link:")
)
async def search_vpn_link(
    callback: CallbackQuery,
):
    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:

        subscription_info_service = SubscriptionInfoService(
            session=session,
        )

        info = await subscription_info_service.get_info(
            user_id=user_id
        )

    vpn_account = info["vpn_account"]

    if vpn_account is None:
        await callback.answer(
            "Foydalanuvchida VPN hisob mavjud emas.",
            show_alert=True,
        )
        return

    vpn_link = None

    marzban_data = await get_marzban_user_data(
        username=vpn_account.marzban_username,
    )

    if marzban_data:

        links = marzban_data.get("links")

        if links:
            vpn_link = links[0]

    if not vpn_link:
        vpn_link = vpn_account.vpn_link

    if not vpn_link:
        await callback.answer(
            "VPN link mavjud emas.",
            show_alert=True,
        )
        return

    await callback.answer()

    text = (
        "📋 <b>VPN LINK</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🔐 Protocol: "
        f"<b>{escape(vpn_account.protocol.upper())}</b>\n"
        f"🔑 Marzban username: "
        f"<code>{escape(vpn_account.marzban_username)}</code>\n\n"
        "🔗 <b>VLESS LINK</b>\n"
        f"<code>{escape(vpn_link)}</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Qidiruv natijasiga qaytish",
                    callback_data=f"search_back:{user_id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# SUBSCRIPTION URL
# ============================================================

# ============================================================
# QIDIRUV — VPN HISOBNI O‘CHIRISH
# ============================================================

@router.callback_query(
    F.data.startswith("search_delete_vpn:")
)
async def search_delete_vpn(
    callback: CallbackQuery,
):
    parts = callback.data.split(":")

    if len(parts) != 2:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(
            user_id=user_id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        marzban_service = create_marzban_service()
        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        vpn_account = await vpn_account_service.get_existing(
            user_id=user_id,
            protocol="vless",
        )

    if vpn_account is None:
        await callback.answer(
            "Foydalanuvchida VPN hisob mavjud emas.",
            show_alert=True,
        )
        return

    full_name = escape(user.first_name)

    if user.last_name:
        full_name += f" {escape(user.last_name)}"

    text = (
        "⚠️ <b>VPN HISOBNI O‘CHIRISH</b>\n\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"🔑 Account ID: <code>{vpn_account.id}</code>\n"
        f"🔐 Marzban username: "
        f"<code>{escape(vpn_account.marzban_username)}</code>\n"
        f"📡 Protocol: "
        f"<b>{escape(vpn_account.protocol.upper())}</b>\n\n"
        "❗ <b>DIQQAT!</b>\n\n"
        "Bu amal VPN hisobni butunlay o‘chiradi.\n\n"
        "• Marzban VPN account o‘chiriladi\n"
        "• VPNAccount bazadagi yozuvi o‘chiriladi\n"
        "• Foydalanuvchi saqlanadi\n"
        "• Obuna saqlanadi\n"
        "• Obunalar tarixi saqlanadi\n\n"
        "Davom etishni xohlaysizmi?"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=search_vpn_delete_confirmation_keyboard(
            user_id=user_id,
            account_id=vpn_account.id,
        ),
    )


@router.callback_query(
    F.data.startswith("search_delete_vpn_cancel:")
)
async def search_delete_vpn_cancel(
    callback: CallbackQuery,
):
    parts = callback.data.split(":")

    if len(parts) != 2:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(
            user_id=user_id
        )

    if user is None:
        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )
        return

    await callback.answer(
        "O‘chirish bekor qilindi."
    )

    await callback.message.edit_text(
        "🔄 <b>Ma'lumotlar yangilanmoqda...</b>",
        parse_mode="HTML",
    )

    await show_user_search_result(
        message=callback.message,
        user=user,
    )


@router.callback_query(
    F.data.startswith("search_delete_vpn_confirm:")
)
async def search_delete_vpn_confirm(
    callback: CallbackQuery,
):
    parts = callback.data.split(":")

    if len(parts) != 3:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    try:
        user_id = int(parts[1])
        account_id = int(parts[2])
    except ValueError:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:
        user_service = UserService(session)
        user = await user_service.get_by_id(
            user_id=user_id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        marzban_service = create_marzban_service()
        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        vpn_account = await vpn_account_service.get_existing(
            user_id=user_id,
            protocol="vless",
        )

        if vpn_account is None:
            await callback.answer(
                "VPN hisob allaqachon o‘chirilgan.",
                show_alert=True,
            )
            return

        if vpn_account.id != account_id:
            await callback.answer(
                "VPN hisob ma'lumotlari o‘zgargan. Qidiruv natijasini yangilang.",
                show_alert=True,
            )
            return

        try:
            deleted_account = await vpn_account_service.delete_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:
            await session.rollback()
            await callback.answer(
                str(e),
                show_alert=True,
            )
            return

        except Exception as e:
            await session.rollback()
            print(
                "SEARCH VPN DELETE ERROR:",
                repr(e),
            )
            await callback.answer(
                "VPN hisobni o‘chirishda xatolik yuz berdi.",
                show_alert=True,
            )
            return

    await callback.answer(
        "VPN hisob o‘chirildi. 🗑"
    )

    await callback.message.edit_text(
        "✅ <b>VPN HISOB O‘CHIRILDI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🔑 Account ID: <code>{deleted_account.id}</code>\n"
        f"🔐 Marzban username: "
        f"<code>{escape(deleted_account.marzban_username)}</code>\n\n"
        "• Marzban VPN account o‘chirildi\n"
        "• VPNAccount bazadagi yozuvi o‘chirildi\n"
        "• Foydalanuvchi saqlanib qoldi\n"
        "• Obuna va obunalar tarixi saqlanib qoldi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Qidiruv natijasini ko‘rish",
                        callback_data=f"search_back:{user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Admin panel",
                        callback_data="search_admin_panel",
                    )
                ],
            ]
        ),
    )


@router.callback_query(
    F.data.startswith("search_subscription:")
)
async def search_subscription(
    callback: CallbackQuery,
):

    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    async with async_session() as session:

        subscription_info_service = SubscriptionInfoService(
            session=session,
        )

        info = await subscription_info_service.get_info(
            user_id=user_id
        )

    vpn_account = info["vpn_account"]

    if vpn_account is None:

        await callback.answer(
            "Foydalanuvchida VPN hisob mavjud emas.",
            show_alert=True,
        )

        return

    subscription_url = None

    marzban_data = await get_marzban_user_data(
        username=vpn_account.marzban_username,
    )

    if marzban_data:

        subscription_url = (
            marzban_data.get("subscription_url")
        )

    if not subscription_url:

        subscription_url = (
            vpn_account.subscription_url
        )

    if not subscription_url:

        await callback.answer(
            "Subscription URL mavjud emas.",
            show_alert=True,
        )

        return

    await callback.answer()

    text = (
        "🔗 <b>SUBSCRIPTION URL</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"🔐 Protocol: "
        f"<b>{escape(vpn_account.protocol.upper())}</b>\n"
        f"🔑 Marzban username: "
        f"<code>{escape(vpn_account.marzban_username)}</code>\n\n"
        "🌐 <b>SUBSCRIPTION URL</b>\n"
        f"<code>{escape(subscription_url)}</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Qidiruv natijasiga qaytish",
                    callback_data=f"search_back:{user_id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(
    F.data == "admin_section_back"
)
async def admin_section_back(
    callback: CallbackQuery,
):
    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()
    await _replace_callback_with_admin_panel(callback)


@router.callback_query(
    F.data == "search_admin_panel"
)
async def search_admin_panel(
    callback: CallbackQuery,
):
    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()

    await _replace_callback_with_admin_panel(callback)


@router.callback_query(F.data == "admin_user_search_back")
async def admin_user_search_back(callback: CallbackQuery):
    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()
    await _replace_callback_with_admin_panel(callback)


@router.callback_query(
    F.data.startswith("search_back:")
)
async def search_back(
    callback: CallbackQuery,
):
    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

    if user is None:
        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "🔄 <b>Ma'lumotlar yangilanmoqda...</b>",
        parse_mode="HTML",
    )

    await show_user_search_result(
        message=callback.message,
        user=user,
    )


@router.callback_query(
    F.data.startswith("search_refresh:")
)
async def search_result_refresh(
    callback: CallbackQuery,
):

    user_id = int(
        callback.data.split(":")[1]
    )

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:

        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )

        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

    if user is None:

        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer(
        "Ma'lumotlar yangilanmoqda... 🔄"
    )

    await callback.message.edit_text(
        "🔄 <b>Ma'lumotlar yangilanmoqda...</b>",
        parse_mode="HTML",
    )

    await show_user_search_result(
        message=callback.message,
        user=user,
    )



# ============================================================
# BARCHA OBUNALAR TARIXI
# ============================================================

ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE = 5


def all_subscription_history_keyboard(
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:

    buttons = []
    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=(
                    f"all_subscription_history:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            text=f"{page} / {total_pages}",
            callback_data="all_subscription_history_noop",
        )
    )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"all_subscription_history:{page + 1}"
                ),
            )
        )

    buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Admin panel",
                callback_data="all_subscription_history_back",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def format_all_subscription_history_item(
    index: int,
    subscription,
) -> str:

    user = subscription.user
    plan = subscription.plan

    if subscription.status == "active":
        status = "🟢 Faol"
    elif subscription.status == "expired":
        status = "🔴 Muddati tugagan"
    else:
        status = f"⚪ {escape(subscription.status)}"

    full_name = user.first_name

    if user.last_name:
        full_name += f" {user.last_name}"

    username = (
        f"@{user.username}"
        if user.username
        else "username yo‘q"
    )

    text = (
        f"<b>{index}️⃣ {escape(plan.name)}</b>\n"
        f"👤 User ID: <code>{user.id}</code>\n"
        f"👨‍💼 Ism: {escape(full_name)}\n"
        f"🔹 Username: {escape(username)}\n"
        f"💰 Narx: <b>{plan.price} ₽</b>\n"
        f"📅 Boshlangan: "
        f"{format_datetime(subscription.start_date)}\n"
    )

    if subscription.previous_end_date is not None:
        text += (
            f"⏳ Rejalashtirilgan tugash: "
            f"{format_datetime(subscription.previous_end_date)}\n"
            f"🛑 Amalda tugatilgan: "
            f"{format_datetime(subscription.end_date)}\n"
        )
    else:
        text += (
            f"⏳ Tugash sanasi: "
            f"{format_datetime(subscription.end_date)}\n"
        )

    text += f"📌 Status: {status}"

    return text


@router.message(F.text == "📜 Barcha obunalar tarixi")
async def all_subscription_history_message(
    message: Message,
):

    admin = await get_admin(
        telegram_id=message.from_user.id
    )

    if admin is None or not admin.is_admin:
        return

    await delete_last_admin_message(message)

    await show_all_subscription_history(
        message=message,
        page=1,
        edit=False,
    )


@router.callback_query(
    F.data == "all_subscription_history_noop"
)
async def all_subscription_history_noop(
    callback: CallbackQuery,
):

    await callback.answer()


@router.callback_query(
    F.data.startswith("all_subscription_history:")
)
async def all_subscription_history_page(
    callback: CallbackQuery,
):

    parts = callback.data.split(":")

    if len(parts) != 2:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    try:
        page = int(parts[1])
    except ValueError:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    if page < 1:
        page = 1

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()

    await show_all_subscription_history(
        message=callback.message,
        page=page,
        edit=True,
    )


@router.callback_query(
    F.data == "all_subscription_history_back"
)
async def all_subscription_history_back(
    callback: CallbackQuery,
):

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    await callback.answer()

    await _replace_callback_with_admin_panel(callback)


async def show_all_subscription_history(
    message: Message,
    page: int,
    edit: bool,
):

    async with async_session() as session:

        subscription_service = SubscriptionService(
            session=session
        )

        subscriptions, total = (
            await subscription_service
            .get_all_subscription_history_paginated(
                page=page,
                page_size=ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE,
            )
        )

    if total == 0:
        text = (
            "📜 <b>BARCHA OBUNALAR TARIXI</b>\n\n"
            "Hozircha obunalar mavjud emas."
        )

        if edit:
            await message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=all_subscription_history_keyboard(
                    page=1,
                    total_pages=1,
                ),
            )
        else:
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=all_subscription_history_keyboard(
                    page=1,
                    total_pages=1,
                ),
            )

        return

    total_pages = (
        total + ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE - 1
    ) // ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE

    if page > total_pages:
        page = total_pages

        async with async_session() as session:
            subscription_service = SubscriptionService(
                session=session
            )

            subscriptions, total = (
                await subscription_service
                .get_all_subscription_history_paginated(
                    page=page,
                    page_size=ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE,
                )
            )

    start_number = (
        (page - 1) * ALL_SUBSCRIPTION_HISTORY_PAGE_SIZE + 1
    )

    items = []

    for offset, subscription in enumerate(
        subscriptions
    ):
        items.append(
            format_all_subscription_history_item(
                index=start_number + offset,
                subscription=subscription,
            )
        )

    text = (
        "📜 <b>BARCHA OBUNALAR TARIXI</b>\n\n"
        f"📊 Jami obunalar: <b>{total}</b>\n\n"
        + "\n\n".join(items)
    )

    keyboard = all_subscription_history_keyboard(
        page=page,
        total_pages=total_pages,
    )

    if edit:
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


# ============================================================
# OBUNALAR TARIXI
# ============================================================

SUBSCRIPTION_HISTORY_PAGE_SIZE = 5


def subscription_history_keyboard(
    user_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:

    buttons = []

    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=(
                    f"search_subscription_history:"
                    f"{user_id}:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            text=f"{page} / {total_pages}",
            callback_data="search_subscription_history_noop",
        )
    )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"search_subscription_history:"
                    f"{user_id}:{page + 1}"
                ),
            )
        )

    buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Qidiruv natijasiga qaytish",
                callback_data=f"search_back:{user_id}",
            ),
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def format_subscription_history_item(
    index: int,
    subscription,
) -> str:

    plan = subscription.plan

    if subscription.status == "active":
        status = "🟢 Faol"
    elif subscription.status == "expired":
        status = "🔴 Muddati tugagan"
    else:
        status = f"⚪ {escape(subscription.status)}"

    text = (
        f"<b>{index}️⃣ {escape(plan.name)}</b>\n"
        f"💰 Narx: <b>{plan.price} ₽</b>\n"
        f"📅 Boshlangan: "
        f"{format_datetime(subscription.start_date)}\n"
    )

    if subscription.previous_end_date is not None:
        text += (
            f"⏳ Rejalashtirilgan tugash: "
            f"{format_datetime(subscription.previous_end_date)}\n"
            f"🛑 Amalda tugatilgan: "
            f"{format_datetime(subscription.end_date)}\n"
        )
    else:
        text += (
            f"⏳ Tugash sanasi: "
            f"{format_datetime(subscription.end_date)}\n"
        )

    text += f"📌 Status: {status}"

    return text


@router.callback_query(
    F.data == "search_subscription_history_noop"
)
async def search_subscription_history_noop(
    callback: CallbackQuery,
):

    await callback.answer()


@router.callback_query(
    F.data.startswith("search_subscription_history:")
)
async def search_subscription_history(
    callback: CallbackQuery,
):

    parts = callback.data.split(":")

    if len(parts) != 3:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    try:
        user_id = int(parts[1])
        page = int(parts[2])
    except ValueError:
        await callback.answer(
            "Noto‘g‘ri so‘rov.",
            show_alert=True,
        )
        return

    if page < 1:
        page = 1

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None or not admin.is_admin:
        await callback.answer(
            "Ruxsat yo‘q.",
            show_alert=True,
        )
        return

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=user_id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

        subscription_service = SubscriptionService(
            session=session
        )

        subscriptions, total = (
            await subscription_service
            .get_subscription_history_paginated(
                user_id=user_id,
                page=page,
                page_size=SUBSCRIPTION_HISTORY_PAGE_SIZE,
            )
        )

    if total == 0:
        await callback.answer(
            "Foydalanuvchida obunalar tarixi mavjud emas.",
            show_alert=True,
        )
        return

    total_pages = (
        total + SUBSCRIPTION_HISTORY_PAGE_SIZE - 1
    ) // SUBSCRIPTION_HISTORY_PAGE_SIZE

    if page > total_pages:
        page = total_pages

        async with async_session() as session:
            subscription_service = SubscriptionService(
                session=session
            )

            subscriptions, total = (
                await subscription_service
                .get_subscription_history_paginated(
                    user_id=user_id,
                    page=page,
                    page_size=SUBSCRIPTION_HISTORY_PAGE_SIZE,
                )
            )

    start_number = (
        (page - 1) * SUBSCRIPTION_HISTORY_PAGE_SIZE + 1
    )

    items = []

    for offset, subscription in enumerate(
        subscriptions
    ):
        items.append(
            format_subscription_history_item(
                index=start_number + offset,
                subscription=subscription,
            )
        )

    text = (
        "📜 <b>OBUNALAR TARIXI</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📊 Jami obunalar: <b>{total}</b>\n\n"
        + "\n\n".join(items)
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=subscription_history_keyboard(
            user_id=user_id,
            page=page,
            total_pages=total_pages,
        ),
    )



def bonus_statistics_keyboard(
    period_days: int | None,
) -> InlineKeyboardMarkup:
    selected = period_days

    def label(days: int | None, text: str) -> str:
        return (
            f"✅ {text}"
            if days == selected
            else text
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label(0, "📅 Bugun"),
                    callback_data="bonus_stats:today",
                ),
                InlineKeyboardButton(
                    text=label(7, "7 kun"),
                    callback_data="bonus_stats:7",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=label(30, "30 kun"),
                    callback_data="bonus_stats:30",
                ),
                InlineKeyboardButton(
                    text=label(None, "Barcha vaqt"),
                    callback_data="bonus_stats:all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Welcome trafik",
                    callback_data=(
                        f"bonus_stats:welcome:{period_days or 'all'}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤝 Referral statistikasi",
                    callback_data=(
                        f"bonus_stats:referral:{period_days or 'all'}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data="bonus_stats:back",
                ),
            ],
        ]
    )


def bonus_user_statistics_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Yangilash",
                    callback_data=f"search_bonus_stats:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📜 Bonuslar tarixi",
                    callback_data=f"search_bonus_history:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Qidiruv natijasiga qaytish",
                    callback_data=f"search_bonus_stats_back:{user_id}",
                ),
            ],
        ]
    )


def _bonus_type_line(
    stats,
    title: str,
) -> str:
    return (
        f"{title}: <b>{stats.total}</b> "
        f"(🟢 {stats.active} / ⏳ {stats.pending} / "
        f"⚪ {stats.expired} / 🚫 {stats.revoked})"
    )


def _period_title(period_days: int | None) -> str:
    if period_days == 0:
        return "BUGUN"
    if period_days == 7:
        return "SO‘NGGI 7 KUN"
    if period_days == 30:
        return "SO‘NGGI 30 KUN"
    return "BARCHA VAQT"


def _render_bonus_statistics(stats) -> str:
    welcome = stats.by_type.get("welcome", BonusTypeStats())
    promo = stats.by_type.get("promo", BonusTypeStats())
    referral = stats.by_type.get("referral", BonusTypeStats())
    admin = stats.by_type.get("admin", BonusTypeStats())
    traffic = stats.welcome_traffic
    ref = stats.referral
    promo_stats = stats.promo

    return (
        f"🎁 <b>BONUSLAR STATISTIKASI — "
        f"{_period_title(stats.period_days)}</b>\n\n"
        f"👥 <b>Jami berilgan bonuslar:</b> {stats.total}\n"
        f"🟢 Faol: <b>{stats.active}</b>\n"
        f"⏳ Kutilmoqda: <b>{stats.pending}</b>\n"
        f"⚪ Tugagan: <b>{stats.expired}</b>\n"
        f"🚫 Bekor qilingan: <b>{stats.revoked}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎁 <b>BONUS TURLARI</b>\n"
        f"{_bonus_type_line(welcome, '🎁 Welcome')}\n"
        f"{_bonus_type_line(promo, '🎟 Promo')}\n"
        f"{_bonus_type_line(referral, '🤝 Referral')}\n"
        f"{_bonus_type_line(admin, '👨‍💼 Admin')}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤝 <b>REFERRAL</b>\n"
        f"👥 Jami referral: <b>{ref.total}</b>\n"
        f"✅ Mukofotga aylangan: <b>{ref.rewarded}</b>\n"
        f"⏳ Hali xarid qilmagan: <b>{ref.pending}</b>\n"
        f"🎁 3 kunlik reward: <b>{ref.reward_3_days}</b>\n"
        f"🎁 7 kunlik reward: <b>{ref.reward_7_days}</b>\n"
        f"📅 Jami berilgan muddat: <b>{ref.total_reward_days} kun</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎟 <b>PROMO</b>\n"
        f"🔑 Redeem qilingan: <b>{promo_stats.redemptions}</b>\n"
        f"🎁 Promo bonuslari: <b>{promo_stats.bonuses}</b>\n"
        f"📅 Jami bonus muddati: <b>{promo_stats.total_duration_days} kun</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📦 <b>WELCOME TRAFFIC</b>\n"
        f"👥 Welcome bonuslar: <b>{traffic.total_welcome}</b>\n"
        f"🟢 Faollashgan: <b>{traffic.active}</b>\n"
        f"⏳ Navbatda: <b>{traffic.pending}</b>\n"
        f"⚪ Tugagan: <b>{traffic.expired}</b>\n"
        f"📦 Jami limit: <b>{format_traffic(traffic.total_limit_bytes)}</b>\n"
        f"📊 Ishlatilgan: <b>{format_traffic(traffic.total_used_bytes)}</b>\n"
        f"📉 Qolgan: <b>{format_traffic(traffic.remaining_bytes)}</b>\n"
        f"⚠️ 500 MB warning: <b>{traffic.warning_500mb_sent}</b>\n"
        f"🚫 3 GB tugagan: <b>{traffic.exhausted}</b>"
    )


async def _show_bonus_statistics(
    message: Message,
    period_days: int | None = None,
):
    async with async_session() as session:
        service = BonusStatisticsService(session)
        stats = await service.get_global_statistics(
            period_days=period_days,
        )

    return await message.answer(
        _render_bonus_statistics(stats),
        parse_mode="HTML",
        reply_markup=bonus_statistics_keyboard(period_days),
    )


@router.message(F.text == "🎁 Bonuslar")
async def bonus_statistics_entry(message: Message):
    admin = await get_admin(
        telegram_id=message.from_user.id,
    )
    if admin is None or not admin.is_admin:
        return

    await delete_last_admin_message(message)
    sent = await _show_bonus_statistics(message, period_days=None)
    await remember_admin_message(sent)


@router.callback_query(F.data.startswith("bonus_stats:"))
async def bonus_statistics_callback(callback: CallbackQuery):
    admin = await get_admin(
        telegram_id=callback.from_user.id,
    )
    if admin is None or not admin.is_admin:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "back":
        await callback.answer()
        await _replace_callback_with_admin_panel(callback)
        return

    if action in {"today", "7", "30", "all"}:
        period_days = {
            "today": 0,
            "7": 7,
            "30": 30,
            "all": None,
        }[action]

        async with async_session() as session:
            service = BonusStatisticsService(session)
            stats = await service.get_global_statistics(
                period_days=period_days,
            )

        await callback.answer()
        await callback.message.edit_text(
            _render_bonus_statistics(stats),
            parse_mode="HTML",
            reply_markup=bonus_statistics_keyboard(period_days),
        )
        return

    if action in {"welcome", "referral"}:
        period_value = parts[2] if len(parts) > 2 else "all"
        period_days = (
            None
            if period_value == "all"
            else int(period_value)
        )

        async with async_session() as session:
            service = BonusStatisticsService(session)
            stats = await service.get_global_statistics(
                period_days=period_days,
            )

        await callback.answer()
        if action == "welcome":
            traffic = stats.welcome_traffic
            text = (
                f"📦 <b>WELCOME TRAFFIC — "
                f"{_period_title(period_days)}</b>\n\n"
                f"👥 Jami Welcome: <b>{traffic.total_welcome}</b>\n"
                f"🟢 Faollashgan: <b>{traffic.active}</b>\n"
                f"⏳ Navbatda: <b>{traffic.pending}</b>\n"
                f"⚪ Tugagan: <b>{traffic.expired}</b>\n\n"
                f"📦 Jami limit: <b>{format_traffic(traffic.total_limit_bytes)}</b>\n"
                f"📊 Ishlatilgan: <b>{format_traffic(traffic.total_used_bytes)}</b>\n"
                f"📉 Qolgan: <b>{format_traffic(traffic.remaining_bytes)}</b>\n\n"
                f"⚠️ 500 MB warning: <b>{traffic.warning_500mb_sent}</b>\n"
                f"🚫 3 GB tugagan: <b>{traffic.exhausted}</b>"
            )
        else:
            ref = stats.referral
            text = (
                f"🤝 <b>REFERRAL STATISTIKASI — "
                f"{_period_title(period_days)}</b>\n\n"
                f"👥 Jami referral: <b>{ref.total}</b>\n"
                f"✅ Mukofotga aylangan: <b>{ref.rewarded}</b>\n"
                f"⏳ Hali xarid qilmagan: <b>{ref.pending}</b>\n\n"
                f"🎁 3 kunlik reward: <b>{ref.reward_3_days}</b>\n"
                f"🎁 7 kunlik reward: <b>{ref.reward_7_days}</b>\n"
                f"📅 Jami berilgan muddat: <b>{ref.total_reward_days} kun</b>"
            )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=bonus_statistics_keyboard(period_days),
        )
        return

    await callback.answer("Noma’lum amal.", show_alert=True)


@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        await delete_last_admin_message(message)

        statistics_service = StatisticsService(session)

        stats = await statistics_service.get_statistics()

        daily_total = await session.scalar(
            select(func.count())
            .select_from(DailySubscription)
        )
        daily_active = await session.scalar(
            select(func.count())
            .select_from(DailySubscription)
            .where(DailySubscription.status == "active")
        )
        daily_expired = await session.scalar(
            select(func.count())
            .select_from(DailySubscription)
            .where(DailySubscription.status == "expired")
        )

    protocol_lines = []

    for protocol, count in stats.protocol_counts.items():
        protocol_lines.append(
            f"├ {protocol.upper()}: <b>{count}</b>"
        )

    protocol_text = "\n".join(protocol_lines)

    if not protocol_text:
        protocol_text = (
            "└ Hozircha VPN hisoblar mavjud emas."
        )

    text = (
        "📊 <b>STATISTIKA</b>\n\n"

        "👥 <b>FOYDALANUVCHILAR</b>\n"
        f"├ Jami: <b>{stats.total_users}</b>\n"
        f"├ Faol: <b>{stats.active_users}</b>\n"
        f"├ Faol emas: <b>{stats.inactive_users}</b>\n"
        f"├ Bugun: <b>{stats.users_today}</b>\n"
        f"└ Shu oy: <b>{stats.users_this_month}</b>\n\n"

        "💳 <b>OBUNALAR</b>\n"
        f"├ Jami: <b>{stats.total_subscriptions}</b>\n"
        f"├ Faol: <b>{stats.active_subscriptions}</b>\n"
        f"└ Muddati tugagan: "
        f"<b>{stats.expired_subscriptions}</b>\n\n"

        "📅 <b>DAILY OBUNALAR</b>\n"
        f"├ Jami: <b>{daily_total or 0}</b>\n"
        f"├ Faol: <b>{daily_active or 0}</b>\n"
        f"└ Muddati tugagan: <b>{daily_expired or 0}</b>\n\n"

        "🔑 <b>VPN HISOBLAR</b>\n"
        f"├ Jami: <b>{stats.total_vpn_accounts}</b>\n"
        f"├ Faol: <b>{stats.active_vpn_accounts}</b>\n"
        f"{protocol_text}\n\n"

        "📩 <b>MUROJAATLAR</b>\n"
        f"├ Jami: <b>{stats.total_tickets}</b>\n"
        f"├ Yangi: <b>{stats.new_tickets}</b>\n"
        f"├ Ochiq: <b>{stats.open_tickets}</b>\n"
        f"└ Yopilgan: <b>{stats.closed_tickets}</b>"
    )

    sent = await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await remember_admin_message(sent)


@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        await delete_last_admin_message(message)

        users = await user_service.get_all_users()
        total = await user_service.count_users()

    if not users:

        sent = await message.answer(
            "👥 <b>Foydalanuvchilar</b>\n\n"
            "Hozircha foydalanuvchilar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_back_keyboard(),
        )
        await remember_admin_message(sent)

        return

    text = (
        "👥 <b>Foydalanuvchilar</b>\n\n"
        f"📊 Jami: <b>{total}</b>\n\n"
    )

    for user in users:

        username = (
            f"@{escape(user.username)}"
            if user.username
            else "—"
        )

        status = (
            "🟢 Faol"
            if user.is_active
            else "🔴 Faol emas"
        )

        full_name = escape(
            user.first_name
        )

        if user.last_name:
            full_name += (
                f" {escape(user.last_name)}"
            )

        text += (
            f"👤 <b>#{user.id}</b>\n"
            f"Ism: {full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: "
            f"<code>{user.telegram_id}</code>\n"
            f"Status: {status}\n\n"
        )

    sent = await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_back_keyboard(),
    )
    await remember_admin_message(sent)


@router.message(F.text == "🔑 VPN hisoblar")
async def vpn_accounts_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        await delete_last_admin_message(message)

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        accounts = await vpn_account_service.get_all_accounts()

    if not accounts:

        sent = await message.answer(
            "🔑 <b>VPN HISOBLAR</b>\n\n"
            "Hozircha VPN hisoblar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_back_keyboard(),
        )
        await remember_admin_message(sent)

        return

    text = (
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        f"📊 Jami: <b>{len(accounts)}</b>\n\n"
        "Hisobni tanlang:"
    )

    sent = await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=vpn_accounts_keyboard(accounts),
    )
    await remember_admin_message(sent)


@router.callback_query(F.data == "vpn_accounts:back")
async def vpn_accounts_back(
    callback: CallbackQuery,
):

    user = await get_admin(
        telegram_id=callback.from_user.id
    )

    if user is None or not user.is_admin:

        await callback.answer(
            "Ruxsat yo'q.",
            show_alert=True,
        )

        return

    await callback.answer()

    await callback.message.edit_text(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "Admin panel:",
        reply_markup=admin_menu,
    )


@router.callback_query(F.data == "vpn_accounts:list")
async def vpn_accounts_list_callback(
    callback: CallbackQuery,
):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        accounts = await vpn_account_service.get_all_accounts()

    if not accounts:

        await callback.answer()

        await callback.message.edit_text(
            "🔑 <b>VPN HISOBLAR</b>\n\n"
            "Hozircha VPN hisoblar mavjud emas.",
            parse_mode="HTML",
        )

        return

    text = (
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        f"📊 Jami: <b>{len(accounts)}</b>\n\n"
        "Hisobni tanlang:"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_accounts_keyboard(accounts),
    )


@router.callback_query(F.data.startswith("vpn_account:"))
async def vpn_account_detail(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer()

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_activate:"))
async def vpn_account_activate(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.activate_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN ACTIVATE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni faollashtirishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob faollashtirildi. 🟢"
    )

    await callback.message.edit_text(
        "VPN hisob yangilanmoqda...",
        parse_mode="HTML",
    )

    async with async_session() as session:

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.message.edit_text(
            "VPN hisob topilmadi.",
            parse_mode="HTML",
        )

        return

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_deactivate:"))
async def vpn_account_deactivate(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.deactivate_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN DEACTIVATE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni deaktivatsiya qilishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob deaktivatsiya qilindi. 🔴"
    )

    await callback.message.edit_text(
        "VPN hisob yangilanmoqda...",
        parse_mode="HTML",
    )

    async with async_session() as session:

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.message.edit_text(
            "VPN hisob topilmadi.",
            parse_mode="HTML",
        )

        return

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_refresh:"))
async def vpn_account_refresh(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer(
        "Ma'lumotlar yangilandi. 🔄"
    )

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_delete:"))
async def vpn_account_delete(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    user = account.user

    full_name = escape(
        user.first_name
    )

    if user.last_name:
        full_name += (
            f" {escape(user.last_name)}"
        )

    text = (
        "⚠️ <b>VPN HISOBNI O‘CHIRISH</b>\n\n"
        f"🔑 Account: <b>#{account.id}</b>\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"🔐 Marzban username: "
        f"<code>{escape(account.marzban_username)}</code>\n\n"

        "❗ <b>DIQQAT!</b>\n\n"
        "Bu amal VPN hisobni butunlay o‘chiradi.\n\n"
        "• Marzban VPN account o‘chiriladi\n"
        "• VPNAccount bazadagi yozuvi o‘chiriladi\n"
        "• Foydalanuvchi saqlanadi\n"
        "• Obuna saqlanadi\n"
        "• Tarif saqlanadi\n\n"

        "Davom etishni xohlaysizmi?"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_delete_confirmation_keyboard(
            account_id=account_id,
        ),
    )


@router.callback_query(
    F.data.startswith("vpn_delete_cancel:")
)
async def vpn_account_delete_cancel(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob allaqachon o‘chirilgan.",
            show_alert=True,
        )

        return

    await callback.answer(
        "O‘chirish bekor qilindi."
    )

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(
    F.data.startswith("vpn_delete_confirm:")
)
async def vpn_account_delete_confirm(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.delete_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN DELETE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni o‘chirishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob o‘chirildi. 🗑"
    )

    await callback.message.edit_text(
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        "VPN hisob muvaffaqiyatli o‘chirildi.\n\n"
        "Hisoblar ro‘yxatini yangilash uchun "
        "pastdagi tugmani bosing.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 VPN hisoblar",
                        callback_data="vpn_accounts:list",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Admin panel",
                        callback_data="vpn_accounts:back",
                    )
                ],
            ]
        ),
    )


@router.message(F.text == "⬅️ Admin panel")
async def back_to_admin_panel(message: Message):

    user = await get_admin(
        telegram_id=message.from_user.id
    )

    if user is None or not user.is_admin:
        return

    await replace_with_admin_panel(
        message=message,
    )


@router.message(F.text == "⬅️ Asosiy menyu")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )