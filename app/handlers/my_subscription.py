from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config.config import config
from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.keyboards.subscription_keyboard import subscription_keyboard
from app.services.service_access_service import ServiceAccessService
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.user_service import UserService


router = Router()


BONUS_NAMES = {
    "welcome": "🎁 Welcome Bonus",
    "promo": "🎟 Promo Bonus",
    "referral": "👥 Referral Bonus",
    "admin": "🛠 Admin Bonus",
}


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"

    return value.strftime("%d.%m.%Y %H:%M")


def format_date(value: datetime | None) -> str:
    if value is None:
        return "—"

    return value.strftime("%d.%m.%Y")


def format_remaining_days(end_date: datetime | None) -> int | None:
    if end_date is None:
        return None

    now = datetime.now(end_date.tzinfo)
    seconds = (end_date - now).total_seconds()

    if seconds <= 0:
        return 0

    return max(1, int((seconds + 86399) // 86400))


def get_bonus_name(bonus_type: str) -> str:
    return BONUS_NAMES.get(
        bonus_type.lower(),
        f"🎁 {bonus_type.title()} Bonus",
    )


def format_queue_item(index: int, period) -> str:
    name = (
        "📦 Oylik obuna"
        if period.service_type == "paid"
        else "📅 Kunlik obuna"
        if period.service_type == "daily"
        else get_bonus_name(period.service_type)
    )

    return (
        f"{index}️⃣ {name}\n"
        f"   ⏳ Muddat: <b>{period.duration_days} kun</b>\n"
        f"   📅 {format_datetime(period.start_date)} → "
        f"{format_datetime(period.end_date)}"
    )


def format_bonus_history(bonuses: list) -> str:
    if not bonuses:
        return ""

    lines = ["📜 <b>Bonuslar tarixi</b>", ""]

    for bonus in bonuses:
        name = get_bonus_name(bonus.bonus_type)
        status = {
            "pending": "⏳ Kutilmoqda",
            "active": "🟢 Faol",
            "expired": "⚪ Tugagan",
            "revoked": "🔴 Bekor qilingan",
        }.get(
            bonus.status,
            bonus.status,
        )

        lines.append(
            f"• {name}"
        )
        lines.append(
            f"  ⏳ {bonus.duration_days} kun"
        )

        if (
            bonus.bonus_type.lower() == "welcome"
            and getattr(bonus, "traffic", None) is not None
        ):
            traffic = bonus.traffic
            limit_gb = (
                traffic.traffic_limit_bytes
                / (1024 ** 3)
            )
            lines.append(
                f"  📦 {limit_gb:.0f} GB"
            )

        lines.append(
            f"  {status}"
        )

    return "\n".join(lines)


def format_pending_bonus_summary(bonuses: list) -> str:
    if not bonuses:
        return ""

    grouped: dict[str, list] = {}

    for bonus in bonuses:
        bonus_type = bonus.bonus_type.lower()

        if bonus_type == "welcome":
            continue

        grouped.setdefault(bonus_type, []).append(bonus)

    if not grouped:
        return ""

    lines = ["🎁 <b>Kutilayotgan bonuslar</b>", ""]

    for bonus_type in ("promo", "referral", "admin"):
        items = grouped.get(bonus_type)

        if not items:
            continue

        total_days = sum(
            bonus.duration_days
            for bonus in items
        )

        name = get_bonus_name(bonus_type)

        lines.append(
            f"{name}: <b>{len(items)} ta = {total_days} kun</b>"
        )

    for bonus_type, items in grouped.items():
        if bonus_type in {"promo", "referral", "admin"}:
            continue

        total_days = sum(
            bonus.duration_days
            for bonus in items
        )

        lines.append(
            f"{get_bonus_name(bonus_type)}: "
            f"<b>{len(items)} ta = {total_days} kun</b>"
        )

    return "\n".join(lines)


async def get_marzban_status(username: str) -> str | None:
    try:
        marzban_service = create_marzban_service()
        data = await marzban_service.get_user(username=username)

        if data is None:
            return None

        return data.get("status")

    except Exception as e:
        print(
            "MY SUBSCRIPTION MARZBAN STATUS ERROR:",
            repr(e),
        )
        return None


def build_current_service_text(info: dict) -> str:
    current_service = info["current_service"]
    subscription = info["subscription"]
    daily_subscription = info["daily_subscription"]
    active_bonus = info["active_bonus"]

    if current_service is None:
        return ""

    lines = [
        "🟢 <b>HOZIRGI XIZMAT</b>",
        "",
    ]

    if current_service.service_type == "paid":
        item = subscription

        lines.extend(
            [
                f"📦 Tarif: <b>{item.plan.name}</b>",
                f"💰 Narxi: <b>{item.plan.price} ₽</b>",
                f"📅 Boshlangan sana: "
                f"<b>{format_datetime(item.start_date)}</b>",
                f"⏳ Tugash sanasi: "
                f"<b>{format_datetime(item.end_date)}</b>",
            ]
        )

    elif current_service.service_type == "daily":
        item = daily_subscription

        lines.extend(
            [
                "📅 Obuna turi: <b>Kunlik</b>",
                f"⏳ Muddat: <b>{item.duration_days} kun</b>",
                f"💰 Narxi: <b>{item.price} ₽</b>",
                f"📅 Boshlangan sana: "
                f"<b>{format_datetime(item.start_date)}</b>",
                f"⏳ Tugash sanasi: "
                f"<b>{format_datetime(item.end_date)}</b>",
            ]
        )

    else:
        item = active_bonus
        lines.extend(
            [
                get_bonus_name(item.bonus_type),
                f"⏳ Muddat: <b>{item.duration_days} kun</b>",
                f"📅 Boshlangan sana: "
                f"<b>{format_datetime(item.start_date)}</b>",
                f"⏳ Tugash sanasi: "
                f"<b>{format_datetime(item.end_date)}</b>",
            ]
        )

        if item.bonus_type.lower() == "welcome":
            traffic = getattr(item, "traffic", None)

            if traffic is not None:
                used_gb = (
                    traffic.traffic_used_bytes
                    / (1024 ** 3)
                )
                limit_gb = (
                    traffic.traffic_limit_bytes
                    / (1024 ** 3)
                )

                lines.append(
                    f"📊 Trafik: <b>{used_gb:.2f} / "
                    f"{limit_gb:.0f} GB</b>"
                )

    remaining_days = format_remaining_days(
        current_service.end_date
    )

    if remaining_days is not None:
        lines.append(
            f"⏱ Qolgan: <b>{remaining_days} kun</b>"
        )

    return "\n".join(lines)


def build_vpn_text(
    info: dict,
) -> str:
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
    queue = info["pending_queue"]

    if not queue:
        return ""

    lines = [
        "📋 <b>KEYINGI NAVBAT</b>",
        "",
    ]

    for index, period in enumerate(queue, start=1):
        lines.append(
            format_queue_item(index, period)
        )
        lines.append("")

    return "\n".join(lines).rstrip()


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):
    async with async_session() as session:
        user_service = UserService(session)
        service_access_service = ServiceAccessService(session)
        subscription_info_service = SubscriptionInfoService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        try:
            await service_access_service.sync_user(
                user_id=user.id
            )
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(
                "MY SUBSCRIPTION SYNC ERROR:",
                repr(exc),
            )

        info = await subscription_info_service.get_info(
            user.id
        )

        if info is None:
            await message.answer(
                "❌ Sizda hozircha xizmat yoki bonus mavjud emas.\n\n"
                "🛒 Obuna sotib olish bo‘limidan "
                "tarif tanlang yoki bonus oling."
            )
            return

        current_service_text = build_current_service_text(
            info
        )

        vpn_text = ""

        if info["current_service"] is not None:
            vpn_text = build_vpn_text(info)

        queue_text = build_queue_text(info)

        pending_summary = format_pending_bonus_summary(
            info["pending_bonuses"]
        )

        history_text = format_bonus_history(
            info["bonus_history"]
        )

        sections = []

        if current_service_text:
            sections.append(current_service_text)

        if vpn_text:
            sections.append(vpn_text)

        if queue_text:
            sections.append(queue_text)

        if pending_summary:
            sections.append(pending_summary)

        if history_text:
            sections.append(history_text)

        text = "\n\n".join(sections)

        if not text:
            text = (
                "❌ Sizda hozircha faol yoki kutilayotgan "
                "xizmat mavjud emas."
            )

        keyboard = None

        if (
            info["current_service"] is not None
            and info["vpn_account"] is None
        ):
            keyboard = subscription_keyboard(
                show_create_vpn=True
            )
        elif info["vpn_account"] is not None:
            subscription_url = (
                f"{config.MARZBAN_PUBLIC_URL}"
                f"{info['vpn_account'].subscription_url}"
            )
            keyboard = subscription_keyboard(
                subscription_url=subscription_url
            )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


@router.callback_query(F.data == "subscription:create_vpn")
async def create_vpn_for_subscription(
    callback: CallbackQuery,
):
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
            current_service, vpn_account = (
                await service_access_service.sync_user(
                    user_id=user.id
                )
            )
            await session.commit()

        except Exception as exc:
            await session.rollback()

            print(
                "CREATE VPN ACCOUNT ERROR:",
                repr(exc),
            )

            await callback.message.edit_text(
                "❌ VPN hisob yaratishda xatolik yuz berdi.\n\n"
                "Iltimos, birozdan keyin qayta urinib ko‘ring."
            )
            return

        if current_service is None or vpn_account is None:
            await callback.message.edit_text(
                "❌ Hozirda faol xizmat mavjud emas.\n\n"
                "🛒 Yangi xizmat sotib oling yoki "
                "bonus navbatini kuting."
            )
            return

        subscription_url = (
            f"{config.MARZBAN_PUBLIC_URL}"
            f"{vpn_account.subscription_url}"
        )

        if current_service.service_type == "paid":
            subscription = current_service.item

            await callback.message.edit_text(
                f"👤 <b>Mening obunam</b>\n\n"
                f"🟢 <b>HOZIRGI XIZMAT</b>\n\n"
                f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
                f"💰 Narxi: <b>{subscription.plan.price} ₽</b>\n"
                f"📅 Tugash sanasi: "
                f"<b>{format_datetime(subscription.end_date)}</b>\n"
                f"⏱ Qolgan: "
                f"<b>{format_remaining_days(subscription.end_date)} kun</b>\n\n"
                f"👤 Username: "
                f"<code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n"
                f"<code>{vpn_account.vpn_link}</code>",
                parse_mode="HTML",
                reply_markup=subscription_keyboard(
                    subscription_url=subscription_url,
                ),
            )
            return

        if current_service.service_type == "daily":
            daily_subscription = current_service.item

            await callback.message.edit_text(
                f"👤 <b>Mening obunam</b>\n\n"
                f"🟢 <b>HOZIRGI XIZMAT</b>\n\n"
                f"📅 Obuna turi: <b>Kunlik</b>\n"
                f"⏳ Muddat: <b>{daily_subscription.duration_days} kun</b>\n"
                f"💰 Narxi: <b>{daily_subscription.price} ₽</b>\n"
                f"📅 Tugash sanasi: "
                f"<b>{format_datetime(daily_subscription.end_date)}</b>\n"
                f"⏱ Qolgan: "
                f"<b>{format_remaining_days(daily_subscription.end_date)} kun</b>\n\n"
                f"👤 Username: "
                f"<code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n"
                f"<code>{vpn_account.vpn_link}</code>",
                parse_mode="HTML",
                reply_markup=subscription_keyboard(
                    subscription_url=subscription_url,
                ),
            )
            return

        bonus = current_service.item
        bonus_name = get_bonus_name(
            bonus.bonus_type
        )

        traffic_text = ""

        if bonus.bonus_type.lower() == "welcome":
            traffic = getattr(bonus, "traffic", None)

            if traffic is not None:
                used_gb = (
                    traffic.traffic_used_bytes
                    / (1024 ** 3)
                )
                limit_gb = (
                    traffic.traffic_limit_bytes
                    / (1024 ** 3)
                )

                traffic_text = (
                    f"📊 Trafik: <b>{used_gb:.2f} / "
                    f"{limit_gb:.0f} GB</b>\n\n"
                )

        await callback.message.edit_text(
            f"👤 <b>Mening xizmatim</b>\n\n"
            f"🟢 <b>HOZIRGI XIZMAT</b>\n\n"
            f"{bonus_name}\n"
            f"⏳ Muddat: <b>{bonus.duration_days} kun</b>\n"
            f"📅 Tugash sanasi: "
            f"<b>{format_datetime(bonus.end_date)}</b>\n"
            f"⏱ Qolgan: "
            f"<b>{format_remaining_days(bonus.end_date)} kun</b>\n\n"
            f"{traffic_text}"
            f"👤 Username: "
            f"<code>{vpn_account.marzban_username}</code>\n\n"
            f"🔗 <b>VLESS havola:</b>\n"
            f"<code>{vpn_account.vpn_link}</code>",
            parse_mode="HTML",
            reply_markup=subscription_keyboard(
                subscription_url=subscription_url,
            ),
        )
