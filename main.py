import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
from waitress import serve

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GROUP_ID = -1001918569531
CHANNEL_IDS = [-1001918569531, -1001918569532]

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Falta la variable de entorno TELEGRAM_BOT_TOKEN")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://entrebusqueda.onrender.com/webhook")
PORT = int(os.getenv("PORT", 10000))

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID:
        return
    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al *Buscador de EntresHijos* 🔍\n\n"
        "📌 *Comandos disponibles:*\n"
        "▶️ `/go` - Mostrar este mensaje\n"
        "▶️ `/buscar [palabra clave]` - Buscar contenido\n\n"
        "🔎 *Escribe una palabra clave para encontrar información!*",
        parse_mode="Markdown"
    )

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID:
        return
    
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("⚠️ *Uso incorrecto:* `/buscar [palabra clave]`", parse_mode="Markdown")
        return

    await update.message.reply_text(f"🔎 *Buscando:* `{keyword}` ⏳", parse_mode="Markdown")
    
    resultados = []
    for channel_id in CHANNEL_IDS:
        try:
            chat = await application.bot.get_chat(channel_id)
            async for message in application.bot.get_chat_history(chat.id, limit=200):
                if message.text and keyword.lower() in message.text.lower():
                    resultados.append((channel_id, message.message_id, message.text[:100]))
        except Exception as e:
            logger.error(f"Error en canal {channel_id}: {e}")
    
    if not resultados:
        await update.message.reply_text(f"❌ *No se encontraron resultados para:* `{keyword}`", parse_mode="Markdown")
        return
    
    keyboard = [[InlineKeyboardButton(f"📌 Mensaje {r[1]}", url=f"https://t.me/c/{abs(r[0])}/{r[1]}")] for r in resultados[:10]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *Resultados para:* `{keyword}` 📚\n\n"
        "📥 *Haz clic en los enlaces:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

application.add_handler(CommandHandler("go", go))
application.add_handler(CommandHandler("buscar", buscar))

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

def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    async def main():
        await application.initialize()
        await application.start()
        await set_webhook()
        logger.info("✅ Bot en funcionamiento.")
    
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())