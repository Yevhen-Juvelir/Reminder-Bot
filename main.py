from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой бот 🤖")

app = ApplicationBuilder().token("8411849882:AAEJNZ9B0WPoxFokfquZlV0Uv-L2Jft1gD8").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
