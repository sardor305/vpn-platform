from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError

from app.database.database import async_session
from app.keyboards.admin import admin_menu
from app.keyboards.promo_admin import (
    promo_admin_menu,
    promo_create_cancel_keyboard,
    promo_detail_keyboard,
    promo_edit_keyboard,
    promo_list_keyboard,
)
from app.models.promo import Promo
from app.repositories.promo_repository import PromoRepository
from app.services.user_service import UserService


router = Router()


class PromoAdminStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_duration = State()
    waiting_for_total_limit = State()
    waiting_for_user_limit = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()

    waiting_for_edit_duration = State()
    waiting_for_edit_total_limit = State()
    waiting_for_edit_user_limit = State()
    waiting_for_edit_start = State()
    waiting_for_edit_end = State()


def _parse_date(value: str) -> datetime | None:
    value = value.strip()

    if value in {"-", "0", "none", "None", "yo‘q", "yo'q"}:
        return None

    formats = (
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y",
    )

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    raise ValueError(
        "Sana formati noto‘g‘ri. "
        "Masalan: 15.09.2026 00:00 yoki 15.09.2026"
    )


def _format_date(value: datetime | None) -> str:
    if value is None:
        return "Cheklanmagan"

    if value.tzinfo is None:
        return value.strftime("%d.%m.%Y %H:%M")

    return value.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def _format_limit(value: int | None) -> str:
    return "∞" if value is None else str(value)


async def _get_admin(telegram_id: int):
    async with async_session() as session:
        user = await UserService(session).get_by_telegram_id(
            telegram_id=telegram_id
        )

    if user is None or not user.is_admin:
        return None

    return user


async def _show_promo_list(message: Message | CallbackQuery):
    if isinstance(message, CallbackQuery):
        target = message.message
    else:
        target = message

    async with async_session() as session:
        promos = await PromoRepository(session).get_all()

    if not promos:
        await target.edit_text(
            "🎟 <b>Promo kodlar</b>\n\n"
            "Hozircha promo kodlar mavjud emas.",
            parse_mode="HTML",
            reply_markup=promo_admin_menu(),
        )
        return

    text = (
        "🎟 <b>Promo kodlar</b>\n\n"
        "Kerakli promo kodni tanlang:"
    )

    await target.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=promo_list_keyboard(promos),
    )


async def _show_promo_detail(
    target_message: Message,
    promo_id: int,
):
    async with async_session() as session:
        repository = PromoRepository(session)
        promo = await repository.get_by_id(promo_id)

        if promo is None:
            await target_message.edit_text(
                "❌ Promo kod topilmadi.",
                parse_mode="HTML",
                reply_markup=promo_admin_menu(),
            )
            return

        redemption_count = await repository.count_redemptions(
            promo_id=promo.id
        )

    status = "🟢 Faol" if promo.is_active else "🔴 O‘chiq"
    total_limit = _format_limit(promo.total_redemption_limit)

    text = (
        "🎟 <b>PROMO MA’LUMOTLARI</b>\n\n"
        f"🔑 Kod: <code>{promo.code}</code>\n"
        f"🎁 Bonus: <b>{promo.duration_days} kun</b>\n"
        f"👥 Umumiy limit: <b>{total_limit}</b>\n"
        f"👤 1 foydalanuvchi limiti: <b>{promo.per_user_limit}</b>\n"
        f"📊 Ishlatilgan: <b>{redemption_count}</b>\n"
        f"📅 Boshlanishi: <b>{_format_date(promo.start_date)}</b>\n"
        f"📅 Tugashi: <b>{_format_date(promo.end_date)}</b>\n"
        f"⚙️ Status: <b>{status}</b>"
    )

    await target_message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=promo_detail_keyboard(
            promo_id=promo.id,
            is_active=promo.is_active,
        ),
    )


@router.message(F.text == "🎟 Promo")
async def promo_admin_entry(message: Message):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        return

    await message.answer(
        "🎟 <b>Promo boshqaruvi</b>\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=promo_admin_menu(),
    )


@router.callback_query(F.data == "promo_admin:list")
async def promo_admin_list(callback: CallbackQuery):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    await callback.answer()
    await _show_promo_list(callback)


@router.callback_query(F.data == "promo_admin:back")
async def promo_admin_back(callback: CallbackQuery):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    await callback.answer()

    await callback.message.edit_text(
        "🎟 <b>Promo boshqaruvi</b>\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=promo_admin_menu(),
    )


@router.callback_query(F.data.startswith("promo_admin:view:"))
async def promo_admin_view(callback: CallbackQuery):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        promo_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Promo ID noto‘g‘ri.", show_alert=True)
        return

    await callback.answer()
    await _show_promo_detail(
        target_message=callback.message,
        promo_id=promo_id,
    )


@router.callback_query(F.data == "promo_admin:create")
async def promo_admin_create_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    await callback.answer()
    await state.clear()
    await state.set_state(PromoAdminStates.waiting_for_code)

    await callback.message.edit_text(
        "➕ <b>Promo yaratish</b>\n\n"
        "1/6. Promo kodini yuboring.\n\n"
        "Masalan: <code>SUMMER2026</code>",
        parse_mode="HTML",
        reply_markup=promo_create_cancel_keyboard(),
    )


@router.message(PromoAdminStates.waiting_for_code)
async def promo_admin_create_code(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    code = (message.text or "").strip().upper()

    if code in {"CANCEL", "BEKOR"}:
        await state.clear()
        await message.answer(
            "❌ Promo yaratish bekor qilindi.",
            reply_markup=admin_menu,
        )
        return

    if not code or len(code) > 64 or any(ch.isspace() for ch in code):
        await message.answer(
            "❌ Promo kod noto‘g‘ri. 1–64 belgidan iborat, "
            "bo‘shliqsiz kod yuboring."
        )
        return

    async with async_session() as session:
        existing = await PromoRepository(session).get_by_code(code)

    if existing is not None:
        await message.answer(
            "❌ Bu promo kod allaqachon mavjud. Boshqa kod kiriting."
        )
        return

    await state.update_data(code=code)
    await state.set_state(PromoAdminStates.waiting_for_duration)

    await message.answer(
        "2/6. Bonus muddatini kunlarda yuboring.\n\n"
        "Masalan: <code>7</code>"
    )


@router.message(PromoAdminStates.waiting_for_duration)
async def promo_admin_create_duration(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        duration = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting. Masalan: 7")
        return

    if duration <= 0:
        await message.answer("❌ Bonus kunlari 0 dan katta bo‘lishi kerak.")
        return

    await state.update_data(duration_days=duration)
    await state.set_state(PromoAdminStates.waiting_for_total_limit)

    await message.answer(
        "3/6. Umumiy foydalanish limitini yuboring.\n\n"
        "Masalan: <code>100</code>\n"
        "Cheksiz limit uchun: <code>0</code>"
    )


@router.message(PromoAdminStates.waiting_for_total_limit)
async def promo_admin_create_total_limit(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting.")
        return

    if value < 0:
        await message.answer("❌ Limit manfiy bo‘lishi mumkin emas.")
        return

    total_limit = None if value == 0 else value

    await state.update_data(total_redemption_limit=total_limit)
    await state.set_state(PromoAdminStates.waiting_for_user_limit)

    await message.answer(
        "4/6. Bitta foydalanuvchi promo koddan necha marta "
        "foydalana olishini yuboring.\n\n"
        "Masalan: <code>1</code>"
    )


@router.message(PromoAdminStates.waiting_for_user_limit)
async def promo_admin_create_user_limit(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting.")
        return

    if value <= 0:
        await message.answer("❌ Foydalanuvchi limiti 0 dan katta bo‘lishi kerak.")
        return

    await state.update_data(per_user_limit=value)
    await state.set_state(PromoAdminStates.waiting_for_start_date)

    await message.answer(
        "5/6. Boshlanish sanasini yuboring.\n\n"
        "Format: <code>15.09.2026 00:00</code>\n"
        "Cheklovsiz darhol boshlash uchun: <code>-</code>"
    )


@router.message(PromoAdminStates.waiting_for_start_date)
async def promo_admin_create_start_date(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        start_date = _parse_date(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    await state.update_data(start_date=start_date)
    await state.set_state(PromoAdminStates.waiting_for_end_date)

    await message.answer(
        "6/6. Tugash sanasini yuboring.\n\n"
        "Format: <code>30.09.2026 23:59</code>\n"
        "Cheklovsiz tugash uchun: <code>-</code>"
    )


@router.message(PromoAdminStates.waiting_for_end_date)
async def promo_admin_create_end_date(
    message: Message,
    state: FSMContext,
):
    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        end_date = _parse_date(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    data = await state.get_data()
    start_date = data.get("start_date")

    if start_date is not None and end_date is not None and end_date <= start_date:
        await message.answer(
            "❌ Tugash sanasi boshlanish sanasidan keyin bo‘lishi kerak."
        )
        return

    try:
        async with async_session() as session:
            repository = PromoRepository(session)

            promo = await repository.create(
                code=data["code"],
                duration_days=data["duration_days"],
                total_redemption_limit=data["total_redemption_limit"],
                per_user_limit=data["per_user_limit"],
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )

            await session.commit()

    except IntegrityError:
        await message.answer(
            "❌ Promo kod yaratilmadi: bu kod allaqachon mavjud."
        )
        await state.clear()
        return

    except Exception as exc:
        print("PROMO CREATE ERROR:", repr(exc))
        await message.answer(
            "❌ Promo yaratishda xatolik yuz berdi."
        )
        await state.clear()
        return

    await state.clear()

    await message.answer(
        "✅ <b>Promo muvaffaqiyatli yaratildi.</b>\n\n"
        f"🔑 Kod: <code>{promo.code}</code>\n"
        f"🎁 Bonus: <b>{promo.duration_days} kun</b>\n"
        f"👥 Umumiy limit: <b>{_format_limit(promo.total_redemption_limit)}</b>\n"
        f"👤 Foydalanuvchi limiti: <b>{promo.per_user_limit}</b>\n"
        f"📅 Boshlanishi: <b>{_format_date(promo.start_date)}</b>\n"
        f"📅 Tugashi: <b>{_format_date(promo.end_date)}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.callback_query(F.data.startswith("promo_admin:create_cancel"))
async def promo_admin_create_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    await state.clear()
    await callback.answer("Bekor qilindi.")

    await callback.message.edit_text(
        "🎟 <b>Promo boshqaruvi</b>\n\n"
        "Kerakli amalni tanlang:",
        parse_mode="HTML",
        reply_markup=promo_admin_menu(),
    )


@router.callback_query(F.data.startswith("promo_admin:activate:"))
async def promo_admin_activate(callback: CallbackQuery):
    await _set_promo_active(callback, True)


@router.callback_query(F.data.startswith("promo_admin:deactivate:"))
async def promo_admin_deactivate(callback: CallbackQuery):
    await _set_promo_active(callback, False)


async def _set_promo_active(
    callback: CallbackQuery,
    active: bool,
):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        promo_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Promo ID noto‘g‘ri.", show_alert=True)
        return

    async with async_session() as session:
        repository = PromoRepository(session)
        promo = await repository.get_by_id(promo_id)

        if promo is None:
            await callback.answer(
                "Promo kod topilmadi.",
                show_alert=True,
            )
            return

        promo.is_active = active
        await repository.update(promo)
        await session.commit()

    await callback.answer(
        "Promo faollashtirildi." if active else "Promo o‘chirildi."
    )

    await _show_promo_detail(
        target_message=callback.message,
        promo_id=promo_id,
    )


@router.callback_query(F.data.startswith("promo_admin:edit:"))
async def promo_admin_edit(
    callback: CallbackQuery,
    state: FSMContext,
):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        promo_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Promo ID noto‘g‘ri.", show_alert=True)
        return

    async with async_session() as session:
        promo = await PromoRepository(session).get_by_id(promo_id)

    if promo is None:
        await callback.answer("Promo kod topilmadi.", show_alert=True)
        return

    await callback.answer()
    await state.clear()
    await state.update_data(promo_id=promo_id)

    await callback.message.edit_text(
        f"✏️ <b>{promo.code}</b> tahrirlash\n\n"
        "O‘zgartirmoqchi bo‘lgan parametrni tanlang:",
        parse_mode="HTML",
        reply_markup=promo_edit_keyboard(promo_id),
    )


@router.callback_query(F.data.startswith("promo_admin:edit_duration:"))
async def promo_admin_edit_duration_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await _start_edit_state(
        callback,
        state,
        PromoAdminStates.waiting_for_edit_duration,
        "Bonus kunlari",
        "Masalan: <code>7</code>",
    )


@router.callback_query(F.data.startswith("promo_admin:edit_total_limit:"))
async def promo_admin_edit_total_limit_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await _start_edit_state(
        callback,
        state,
        PromoAdminStates.waiting_for_edit_total_limit,
        "Umumiy limit",
        "Masalan: <code>100</code>. Cheksiz uchun: <code>0</code>",
    )


@router.callback_query(F.data.startswith("promo_admin:edit_user_limit:"))
async def promo_admin_edit_user_limit_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await _start_edit_state(
        callback,
        state,
        PromoAdminStates.waiting_for_edit_user_limit,
        "Foydalanuvchi limiti",
        "Masalan: <code>1</code>",
    )


@router.callback_query(F.data.startswith("promo_admin:edit_start:"))
async def promo_admin_edit_start_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await _start_edit_state(
        callback,
        state,
        PromoAdminStates.waiting_for_edit_start,
        "Boshlanish sanasi",
        "Masalan: <code>15.09.2026 00:00</code>. Cheklovsiz uchun: <code>-</code>",
    )


@router.callback_query(F.data.startswith("promo_admin:edit_end:"))
async def promo_admin_edit_end_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    await _start_edit_state(
        callback,
        state,
        PromoAdminStates.waiting_for_edit_end,
        "Tugash sanasi",
        "Masalan: <code>30.09.2026 23:59</code>. Cheklovsiz uchun: <code>-</code>",
    )


async def _start_edit_state(
    callback: CallbackQuery,
    state: FSMContext,
    new_state: State,
    title: str,
    example: str,
):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        promo_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Promo ID noto‘g‘ri.", show_alert=True)
        return

    async with async_session() as session:
        promo = await PromoRepository(session).get_by_id(promo_id)

    if promo is None:
        await callback.answer("Promo kod topilmadi.", show_alert=True)
        return

    await state.clear()
    await state.update_data(promo_id=promo_id)
    await state.set_state(new_state)
    await callback.answer()

    await callback.message.edit_text(
        f"✏️ <b>{title}</b>\n\n"
        f"{example}\n\n"
        "Bekor qilish uchun <code>BEKOR</code> yuboring.",
        parse_mode="HTML",
        reply_markup=promo_create_cancel_keyboard(),
    )


async def _cancel_edit_if_requested(
    message: Message,
    state: FSMContext,
) -> bool:
    value = (message.text or "").strip().upper()

    if value not in {"BEKOR", "CANCEL"}:
        return False

    data = await state.get_data()
    promo_id = data.get("promo_id")
    await state.clear()

    if promo_id is not None:
        async with async_session() as session:
            promo = await PromoRepository(session).get_by_id(int(promo_id))

        if promo is not None:
            await message.answer(
                "↩️ Tahrirlash bekor qilindi.",
                reply_markup=promo_admin_menu(),
            )
            return True

    await message.answer(
        "↩️ Tahrirlash bekor qilindi.",
        reply_markup=admin_menu,
    )
    return True


@router.message(PromoAdminStates.waiting_for_edit_duration)
async def promo_admin_edit_duration(
    message: Message,
    state: FSMContext,
):
    if await _cancel_edit_if_requested(message, state):
        return

    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting.")
        return

    if value <= 0:
        await message.answer("❌ Bonus kunlari 0 dan katta bo‘lishi kerak.")
        return

    await _save_edit(
        message=message,
        state=state,
        field="duration_days",
        value=value,
    )


@router.message(PromoAdminStates.waiting_for_edit_total_limit)
async def promo_admin_edit_total_limit(
    message: Message,
    state: FSMContext,
):
    if await _cancel_edit_if_requested(message, state):
        return

    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting.")
        return

    if value < 0:
        await message.answer("❌ Limit manfiy bo‘lishi mumkin emas.")
        return

    await _save_edit(
        message=message,
        state=state,
        field="total_redemption_limit",
        value=None if value == 0 else value,
    )


@router.message(PromoAdminStates.waiting_for_edit_user_limit)
async def promo_admin_edit_user_limit(
    message: Message,
    state: FSMContext,
):
    if await _cancel_edit_if_requested(message, state):
        return

    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ Faqat butun son kiriting.")
        return

    if value <= 0:
        await message.answer(
            "❌ Foydalanuvchi limiti 0 dan katta bo‘lishi kerak."
        )
        return

    await _save_edit(
        message=message,
        state=state,
        field="per_user_limit",
        value=value,
    )


@router.message(PromoAdminStates.waiting_for_edit_start)
async def promo_admin_edit_start(
    message: Message,
    state: FSMContext,
):
    if await _cancel_edit_if_requested(message, state):
        return

    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = _parse_date(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    await _save_edit(
        message=message,
        state=state,
        field="start_date",
        value=value,
    )


@router.message(PromoAdminStates.waiting_for_edit_end)
async def promo_admin_edit_end(
    message: Message,
    state: FSMContext,
):
    if await _cancel_edit_if_requested(message, state):
        return

    admin = await _get_admin(message.from_user.id)

    if admin is None:
        await state.clear()
        return

    try:
        value = _parse_date(message.text or "")
    except ValueError as exc:
        await message.answer(f"❌ {exc}")
        return

    data = await state.get_data()
    promo_id = data.get("promo_id")

    if promo_id is None:
        await state.clear()
        await message.answer(
            "❌ Promo ID topilmadi.",
            reply_markup=admin_menu,
        )
        return

    async with async_session() as session:
        repository = PromoRepository(session)
        promo = await repository.get_by_id(int(promo_id))

        if promo is None:
            await state.clear()
            await message.answer(
                "❌ Promo kod topilmadi.",
                reply_markup=promo_admin_menu(),
            )
            return

        if (
            promo.start_date is not None
            and value is not None
            and value <= promo.start_date
        ):
            await message.answer(
                "❌ Tugash sanasi boshlanish sanasidan keyin bo‘lishi kerak."
            )
            return

        promo.end_date = value
        await repository.update(promo)
        await session.commit()

    await state.clear()

    await message.answer(
        "✅ Tugash sanasi yangilandi.",
        reply_markup=promo_admin_menu(),
    )


async def _save_edit(
    message: Message,
    state: FSMContext,
    field: str,
    value,
):
    data = await state.get_data()
    promo_id = data.get("promo_id")

    if promo_id is None:
        await state.clear()
        await message.answer(
            "❌ Promo ID topilmadi.",
            reply_markup=admin_menu,
        )
        return

    async with async_session() as session:
        repository = PromoRepository(session)
        promo = await repository.get_by_id(int(promo_id))

        if promo is None:
            await state.clear()
            await message.answer(
                "❌ Promo kod topilmadi.",
                reply_markup=promo_admin_menu(),
            )
            return

        if field == "start_date":
            if (
                promo.end_date is not None
                and value is not None
                and value >= promo.end_date
            ):
                await message.answer(
                    "❌ Boshlanish sanasi tugash sanasidan oldin bo‘lishi kerak."
                )
                return

        if field == "duration_days" and value <= 0:
            await message.answer(
                "❌ Bonus kunlari 0 dan katta bo‘lishi kerak."
            )
            return

        setattr(promo, field, value)
        await repository.update(promo)
        await session.commit()

    await state.clear()

    await message.answer(
        "✅ Promo ma’lumoti yangilandi.",
        reply_markup=promo_admin_menu(),
    )


@router.callback_query(F.data.startswith("promo_admin:stats:"))
async def promo_admin_stats(callback: CallbackQuery):
    admin = await _get_admin(callback.from_user.id)

    if admin is None:
        await callback.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        promo_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Promo ID noto‘g‘ri.", show_alert=True)
        return

    async with async_session() as session:
        repository = PromoRepository(session)
        promo = await repository.get_by_id(promo_id)

        if promo is None:
            await callback.answer("Promo kod topilmadi.", show_alert=True)
            return

        total = await repository.count_redemptions(promo_id)

    remaining = (
        "∞"
        if promo.total_redemption_limit is None
        else max(promo.total_redemption_limit - total, 0)
    )

    await callback.answer()

    await callback.message.edit_text(
        "📊 <b>PROMO STATISTIKASI</b>\n\n"
        f"🔑 Kod: <code>{promo.code}</code>\n"
        f"🎁 Bonus: <b>{promo.duration_days} kun</b>\n"
        f"📈 Jami foydalanish: <b>{total}</b>\n"
        f"📉 Qolgan limit: <b>{remaining}</b>\n"
        f"👤 Bir foydalanuvchi limiti: <b>{promo.per_user_limit}</b>",
        parse_mode="HTML",
        reply_markup=promo_detail_keyboard(
            promo_id=promo.id,
            is_active=promo.is_active,
        ),
    )
