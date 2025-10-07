from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater

from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой бот 🤖")

app = ApplicationBuilder().token(BOT_TOKEN).build()
print("BOT started")

print(BOT_TOKEN)
app.add_handler(CommandHandler("start", start))
app.run_polling()
