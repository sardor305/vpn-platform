from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config.config import config
from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.keyboards.subscription_keyboard import subscription_keyboard
from app.services.subscription_info_service import SubscriptionInfoService
from app.services.user_service import UserService
from app.services.vpn_account_service import VPNAccountService


router = Router()


@router.message(F.text == "👤 Mening obunam")
async def my_subscription(message: Message):

    async with async_session() as session:

        user_service = UserService(session)
        subscription_info_service = SubscriptionInfoService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
        )

        info = await subscription_info_service.get_info(
            user.id,
        )

        if info is None:

            await message.answer(
                "❌ Sizda faol obuna mavjud emas.\n\n"
                "🛒 \"Obuna sotib olish\" bo'limidan tarif tanlang."
            )

            return

        subscription = info["subscription"]
        vpn_account = info["vpn_account"]

    status = (
        "🟢 Faol"
        if subscription.status == "active"
        else "🔴 Faol emas"
    )

    if vpn_account is None:

        await message.answer(
            f"👤 <b>Mening obunam</b>\n\n"
            f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
            f"💰 Narxi: <b>{subscription.plan.price} ₽</b>\n\n"
            f"📅 Boshlangan sana:\n"
            f"{subscription.start_date.strftime('%d.%m.%Y')}\n\n"
            f"⏳ Tugash sanasi:\n"
            f"{subscription.end_date.strftime('%d.%m.%Y')}\n\n"
            f"{status}\n\n"
            f"⚠️ <b>VPN hisob mavjud emas.</b>\n\n"
            f"Faol obunangiz uchun yangi VPN hisob yaratish "
            f"uchun quyidagi tugmani bosing.",
            parse_mode="HTML",
            reply_markup=subscription_keyboard(
                show_create_vpn=True,
            ),
        )

        return

    subscription_url = (
        f"{config.MARZBAN_PUBLIC_URL}"
        f"{vpn_account.subscription_url}"
    )

    await message.answer(
        f"👤 <b>Mening obunam</b>\n\n"
        f"📦 Tarif: <b>{subscription.plan.name}</b>\n"
        f"💰 Narxi: <b>{subscription.plan.price} ₽</b>\n\n"
        f"👤 Username:\n"
        f"<code>{vpn_account.marzban_username}</code>\n\n"
        f"📅 Boshlangan sana:\n"
        f"{subscription.start_date.strftime('%d.%m.%Y')}\n\n"
        f"⏳ Tugash sanasi:\n"
        f"{subscription.end_date.strftime('%d.%m.%Y')}\n\n"
        f"{status}\n\n"
        f"🔗 <b>VLESS havola:</b>\n"
        f"<code>{vpn_account.vpn_link}</code>",
        parse_mode="HTML",
        reply_markup=subscription_keyboard(
            subscription_url=subscription_url,
        ),
    )


@router.callback_query(
    F.data == "subscription:create_vpn"
)
async def create_vpn_for_subscription(
    callback: CallbackQuery,
):

    await callback.answer()

    async with async_session() as session:

        user_service = UserService(session)
        subscription_info_service = SubscriptionInfoService(session)

        user, _ = await user_service.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            language_code=callback.from_user.language_code,
        )

        info = await subscription_info_service.get_info(
            user.id,
        )

        if info is None:

            await callback.message.edit_text(
                "❌ Sizda faol obuna mavjud emas.\n\n"
                "🛒 \"Obuna sotib olish\" bo'limidan tarif tanlang."
            )

            return

        subscription = info["subscription"]
        vpn_account = info["vpn_account"]

        if vpn_account is not None:

            subscription_url = (
                f"{config.MARZBAN_PUBLIC_URL}"
                f"{vpn_account.subscription_url}"
            )

            await callback.message.edit_text(
                f"👤 <b>Mening obunam</b>\n\n"
                f"📦 Tarif: <b>{subscription.plan.name}</b>\n\n"
                f"👤 Username:\n"
                f"<code>{vpn_account.marzban_username}</code>\n\n"
                f"🔗 <b>VLESS havola:</b>\n"
                f"<code>{vpn_account.vpn_link}</code>",
                parse_mode="HTML",
                reply_markup=subscription_keyboard(
                    subscription_url=subscription_url,
                ),
            )

            return

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=create_marzban_service(),
        )

        try:

            vpn_account = await vpn_account_service.get_or_create(
                subscription_id=subscription.id,
                user_id=user.id,
                protocol="vless",
            )

            await session.commit()

        except Exception as e:

            await session.rollback()

            print(
                "CREATE VPN ACCOUNT ERROR:",
                repr(e),
            )

            await callback.message.edit_text(
                "❌ VPN hisob yaratishda xatolik yuz berdi.\n\n"
                "Iltimos, birozdan keyin qayta urinib ko‘ring."
            )

            return

    subscription_url = (
        f"{config.MARZBAN_PUBLIC_URL}"
        f"{vpn_account.subscription_url}"
    )

    await callback.message.edit_text(
        f"🎉 <b>VPN hisob muvaffaqiyatli yaratildi!</b>\n\n"
        f"👤 Username:\n"
        f"<code>{vpn_account.marzban_username}</code>\n\n"
        f"🔗 <b>VLESS havola:</b>\n"
        f"<code>{vpn_account.vpn_link}</code>",
        parse_mode="HTML",
        reply_markup=subscription_keyboard(
            subscription_url=subscription_url,
        ),
    )