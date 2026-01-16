import os
import stripe
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# -------------------
# Variables de entorno
# -------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

bot = Bot(token=TOKEN)
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

# -------------------
# MODELOS / GRUPOS
# -------------------
PRICE_TO_GROUP = {}
i = 1
while True:
    price = os.getenv(f"MODEL_{i}_PRICE")
    group = os.getenv(f"MODEL_{i}_GROUP")
    if not price or not group:
        break
    PRICE_TO_GROUP[price] = int(group)
    i += 1

# -------------------
# COMANDOS TELEGRAM
# -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenido! Usa /vip para acceder al contenido VIP."
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    price = list(PRICE_TO_GROUP.keys())[0]  # solo ejemplo: selecciona el primer modelo
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price, "quantity": 1}],
        success_url=f"https://t.me/{os.getenv('BOT_USERNAME')}",
        cancel_url=f"https://t.me/{os.getenv('BOT_USERNAME')}",
        metadata={"telegram_id": tg_id, "price": price}
    )
    await update.message.reply_text(session.url)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("vip", vip))

# -------------------
# WEBHOOK TELEGRAM
# -------------------
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.json, bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

# -------------------
# WEBHOOK STRIPE
# -------------------
@app.route("/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")
    event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    obj = event["data"]["object"]
    tg_id = int(obj["metadata"]["telegram_id"])
    price = obj["metadata"]["price"]
    group = PRICE_TO_GROUP.get(price)
    if not group:
        return "unknown price", 400
    if event["type"] == "checkout.session.completed":
        bot.add_chat_members(group, [tg_id])
    if event["type"] in ["customer.subscription.deleted", "invoice.payment_failed"]:
        bot.ban_chat_member(group, tg_id)
    return "ok"

# -------------------
# ENDPOINT DE PRUEBA
# -------------------
@app.route("/")
def home():
    return "Bot online 🚀"

# -------------------
# RUN FLASK
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
