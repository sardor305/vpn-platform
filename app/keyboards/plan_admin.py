from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app.models.plan import Plan


def admin_plans_keyboard(
    plans: list[Plan],
) -> InlineKeyboardMarkup:

    buttons = []

    for plan in plans:

        status = "🟢" if plan.is_active else "🔴"

        buttons.append([
            InlineKeyboardButton(
                text=(
                    f"{status} {plan.name} — "
                    f"{plan.price} ₽ / "
                    f"{plan.duration_days} kun"
                ),
                callback_data=f"admin_plan:{plan.id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="➕ Yangi tarif",
            callback_data="admin_plan_create",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="✏️ Kunlik narxni o‘zgartirish",
            callback_data="daily_price:change",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Admin panel",
            callback_data="admin_plan_back",
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def admin_plan_detail_keyboard(
    plan: Plan,
) -> InlineKeyboardMarkup:

    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Tahrirlash",
                callback_data=f"admin_plan_edit:{plan.id}",
            )
        ]
    ]

    if plan.is_active:
        buttons.append([
            InlineKeyboardButton(
                text="🔴 Deaktivatsiya qilish",
                callback_data=f"admin_plan_deactivate:{plan.id}",
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🟢 Aktivlashtirish",
                callback_data=f"admin_plan_activate:{plan.id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Tariflar",
            callback_data="admin_plan_list",
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )