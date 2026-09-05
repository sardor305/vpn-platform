from datetime import datetime, timezone
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
from app.services.plan_service import PlanService
from app.services.setting_service import SettingService
from app.services.statistics_service import StatisticsService
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.user_service import UserService
from app.services.vpn_account_service import VPNAccountService


router = Router()


class AdminSearchStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_custom_plan_days = State()
    waiting_for_custom_extend_days = State()
    waiting_for_daily_price = State()


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
                    text="📦 Obunani o‘zgartirish",
                    callback_data=f"search_change_plan:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Muddatni uzaytirish",
                    callback_data=f"search_extend:{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 VPNni o‘chirish",
                    callback_data=f"search_delete_vpn:{user_id}",
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

    await message.answer(
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

    await message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


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

    await state.set_state(
        AdminSearchStates.waiting_for_user_id
    )

    await message.answer(
        "🔎 <b>Foydalanuvchi qidirish</b>\n\n"
        "User ID yoki Telegram ID raqamini yuboring.\n\n"
        "Masalan:\n"
        "<code>7</code>\n"
        "yoki\n"
        "<code>522599954</code>",
        parse_mode="HTML",
    )


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

    if found_user is None:

        await message.answer(
            "❌ <b>Foydalanuvchi topilmadi.</b>\n\n"
            f"Qidirilgan raqam: "
            f"<code>{search_id}</code>",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    await show_user_search_result(
        message=message,
        user=found_user,
    )


# ============================================================
# OBUNANI O‘ZGARTIRISH
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


@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        statistics_service = StatisticsService(session)

        stats = await statistics_service.get_statistics()

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

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        users = await user_service.get_all_users()
        total = await user_service.count_users()

    if not users:

        await message.answer(
            "👥 <b>Foydalanuvchilar</b>\n\n"
            "Hozircha foydalanuvchilar mavjud emas.",
            parse_mode="HTML",
            reply_markup=users_menu,
        )

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

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=users_menu,
    )


@router.message(F.text == "🔑 VPN hisoblar")
async def vpn_accounts_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        accounts = await vpn_account_service.get_all_accounts()

    if not accounts:

        await message.answer(
            "🔑 <b>VPN HISOBLAR</b>\n\n"
            "Hozircha VPN hisoblar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    text = (
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        f"📊 Jami: <b>{len(accounts)}</b>\n\n"
        "Hisobni tanlang:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=vpn_accounts_keyboard(accounts),
    )


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

    await message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.message(F.text == "⬅️ Asosiy menyu")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )