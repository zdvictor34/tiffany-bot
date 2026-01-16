import os
import stripe
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_KEY
bot = Bot(token=TOKEN)
app = Flask(__name__)
bot = Bot(token=TOKEN)
app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


# -------------------
# MODELOS DÍNAMICOS
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
# TELEGRAM COMMANDS
# -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Modelos disponibles:\n"
    for price in PRICE_TO_GROUP:
        msg += f"/buy_{price}\n"
    await update.message.reply_text(msg)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.replace("/buy_", "")
    price = command
    tg_id = update.effective_user.id

    if price not in PRICE_TO_GROUP:
        await update.message.reply_text("Modelo no válido")
        return

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price, "quantity": 1}],
        success_url="https://t.me/TU_BOT",
        cancel_url="https://t.me/TU_BOT",
        metadata={"telegram_id": tg_id, "price": price}
    )

    await update.message.reply_text(session.url)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("buy", buy))

# -------------------
# TELEGRAM WEBHOOK
# -------------------

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.json, bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

# -------------------
# STRIPE WEBHOOK
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
# HOME
# -------------------

@app.route("/")
def home():
    return "online"

if __name__ == "__main__":
    app.run("0.0.0.0", int(os.getenv("PORT", 8080)))

