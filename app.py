import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import stripe
import asyncio
import threading

# -----------------------------
# CARGAR VARIABLES
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

VIP_GROUPS = {
    "jacqueline": os.getenv("VIP_GROUP_ID_JACQUELINE"),
    "jennifer": os.getenv("VIP_GROUP_ID_JENNIFER")
}

PRICES = {
    "jacqueline": os.getenv("PRICE_JACQUELINE"),
    "jennifer": os.getenv("PRICE_JENNIFER")
}

stripe.api_key = STRIPE_API_KEY

# -----------------------------
# SUSCRIPCIONES EN MEMORIA
# -----------------------------
subscriptions = {}

# -----------------------------
# FUNCION PARA CREAR CHECKOUT
# -----------------------------
def crear_sesion_checkout(telegram_id, modelo):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": PRICES[modelo], "quantity": 1}],
        mode="subscription",
        success_url=f"https://t.me/TiffanyOficialBot?start={modelo}",
        cancel_url=f"https://t.me/TiffanyOficialBot?start={modelo}",
        client_reference_id=str(telegram_id)
    )
    return session.url

# -----------------------------
# TELEGRAM HANDLERS
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola, para acceder al canal VIP🔥👅 escribe /vip")

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    modelo = "jacqueline"  # default
    if context.args:
        arg = context.args[0].lower()
        if arg in VIP_GROUPS:
            modelo = arg
    try:
        checkout_url = crear_sesion_checkout(telegram_id, modelo)
        keyboard = [[InlineKeyboardButton("Accede al VIP aquí 🔥", url=checkout_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Pulsa el botón para suscribirte:", reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text("❌ Error al generar el pago. Revisa Stripe.")
        print("Stripe error:", e)

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if subscriptions.get(user_id):
        await update.message.reply_text("Ya tienes acceso al canal VIP ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# -----------------------------
# FLASK APP PARA WEBHOOK STRIPE
# -----------------------------
flask_app = Flask(__name__)

@flask_app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        print("Webhook error:", e)
        return jsonify(success=False), 400

    # -----------------------------
    # Manejar eventos
    # -----------------------------
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = session.get("client_reference_id")
        modelo = session.get("metadata", {}).get("modelo", "jacqueline")
        if telegram_id:
            subscriptions[str(telegram_id)] = True
            print(f"✅ Usuario {telegram_id} pagó modelo {modelo}")
            # Aquí puedes añadir al grupo VIP si quieres automatizar
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        telegram_id = subscription.get("metadata", {}).get("telegram_id")
        if telegram_id and telegram_id in subscriptions:
            subscriptions.pop(telegram_id)
            print(f"❌ Usuario {telegram_id} canceló la suscripción")
    return jsonify(success=True)

# -----------------------------
# FUNCION PARA LEVANTAR TELEGRAM
# -----------------------------
def run_telegram():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("confirmar", confirmar))
    print("Tiffany Bot Online 🚀")
    app.run_polling()

# -----------------------------
# EJECUTAR TELEGRAM EN HILO PARA FLASK
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_telegram).start()
    PORT = int(os.getenv("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=PORT)

