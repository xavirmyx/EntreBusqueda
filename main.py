import logging
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Verificar si SQLite está disponible
def check_sqlite():
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()[0]
        conn.close()
        logging.info(f"SQLite version: {version}")
    except Exception as e:
        logging.error(f"SQLite no está disponible: {e}")
        exit(1)

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Canales donde se buscará el contenido
CHANNEL_IDS = [
    "-1001918569531"  # Reemplaza con el ID correcto de los canales si es necesario
]

# Comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenido al bot avanzado de búsqueda de EntresHijos!\n\nComandos disponibles:\n/start - Mostrar este mensaje\n/buscar [palabra clave] - Buscar contenido\n/listar - Listar tus contenidos guardados\n/eliminar [ID] - Eliminar un contenido específico")

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
                    resultados.append((message.message_id, message.text[:100]))
        except Exception as e:
            logger.error(f"Error al obtener mensajes del canal {channel_id}: {e}")

    if not resultados:
        await update.message.reply_text("No se encontraron resultados.")
        return

    keyboard = [[InlineKeyboardButton(f"Mensaje {r[0]}", url=f"https://t.me/c/{channel_id[4:]}/{r[0]}")] for r in resultados]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Resultados encontrados:", reply_markup=reply_markup)

# Función principal
def main():
    check_sqlite()

    # Crear la aplicación de Telegram
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Agregar los manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buscar", buscar))

    # Ejecutar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
