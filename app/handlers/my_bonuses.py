from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.bonus_keyboard import (
    bonus_history_keyboard,
    bonus_keyboard,
)
from app.services.user_bonus_service import UserBonusService
from app.services.user_service import UserService
from app.repositories.promo_repository import PromoRepository


router = Router()


BONUS_NAMES = {
    "welcome": "🎁 Welcome Bonus",
    "promo": "🎟 Promo Bonus",
    "referral": "👥 Referral Bonus",
    "admin": "👨‍💼 Admin Bonus",
}

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


def format_bytes(value: int) -> str:
    if value < 1024 ** 2:
        return f"{value / 1024:.0f} KB"

    if value < 1024 ** 3:
        return f"{value / (1024 ** 2):.0f} MB"

    return f"{value / (1024 ** 3):.2f} GB"


def bonus_name(bonus_type: str) -> str:
    return BONUS_NAMES.get(
        bonus_type.lower(),
        f"🎁 {bonus_type.title()} Bonus",
    )


def status_name(status: str) -> str:
    return STATUS_NAMES.get(status, status)


def bonus_public_number(bonus) -> str:
    if bonus.bonus_number is None:
        return ""
    return f" #{bonus.bonus_number}"


async def get_promo_code(session, bonus_id: int) -> str | None:
    try:
        repository = PromoRepository(session)
        redemption = await repository.get_redemption_by_bonus_id(bonus_id)
        if redemption is None or redemption.promo is None:
            return None
        return redemption.promo.code
    except Exception as exc:
        print("MY BONUSES PROMO SOURCE ERROR:", repr(exc))
        return None


def format_bonus_block(bonus, promo_code: str | None = None) -> str:
    bonus_type = bonus.bonus_type.lower()
    lines = [
        f"{bonus_name(bonus_type)}{bonus_public_number(bonus)}",
        f"📌 Holati: <b>{status_name(bonus.status)}</b>",
        f"⏳ Muddat: <b>{bonus.duration_days} kun</b>",
    ]

    if bonus.start_date is not None:
        lines.append(
            f"📅 Boshlangan sana: <b>{format_datetime(bonus.start_date)}</b>"
        )

    if bonus.end_date is not None:
        lines.append(
            f"⏳ Tugash sanasi: <b>{format_datetime(bonus.end_date)}</b>"
        )

    if bonus.status == "active" and bonus.end_date is not None:
        lines.append(
            f"⏱ Qolgan: <b>{format_remaining_days(bonus.end_date)} kun</b>"
        )

    if bonus_type == "welcome":
        traffic = getattr(bonus, "traffic", None)
        if traffic is not None:
            total = traffic.traffic_limit_bytes
            used = traffic.traffic_used_bytes
            remaining = max(0, total - used)
            lines.extend(
                [
                    f"📊 Jami trafik: <b>{format_bytes(total)}</b>",
                    f"📤 Ishlatilgan: <b>{format_bytes(used)}</b>",
                    f"📥 Qolgan: <b>{format_bytes(remaining)}</b>",
                ]
            )

    elif bonus_type == "promo" and promo_code:
        lines.append(f"🎟 Promo kod: <code>{promo_code}</code>")

    elif bonus_type == "admin" and bonus.reason:
        lines.append(f"📝 Sabab: <b>{bonus.reason}</b>")

    return "\n".join(lines)


def format_bonus_history_item(bonus, promo_code: str | None = None) -> str:
    return format_bonus_block(bonus, promo_code)


async def _load_bonuses(telegram_id: int):
    async with async_session() as session:
        user_service = UserService(session)
        bonus_service = UserBonusService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=telegram_id,
        )

        if user is None:
            return None

        bonuses = await bonus_service.get_bonus_history(user.id)

        current = [
            bonus
            for bonus in bonuses
            if bonus.status in {"active", "pending"}
        ]

        history = [
            bonus
            for bonus in bonuses
            if bonus.status in {"expired", "revoked"}
        ]

        promo_codes = {}
        for bonus in current + history:
            if bonus.bonus_type.lower() == "promo":
                promo_codes[bonus.id] = await get_promo_code(
                    session,
                    bonus.id,
                )

        return user, current, history, promo_codes


async def _build_bonus_dashboard(telegram_id: int):
    result = await _load_bonuses(telegram_id)

    if result is None:
        return "❌ Foydalanuvchi topilmadi."

    user, bonuses, _history, promo_codes = result

    if not bonuses:
        return (
            "🎁 <b>MENING BONUSLARIM</b>\n\n"
            "Hozirda sizda faol yoki kutilayotgan bonus mavjud emas."
        )

    ordered_types = ("welcome", "promo", "referral", "admin")
    ordered = []

    for bonus_type in ordered_types:
        ordered.extend(
            bonus
            for bonus in bonuses
            if bonus.bonus_type.lower() == bonus_type
        )

    ordered.extend(
        bonus
        for bonus in bonuses
        if bonus.bonus_type.lower() not in ordered_types
    )

    lines = ["🎁 <b>MENING BONUSLARIM</b>", ""]

    for bonus in ordered:
        lines.append(
            format_bonus_block(
                bonus,
                promo_codes.get(bonus.id),
            )
        )
        lines.append("")

    return "\n".join(lines).rstrip()


async def _build_bonus_history(telegram_id: int):
    result = await _load_bonuses(telegram_id)

    if result is None:
        return "❌ Foydalanuvchi topilmadi."

    _user, _current, history, promo_codes = result

    lines = ["📜 <b>BONUSLAR TARIXI</b>", ""]

    if not history:
        lines.append("Hozircha tugagan yoki bekor qilingan bonuslar mavjud emas.")
        return "\n".join(lines)

    for bonus in history:
        lines.append(
            format_bonus_history_item(
                bonus,
                promo_codes.get(bonus.id),
            )
        )
        lines.append("")

    return "\n".join(lines).rstrip()


@router.message(F.text == "🎁 Mening bonuslarim")
async def my_bonuses(message: Message):
    text = await _build_bonus_dashboard(message.from_user.id)
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=bonus_keyboard(),
    )


@router.callback_query(F.data == "bonus_history")
async def bonus_history(callback: CallbackQuery):
    await callback.answer()

    text = await _build_bonus_history(callback.from_user.id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=bonus_history_keyboard(),
    )


@router.callback_query(F.data == "bonus_history_back")
async def bonus_history_back(callback: CallbackQuery):
    await callback.answer()

    text = await _build_bonus_dashboard(callback.from_user.id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=bonus_keyboard(),
    )
