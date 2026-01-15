import os
import stripe
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_ID = os.getenv("STRIPE_PRICE_ID")
VIP_GROUP_ID = int(os.getenv("VIP_CHAT_ID"))

stripe.api_key = STRIPE_KEY

bot = Bot(token=TOKEN)
app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

# ----------------
# COMMANDS
# ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Escribe /vip para entrar 🔥")

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        success_url="https://t.me/TU_BOT",
        cancel_url="https://t.me/TU_BOT",
        metadata={"telegram_id": tg_id}
    )

    await update.message.reply_text(session.url)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("vip", vip))

# ----------------
# TELEGRAM WEBHOOK
# ----------------

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.json, bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok"

# ----------------
# STRIPE WEBHOOK
# ----------------

@app.route("/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    event = stripe.Webhook.construct_event(
        payload, sig, STRIPE_WEBHOOK_SECRET
    )

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        tg_id = int(s["metadata"]["telegram_id"])
        bot.add_chat_members(VIP_GROUP_ID, [tg_id])

    if event["type"] in ["customer.subscription.deleted", "invoice.payment_failed"]:
        s = event["data"]["object"]
        tg_id = int(s["metadata"]["telegram_id"])
        bot.ban_chat_member(VIP_GROUP_ID, tg_id)

    return "ok"

@app.route("/")
def home():
    return "online"

if __name__ == "__main__":
    app.run("0.0.0.0", int(os.getenv("PORT", 8080)))

