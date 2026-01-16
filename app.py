import os
import stripe
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# --------------------
# ENV
# --------------------

TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_KEY

# --------------------
# TELEGRAM APP
# --------------------

app = Application.builder().token(TOKEN).build()

# --------------------
# MODELOS (ESCALABLE)
# --------------------

MODELS = {}

i = 1
while True:
    price = os.getenv(f"MODEL_{i}_PRICE")
    group = os.getenv(f"MODEL_{i}_GROUP")
    if not price or not group:
        break
    MODELS[price] = int(group)
    i += 1

# --------------------
# COMMANDS
# --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    model = args[0] if args else None

    msg = "🔥 Bienvenido\n\n"
    msg += "Para acceder al VIP escribe /vip\n"

    if model:
        context.user_data["model"] = model
        msg += f"\nModelo seleccionado: {model}"

    await update.message.reply_text(msg)

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = context.user_data.get("model")

    if not model:
        await update.message.reply_text("Enlace inválido")
        return

    if model not in MODELS:
        await update.message.reply_text("Modelo no válido")
        return

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": model, "quantity": 1}],
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        metadata={
            "telegram_id": update.effective_user.id,
            "price": model
        }
    )

    await update.message.reply_text(session.url)

# --------------------
# HANDLERS
# --------------------

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("vip", vip))

# --------------------
# START WEBHOOK SERVER
# --------------------

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        webhook_url="https://tiffany-bot.up.railway.app"
    )

