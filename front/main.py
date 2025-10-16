"""
main.py — точка входу для Telegram-бота Cyberfield NeT Reminder
"""

import os
import nest_asyncio
import logging
from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

# === Імпорти власних модулів ===
from backend import database, models
from front.handlers import (
    start, addevent, get_phone,
    start_create_event, get_title, get_description,
    get_link, get_photo, get_time, cancel, myevents,
    ASK_PHONE, TITLE, DESCRIPTION, LINK, PHOTO, TIME
)
from front.handlers_admin import (
    show_all_events, delete_event, cancel_delete, confirm_delete
)
from front.scheduler import start_scheduler

# === Налаштування ===
nest_asyncio.apply()
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# === Ініціалізація БД ===
models.Base.metadata.create_all(bind=database.engine)



# === Команди для Telegram ===
async def set_commands(app):
    commands = [
        BotCommand("start", "Почати роботу з ботом"),
        BotCommand("addevent", "Додати подію (для адміністратора)"),
        BotCommand("myevents", "Переглянути заплановані події"),
        BotCommand("cancel", "Скасувати дію"),
    ]
    await app.bot.set_my_commands(commands)

# === Обробка помилок ===
async def on_error(update, context):
    logging.exception("Unhandled exception in handler:", exc_info=context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Вибач, сталася неочікувана помилка. Я вже записав лог."
            )
    except Exception:
        pass

# === Події після запуску ===
async def post_startup(app):
    start_scheduler()
    print("Планувальник запущено")
    await set_commands(app)

# === Створення застосунку Telegram ===
app = (
    ApplicationBuilder()
    .token(TOKEN)
    .post_init(post_startup)
    .build()
)

# Глобальний error handler
app.add_error_handler(on_error)

# === Команди ===
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("myevents", myevents))

# === Додавання події (перевірка номера) ===
conv_addevent = ConversationHandler(
    entry_points=[CommandHandler("addevent", addevent)],
    states={
        ASK_PHONE: [MessageHandler(filters.CONTACT, get_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
app.add_handler(conv_addevent)

# === Діалог створення події ===
conv_create_event = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_create_event, pattern="create_event")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
        PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), get_photo)],
        TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
app.add_handler(conv_create_event)

# === Адмін-функції ===
app.add_handler(CallbackQueryHandler(show_all_events, pattern="show_events"))
app.add_handler(CallbackQueryHandler(confirm_delete, pattern=r"confirm_delete_\d+"))
app.add_handler(CallbackQueryHandler(delete_event, pattern=r"delete_\d+"))
app.add_handler(CallbackQueryHandler(cancel_delete, pattern="cancel_delete"))

# === Запуск ===
print("Бота запущено 🚀")
app.run_polling()
