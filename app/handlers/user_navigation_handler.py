from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards.menu import main_menu


router = Router()


async def _show_main_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🏠 <b>ASOSIY MENYU</b>",
            parse_mode="HTML",
            reply_markup=main_menu,
        )
    except Exception:
        await callback.message.answer(
            "🏠 <b>ASOSIY MENYU</b>",
            parse_mode="HTML",
            reply_markup=main_menu,
        )


@router.callback_query(F.data == "user_main_menu")
async def user_main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await _show_main_menu(callback)


@router.callback_query(F.data == "user_close")
async def user_close(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await _show_main_menu(callback)


@router.callback_query(F.data == "user_back")
async def user_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await _show_main_menu(callback)
