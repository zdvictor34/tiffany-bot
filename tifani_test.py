import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Mensaje recibido de {update.message.from_user.id}")
    await update.message.reply_text("¡Hola! El bot está funcionando.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot de prueba en línea... 🤖")
    app.run_polling()

if __name__ == "__main__":
    main()


