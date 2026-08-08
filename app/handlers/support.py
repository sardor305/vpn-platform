from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.help import help_keyboard
from app.models.user import User
from app.services.support_ticket_service import SupportTicketService
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

        ticket = await support_service.create_ticket(
            user_id=user.id,
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
        reply_markup=help_keyboard(
            has_phone=bool(user.phone_number)
        ),
    )


@router.message(F.text == "/cancel")
async def cancel_support(
    message: Message,
    state: FSMContext,
):

    current_state = await state.get_state()

    if current_state != SupportStates.waiting_for_message.state:
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
        "❌ Murojaat yuborish bekor qilindi.",
        reply_markup=help_keyboard(
            has_phone=bool(user.phone_number)
        ),
    )