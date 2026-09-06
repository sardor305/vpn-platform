from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.keyboards.admin import admin_menu


_last_admin_message_ids: dict[int, int] = {}


def admin_back_keyboard(
    callback_data: str = "admin_section_back",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Admin panel",
                    callback_data=callback_data,
                )
            ]
        ]
    )


async def delete_last_admin_message(
    message: Message,
) -> None:
    telegram_id = message.from_user.id
    message_id = _last_admin_message_ids.get(telegram_id)

    if message_id is None:
        return

    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message_id,
        )
    except Exception:
        pass

    _last_admin_message_ids.pop(telegram_id, None)


async def remember_admin_message(
    message: Message,
) -> None:
    _last_admin_message_ids[
        message.from_user.id
    ] = message.message_id


async def send_admin_panel(
    message: Message,
) -> Message:
    await delete_last_admin_message(message)

    sent = await message.answer(
        "👨‍💼 <b>ADMIN PANEL</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )

    await remember_admin_message(sent)
    return sent


async def replace_with_admin_panel(
    message: Message,
) -> Message:
    telegram_id = message.from_user.id
    current_id = _last_admin_message_ids.get(
        telegram_id
    )

    try:
        if current_id is not None:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=current_id,
            )
        elif message.message_id is not None:
            await message.delete()
    except Exception:
        pass

    _last_admin_message_ids.pop(telegram_id, None)

    sent = await message.bot.send_message(
        chat_id=message.chat.id,
        text="👨‍💼 <b>ADMIN PANEL</b>",
        parse_mode="HTML",
        reply_markup=admin_menu,
    )

    await remember_admin_message(sent)
    return sent
