import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import stripe
from webhook import subscriptions, GROUP_ID  # Suscripciones y grupo VIP

# -----------------------------
# CARGAR VARIABLES DEL .env
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
stripe.api_key = os.getenv("STRIPE_API_KEY")

# -----------------------------
# FUNCION PARA CREAR CHECKOUT
# -----------------------------
def crear_sesion_checkout(telegram_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": "price_1SiLnREvKUSsN6hkkTYzkB1M",  # Reemplaza con tu price_id
            "quantity": 1
        }],
        mode="subscription",  # Suscripción mensual
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        client_reference_id=str(telegram_id)
    )
    return session.url

# -----------------------------
# FUNCION PARA ENVIAR BOTON VIP
# -----------------------------
async def enviar_boton_vip(update: Update, checkout_url: str = None):
    if checkout_url is None:
        checkout_url = "https://t.me/TiffanyOficialBot?start=vip"
    
    keyboard = [
        [InlineKeyboardButton("Accede al canal VIP aquí", url=checkout_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "¡Haz clic en el botón para hablar con Tiffany y suscribirte al canal VIP!",
        reply_markup=reply_markup
    )

# -----------------------------
# HANDLERS DE TELEGRAM
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await enviar_boton_vip(update)

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        checkout_url = crear_sesion_checkout(telegram_id)
        await enviar_boton_vip(update, checkout_url)
    except Exception as e:
        await update.message.reply_text(
            "❌ Error al generar el pago. Revisa Stripe."
        )
        print("ERROR STRIPE:", e)

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if subscriptions.get(user_id):
        await update.message.reply_text("Ya tienes acceso al canal VIP ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# -----------------------------
# INICIAR BOT
# -----------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("confirmar", confirmar))

    print("Tiffany InviteMemberBot está en línea... 🤖")
    app.run_polling()

if __name__ == "__main__":
    main()

