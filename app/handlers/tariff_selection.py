from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.database.database import async_session
from app.services.purchase_service import PurchaseService
from app.services.user_service import UserService


router = Router()


@router.callback_query(F.data.startswith("buy:"))
async def select_tariff(callback: CallbackQuery):

    await callback.answer()

    plan_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)
        purchase_service = PurchaseService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            language_code=callback.from_user.language_code,
        )

        result = await purchase_service.purchase_plan(
            user_id=user.id,
            plan_id=plan_id,
        )

        if result.success:
            await session.commit()
        else:
            await session.rollback()

    if not result.success:

        await callback.message.answer(
            result.message,
        )

        return

    if (
        result.subscription is not None
        and result.subscription.end_date is not None
    ):
        end_date_text = (
            result.subscription.end_date.strftime(
                "%d.%m.%Y"
            )
        )
    else:
        end_date_text = "Navbatdagi xizmat davrida"

    if result.vpn_link:
        vpn_text = (
            "🔗 <b>VLESS havola:</b>\n"
            f"<code>{result.vpn_link}</code>\n\n"
        )
    else:
        vpn_text = (
            "🔗 <b>VLESS havola:</b>\n"
            "VPN hisob faol xizmat davri boshlanganda "
            "sinxronlanadi.\n\n"
        )

    if result.subscription_url:
        subscription_text = (
            "🔄 <b>Subscription:</b>\n"
            f"<code>{result.subscription_url}</code>"
        )
    else:
        subscription_text = (
            "🔄 <b>Subscription:</b>\n"
            "Faol xizmat davri boshlanganda mavjud bo‘ladi."
        )

    if (
        result.subscription is not None
        and result.subscription.status == "pending"
    ):
        title = "✅ <b>Tarif muvaffaqiyatli xarid qilindi!</b>"
        period_text = (
            "⏳ <b>Holat:</b> Navbatda\n"
            "Tarifingiz hozirgi faol xizmat tugagach "
            "avtomatik ishga tushadi.\n"
            f"📅 <b>Taxminiy tugash sanasi:</b> "
            f"{end_date_text}\n\n"
        )
    else:
        title = "🎉 <b>VPN muvaffaqiyatli yaratildi!</b>"
        period_text = (
            f"📅 <b>Amal qilish muddati:</b> "
            f"{end_date_text}\n\n"
        )

    text = (
        f"{title}\n\n"
        f"📦 <b>Tarif:</b> "
        f"{result.plan.name}\n"
        f"💰 <b>Narxi:</b> "
        f"{result.plan.price} ₽\n"
        f"{period_text}"
        f"{vpn_text}"
        f"{subscription_text}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
    )