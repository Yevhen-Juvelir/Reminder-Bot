"""
handlers.py — обробка команд користувачів і створення подій
"""

import os
import re
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from backend import database, crud
from .keyboards import start_keyboard
from backend.models import Event

ALLOWED_PHONE = os.getenv("ALLOWED_PHONE")

# Стан для діалогів
ASK_PHONE, TITLE, DESCRIPTION, LINK, PHOTO, TIME = range(6)

# Папка для зображень
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# === Хелпер для нормалізації номера ===
def normalize_phone(p: str | None) -> str | None:
    if not p:
        return None
    return re.sub(r"\D+", "", p)  # лишаємо лише цифри


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    user = update.effective_user

    db_user = crud.get_user(db, user.id)
    if not db_user:
        crud.create_user(db, user.id, user.username or "unknown")
    db.close()

    await update.message.reply_text(
        "👋 Привіт! Я бот-нагадувач **Cyberfield NeT**.\n"
        "Я надсилаю сповіщення про події.\n\n"
        "Якщо ти адміністратор, скористайся командою /addevent, щоб увійти до панелі."
    )


# === /addevent ===
async def addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_button = KeyboardButton("📱 Надіслати номер", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "🔐 Для підтвердження прав адміністратора надішли свій номер телефону:",
        reply_markup=reply_markup
    )
    return ASK_PHONE


# === отримання номера телефону ===
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    user = update.effective_user
    db_user = crud.get_user(db, user.id)

    if not update.message.contact:
        await update.message.reply_text(
            "⚠️ Будь ласка, скористайся кнопкою '📱 Надіслати номер'.",
            reply_markup=ReplyKeyboardRemove()
        )
        db.close()
        return ConversationHandler.END

    raw_phone = update.message.contact.phone_number
    phone_number = normalize_phone(raw_phone)
    allowed_norm = normalize_phone(ALLOWED_PHONE)

    if db_user:
        db_user.phone = phone_number
        db.commit()
    db.close()

    if phone_number != allowed_norm:
        await update.message.reply_text(
            "🚫 Твій номер не має прав адміністратора.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Вітаю, адміністраторе! Доступ дозволено.\n"
        "📋 Вибери дію нижче:",
        reply_markup=start_keyboard()
    )
    return ConversationHandler.END


# === початок створення події ===
async def start_create_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    query = update.callback_query
    await query.answer()

    user = crud.get_user(db, query.from_user.id)
    db.close()

    if not user or normalize_phone(user.phone) != normalize_phone(ALLOWED_PHONE):
        await query.message.reply_text("🚫 Ти не маєш права створювати події.")
        return ConversationHandler.END

    await query.message.reply_text("📝 Введи *назву події*:", parse_mode="Markdown")
    return TITLE


# === введення назви ===
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text("💬 Введи опис або `-`, щоб пропустити:", parse_mode="Markdown")
    return DESCRIPTION


# === опис ===
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["description"] = None if text == "-" else text
    await update.message.reply_text("🔗 Введи посилання або `-`, щоб пропустити:", parse_mode="Markdown")
    return LINK


# === посилання ===
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["link"] = None if text == "-" else text
    await update.message.reply_text("📸 Надішли фото або `-`, щоб пропустити:", parse_mode="Markdown")
    return PHOTO


# === фото ===
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


# === збереження події ===
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


# === скасування ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Створення події скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# === /myevents ===
async def myevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    try:
        events = (
            db.query(Event)
            .filter(Event.time >= datetime.now())
            .order_by(Event.time.asc())
            .all()
        )

        if not events:
            await update.message.reply_text("📭 Наразі немає жодної запланованої події.")
            return

        for ev in events:
            summary = f"📅 *{ev.title}*\n"
            if ev.description:
                summary += f"💬 {ev.description}\n"
            summary += f"🕒 {ev.time.strftime('%Y-%m-%d %H:%M')}\n"
            if getattr(ev, "link", None):
                summary += f"🔗 [Відкрити посилання]({ev.link})\n"

            if ev.image_url and os.path.exists(ev.image_url):
                try:
                    with open(ev.image_url, "rb") as img:
                        await update.message.reply_photo(photo=img, caption=summary, parse_mode="Markdown")
                except Exception as e:
                    print(f"[myevents] Помилка фото: {e}")
                    await update.message.reply_text(summary, parse_mode="Markdown")
            else:
                await update.message.reply_text(summary, parse_mode="Markdown")
    except Exception as e:
        print(f"[myevents] ERROR: {e}")
        await update.message.reply_text("⚠️ Сталася помилка при отриманні подій.")
    finally:
        db.close()
