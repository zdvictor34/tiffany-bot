import os
import stripe
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# -------------------
# ENV
# -------------------

TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_KEY

app = Flask(__name__)
bot = Bot(token=TOKEN)

telegram_app = Application.builder().token(TOKEN).build()

# -------------------
# MODELOS DINÁMICOS
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
    args = context.args
    model = args[0] if args else None

    msg = "🔥 Bienvenido al contenido exclusivo\n\n"
    msg += "Para acceder al VIP usa /vip\n"

    if model:
        msg += f"\nModelo seleccionado: {model}"

    await update.message.reply_text(msg)

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Enlace inválido")
        return

    price = context.args[0]

    if price not in PRICE_TO_GROUP:
        await update.message.reply_text("Modelo no válido")
        return

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price, "quantity": 1}],
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        metadata={"telegram_id": tg_id, "price": price}
    )

    await update.message.reply_text(
        f"Accede al VIP aquí 👇\n{session.url}"
    )

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("vip", vip))

# -------------------
# TELEGRAM WEBHOOK
# -------------------

@app.route("/telegram", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.json, bot)
    await telegram_app.process_update(update)
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
    return "Bot online 🚀"

# -------------------
# START
# -------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
