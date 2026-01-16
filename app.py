import os
import stripe
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# -------------------
# ENV
# -------------------

TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_KEY

bot = Bot(token=TOKEN)
app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()

# 🔥 ESTO ES CLAVE
asyncio.get_event_loop().run_until_complete(telegram_app.initialize())

# -------------------
# MODELOS DINÁMICOS
# -------------------
# Railway:
# MODEL_1_SLUG=jennifer
# MODEL_1_PRICE=price_xxx
# MODEL_1_GROUP=-100xxxx
# MODEL_2_SLUG=jacquelin
# ...

MODELS = {}
i = 1
while True:
    slug = os.getenv(f"MODEL_{i}_SLUG")
    price = os.getenv(f"MODEL_{i}_PRICE")
    group = os.getenv(f"MODEL_{i}_GROUP")

    if not slug or not price or not group:
        break

    MODELS[slug] = {
        "price": price,
        "group": int(group)
    }
    i += 1

# -------------------
# TELEGRAM COMMANDS
# -------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = None

    if context.args:
        model = context.args[0]
        context.user_data["model"] = model

    if model in MODELS:
        await update.message.reply_text(
            f"🔥 Acceso VIP {model.capitalize()}\n\n"
            f"Escribe /vip para suscribirte"
        )
    else:
        msg = "🔥 Modelos disponibles:\n\n"
        for m in MODELS:
            msg += f"https://t.me/TiffanyOficialBot?start={m}\n"
        await update.message.reply_text(msg)

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = context.user_data.get("model")

    if model not in MODELS:
        await update.message.reply_text("Accede desde el link del modelo primero.")
        return

    tg_id = update.effective_user.id
    price = MODELS[model]["price"]

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price, "quantity": 1}],
        success_url=f"https://t.me/TiffanyOficialBot",
        cancel_url=f"https://t.me/TiffanyOficialBot",
        metadata={
            "telegram_id": tg_id,
            "model": model
        }
    )

    await update.message.reply_text(session.url)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("vip", vip))

# -------------------
# TELEGRAM WEBHOOK
# -------------------

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.json, bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok"

# -------------------
# STRIPE WEBHOOK
# -------------------

@app.route("/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    event = stripe.Webhook.construct_event(
        payload, sig, STRIPE_WEBHOOK_SECRET
    )

    obj = event["data"]["object"]
    tg_id = int(obj["metadata"]["telegram_id"])
    model = obj["metadata"]["model"]
    group = MODELS[model]["group"]

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


