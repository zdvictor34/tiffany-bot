# webhook.py
import os
from flask import Flask, request, jsonify
import stripe
from telegram import Bot
from datetime import datetime, timedelta
from dotenv import load_dotenv

# -----------------------------
# Cargar variables del .env
# -----------------------------
load_dotenv()
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("VIP_GROUP_ID"))

# Inicializar Stripe y Telegram
stripe.api_key = STRIPE_API_KEY
bot = Bot(token=TELEGRAM_TOKEN)

# Diccionario de suscripciones: {telegram_id: expiration_datetime}
subscriptions = {}

# Inicializar Flask
app = Flask(__name__)

@app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    # Verificar firma de Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        print("❌ Firma inválida:", e)
        return "❌ Firma inválida", 400

    # Manejar evento de pago completado
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = session.get("client_reference_id")
        if telegram_id:
            telegram_id_int = int(telegram_id)
            # Guardar suscripción: 30 días
            subscriptions[telegram_id] = datetime.utcnow() + timedelta(days=30)
            print(f"✅ Suscripción registrada para usuario {telegram_id}")

            # Intentar agregar al canal VIP
            try:
                bot.add_chat_members(chat_id=GROUP_ID, user_ids=[telegram_id_int])
                print(f"Usuario {telegram_id} agregado al canal VIP")
            except Exception as e:
                print("⚠️ Error agregando usuario al canal:", e)

    return jsonify(success=True)

# -----------------------------
# Ejecutar servidor Flask
# -----------------------------
if __name__ == "__main__":
    print("Webhook de Stripe escuchando en el puerto 5000...")
    app.run(port=5000)

