from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards.menu import main_menu


router = Router()


async def _show_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Close the current inline section message and return to the
    real main menu (ReplyKeyboardMarkup).

    IMPORTANT:
    ReplyKeyboardMarkup cannot be passed to edit_text().
    Therefore the current section message is deleted first,
    then a new main-menu message is sent.
    """
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        # The message may already be deleted or otherwise unavailable.
        pass

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="🏠 <b>ASOSIY MENYU</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


@router.callback_query(F.data == "user_main_menu")
async def user_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await _show_main_menu(callback, state)


@router.callback_query(F.data == "user_close")
async def user_close(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await _show_main_menu(callback, state)


@router.callback_query(F.data == "user_back")
async def user_back(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await _show_main_menu(callback, state)
