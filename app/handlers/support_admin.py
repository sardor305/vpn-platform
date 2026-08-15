from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.admin import admin_menu
from app.keyboards.support_admin import (
    ticket_keyboard,
    ticket_list_keyboard,
)
from app.keyboards.support_user import (
    user_ticket_reply_keyboard,
)

from app.services.support_message_service import (
    SupportMessageService,
)
from app.services.support_ticket_service import (
    SupportTicketService,
)
from app.services.user_service import UserService
from app.states.support import SupportStates


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
        f"Jami faol murojaatlar: "
        f"<b>{len(tickets)}</b>\n\n"
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

        message_service = SupportMessageService(
            session
        )

        messages = (
            await message_service.get_by_ticket_id(
                ticket_id=ticket.id
            )
        )

    username = (
        f"@{escape(user.username)}"
        if user.username
        else "—"
    )

    full_name = escape(user.first_name)

    if user.last_name:
        full_name += f" {escape(user.last_name)}"

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
        f"💬 <b>Yozishmalar:</b>\n\n"
    )

    if not messages:
        text += "Hozircha xabarlar mavjud emas.\n"

    else:
        for support_message in messages:

            if support_message.sender_type == "user":
                sender = "👤 Foydalanuvchi"
            else:
                sender = "👨‍💼 Admin"

            text += (
                f"<b>{sender}:</b>\n"
                f"{escape(support_message.message)}\n\n"
            )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=ticket_keyboard(
            ticket.id
        ),
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("ticket_reply:")
)
async def start_ticket_reply(
    callback: CallbackQuery,
    state: FSMContext,
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

    if ticket.status in (
        "closed",
        "deleted",
    ):
        await callback.answer(
            "Bu murojaat yopilgan.",
            show_alert=True,
        )
        return

    await state.set_state(
        SupportStates.waiting_for_admin_reply
    )

    await state.update_data(
        ticket_id=ticket_id
    )

    await callback.message.answer(
        f"✍️ <b>Murojaat #{ticket_id}</b> uchun "
        "javobingizni yozing.\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(
    SupportStates.waiting_for_admin_reply,
    F.text,
)
async def receive_admin_reply(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    ticket_id = data.get("ticket_id")

    if ticket_id is None:
        await state.clear()

        await message.answer(
            "❌ Murojaat ma'lumotlari topilmadi."
        )

        return

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            await state.clear()
            return

        support_service = SupportTicketService(
            session
        )

        ticket = await support_service.get_by_id(
            ticket_id=ticket_id
        )

        if ticket is None:
            await state.clear()

            await message.answer(
                "❌ Murojaat topilmadi."
            )

            return

        if ticket.status in (
            "closed",
            "deleted",
        ):
            await state.clear()

            await message.answer(
                "❌ Bu murojaat yopilgan."
            )

            return

        message_service = SupportMessageService(
            session
        )

        await message_service.create_message(
            ticket_id=ticket.id,
            sender_id=admin.id,
            sender_type="admin",
            message=message.text,
        )

        # Birinchi admin javobida ticket open bo'ladi.
        # Keyingi javoblarda ham aynan shu admin
        # biriktirilgan holda qoladi.
        await support_service.assign_admin(
            ticket_id=ticket.id,
            admin_id=admin.id,
        )

        user = await user_service.get_by_id(
            user_id=ticket.user_id
        )

        await session.commit()

    await state.clear()

    if user is None:
        await message.answer(
            "⚠️ Javob saqlandi, "
            "lekin foydalanuvchi topilmadi."
        )
        return

    try:
        await message.bot.send_message(
            chat_id=user.telegram_id,
            text=(
                f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
                "👨‍💼 <b>Admin javobi:</b>\n"
                f"{escape(message.text)}"
            ),
            parse_mode="HTML",
            reply_markup=user_ticket_reply_keyboard(
                ticket.id
            ),
        )

        await message.answer(
            f"✅ <b>Murojaat #{ticket.id}</b> ga "
            "javob yuborildi.",
            parse_mode="HTML",
        )

    except Exception:
        await message.answer(
            "⚠️ Javob database'ga saqlandi, "
            "ammo foydalanuvchiga Telegram orqali "
            "yuborishda xatolik yuz berdi."
        )


@router.callback_query(
    F.data.startswith("ticket_close:")
)
async def close_ticket(
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

        ticket = await support_service.close_ticket(
            ticket_id=ticket_id
        )

        if ticket is None:
            await callback.answer(
                "Murojaat topilmadi.",
                show_alert=True,
            )
            return

        await session.commit()

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=ticket.user_id
        )

    if user is not None:

        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
                    "✅ Murojaatingiz "
                    "qo‘llab-quvvatlash xizmati tomonidan "
                    "yechilgan deb belgilandi."
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

    await callback.message.answer(
        f"✅ Murojaat #{ticket.id} yopildi.",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("ticket_delete:")
)
async def delete_ticket(
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

        ticket = await support_service.delete_ticket(
            ticket_id=ticket_id
        )

        if ticket is None:
            await callback.answer(
                "Murojaat topilmadi.",
                show_alert=True,
            )
            return

        await session.commit()

        user_service = UserService(session)

        user = await user_service.get_by_id(
            user_id=ticket.user_id
        )

    if user is not None:

        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
                    "🗑 Murojaatingiz o‘chirildi."
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

    await callback.message.answer(
        f"🗑 Murojaat #{ticket.id} o‘chirildi.",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )

    await callback.answer()


@router.message(F.text == "/cancel")
async def cancel_admin_reply(
    message: Message,
    state: FSMContext,
):
    current_state = await state.get_state()

    if (
        current_state
        != SupportStates.waiting_for_admin_reply.state
    ):
        return

    await state.clear()

    await message.answer(
        "❌ Murojaatga javob berish bekor qilindi.",
        reply_markup=admin_menu,
    )
