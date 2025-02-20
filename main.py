import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Canales donde se buscará el contenido
CHANNEL_IDS = [
    "-1001918569531",  # ID del primer canal
    "-1001918569531"   # ID del segundo canal (cambia según corresponda)
]

# Comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Bienvenido al bot avanzado de búsqueda de EntresHijos!\n\n"
        "Comandos disponibles:\n"
        "/start - Mostrar este mensaje\n"
        "/buscar [palabra clave] - Buscar contenido en los canales"
    )

# Comando /buscar
async def buscar(update: Update, context: CallbackContext):
    keyword = " ".join(context.args).strip()

    if not keyword:
        await update.message.reply_text("Uso: /buscar [palabra clave]")
        return

    resultados = []
    for channel_id in CHANNEL_IDS:
        try:
            async for message in context.bot.get_chat_history(channel_id, limit=100):
                if message.text and keyword.lower() in message.text.lower():
                    resultados.append((channel_id, message.message_id, message.text[:100]))
        except Exception as e:
            logger.error(f"Error al obtener mensajes del canal {channel_id}: {e}")

    if not resultados:
        await update.message.reply_text("No se encontraron resultados.")
        return

    keyboard = [
        [InlineKeyboardButton(f"Mensaje {r[1]}", url=f"https://t.me/c/{r[0][4:]}/{r[1]}")]
        for r in resultados
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Resultados encontrados:", reply_markup=reply_markup)

# Función principal
def main():
    # Crear la aplicación de Telegram
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Agregar los manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buscar", buscar))

    # Ejecutar el bot
    application.run_polling()

if __name__ == "__main__":
    main()