import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
import stripe
from webhook import subscriptions, GROUP_ID  # Suscripciones y grupo VIP

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -----------------------------
# FUNCIONES DEL BOT
# -----------------------------

# Crear sesión de pago Stripe
def crear_sesion_checkout(telegram_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": "price_1SiLnREvKUSsN6hkkTYzkB1M",  # Reemplaza con tu price ID
            "quantity": 1
        }],
        mode="subscription",
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        client_reference_id=str(telegram_id)
    )
    return session.url

# Enviar botón VIP
async def enviar_boton_vip(update: Update, checkout_url: str = None):
    if checkout_url is None:
        checkout_url = "https://t.me/TiffanyOficialBot?start=vip"

    keyboard = [
        [InlineKeyboardButton("Accede al canal VIP aquí", url=checkout_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "¡Haz clic en el botón para suscribirte al canal VIP!",
        reply_markup=reply_markup
    )

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Bienvenido! Escribe /vip para proceder al pago y acceder al canal VIP."
    )

# Comando /vip
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        checkout_url = crear_sesion_checkout(telegram_id)
        await enviar_boton_vip(update, checkout_url)
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error Stripe:\n{str(e)}"
        )
        raise e

# Comando /confirmar
async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if subscriptions.get(user_id):
        await update.message.reply_text("Ya tienes acceso al canal VIP ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# Manejador de errores global
async def error_handler(update: object, context: CallbackContext):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

# -----------------------------
# INICIAR BOT
# -----------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("confirmar", confirmar))
    app.add_error_handler(error_handler)

    print("Tiffany InviteMemberBot está en línea... 🤖")
    # run_polling maneja reconexión automática
    app.run_polling()

if __name__ == "__main__":
    main()

