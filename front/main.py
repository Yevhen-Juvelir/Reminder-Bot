"""
main.py — точка входу для Telegram-бота
"""

from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from front.handlers import (
    start, start_create_event, get_title, get_description,
    get_link, get_photo, get_time, cancel
)
from front.handlers_admin import show_all_events, delete_event, cancel_delete, confirm_delete
from front.scheduler import start_scheduler
from backend import database, models
from dotenv import load_dotenv
import os
import nest_asyncio

# Включаем поддержку asyncio в уже запущенном цикле (для Jupyter или IDE)
nest_asyncio.apply()
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Создание таблиц, если не существуют
models.Base.metadata.create_all(bind=database.engine)

# Функция, запускаемая при старте приложения
async def post_startup(app):
    start_scheduler()
    print("Планувальник запущено")

# Создание и настройка приложения Telegram
app = (
    ApplicationBuilder()
    .token(TOKEN)
    .post_init(post_startup)
    .build()
)

# Регистрация команд и хендлеров
app.add_handler(CommandHandler("start", start))

from front.handlers import TITLE, DESCRIPTION, LINK, PHOTO, TIME
conv_handler = ConversationHandler(
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
app.add_handler(conv_handler)

app.add_handler(CallbackQueryHandler(show_all_events, pattern="show_events"))
app.add_handler(CallbackQueryHandler(confirm_delete, pattern=r"confirm_delete_\d+"))
app.add_handler(CallbackQueryHandler(delete_event, pattern=r"delete_\d+"))
app.add_handler(CallbackQueryHandler(cancel_delete, pattern="cancel_delete"))

print("Бота запущено")
app.run_polling()
