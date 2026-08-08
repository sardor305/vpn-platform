from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.admin import admin_menu
from app.keyboards.support_admin import (
    ticket_keyboard,
    ticket_list_keyboard,
)
from app.services.support_ticket_service import SupportTicketService
from app.services.user_service import UserService


router = Router()


async def get_admin(
    telegram_id: int,
):
    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=telegram_id
        )

    if user is None or not user.is_admin:
        return None

    return user


@router.message(F.text == "📩 Murojaatlar")
async def support_tickets_list(
    message: Message,
):

    admin = await get_admin(
        telegram_id=message.from_user.id
    )

    if admin is None:
        return

    async with async_session() as session:

        support_service = SupportTicketService(
            session
        )

        tickets = await support_service.get_active_tickets()

    if not tickets:

        await message.answer(
            "📩 <b>Murojaatlar</b>\n\n"
            "Hozircha murojaatlar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    await message.answer(
        "📩 <b>Murojaatlar</b>\n\n"
        f"Jami faol murojaatlar: <b>{len(tickets)}</b>\n\n"
        "Kerakli murojaatni tanlang:",
        parse_mode="HTML",
    )

    for ticket in tickets:

        status = {
            "new": "🟡 Yangi",
            "open": "🔵 Jarayonda",
            "closed": "🟢 Yechilgan",
        }.get(
            ticket.status,
            ticket.status,
        )

        await message.answer(
            f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
            f"Status: {status}",
            parse_mode="HTML",
            reply_markup=ticket_list_keyboard(
                ticket.id
            ),
        )


@router.callback_query(
    F.data.startswith("ticket_view:")
)
async def view_ticket(
    callback: CallbackQuery,
):

    admin = await get_admin(
        telegram_id=callback.from_user.id
    )

    if admin is None:
        await callback.answer(
            "Ruxsat berilmagan.",
            show_alert=True,
        )
        return

    ticket_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        support_service = SupportTicketService(
            session
        )

        ticket = await support_service.get_by_id(
            ticket_id=ticket_id
        )

        if ticket is None:
            await callback.answer(
                "Murojaat topilmadi.",
                show_alert=True,
            )
            return

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=ticket.user_id
        )

    if user is None:
        await callback.answer(
            "Foydalanuvchi topilmadi.",
            show_alert=True,
        )
        return

    username = (
        f"@{user.username}"
        if user.username
        else "—"
    )

    full_name = user.first_name

    if user.last_name:
        full_name += f" {user.last_name}"

    status = {
        "new": "🟡 Yangi",
        "open": "🔵 Jarayonda",
        "closed": "🟢 Yechilgan",
        "deleted": "🗑 O‘chirilgan",
    }.get(
        ticket.status,
        ticket.status,
    )

    text = (
        f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
        f"👤 Ism: {full_name}\n"
        f"Username: {username}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"📊 Status: {status}\n\n"
        f"💬 <b>Murojaat:</b>\n"
        f"{ticket.message}"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=ticket_keyboard(
            ticket.id
        ),
    )

    await callback.answer()