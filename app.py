import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import stripe
from flask import Flask, request, abort

# -----------------------------
# CARGAR VARIABLES DEL .env
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

VIP_GROUPS = {
    "jacqueline": int(os.getenv("VIP_GROUP_ID_JACQUELINE")),
    "jennifer": int(os.getenv("VIP_GROUP_ID_JENNIFER"))
}

PRICE_IDS = {
    "jacqueline": os.getenv("PRICE_JACQUELINE"),
    "jennifer": os.getenv("PRICE_JENNIFER")
}

subscriptions = {}  # Guarda usuarios suscritos temporalmente

print("VIP GROUPS:", VIP_GROUPS)

# -----------------------------
# FUNCION PARA CREAR CHECKOUT
# -----------------------------
def crear_sesion_checkout(telegram_id, modelo):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": PRICE_IDS[modelo],
            "quantity": 1
        }],
        mode="subscription",
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        client_reference_id=str(telegram_id)
    )
    return session.url

# -----------------------------
# HANDLERS DE TELEGRAM
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola, para acceder al canal VIP🔥👅 escribe /vip <modelo>\nEjemplo: /vip jacqueline"
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args or args[0].lower() not in VIP_GROUPS:
            await update.message.reply_text("Debes poner el modelo: jacqueline o jennifer\nEjemplo: /vip jacqueline")
            return

        modelo = args[0].lower()
        telegram_id = update.message.from_user.id
        checkout_url = crear_sesion_checkout(telegram_id, modelo)

        # Botón oculto con link
        keyboard = [[InlineKeyboardButton("Accede al VIP aquí 🔥", url=checkout_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Pulsa el botón para suscribirte al VIP de {modelo.capitalize()}:",
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text("❌ Error al generar el pago. Revisa Stripe.")
        print("ERROR STRIPE:", e)

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in subscriptions:
        await update.message.reply_text(f"Ya tienes acceso al VIP de {subscriptions[user_id]} ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# -----------------------------
# FLASK PARA WEBHOOK STRIPE
# -----------------------------
app_flask = Flask(__name__)

@app_flask.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = session["client_reference_id"]
        price_id = session["line_items"]["data"][0]["price"]["id"] if "line_items" in session else session.get("display_items", [{}])[0].get("price", {}).get("id")
        
        # Determinar a qué grupo pertenece
        modelo = None
        for m, pid in PRICE_IDS.items():
            if pid == price_id:
                modelo = m
                break
        
        if modelo:
            subscriptions[telegram_id] = modelo
            print(f"Usuario {telegram_id} suscrito al VIP de {modelo}")

    return "", 200

# -----------------------------
# INICIAR TELEGRAM BOT
# -----------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("vip", vip))
    application.add_handler(CommandHandler("confirmar", confirmar))

    print("Tiffany Bot Online 🚀")

    # Webhook para Railway
    PORT = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()

