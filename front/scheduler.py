from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from backend import crud, database, models
from telegram import Bot
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
scheduler = AsyncIOScheduler()


async def check_events():
    db = database.SessionLocal()
    now = datetime.now()
    events = crud.get_upcoming_events(db, now)

    if not events:
        db.close()
        return

    users = db.query(models.User).all()

    for ev in events:
        # 🧩 Формуємо повідомлення (з описом, посиланням і часом)
        summary = f"🔔 *Нагадування*\n\n" \
                  f"🗓 *{ev.title}*\n"

        if ev.description:
            summary += f"💬 {ev.description}\n"

        if ev.image_url:
            summary += f"🕒 {ev.time.strftime('%Y-%m-%d %H:%M')}\n"
        else:
            summary += f"🕒 {ev.time.strftime('%Y-%m-%d %H:%M')}\n"

        # 🧩 додаємо посилання (Markdown формат)
        if hasattr(ev, "link") and ev.link:
            summary += f"🔗 [Відкрити посилання]({ev.link})\n"

        # надсилаємо всім користувачам
        for usr in users:
            try:
                if ev.image_url and os.path.exists(ev.image_url):
                    with open(ev.image_url, "rb") as img:
                        await bot.send_photo(
                            chat_id=usr.telegram_id,
                            photo=img,
                            caption=summary,
                            parse_mode="Markdown"
                        )
                else:
                    await bot.send_message(
                        chat_id=usr.telegram_id,
                        text=summary,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                print(f"⚠️ Помилка надсилання користувачу {usr.telegram_id}: {e}")

        # 🧹 видаляємо фото після розсилки
        if ev.image_url and os.path.exists(ev.image_url):
            try:
                os.remove(ev.image_url)
                print(f"🗑 Видалено фото: {ev.image_url}")
            except Exception as e:
                print(f"⚠️ Не вдалося видалити фото {ev.image_url}: {e}")

        db.delete(ev)
        db.commit()

    db.close()


def start_scheduler():
    scheduler.add_job(check_events, "interval", seconds=30)
    scheduler.start()
