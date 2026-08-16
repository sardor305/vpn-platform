from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.keyboards.admin import (
    admin_menu,
    users_menu,
    vpn_account_actions_keyboard,
    vpn_accounts_keyboard,
)
from app.keyboards.menu import main_menu
from app.services.statistics_service import StatisticsService
from app.services.user_service import UserService
from app.services.vpn_account_service import VPNAccountService


router = Router()


async def get_admin(
    telegram_id: int,
):
    async with async_session() as session:

        user_service = UserService(session)

        return await user_service.get_by_telegram_id(
            telegram_id=telegram_id
        )


def vpn_delete_confirmation_keyboard(
    account_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Ha, o‘chirish",
                    callback_data=f"vpn_delete_confirm:{account_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"vpn_delete_cancel:{account_id}",
                ),
            ],
        ]
    )


async def show_vpn_account_detail(
    message: Message,
    account,
):
    user = account.subscription.user
    plan = account.subscription.plan

    full_name = user.first_name

    if user.last_name:
        full_name += f" {user.last_name}"

    status = (
        "🟢 Faol"
        if account.is_active
        else "🔴 Faol emas"
    )

    username = (
        f"@{user.username}"
        if user.username
        else "—"
    )

    text = (
        f"🔑 <b>VPN ACCOUNT #{account.id}</b>\n\n"

        "👤 <b>FOYDALANUVCHI</b>\n"
        f"├ Ism: {full_name}\n"
        f"├ Username: {username}\n"
        f"└ Telegram ID: "
        f"<code>{user.telegram_id}</code>\n\n"

        "📦 <b>OBUNA</b>\n"
        f"├ Tarif: {plan.name}\n"
        f"├ Boshlanishi: "
        f"{account.subscription.start_date}\n"
        f"└ Tugashi: "
        f"{account.subscription.end_date}\n\n"

        "🔐 <b>VPN</b>\n"
        f"├ Protocol: "
        f"<b>{account.protocol.upper()}</b>\n"
        f"├ Marzban username: "
        f"<code>{account.marzban_username}</code>\n"
        f"└ Status: {status}"
    )

    await message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_account_actions_keyboard(
            account_id=account.id,
            is_active=account.is_active,
        ),
    )


@router.message(F.text == "admin")
async def admin_panel(message: Message):

    user = await get_admin(
        telegram_id=message.from_user.id
    )

    if user is None or not user.is_admin:
        return

    await message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        statistics_service = StatisticsService(session)

        stats = await statistics_service.get_statistics()

    protocol_lines = []

    for protocol, count in stats.protocol_counts.items():
        protocol_lines.append(
            f"├ {protocol.upper()}: <b>{count}</b>"
        )

    protocol_text = "\n".join(protocol_lines)

    if not protocol_text:
        protocol_text = "└ Hozircha VPN hisoblar mavjud emas."

    text = (
        "📊 <b>STATISTIKA</b>\n\n"

        "👥 <b>FOYDALANUVCHILAR</b>\n"
        f"├ Jami: <b>{stats.total_users}</b>\n"
        f"├ Faol: <b>{stats.active_users}</b>\n"
        f"├ Faol emas: <b>{stats.inactive_users}</b>\n"
        f"├ Bugun: <b>{stats.users_today}</b>\n"
        f"└ Shu oy: <b>{stats.users_this_month}</b>\n\n"

        "💳 <b>OBUNALAR</b>\n"
        f"├ Jami: <b>{stats.total_subscriptions}</b>\n"
        f"├ Faol: <b>{stats.active_subscriptions}</b>\n"
        f"└ Muddati tugagan: <b>{stats.expired_subscriptions}</b>\n\n"

        "🔑 <b>VPN HISOBLAR</b>\n"
        f"├ Jami: <b>{stats.total_vpn_accounts}</b>\n"
        f"├ Faol: <b>{stats.active_vpn_accounts}</b>\n"
        f"{protocol_text}\n\n"

        "📩 <b>MUROJAATLAR</b>\n"
        f"├ Jami: <b>{stats.total_tickets}</b>\n"
        f"├ Yangi: <b>{stats.new_tickets}</b>\n"
        f"├ Ochiq: <b>{stats.open_tickets}</b>\n"
        f"└ Yopilgan: <b>{stats.closed_tickets}</b>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        users = await user_service.get_all_users()
        total = await user_service.count_users()

    if not users:

        await message.answer(
            "👥 <b>Foydalanuvchilar</b>\n\n"
            "Hozircha foydalanuvchilar mavjud emas.",
            parse_mode="HTML",
            reply_markup=users_menu,
        )

        return

    text = (
        "👥 <b>Foydalanuvchilar</b>\n\n"
        f"📊 Jami: <b>{total}</b>\n\n"
    )

    for user in users:

        username = (
            f"@{user.username}"
            if user.username
            else "—"
        )

        status = (
            "🟢 Faol"
            if user.is_active
            else "🔴 Faol emas"
        )

        full_name = user.first_name

        if user.last_name:
            full_name += f" {user.last_name}"

        text += (
            f"👤 <b>#{user.id}</b>\n"
            f"Ism: {full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: <code>{user.telegram_id}</code>\n"
            f"Status: {status}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=users_menu,
    )


@router.message(F.text == "🔑 VPN hisoblar")
async def vpn_accounts_list(message: Message):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=message.from_user.id
        )

        if admin is None or not admin.is_admin:
            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        accounts = await vpn_account_service.get_all_accounts()

    if not accounts:

        await message.answer(
            "🔑 <b>VPN HISOBLAR</b>\n\n"
            "Hozircha VPN hisoblar mavjud emas.",
            parse_mode="HTML",
            reply_markup=admin_menu,
        )

        return

    text = (
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        f"📊 Jami: <b>{len(accounts)}</b>\n\n"
        "Hisobni tanlang:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=vpn_accounts_keyboard(accounts),
    )


@router.callback_query(F.data == "vpn_accounts:back")
async def vpn_accounts_back(
    callback: CallbackQuery,
):

    user = await get_admin(
        telegram_id=callback.from_user.id
    )

    if user is None or not user.is_admin:

        await callback.answer(
            "Ruxsat yo'q.",
            show_alert=True,
        )

        return

    await callback.answer()

    await callback.message.edit_text(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "Admin panel:",
        reply_markup=admin_menu,
    )


@router.callback_query(F.data == "vpn_accounts:list")
async def vpn_accounts_list_callback(
    callback: CallbackQuery,
):

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        accounts = await vpn_account_service.get_all_accounts()

    if not accounts:

        await callback.answer()

        await callback.message.edit_text(
            "🔑 <b>VPN HISOBLAR</b>\n\n"
            "Hozircha VPN hisoblar mavjud emas.",
            parse_mode="HTML",
        )

        return

    text = (
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        f"📊 Jami: <b>{len(accounts)}</b>\n\n"
        "Hisobni tanlang:"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_accounts_keyboard(accounts),
    )


@router.callback_query(F.data.startswith("vpn_account:"))
async def vpn_account_detail(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer()

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_activate:"))
async def vpn_account_activate(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.activate_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN ACTIVATE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni faollashtirishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob faollashtirildi. 🟢"
    )

    await callback.message.edit_text(
        "VPN hisob yangilanmoqda...",
        parse_mode="HTML",
    )

    async with async_session() as session:

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.message.edit_text(
            "VPN hisob topilmadi.",
            parse_mode="HTML",
        )

        return

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_deactivate:"))
async def vpn_account_deactivate(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.deactivate_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN DEACTIVATE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni deaktivatsiya qilishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob deaktivatsiya qilindi. 🔴"
    )

    await callback.message.edit_text(
        "VPN hisob yangilanmoqda...",
        parse_mode="HTML",
    )

    async with async_session() as session:

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.message.edit_text(
            "VPN hisob topilmadi.",
            parse_mode="HTML",
        )

        return

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_refresh:"))
async def vpn_account_refresh(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    await callback.answer(
        "Ma'lumotlar yangilandi. 🔄"
    )

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(F.data.startswith("vpn_delete:"))
async def vpn_account_delete(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob topilmadi.",
            show_alert=True,
        )

        return

    user = account.subscription.user

    full_name = user.first_name

    if user.last_name:
        full_name += f" {user.last_name}"

    text = (
        "⚠️ <b>VPN HISOBNI O‘CHIRISH</b>\n\n"
        f"🔑 Account: <b>#{account.id}</b>\n"
        f"👤 Foydalanuvchi: <b>{full_name}</b>\n"
        f"🔐 Marzban username: "
        f"<code>{account.marzban_username}</code>\n\n"

        "❗ <b>DIQQAT!</b>\n\n"
        "Bu amal VPN hisobni butunlay o‘chiradi.\n\n"
        "• Marzban VPN account o‘chiriladi\n"
        "• VPNAccount bazadagi yozuvi o‘chiriladi\n"
        "• Foydalanuvchi saqlanadi\n"
        "• Obuna saqlanadi\n"
        "• Tarif saqlanadi\n\n"

        "Davom etishni xohlaysizmi?"
    )

    await callback.answer()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=vpn_delete_confirmation_keyboard(
            account_id=account_id,
        ),
    )


@router.callback_query(
    F.data.startswith("vpn_delete_cancel:")
)
async def vpn_account_delete_cancel(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        account = await vpn_account_service.get_account(
            account_id=account_id
        )

    if account is None:

        await callback.answer(
            "VPN hisob allaqachon o‘chirilgan.",
            show_alert=True,
        )

        return

    await callback.answer(
        "O‘chirish bekor qilindi."
    )

    await show_vpn_account_detail(
        message=callback.message,
        account=account,
    )


@router.callback_query(
    F.data.startswith("vpn_delete_confirm:")
)
async def vpn_account_delete_confirm(
    callback: CallbackQuery,
):

    account_id = int(
        callback.data.split(":")[1]
    )

    async with async_session() as session:

        user_service = UserService(session)

        admin = await user_service.get_by_telegram_id(
            telegram_id=callback.from_user.id
        )

        if admin is None or not admin.is_admin:

            await callback.answer(
                "Ruxsat yo'q.",
                show_alert=True,
            )

            return

        marzban_service = create_marzban_service()

        vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=marzban_service,
        )

        try:

            account = await vpn_account_service.delete_account(
                account_id=account_id
            )

            await session.commit()

        except ValueError as e:

            await session.rollback()

            await callback.answer(
                str(e),
                show_alert=True,
            )

            return

        except Exception as e:

            await session.rollback()

            print(
                "VPN DELETE ERROR:",
                repr(e),
            )

            await callback.answer(
                "VPN hisobni o‘chirishda xatolik yuz berdi.",
                show_alert=True,
            )

            return

    await callback.answer(
        "VPN hisob o‘chirildi. 🗑"
    )

    await callback.message.edit_text(
        "🔑 <b>VPN HISOBLAR</b>\n\n"
        "VPN hisob muvaffaqiyatli o‘chirildi.\n\n"
        "Hisoblar ro‘yxatini yangilash uchun "
        "pastdagi tugmani bosing.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 VPN hisoblar",
                        callback_data="vpn_accounts:list",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Admin panel",
                        callback_data="vpn_accounts:back",
                    )
                ],
            ]
        ),
    )


@router.message(F.text == "⬅️ Admin panel")
async def back_to_admin_panel(message: Message):

    user = await get_admin(
        telegram_id=message.from_user.id
    )

    if user is None or not user.is_admin:
        return

    await message.answer(
        "🔐 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )


@router.message(F.text == "⬅️ Asosiy menyu")
async def back_to_main_menu(message: Message):

    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=main_menu,
    )