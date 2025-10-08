"""
handlers.py — обработка пользовательских команд и создание событий
"""

import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from backend import database, crud
from .keyboards import start_keyboard

ALLOWED_PHONE = os.getenv("ALLOWED_PHONE")

# Состояния для пошагового диалога
TITLE, DESCRIPTION, LINK, PHOTO, TIME = range(5)

# Папка для сохранения фото
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Команда /start — регистрация пользователя и приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    user = update.effective_user
    db_user = crud.get_user(db, user.id)
    if not db_user:
        crud.create_user(db, user.id, user.username or "unknown")
    await update.message.reply_text(
        "👋 Привіт! Я бот-нагадувач.\nЯкщо ти адміністратор — можеш додати подію.",
        reply_markup=start_keyboard()
    )

# Начало создания события (проверка админа)
async def start_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    query = update.callback_query
    await query.answer()

    user = crud.get_user(db, query.from_user.id)
    if not user or user.phone != ALLOWED_PHONE:
        await query.message.reply_text("🚫 Лише адміністратор може створювати події.")
        return ConversationHandler.END

    await query.message.reply_text("📝 Введи *назву події*:", parse_mode="Markdown")
    return TITLE

# Получение названия события
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("💬 Введи опис або `-`, щоб пропустити:", parse_mode="Markdown")
    return DESCRIPTION

# Получение описания
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["description"] = None if text == "-" else text
    await update.message.reply_text("🔗 Введи посилання або `-`, щоб пропустити:", parse_mode="Markdown")
    return LINK

# Получение ссылки
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["link"] = None if text == "-" else text
    await update.message.reply_text("📸 Надішли фото або `-`, щоб пропустити:", parse_mode="Markdown")
    return PHOTO

# Получение фото
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        file_path = os.path.join(IMAGES_DIR, f"{file.file_unique_id}.jpg")
        await file.download_to_drive(file_path)
        context.user_data["image_url"] = file_path
    else:
        text = update.message.text.strip()
        context.user_data["image_url"] = None if text == "-" else text

    await update.message.reply_text("⏰ Введи дату і час у форматі 2025-10-08T17:00:", parse_mode="Markdown")
    return TIME

# Финальный шаг — сохранение события
async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    user = crud.get_user(db, update.effective_user.id)

    try:
        time = datetime.fromisoformat(update.message.text.strip())

        event = crud.create_event(
            db,
            user.id,
            context.user_data["title"],
            context.user_data.get("description"),
            time,
        )
        event.image_url = context.user_data.get("image_url")
        db.commit()

        summary = f"✅ Подію створено!\n\n🗓 *{context.user_data['title']}*\n"
        if context.user_data.get("description"):
            summary += f"💬 {context.user_data['description']}\n"
        if context.user_data.get("link"):
            summary += f"🔗 {context.user_data['link']}\n"
        summary += f"🕒 {time.strftime('%Y-%m-%d %H:%M')}\n"

        if context.user_data.get("image_url"):
            with open(context.user_data["image_url"], "rb") as img:
                await update.message.reply_photo(photo=img, caption=summary, parse_mode="Markdown")
        else:
            await update.message.reply_text(summary, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("⚠️ Помилка! Перевір формат дати: YYYY-MM-DDTHH:MM.")
        print("DATE ERROR:", e)
    finally:
        db.close()

    return ConversationHandler.END

# Отмена создания
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Створення події скасовано.")
    return ConversationHandler.END
