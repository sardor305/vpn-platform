from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.admin import admin_menu
from app.keyboards.plan_admin import (
    admin_plan_detail_keyboard,
    admin_plans_keyboard,
)
from app.services.plan_service import PlanService
from app.services.user_service import UserService
from app.states.plan import PlanStates


router = Router()


async def get_admin_user(
    message_or_callback,
):
    telegram_id = message_or_callback.from_user.id

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=telegram_id
        )

    if user is None or not user.is_admin:
        return None

    return user


@router.message(F.text == "📦 Tariflar")
async def admin_plans(
    message: Message,
):
    admin = await get_admin_user(message)

    if admin is None:
        return

    async with async_session() as session:

        plan_service = PlanService(session)

        plans = await plan_service.get_all_plans()

    if not plans:

        await message.answer(
            "📦 <b>Tariflar</b>\n\n"
            "Hozircha tariflar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    await message.answer(
        "📦 <b>Tariflar</b>\n\n"
        "Kerakli tarifni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_plans_keyboard(plans),
    )


@router.callback_query(
    F.data.startswith("admin_plan:")
)
async def admin_plan_view(
    callback: CallbackQuery,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    plan_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

    if plan is None:

        await callback.answer(
            "Tarif topilmadi.",
            show_alert=True,
        )

        return

    status = (
        "🟢 Faol"
        if plan.is_active
        else "🔴 Faol emas"
    )

    text = (
        f"📦 <b>{escape(plan.name)}</b>\n\n"
        f"💰 Narx: <b>{plan.price} ₽</b>\n"
        f"⏱ Muddat: <b>{plan.duration_days} kun</b>\n"
        f"📊 Holat: <b>{status}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_plan_detail_keyboard(
            plan
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data == "admin_plan_list"
)
async def admin_plan_list(
    callback: CallbackQuery,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    async with async_session() as session:

        plan_service = PlanService(session)

        plans = await plan_service.get_all_plans()

    if not plans:

        await callback.message.edit_text(
            "📦 <b>Tariflar</b>\n\n"
            "Hozircha tariflar mavjud emas.",
            parse_mode="HTML",
        )

        await callback.answer()

        return

    await callback.message.edit_text(
        "📦 <b>Tariflar</b>\n\n"
        "Kerakli tarifni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_plans_keyboard(
            plans
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data == "admin_plan_create"
)
async def admin_plan_create(
    callback: CallbackQuery,
    state: FSMContext,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    await state.set_state(
        PlanStates.waiting_for_name
    )

    await callback.message.answer(
        "➕ <b>Yangi tarif</b>\n\n"
        "1️⃣ Tarif nomini kiriting.\n\n"
        "Masalan:\n"
        "<code>Standard</code>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(
    PlanStates.waiting_for_name,
    F.text,
)
async def admin_plan_name(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    if not name:
        await message.answer(
            "❌ Tarif nomi bo'sh bo'lishi mumkin emas.\n\n"
            "Qaytadan kiriting:"
        )
        return

    async with async_session() as session:

        plan_service = PlanService(session)

        existing_plan = (
            await plan_service.plan_repository.get_by_name(
                name
            )
        )

    if existing_plan is not None:
        await message.answer(
            "❌ Bunday nomdagi tarif allaqachon mavjud.\n\n"
            "Boshqa nom kiriting:"
        )
        return

    await state.update_data(
        plan_name=name
    )

    await state.set_state(
        PlanStates.waiting_for_price
    )

    await message.answer(
        f"📦 Tarif: <b>{escape(name)}</b>\n\n"
        "2️⃣ Tarif narxini kiriting.\n\n"
        "Faqat butun son kiriting.\n"
        "Masalan: <code>300</code>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(
    PlanStates.waiting_for_price,
    F.text,
)
async def admin_plan_price(
    message: Message,
    state: FSMContext,
):
    price_text = message.text.strip()

    try:
        price = int(price_text)

    except ValueError:

        await message.answer(
            "❌ Narx faqat butun son bo'lishi kerak.\n\n"
            "Masalan: <code>300</code>\n\n"
            "Qaytadan kiriting:",
            parse_mode="HTML",
        )

        return

    if price <= 0:

        await message.answer(
            "❌ Narx 0 dan katta bo'lishi kerak.\n\n"
            "Qaytadan kiriting:"
        )

        return

    await state.update_data(
        plan_price=price
    )

    await state.set_state(
        PlanStates.waiting_for_duration
    )

    await message.answer(
        "3️⃣ Tarif amal qilish muddatini kiriting.\n\n"
        "Kunlarda, faqat butun son.\n"
        "Masalan: <code>30</code>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(
    PlanStates.waiting_for_duration,
    F.text,
)
async def admin_plan_duration(
    message: Message,
    state: FSMContext,
):
    duration_text = message.text.strip()

    try:
        duration_days = int(duration_text)

    except ValueError:

        await message.answer(
            "❌ Muddat faqat butun son bo'lishi kerak.\n\n"
            "Masalan: <code>30</code>\n\n"
            "Qaytadan kiriting:",
            parse_mode="HTML",
        )

        return

    if duration_days <= 0:

        await message.answer(
            "❌ Muddat 0 kundan katta bo'lishi kerak.\n\n"
            "Qaytadan kiriting:"
        )

        return

    data = await state.get_data()

    plan_name = data.get("plan_name")
    plan_price = data.get("plan_price")

    if not plan_name or plan_price is None:

        await state.clear()

        await message.answer(
            "❌ Tarif ma'lumotlari yo'qolgan.\n\n"
            "Jarayon bekor qilindi."
        )

        return

    async with async_session() as session:

        plan_service = PlanService(session)

        existing_plan = (
            await plan_service.plan_repository.get_by_name(
                plan_name
            )
        )

        if existing_plan is not None:

            await state.clear()

            await message.answer(
                "❌ Bunday nomdagi tarif allaqachon mavjud."
            )

            return

        plan = await plan_service.create_plan(
            name=plan_name,
            price=plan_price,
            duration_days=duration_days,
        )

        await session.commit()

    await state.clear()

    await message.answer(
        "✅ <b>Tarif muvaffaqiyatli yaratildi!</b>\n\n"
        f"📦 Nomi: <b>{escape(plan.name)}</b>\n"
        f"💰 Narxi: <b>{plan.price} ₽</b>\n"
        f"⏱ Muddat: <b>{plan.duration_days} kun</b>\n"
        "📊 Holat: <b>🟢 Faol</b>",
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.startswith("admin_plan_edit:")
)
async def admin_plan_edit(
    callback: CallbackQuery,
    state: FSMContext,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    plan_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

    if plan is None:
        await callback.answer(
            "Tarif topilmadi.",
            show_alert=True,
        )
        return

    await state.update_data(
        edit_plan_id=plan.id
    )

    await state.set_state(
        PlanStates.waiting_for_edit_name
    )

    await callback.message.answer(
        f"✏️ <b>Tarifni tahrirlash</b>\n\n"
        f"📦 Hozirgi nomi: "
        f"<b>{escape(plan.name)}</b>\n\n"
        "Yangi nomni kiriting.\n\n"
        "Agar nomni o'zgartirmoqchi bo'lmasangiz, "
        "hozirgi nomini qayta kiriting.\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(
    PlanStates.waiting_for_edit_name,
    F.text,
)
async def admin_plan_edit_name(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    if not name:
        await message.answer(
            "❌ Tarif nomi bo'sh bo'lishi mumkin emas.\n\n"
            "Qaytadan kiriting:"
        )
        return

    data = await state.get_data()

    plan_id = data.get("edit_plan_id")

    if plan_id is None:
        await state.clear()

        await message.answer(
            "❌ Tarif ma'lumotlari topilmadi."
        )

        return

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

        if plan is None:
            await state.clear()

            await message.answer(
                "❌ Tarif topilmadi."
            )

            return

        existing_plan = (
            await plan_service.plan_repository.get_by_name(
                name
            )
        )

        if (
            existing_plan is not None
            and existing_plan.id != plan.id
        ):
            await message.answer(
                "❌ Bunday nomdagi tarif allaqachon mavjud.\n\n"
                "Boshqa nom kiriting:"
            )
            return

    await state.update_data(
        edit_plan_name=name
    )

    await state.set_state(
        PlanStates.waiting_for_edit_price
    )

    await message.answer(
        f"📦 Yangi nom: <b>{escape(name)}</b>\n\n"
        "💰 Yangi narxni kiriting.\n\n"
        "Masalan: <code>300</code>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(
    PlanStates.waiting_for_edit_price,
    F.text,
)
async def admin_plan_edit_price(
    message: Message,
    state: FSMContext,
):
    price_text = message.text.strip()

    try:
        price = int(price_text)

    except ValueError:

        await message.answer(
            "❌ Narx faqat butun son bo'lishi kerak.\n\n"
            "Masalan: <code>300</code>\n\n"
            "Qaytadan kiriting:",
            parse_mode="HTML",
        )

        return

    if price <= 0:

        await message.answer(
            "❌ Narx 0 dan katta bo'lishi kerak.\n\n"
            "Qaytadan kiriting:"
        )

        return

    await state.update_data(
        edit_plan_price=price
    )

    await state.set_state(
        PlanStates.waiting_for_edit_duration
    )

    await message.answer(
        "⏱ Yangi muddatni kiriting.\n\n"
        "Kunlarda, faqat butun son.\n"
        "Masalan: <code>30</code>\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(
    PlanStates.waiting_for_edit_duration,
    F.text,
)
async def admin_plan_edit_duration(
    message: Message,
    state: FSMContext,
):
    duration_text = message.text.strip()

    try:
        duration_days = int(duration_text)

    except ValueError:

        await message.answer(
            "❌ Muddat faqat butun son bo'lishi kerak.\n\n"
            "Masalan: <code>30</code>\n\n"
            "Qaytadan kiriting:",
            parse_mode="HTML",
        )

        return

    if duration_days <= 0:

        await message.answer(
            "❌ Muddat 0 kundan katta bo'lishi kerak.\n\n"
            "Qaytadan kiriting:"
        )

        return

    data = await state.get_data()

    plan_id = data.get("edit_plan_id")
    plan_name = data.get("edit_plan_name")
    plan_price = data.get("edit_plan_price")

    if (
        plan_id is None
        or not plan_name
        or plan_price is None
    ):
        await state.clear()

        await message.answer(
            "❌ Tarif ma'lumotlari topilmadi."
        )

        return

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

        if plan is None:
            await state.clear()

            await message.answer(
                "❌ Tarif topilmadi."
            )

            return

        existing_plan = (
            await plan_service.plan_repository.get_by_name(
                plan_name
            )
        )

        if (
            existing_plan is not None
            and existing_plan.id != plan.id
        ):
            await state.clear()

            await message.answer(
                "❌ Bunday nomdagi tarif allaqachon mavjud."
            )

            return

        plan.name = plan_name
        plan.price = plan_price
        plan.duration_days = duration_days

        await plan_service.update_plan(
            plan
        )

        await session.commit()

    await state.clear()

    status = (
        "🟢 Faol"
        if plan.is_active
        else "🔴 Faol emas"
    )

    await message.answer(
        "✅ <b>Tarif muvaffaqiyatli yangilandi!</b>\n\n"
        f"📦 Nomi: <b>{escape(plan.name)}</b>\n"
        f"💰 Narxi: <b>{plan.price} ₽</b>\n"
        f"⏱ Muddat: <b>{plan.duration_days} kun</b>\n"
        f"📊 Holat: <b>{status}</b>",
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.startswith("admin_plan_deactivate:")
)
async def admin_plan_deactivate(
    callback: CallbackQuery,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    plan_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

        if plan is None:
            await callback.answer(
                "Tarif topilmadi.",
                show_alert=True,
            )
            return

        plan.is_active = False

        await plan_service.update_plan(
            plan
        )

        await session.commit()

    await callback.answer(
        "Tarif deaktivatsiya qilindi."
    )

    status = "🔴 Faol emas"

    text = (
        f"📦 <b>{escape(plan.name)}</b>\n\n"
        f"💰 Narx: <b>{plan.price} ₽</b>\n"
        f"⏱ Muddat: <b>{plan.duration_days} kun</b>\n"
        f"📊 Holat: <b>{status}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_plan_detail_keyboard(
            plan
        ),
    )


@router.callback_query(
    F.data.startswith("admin_plan_activate:")
)
async def admin_plan_activate(
    callback: CallbackQuery,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    plan_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        plan_service = PlanService(session)

        plan = await plan_service.get_plan(
            plan_id
        )

        if plan is None:
            await callback.answer(
                "Tarif topilmadi.",
                show_alert=True,
            )
            return

        plan.is_active = True

        await plan_service.update_plan(
            plan
        )

        await session.commit()

    await callback.answer(
        "Tarif aktivlashtirildi."
    )

    status = "🟢 Faol"

    text = (
        f"📦 <b>{escape(plan.name)}</b>\n\n"
        f"💰 Narx: <b>{plan.price} ₽</b>\n"
        f"⏱ Muddat: <b>{plan.duration_days} kun</b>\n"
        f"📊 Holat: <b>{status}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_plan_detail_keyboard(
            plan
        ),
    )


@router.callback_query(
    F.data == "admin_plan_back"
)
async def admin_plan_back(
    callback: CallbackQuery,
):
    admin = await get_admin_user(callback)

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )

    await callback.answer()


@router.message(F.text == "/cancel")
async def cancel_plan_action(
    message: Message,
    state: FSMContext,
):
    current_state = await state.get_state()

    plan_states = (
        PlanStates.waiting_for_name.state,
        PlanStates.waiting_for_price.state,
        PlanStates.waiting_for_duration.state,
        PlanStates.waiting_for_edit_name.state,
        PlanStates.waiting_for_edit_price.state,
        PlanStates.waiting_for_edit_duration.state,
    )

    if current_state not in plan_states:
        return

    await state.clear()

    await message.answer(
        "❌ Tarif bilan ishlash bekor qilindi.",
        reply_markup=admin_menu,
    )