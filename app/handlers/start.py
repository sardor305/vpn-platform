from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from app.database.database import async_session
from app.keyboards.menu import main_menu
from app.keyboards.phone import phone_keyboard
from app.services.referral_service import ReferralService
from app.services.user_service import UserService


router = Router()


def _parse_referrer_telegram_id(
    command: CommandObject,
) -> int | None:
    """Extract inviter Telegram ID from a /start ref payload."""
    if not command.args:
        return None

    payload = command.args.strip()

    if not payload.startswith("ref_"):
        return None

    raw_telegram_id = payload[4:]

    if not raw_telegram_id.isdigit():
        return None

    try:
        telegram_id = int(raw_telegram_id)
    except ValueError:
        return None

    if telegram_id <= 0:
        return None

    return telegram_id


@router.message(CommandStart())
async def start_handler(
    message: Message,
    command: CommandObject,
):
    referrer_telegram_id = _parse_referrer_telegram_id(command)

    async with async_session() as session:
        try:
            user_service = UserService(session)

            user, created = await user_service.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
            )

            if created and referrer_telegram_id is not None:
                inviter = await user_service.get_by_telegram_id(
                    telegram_id=referrer_telegram_id
                )

                if inviter is not None and inviter.id != user.id:
                    referral_service = ReferralService(session)

                    await referral_service.bind_referral(
                        inviter_user_id=inviter.id,
                        invited_user_id=user.id,
                    )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    if created:
        await message.answer(
            "🎉 Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
            "👋 Assalomu alaykum!\n\n"
            "VPN Platformaga xush kelibsiz.\n\n"
            "📱 <b>Telefon raqamingiz</b>\n\n"
            "Telefon raqamingiz sizni botdagi akkauntingiz "
            "bilan bog‘lash va xizmatdan foydalanishingizni "
            "qulay boshqarish uchun kerak.\n\n"
            "🔒 Raqamingiz boshqa foydalanuvchilarga "
            "ko‘rsatilmaydi.\n\n"
            "Telefon raqamingizni ulashishni xohlamasangiz, "
            "bu bosqichni o'tkazib yuborishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=phone_keyboard,
        )
        return

    await message.answer(
        "👋 Qaytganingizdan xursandmiz!\n\n"
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )