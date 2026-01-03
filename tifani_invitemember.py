# tifani_invitemember.py
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import stripe
from datetime import datetime, timedelta

# -----------------------------
# CARGAR VARIABLES DEL .env
# -----------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
VIP_GROUP_ID = os.getenv("VIP_GROUP_ID")  # ID numérico del canal
stripe.api_key = STRIPE_API_KEY

# -----------------------------
# DICCIONARIO DE SUSCRIPCIONES
# -----------------------------
# user_id: expiration_datetime
subscriptions = {}

# -----------------------------
# FUNCIONES DE SUSCRIPCIÓN
# -----------------------------
def crear_sesion_checkout(telegram_id):
    """Genera sesión de Stripe Checkout para el usuario"""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": "price_1SiLnREvKUSsN6hkkTYzkB1M",  # Tu precio/subscripción
            "quantity": 1
        }],
        mode="subscription",
        success_url="https://t.me/TiffanyOficialBot",
        cancel_url="https://t.me/TiffanyOficialBot",
        client_reference_id=str(telegram_id)
    )
    return session.url

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica si el usuario tiene suscripción activa"""
    user_id = str(update.message.from_user.id)
    if subscriptions.get(user_id):
        await update.message.reply_text("Ya tienes acceso al canal VIP ✅")
    else:
        await update.message.reply_text("No se ha recibido tu pago aún 💳")

# -----------------------------
# HANDLERS DE CHARLA
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola!\nPara acceder al canal VIP, usa /vip"
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía enlace de pago y charla inicial"""
    telegram_id = update.message.from_user.id
    try:
        checkout_url = crear_sesion_checkout(telegram_id)
        await update.message.reply_text(
            f"¡Hola! Soy Tiffany 😄\nPara suscribirte al canal VIP, realiza el pago aquí:\n{checkout_url}"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ Error al generar el pago. Revisa Stripe."
        )
        print("ERROR STRIPE:", e)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n/start - Bienvenida\n/vip - Hablar y recibir enlace de pago\n/confirmar - Verificar suscripción"
    )

# -----------------------------
# INICIAR BOT
# -----------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Comandos de charla
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("help", help_command))

    # Comando de verificación de suscripción
    app.add_handler(CommandHandler("confirmar", confirmar))

    print("Tiffany InviteMemberBot está en línea... 🤖")
    app.run_polling()

if __name__ == "__main__":
    main()

