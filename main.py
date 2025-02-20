import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import threading
from waitress import serve

# Configuración de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7080995717:AAF_sHSoiZuZEE6MkXws3W5aC-8DttyKOuk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://entrebusqueda.onrender.com/webhook")
GROUP_ID = -1001918569531
CHANNELS = [
    "https://t.me/c/1918569531/152167",  # Canal de películas 1
    "https://t.me/c/1918569531/152839",  # Canal de películas 2
]
PORT = int(os.getenv("PORT", 10000))

# Inicializar Flask y el bot de Telegram
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Función para buscar películas y series
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Filtramos solo mensajes en el grupo específico
    if update.message.chat_id != GROUP_ID:
        return

    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("⚠️ *Uso incorrecto:* `/buscar [película o serie]`", parse_mode="Markdown")
        return

    # Simulando la búsqueda de resultados de películas en los canales
    resultados = []
    for channel_url in CHANNELS:
        try:
            channel_id = channel_url.split("/")[-2]
            message_id = channel_url.split("/")[-1]
            result_url = f"https://t.me/c/{channel_id}/{message_id}"
            resultados.append({
                "url": result_url,
                "text": f"Encontrado: `{keyword}` en {channel_url}"
            })
        except Exception as e:
            logger.error(f"Error procesando el canal {channel_url}: {e}")

    # Si no hay resultados, informar al usuario
    if not resultados:
        await update.message.reply_text(f"❌ *No se encontraron resultados para:* `{keyword}`", parse_mode="Markdown")
        return
    
    # Crear los botones con los resultados encontrados
    keyboard = [
        [InlineKeyboardButton(f"🎬 Ver {r['text']}", url=r["url"])] for r in resultados
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar los resultados como respuesta
    await update.message.reply_text(
        f"✅ *Resultados para:* `{keyword}` 📚\n\n"
        "📥 *Haz clic en los enlaces:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Añadir el comando de búsqueda
application.add_handler(CommandHandler("buscar", buscar))

# Configuración del webhook
async def set_webhook():
    success = await application.bot.set_webhook(WEBHOOK_URL)
    if success:
        logger.info("✅ Webhook configurado correctamente.")
    else:
        logger.error("❌ Error al configurar el webhook.")

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "🤖 Bot funcionando 🚀", 200

# Función para ejecutar el servidor Flask
def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

# Función principal
if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.start()
        await set_webhook()
        logger.info("✅ Bot en funcionamiento.")
    
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())