import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
import stripe
from webhook import subscriptions, GROUP_ID  # Suscripciones y grupo VIP

# -----------------------------
# CONFIGURACION BASICA
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
stripe.api_key = os.getenv("STRIPE_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -----------------------------
# FUNCION PARA CREAR CHECKOUT
# -----------------------------
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
        "¡Haz clic en el botón para suscribirte al canal VIP!",
        reply_markup=reply_markup
    )

# -----------------------------
# COMANDO /START
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Bienvenido! Escribe /vip para proceder al pago y acceder al canal VIP."
    )

# -----------------------------
# COMANDO /VIP
# -----------------------------
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        checkout_url = crear_sesion_checkout(telegram_id)
        await enviar_boton_vip(update, checkout_url)
    except Exception as e:
        await update.message.reply_text("❌ Error al generar el pago. Revisa Stripe.")
        logging.error("ERROR STRIPE: %s", e)

# -----------------------------
# COMANDO /CONFIRMAR
# -----------------------------
async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if subscriptions.get(user_id):
        await update.message.reply_text("Ya tienes acceso al canal VIP ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# -----------------------------
# MANEJADOR DE ERRORES GLOBAL
# -----------------------------
async def error_handler(update: object, context: CallbackContext):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

# -----------------------------
# INICIAR BOT (con reinicio automático)
# -----------------------------
def main():
    while True:
        try:
            app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("vip", vip))
            app.add_handler(CommandHandler("confirmar", confirmar))
            app.add_error_handler(error_handler)

            print("Tiffany InviteMemberBot está en línea... 🤖")
            app.run_polling()
        except Exception as e:
            logging.error("ERROR CRITICO, reiniciando bot: %s", e)
            asyncio.sleep(5)  # Espera 5 segundos antes de reiniciar

if __name__ == "__main__":
    main()

