import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuración de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ID del grupo donde funciona el bot
GROUP_ID = -1001918569531  

# Canales donde se buscará el contenido
CHANNEL_IDS = [
    "-1001918569531",  # ID del primer canal
    "-1001918569531"   # ID del segundo canal (ajustar según sea necesario)
]

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = f"https://entrebusqueda.onrender.com/{TOKEN}"

app = Flask(__name__)

# Crear la aplicación del bot
application = Application.builder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID:
        return  # Ignorar mensajes fuera del grupo

    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al *Buscador de EntresHijos* 🔍\n\n"
        "📌 *Comandos disponibles:*\n"
        "▶️ `/start` - Mostrar este mensaje\n"
        "▶️ `/buscar [palabra clave]` - Buscar contenido en los canales\n\n"
        "🔎 *Escribe una palabra clave para encontrar información rápida!*",
        parse_mode="Markdown"
    )

# Comando /buscar
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != GROUP_ID:
        return  # Ignorar mensajes fuera del grupo

    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("⚠️ *Uso incorrecto:* `/buscar [palabra clave]`", parse_mode="Markdown")
        return

    await update.message.reply_text(f"🔎 *Buscando...* Por favor, espera un momento ⏳", parse_mode="Markdown")

    resultados = []
    for channel_id in CHANNEL_IDS:
        try:
            async for message in application.bot.get_chat_history(int(channel_id), limit=100):
                if message.text and keyword.lower() in message.text.lower():
                    resultados.append((channel_id, message.message_id, message.text[:100]))
        except Exception as e:
            logger.error(f"Error al obtener mensajes del canal {channel_id}: {e}")

    if not resultados:
        await update.message.reply_text("❌ *No se encontraron resultados.* Intenta con otra palabra clave.", parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton(f"📌 Mensaje {r[1]}", url=f"https://t.me/c/{r[0][4:]}/{r[1]}")]
        for r in resultados
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ *Resultados encontrados para:* `{keyword}` 📚\n\n"
        "📥 *Haz clic en los enlaces para ver los mensajes:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Configurar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("buscar", buscar))

# Configurar webhook correctamente
async def set_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    update = Update.de_json(request.get_json(), application.bot)
    loop.run_until_complete(application.process_update(update))
    return "OK", 200

if __name__ == "__main__":
    async def main():
        await application.initialize()
        await set_webhook()
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    asyncio.run(main())
