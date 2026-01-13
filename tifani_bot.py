import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import stripe
from webhook import subscriptions, VIP_GROUPS

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
stripe.api_key = os.getenv("STRIPE_API_KEY")

PRICES = {
    "jacqueline": os.getenv("PRICE_JACQUELINE"),
    "jennifer": os.getenv("PRICE_JENNIFER")
}

# ---------- Stripe checkout ----------
def crear_sesion_checkout(telegram_id, modelo):
    price_id = PRICES.get(modelo)
    if not price_id:
        raise Exception("Price ID no definido")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1
        }],
        mode="subscription",
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        client_reference_id=f"{telegram_id}:{modelo}"
    )
    return session.url


# ---------- Telegram ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola, para acceder al canal VIP🔥👅 escribe /vip"
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    modelo = "jacqueline"

    if context.args:
        modelo = context.args[0].lower()

    if modelo not in PRICES:
        await update.message.reply_text("Modelo no válida.")
        return

    try:
        url = crear_sesion_checkout(telegram_id, modelo)
        await update.message.reply_text(f"Accede al VIP aquí 👉 {url}")
    except Exception as e:
        print("Stripe error:", e)
        await update.message.reply_text("Error creando el pago")

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if user_id in subscriptions:
        modelo = subscriptions[user_id]
        await update.message.reply_text(f"Acceso VIP activo para {modelo} ✅")
    else:
        await update.message.reply_text("Aún no se ha recibido tu pago")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("confirmar", confirmar))
    print("Tiffany Bot Online 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()

