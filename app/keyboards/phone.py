from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Telefon raqamini ulashish",
                request_contact=True,
            )
        ],
        [
            KeyboardButton(
                text="⏭️ O‘tkazib yuborish"
            )
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)