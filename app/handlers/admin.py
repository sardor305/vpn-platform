from aiogram import F, Router
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.admin import admin_menu
from app.services.user_service import UserService


router = Router()


@router.message(F.text.casefold() == "admin")
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