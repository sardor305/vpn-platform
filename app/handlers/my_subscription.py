from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config.config import config
from app.database.database import async_session
from app.keyboards.subscription_keyboard import subscription_keyboard
from app.keyboards.user_navigation import user_navigation_keyboard
from app.services.daily_subscription_service import DailySubscriptionService
from app.services.service_access_service import ServiceAccessService
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService


router = Router()


STATUS_NAMES = {
    "active": "🟢 Faol",
    "pending": "⏳ Kutilmoqda",
    "expired": "⚪ Tugagan",
    "revoked": "🚫 Bekor qilingan",
}


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d.%m.%Y %H:%M")


def format_remaining_days(end_date: datetime | None) -> int | None:
    if end_date is None:
        return None

    now = datetime.now(end_date.tzinfo)
    seconds = (end_date - now).total_seconds()

    if seconds <= 0:
        return 0

    return max(1, int((seconds + 86399) // 86400))


def status_name(status: str) -> str:
    return STATUS_NAMES.get(status, status)


def format_paid_history_item(number: int, subscription) -> str:
    plan_name = (
        subscription.plan.name
        if subscription.plan is not None
        else "Noma'lum tarif"
    )
    price = (
        f"{subscription.plan.price} ₽"
        if subscription.plan is not None
        else "—"
    )

    return (
        f"🔹 <b>Obuna #{number}</b>\n"
        f"📦 Tarif: <b>{plan_name}</b>\n"
        f"💰 Narxi: <b>{price}</b>\n"
        f"📅 Boshlangan sana: <b>{format_datetime(subscription.start_date)}</b>\n"
        f"⏳ Tugash sanasi: <b>{format_datetime(subscription.end_date)}</b>\n"
        f"{status_name(subscription.status)}"
    )


def format_daily_history_item(number: int, subscription) -> str:
    return (
        f"🔹 <b>Kunlik obuna #{number}</b>\n"
        f"⏳ Muddat: <b>{subscription.duration_days} kun</b>\n"
        f"💰 Narxi: <b>{subscription.price} ₽</b>\n"
        f"📅 Boshlangan sana: <b>{format_datetime(subscription.start_date)}</b>\n"
        f"⏳ Tugash sanasi: <b>{format_datetime(subscription.end_date)}</b>\n"
        f"{status_name(subscription.status)}"
    )


def format_subscription_history(
    subscriptions: list,
    daily_subscriptions: list,
) -> str:
    lines = ["📜 <b>OBUNALAR TARIXI</b>", ""]

    if subscriptions:
        lines.extend(["📦 <b>OBUNA</b>", ""])
        total = len(subscriptions)

        for index, subscription in enumerate(subscriptions):
            number = total - index
            lines.append(format_paid_history_item(number, subscription))
            lines.append("")

    if daily_subscriptions:
        lines.extend(["📅 <b>KUNLIK OBUNA</b>", ""])
        total = len(daily_subscriptions)

        for index, subscription in enumerate(daily_subscriptions):
            number = total - index
            lines.append(format_daily_history_item(number, subscription))
            lines.append("")

    if not subscriptions and not daily_subscriptions:
        lines.append("Hozircha obunalar tarixi mavjud emas.")

    return "\n".join(lines).rstrip()


def build_current_service_text(info: dict) -> str:
    current_service = info["current_service"]

    if current_service is None:
        return ""

    if current_service.service_type == "paid":
        item = info["subscription"]
        subscription_number = info.get("subscription_number")

        lines = [
            "🟢 <b>HOZIRGI XIZMAT</b>",
            "",
            "📦 <b>Obuna</b>",
        ]

        if subscription_number is not None:
            lines.append(f"💳 Raqam: <b>#{subscription_number}</b>")

        lines.extend(
            [
                f"📦 Tarif: <b>{item.plan.name}</b>",
                f"💰 Narxi: <b>{item.plan.price} ₽</b>",
                f"📅 Boshlangan sana: <b>{format_datetime(item.start_date)}</b>",
                f"⏳ Tugash sanasi: <b>{format_datetime(item.end_date)}</b>",
                f"⏱ Qolgan: <b>{format_remaining_days(item.end_date)} kun</b>",
            ]
        )
        return "\n".join(lines)

    if current_service.service_type == "daily":
        item = info["daily_subscription"]
        return "\n".join(
            [
                "🟢 <b>HOZIRGI XIZMAT</b>",
                "",
                "📅 <b>Kunlik obuna</b>",
                f"⏳ Muddat: <b>{item.duration_days} kun</b>",
                f"💰 Narxi: <b>{item.price} ₽</b>",
                f"📅 Boshlangan sana: <b>{format_datetime(item.start_date)}</b>",
                f"⏳ Tugash sanasi: <b>{format_datetime(item.end_date)}</b>",
                f"⏱ Qolgan: <b>{format_remaining_days(item.end_date)} kun</b>",
            ]
        )

    # Bonus is intentionally not shown here. Its details live in
    # "🎁 Mening bonuslarim".
    return (
        "🟢 <b>HOZIRGI XIZMAT</b>\n\n"
        "🎁 Hozirda bonus asosida faol xizmat mavjud.\n"
        "ℹ️ Bonus tafsilotlarini <b>🎁 Mening bonuslarim</b> bo‘limidan ko‘ring."
    )


def build_vpn_text(info: dict) -> str:
    vpn_account = info["vpn_account"]

    if vpn_account is None:
        return (
            "⚠️ <b>VPN hisob mavjud emas.</b>\n\n"
            "Faol xizmat uchun VPN hisob yaratishingiz mumkin."
        )

    return (
        f"👤 Username: <code>{vpn_account.marzban_username}</code>\n\n"
        f"🔗 <b>VLESS havola:</b>\n"
        f"<code>{vpn_account.vpn_link}</code>"
    )


def build_queue_text(info: dict) -> str:
    # The queue is global: paid, daily and bonus services are all
    # considered. Only the nearest next service is shown.
    queue = info["pending_queue"]

    if not queue:
        return ""

    period = queue[0]
    service_type = period.service_type.lower()

    if service_type == "paid":
        subscription = period.item
        plan_name = (
            subscription.plan.name
            if subscription.plan is not None
            else "Noma'lum tarif"
        )
        price = (
            f"{subscription.plan.price} ₽"
            if subscription.plan is not None
            else "—"
        )
        lines = [
            "📋 <b>KEYINGI XIZMAT</b>",
            "",
            "📦 <b>Obuna</b>",
            f"📦 Tarif: <b>{plan_name}</b>",
            f"💰 Narxi: <b>{price}</b>",
        ]
    elif service_type == "daily":
        daily_subscription = period.item
        lines = [
            "📋 <b>KEYINGI XIZMAT</b>",
            "",
            "📅 <b>Kunlik obuna</b>",
            f"⏳ Muddat: <b>{period.duration_days} kun</b>",
            f"💰 Narxi: <b>{daily_subscription.price} ₽</b>",
        ]
    else:
        # Bonus details are intentionally kept in My Bonuses, but a pending
        # bonus can still be the nearest service in the global service queue.
        bonus = period.item
        bonus_names = {
            "welcome": "🎁 Welcome Bonus",
            "promo": "🎟 Promo Bonus",
            "referral": "👥 Referral Bonus",
            "admin": "👨‍💼 Admin Bonus",
        }
        bonus_name = bonus_names.get(
            service_type,
            f"🎁 {service_type.title()} Bonus",
        )
        lines = [
            "📋 <b>KEYINGI XIZMAT</b>",
            "",
            f"{bonus_name}",
            f"⏳ Muddat: <b>{period.duration_days} kun</b>",
        ]

        traffic = getattr(bonus, "traffic", None)
        if service_type == "welcome" and traffic is not None:
            limit_gb = traffic.traffic_limit_bytes / (1024 ** 3)
            lines.append(f"📦 Trafik: <b>{limit_gb:.0f} GB</b>")

    lines.extend(
        [
            f"📅 Boshlanishi: <b>{format_datetime(period.start_date)}</b>",
            f"⏳ Tugashi: <b>{format_datetime(period.end_date)}</b>",
        ]
    )
    return "\n".join(lines)



async def _build_subscription_screen(telegram_id: int):
    async with async_session() as session:
        user_service = UserService(session)
        service_access_service = ServiceAccessService(session)
        subscription_info_service = SubscriptionInfoService(session)
        subscription_service = SubscriptionService(session)

        user = await user_service.get_by_telegram_id(telegram_id=telegram_id)
        if user is None:
            return (
                "❌ Foydalanuvchi topilmadi.",
                None,
            )

        try:
            await service_access_service.sync_user(user_id=user.id)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print("MY SUBSCRIPTION SCREEN SYNC ERROR:", repr(exc))

        info = await subscription_info_service.get_info(user.id)

        if info is None:
            return (
                "❌ Sizda hozircha faol yoki kutilayotgan xizmat mavjud emas.",
                user,
            )

        current = info["current_service"]
        if current is not None and current.service_type == "paid":
            history = await subscription_service.get_subscription_history(user.id)
            chronological = list(reversed(history))
            for number, item in enumerate(chronological, start=1):
                if item.id == current.item.id:
                    info["subscription_number"] = number
                    break

        sections = []
        current_text = build_current_service_text(info)
        vpn_text = build_vpn_text(info) if current is not None else ""
        queue_text = build_queue_text(info)

        for section in (current_text, vpn_text, queue_text):
            if section:
                sections.append(section)

        text = "\n\n".join(sections)
        if not text:
            text = "❌ Sizda hozircha faol yoki kutilayotgan xizmat mavjud emas."

        keyboard = None
        if current is not None and info["vpn_account"] is None:
            keyboard = subscription_keyboard(show_create_vpn=True)
        elif info["vpn_account"] is not None:
            subscription_url = (
                f"{config.MARZBAN_PUBLIC_URL}"
                f"{info['vpn_account'].subscription_url}"
            )
            keyboard = subscription_keyboard(subscription_url=subscription_url)
        else:
            keyboard = subscription_keyboard()

        return text, keyboard


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):
    text, keyboard = await _build_subscription_screen(message.from_user.id)
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "subscription_back")
async def subscription_back(callback: CallbackQuery):
    await callback.answer()

    text, keyboard = await _build_subscription_screen(
        callback.from_user.id
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "subscription_history")
async def subscription_history(callback: CallbackQuery):
    await callback.answer()

    async with async_session() as session:
        user_service = UserService(session)
        daily_service = DailySubscriptionService(session)
        subscription_service = SubscriptionService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id,
        )

        if user is None:
            await callback.message.edit_text(
                "❌ Foydalanuvchi topilmadi.",
                reply_markup=user_navigation_keyboard(
                    back_callback="subscription_history_back",
                    home_callback="user_main_menu",
                ),
            )
            return

        subscriptions = await subscription_service.get_subscription_history(user.id)
        daily_subscriptions = await daily_service.get_subscription_history(user.id)

    await callback.message.edit_text(
        format_subscription_history(subscriptions, daily_subscriptions),
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="subscription_history_back",
            home_callback="user_main_menu",
        ),
    )


@router.callback_query(F.data == "subscription_history_back")
async def subscription_history_back(callback: CallbackQuery):
    await callback.answer()

    text, keyboard = await _build_subscription_screen(callback.from_user.id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "subscription:create_vpn")
async def create_vpn_for_subscription(callback: CallbackQuery):
    await callback.answer()

    async with async_session() as session:
        user_service = UserService(session)
        service_access_service = ServiceAccessService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            language_code=callback.from_user.language_code,
        )

        try:
            current_service, vpn_account = await service_access_service.sync_user(
                user_id=user.id
            )
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print("CREATE VPN ACCOUNT ERROR:", repr(exc))
            await callback.message.edit_text(
                "❌ VPN hisob yaratishda xatolik yuz berdi.\n\n"
                "Iltimos, birozdan keyin qayta urinib ko‘ring.",
                reply_markup=user_navigation_keyboard(
                    home_callback="user_main_menu"
                ),
            )
            return

        if current_service is None or vpn_account is None:
            await callback.message.edit_text(
                "❌ Hozirda faol xizmat mavjud emas.\n\n"
                "🛒 Yangi xizmat sotib oling yoki navbatdagi xizmatni kuting.",
                reply_markup=user_navigation_keyboard(
                    home_callback="user_main_menu"
                ),
            )
            return

        subscription_url = (
            f"{config.MARZBAN_PUBLIC_URL}"
            f"{vpn_account.subscription_url}"
        )

        if current_service.service_type == "paid":
            subscription = current_service.item
            text = (
                "👤 <b>Mening obunam</b>\n\n"
                "🟢 <b>HOZIRGI XIZMAT</b>\n\n"
                f"📦 <b>Obuna</b>\n"
                f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
                f"💰 Narxi: <b>{subscription.plan.price} ₽</b>\n"
                f"📅 Tugash sanasi: <b>{format_datetime(subscription.end_date)}</b>\n"
                f"⏱ Qolgan: <b>{format_remaining_days(subscription.end_date)} kun</b>\n\n"
                f"👤 Username: <code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n<code>{vpn_account.vpn_link}</code>"
            )
        elif current_service.service_type == "daily":
            daily_subscription = current_service.item
            text = (
                "👤 <b>Mening obunam</b>\n\n"
                "🟢 <b>HOZIRGI XIZMAT</b>\n\n"
                "📅 <b>Kunlik obuna</b>\n"
                f"⏳ Muddat: <b>{daily_subscription.duration_days} kun</b>\n"
                f"💰 Narxi: <b>{daily_subscription.price} ₽</b>\n"
                f"📅 Tugash sanasi: <b>{format_datetime(daily_subscription.end_date)}</b>\n"
                f"⏱ Qolgan: <b>{format_remaining_days(daily_subscription.end_date)} kun</b>\n\n"
                f"👤 Username: <code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n<code>{vpn_account.vpn_link}</code>"
            )
        else:
            text = (
                "👤 <b>Mening obunam</b>\n\n"
                "🟢 <b>HOZIRGI XIZMAT</b>\n\n"
                "🎁 Bonus asosida faol xizmat mavjud.\n"
                "ℹ️ Bonus tafsilotlarini <b>🎁 Mening bonuslarim</b> bo‘limidan ko‘ring.\n\n"
                f"👤 Username: <code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n<code>{vpn_account.vpn_link}</code>"
            )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=subscription_keyboard(
            subscription_url=subscription_url,
        ),
    )
