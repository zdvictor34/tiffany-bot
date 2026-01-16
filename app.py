import os
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()

# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot activo 🚀. Para acceder a contenido VIP escribe /vip")

telegram_app.add_handler(CommandHandler("start", start))

# TELEGRAM WEBHOOK
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.json, bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

# HOME
@app.route("/")
def home():
    return "Bot online 🚀"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
