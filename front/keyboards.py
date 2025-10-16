"""
keyboards.py — inline-клавиатуры для Telegram-интерфейса
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Главное меню
def start_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Додати подію", callback_data="create_event")],
        [InlineKeyboardButton("📋 Усі події", callback_data="show_events")]
    ]
    return InlineKeyboardMarkup(keyboard)
