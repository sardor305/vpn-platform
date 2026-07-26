from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.services.tariffs import TARIFFS

router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def select_tariff(callback: CallbackQuery):
    tariff_id = callback.data.split(":")[1]

    tariff = next(
        (item for item in TARIFFS if item["id"] == tariff_id),
        None
    )

    if tariff is None:
        await callback.answer("Tarif topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ Siz tanladingiz:\n\n"
        f"{tariff['name']}\n"
        f"💰 {tariff['price']} ₽\n\n"
        f"Keyingi bosqich: to'lov usulini tanlash."
    )

    await callback.answer()