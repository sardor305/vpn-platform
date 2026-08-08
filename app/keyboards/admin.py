from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👥 Foydalanuvchilar"),
            KeyboardButton(text="📦 Tariflar"),
        ],
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="🔑 VPN hisoblar"),
        ],
        [
            KeyboardButton(text="⬅️ Asosiy menyu"),
        ],
    ],
    resize_keyboard=True,
)