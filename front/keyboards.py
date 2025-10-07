from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def start_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Додати подію", callback_data="create_event")],
        [InlineKeyboardButton("📋 Усі події", callback_data="show_events")]
    ]
    return InlineKeyboardMarkup(keyboard)
