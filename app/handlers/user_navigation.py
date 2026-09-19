from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.menu import main_menu


router = Router()


@router.callback_query(F.data == "user_close")
async def user_close(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏠 <b>ASOSIY MENYU</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


@router.callback_query(F.data == "user_back")
async def user_back(callback: CallbackQuery):
    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏠 <b>ASOSIY MENYU</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )
