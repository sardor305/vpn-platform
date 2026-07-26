from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Obuna sotib olish")],
        [KeyboardButton(text="👤 Mening obunam")],
        [KeyboardButton(text="📞 Yordam")],
    ],
    resize_keyboard=True,
)