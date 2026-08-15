from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.help import help_keyboard
from app.keyboards.support_admin import (
    ticket_keyboard,
)
from app.keyboards.support_user import (
    user_ticket_keyboard,
    user_ticket_reply_keyboard,
    user_ticket_new_keyboard,
    user_tickets_list_keyboard,
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


@router.message(F.text == "💬 Qo'llab-quvvatlash")
async def start_support(
    message: Message,
    state: FSMContext,
):
    await state.set_state(
        SupportStates.waiting_for_message
    )

    await message.answer(
        "✍️ <b>Murojaatingizni yozing</b>\n\n"
        "Muammoingiz yoki savolingizni "
        "bitta xabar ko'rinishida yuboring.\n\n"
        "Masalan:\n"
        "VPN ulanishida muammo yuzaga keldi.\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )


@router.message(
    SupportStates.waiting_for_message,
    F.text,
)
async def receive_support_message(
    message: Message,
    state: FSMContext,
):
    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if user is None:
            await state.clear()
            return

        support_service = SupportTicketService(
            session
        )

        # Har bir yangi murojaat uchun
        # alohida ticket yaratiladi.
        ticket = await support_service.create_ticket(
            user_id=user.id,
            message=message.text,
        )

        # Birinchi xabarni ham support_messages
        # jadvaliga yozamiz.
        message_service = SupportMessageService(
            session
        )

        await message_service.create_message(
            ticket_id=ticket.id,
            sender_id=user.id,
            sender_type="user",
            message=message.text,
        )

        await session.commit()

    await state.clear()

    await message.answer(
        f"✅ <b>Murojaatingiz qabul qilindi!</b>\n\n"
        f"📩 Murojaat raqami: <b>#{ticket.id}</b>\n\n"
        "Murojaatingiz qo'llab-quvvatlash xizmatiga "
        "yuborildi.\n"
        "Javob berilganda sizga bot orqali xabar beramiz.",
        parse_mode="HTML",
        reply_markup=user_ticket_keyboard(
            ticket.id
        ),
    )


@router.message(F.text == "📂 Murojaatlarim")
async def my_tickets(
    message: Message,
):
    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if user is None:
            return

        support_service = SupportTicketService(
            session
        )

        tickets = await support_service.get_user_tickets(
            user_id=user.id
        )

    if not tickets:
        await message.answer(
            "📂 <b>Murojaatlarim</b>\n\n"
            "Sizda hozircha murojaatlar mavjud emas.",
            parse_mode="HTML",
        )
        return

    await message.answer(
        "📂 <b>Murojaatlarim</b>\n\n"
        "Kerakli murojaatni tanlang:",
        parse_mode="HTML",
        reply_markup=user_tickets_list_keyboard(
            [ticket.id for ticket in tickets]
        ),
    )


@router.callback_query(
    F.data.startswith("user_ticket_view:")
)
async def view_user_ticket(
    callback: CallbackQuery,
):
    ticket_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

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

        # Faqat ticket egasi ko'ra oladi.
        if ticket.user_id != user.id:
            await callback.answer(
                "Bu murojaat sizga tegishli emas.",
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

    status_text = {
        "new": "🟡 Yangi",
        "open": "🔵 Jarayonda",
        "closed": "🟢 Yechilgan",
        "deleted": "🗑 O‘chirilgan",
    }.get(
        ticket.status,
        ticket.status,
    )

    text = (
        f"📩 <b>Murojaat #{ticket.id}</b>\n"
        f"📊 Holat: {status_text}\n\n"
    )

    if not messages:
        text += "Hozircha xabarlar mavjud emas.\n"
    else:
        for support_message in messages:

            if support_message.sender_type == "user":
                sender = "👤 Siz"
            else:
                sender = "👨‍💼 Admin"

            text += (
                f"<b>{sender}:</b>\n"
                f"{escape(support_message.message)}\n\n"
            )

    # NEW yoki OPEN bo'lsa — shu ticket davom ettiriladi.
    if ticket.status in ("new", "open"):

        reply_markup = user_ticket_reply_keyboard(
            ticket.id
        )

    # CLOSED bo'lsa — eski ticket davom ettirilmaydi.
    # Yangi murojaat ochish tugmasi chiqadi.
    elif ticket.status == "closed":

        reply_markup = user_ticket_new_keyboard()

    else:
        reply_markup = None

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("user_ticket_reply:")
)
async def start_user_ticket_reply(
    callback: CallbackQuery,
    state: FSMContext,
):
    ticket_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if user is None:
            await callback.answer(
                "Foydalanuvchi topilmadi.",
                show_alert=True,
            )
            return

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

        if ticket.user_id != user.id:
            await callback.answer(
                "Bu murojaat sizga tegishli emas.",
                show_alert=True,
            )
            return

        if ticket.status not in ("new", "open"):
            await callback.answer(
                "Bu murojaat yopilgan. "
                "Yangi murojaat oching.",
                show_alert=True,
            )
            return

    await state.set_state(
        SupportStates.waiting_for_user_reply
    )

    await state.update_data(
        ticket_id=ticket_id
    )

    await callback.message.answer(
        f"✍️ <b>Murojaat #{ticket_id}</b>\n\n"
        "Javobingizni yozing.\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )

    await callback.answer()


@router.callback_query(
    F.data == "user_ticket_new"
)
async def start_new_ticket(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.set_state(
        SupportStates.waiting_for_message
    )

    await callback.message.answer(
        "✍️ <b>Yangi murojaat</b>\n\n"
        "Muammoingiz yoki savolingizni yozing.\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(
    SupportStates.waiting_for_user_reply,
    F.text,
)
async def receive_user_reply(
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

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if user is None:
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

        if ticket.user_id != user.id:
            await state.clear()

            await message.answer(
                "❌ Bu murojaat sizga tegishli emas."
            )

            return

        # Faqat NEW yoki OPEN ticket davom ettiriladi.
        if ticket.status not in ("new", "open"):
            await state.clear()

            await message.answer(
                "❌ Bu murojaat yopilgan.\n\n"
                "Yangi murojaat ochish uchun "
                "💬 Qo'llab-quvvatlash tugmasidan foydalaning."
            )

            return

        message_service = SupportMessageService(
            session
        )

        await message_service.create_message(
            ticket_id=ticket.id,
            sender_id=user.id,
            sender_type="user",
            message=message.text,
        )

        admin = None

        if ticket.admin_id is not None:
            admin = await user_service.get_by_id(
                user_id=ticket.admin_id
            )

        await session.commit()

    await state.clear()

    if admin is not None:

        try:
            await message.bot.send_message(
                chat_id=admin.telegram_id,
                text=(
                    f"📩 <b>Murojaat #{ticket.id}</b>\n\n"
                    "👤 <b>Foydalanuvchi javobi:</b>\n"
                    f"{escape(message.text)}"
                ),
                parse_mode="HTML",
                reply_markup=ticket_keyboard(
                    ticket.id
                ),
            )

        except Exception:
            await message.answer(
                "⚠️ Xabaringiz saqlandi, "
                "ammo adminingizga yuborishda "
                "xatolik yuz berdi."
            )

            return

    await message.answer(
        f"✅ <b>Murojaat #{ticket.id}</b> "
        "ga javobingiz yuborildi.",
        parse_mode="HTML",
        reply_markup=user_ticket_reply_keyboard(
            ticket.id
        ),
    )


@router.message(F.text == "/cancel")
async def cancel_support(
    message: Message,
    state: FSMContext,
):
    current_state = await state.get_state()

    if current_state not in (
        SupportStates.waiting_for_message.state,
        SupportStates.waiting_for_user_reply.state,
    ):
        return

    await state.clear()

    async with async_session() as session:

        user_service = UserService(session)

        user = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

    if user is None:
        return

    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=help_keyboard(
            has_phone=bool(user.phone_number)
        ),
    )
