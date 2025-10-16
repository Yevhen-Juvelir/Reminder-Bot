"""
handlers_admin.py — обработка функций администратора
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from backend import database, models
import os

ALLOWED_PHONE = os.getenv("ALLOWED_PHONE")

# Показать все события
async def show_all_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    query = update.callback_query
    await query.answer()

    user = query.from_user
    db_user = db.query(models.User).filter(models.User.telegram_id == user.id).first()

    if not db_user or db_user.phone != ALLOWED_PHONE:
        await query.message.reply_text("🚫 Ти не маєш доступу до цієї функції.")
        db.close()
        return

    events = db.query(models.Event).all()
    if not events:
        await query.message.reply_text("❌ Немає жодної події.")
        db.close()
        return

    for ev in events:
        summary = f"📅 *{ev.title}*\n"
        if ev.description:
            summary += f"💬 {ev.description}\n"
        summary += f"🕒 {ev.time.strftime('%Y-%m-%d %H:%M')}\n"
        if getattr(ev, "link", None):
            summary += f"🔗 [Відкрити посилання]({ev.link})\n"

        keyboard = [[InlineKeyboardButton(f"🗑 Видалити {ev.id}", callback_data=f"confirm_delete_{ev.id}")]]
        markup = InlineKeyboardMarkup(keyboard)

        if ev.image_url and os.path.exists(ev.image_url):
            try:
                with open(ev.image_url, "rb") as img:
                    await query.message.reply_photo(photo=img, caption=summary, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                print(f"Помилка фото: {e}")
                await query.message.reply_text(summary, parse_mode="Markdown", reply_markup=markup)
        else:
            await query.message.reply_text(summary, parse_mode="Markdown", reply_markup=markup)

    db.close()

# Подтверждение удаления
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.replace("confirm_delete_", ""))

    keyboard = [
        [
            InlineKeyboardButton("✅ Так, видалити", callback_data=f"delete_{event_id}"),
            InlineKeyboardButton("❌ Скасувати", callback_data="cancel_delete"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(f"Видалити подію #{event_id}?", reply_markup=markup)

# Удаление события
async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = database.SessionLocal()
    query = update.callback_query
    await query.answer()

    event_id = int(query.data.replace("delete_", ""))
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        await query.message.reply_text("Подію не знайдено.")
        db.close()
        return

    if event.image_url and os.path.exists(event.image_url):
        try:
            os.remove(event.image_url)
            print(f"Видалено фото: {event.image_url}")
        except Exception as e:
            print(f"Не вдалося видалити фото: {e}")

    db.delete(event)
    db.commit()
    db.close()

    await query.message.reply_text(f"Подію *{event.title}* видалено.", parse_mode="Markdown")

# Отмена удаления
async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("❌ Видалення скасовано.")
