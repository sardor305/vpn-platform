from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def promo_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Promo yaratish",
                    callback_data="promo_admin:create",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Promo ro‘yxati",
                    callback_data="promo_admin:list",
                )
            ],
        ]
    )


def promo_list_keyboard(promos) -> InlineKeyboardMarkup:
    rows = []

    for promo in promos:
        status = "🟢" if promo.is_active else "🔴"

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {promo.code}",
                    callback_data=f"promo_admin:view:{promo.id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data="promo_admin:list",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="promo_admin:back",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def promo_detail_keyboard(
    promo_id: int,
    is_active: bool,
) -> InlineKeyboardMarkup:
    status_callback = (
        f"promo_admin:deactivate:{promo_id}"
        if is_active
        else f"promo_admin:activate:{promo_id}"
    )
    status_text = (
        "🔴 O‘chirish"
        if is_active
        else "🟢 Faollashtirish"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Tahrirlash",
                    callback_data=f"promo_admin:edit:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=status_text,
                    callback_data=status_callback,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data=f"promo_admin:stats:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Promo ro‘yxati",
                    callback_data="promo_admin:list",
                )
            ],
        ]
    )


def promo_create_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="promo_admin:create_cancel",
                )
            ]
        ]
    )


def promo_edit_keyboard(promo_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Bonus kunlari",
                    callback_data=f"promo_admin:edit_duration:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Umumiy limit",
                    callback_data=f"promo_admin:edit_total_limit:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Foydalanuvchi limiti",
                    callback_data=f"promo_admin:edit_user_limit:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Boshlanish sanasi",
                    callback_data=f"promo_admin:edit_start:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Tugash sanasi",
                    callback_data=f"promo_admin:edit_end:{promo_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data=f"promo_admin:view:{promo_id}",
                )
            ],
        ]
    )