from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.admin import admin_menu, users_menu
from app.keyboards.menu import main_menu
from app.services.statistics_service import StatisticsService
from app.services.user_service import UserService


router = Router()


@router.message(F.text == "admin")
async def admin_panel(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

    if user is None:
        return

    if not user.is_admin:
        return

    await message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
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
        f"└ Muddati tugagan: <b>{stats.expired_subscriptions}</b>\n\n"

        "🔑 <b>VPN HISOBLAR</b>\n"
        f"├ Jami: <b>{stats.total_vpn_accounts}</b>\n"
        f"├ Faol: <b>{stats.active_vpn_accounts}</b>\n"
        f"└ VLESS: <b>{stats.vless_accounts}</b>\n\n"

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
            f"@{user.username}"
            if user.username
            else "—"
        )

        status = (
            "🟢 Faol"
            if user.is_active
            else "🔴 Faol emas"
        )

        full_name = user.first_name

        if user.last_name:
            full_name += f" {user.last_name}"

        text += (
            f"👤 <b>#{user.id}</b>\n"
            f"Ism: {full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: <code>{user.telegram_id}</code>\n"
            f"Status: {status}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=users_menu,
    )


@router.message(F.text == "⬅️ Admin panel")
async def back_to_admin_panel(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
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