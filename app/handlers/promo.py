from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.user_navigation import user_navigation_keyboard
from app.services.promo_service import PromoService
from app.services.user_service import UserService


router = Router()


class PromoStates(StatesGroup):
    waiting_for_code = State()


@router.message(F.text == "🎟 Promo kod")
async def promo_start(message: Message, state: FSMContext):
    await state.set_state(PromoStates.waiting_for_code)
    await message.answer(
        "🎟 <b>PROMO KOD</b>\n\n"
        "Promo kodingizni yuboring.\n\n"
        "Masalan: <code>WELCOME2026</code>",
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="promo_back",
        ),
    )


@router.callback_query(F.data == "promo_back")
async def promo_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

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


@router.message(PromoStates.waiting_for_code)
async def promo_redeem(message: Message, state: FSMContext):
    code = (message.text or "").strip()

    if not code:
        await message.answer(
            "❌ Promo kodi bo‘sh bo‘lishi mumkin emas.\n"
            "Promo kodingizni yuboring."
        )
        return

    if code.casefold() in {"bekor qilish", "cancel", "/cancel"}:
        await state.clear()
        await message.answer(
            "❌ Promo kod kiritish bekor qilindi.",
            reply_markup=main_menu,
        )
        return

    async with async_session() as session:
        try:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(
                telegram_id=message.from_user.id
            )

            if user is None:
                await session.rollback()
                await state.clear()
                await message.answer(
                    "❌ Foydalanuvchi topilmadi. Avval /start buyrug‘ini yuboring."
                )
                return

            promo_service = PromoService(session)
            result = await promo_service.redeem(user_id=user.id, code=code)

            if not result.success:
                await session.rollback()
                await message.answer(result.message, parse_mode="HTML")
                return

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    await state.clear()
    bonus = result.bonus
    promo = result.promo

    if bonus is None or promo is None:
        await message.answer("✅ Promo kod qabul qilindi.", reply_markup=main_menu)
        return

    await message.answer(
        "🎉 <b>PROMO KOD QABUL QILINDI!</b>\n\n"
        f"🎟 Kod: <code>{promo.code}</code>\n"
        f"🎁 Bonus: <b>{bonus.duration_days} kun</b>\n\n"
        "Bonus xizmat navbatiga qo‘shildi. "
        "Agar hozir faol xizmat bo‘lmasa, bonus darhol ishga tushadi.",
        parse_mode="HTML",
        reply_markup=user_navigation_keyboard(
            back_callback="promo_back",
        ),
    )
