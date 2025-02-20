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

# Conexión a la base de datos
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contenidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            contenido TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenido al bot avanzado de búsqueda de EntresHijos!\n\nComandos disponibles:\n/start - Mostrar este mensaje\n/buscar [palabra clave] - Buscar contenido\n/listar - Listar tus contenidos guardados\n/eliminar [ID] - Eliminar un contenido específico")

# Comando /buscar
async def buscar(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    keyword = " ".join(context.args).strip()

    if not keyword:
        await update.message.reply_text("Uso: /buscar [palabra clave]")
        return

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, contenido FROM contenidos WHERE user_id = ? AND contenido LIKE ?", (user_id, f"%{keyword}%"))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        await update.message.reply_text("No se encontraron resultados.")
        return

    keyboard = [[InlineKeyboardButton(f"{r[0]} - {r[1][:30]}", callback_data=str(r[0]))] for r in resultados]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Resultados encontrados:", reply_markup=reply_markup)

# Manejador de callbacks
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    contenido_id = query.data

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contenido FROM contenidos WHERE id = ?", (contenido_id,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        await query.edit_message_text(text=f"Contenido completo: {resultado[0]}")
    else:
        await query.edit_message_text(text="El contenido ya no está disponible.")

# Comando /listar
async def listar(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, contenido FROM contenidos WHERE user_id = ?", (user_id,))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        await update.message.reply_text("No tienes contenido guardado.")
        return

    mensaje = "\n".join([f"{r[0]}: {r[1][:30]}..." for r in resultados])
    await update.message.reply_text(f"Tu contenido guardado:\n{mensaje}")

# Comando /eliminar
async def eliminar(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Uso: /eliminar [ID]")
        return

    contenido_id = context.args[0]
    user_id = update.message.from_user.id

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contenidos WHERE id = ? AND user_id = ?", (contenido_id, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text("Contenido eliminado correctamente.")

# Función principal
def main():
    check_sqlite()
    init_db()

    # Crear la aplicación de Telegram
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Agregar los manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buscar", buscar))
    application.add_handler(CommandHandler("listar", listar))
    application.add_handler(CommandHandler("eliminar", eliminar))
    application.add_handler(CallbackQueryHandler(button))

    # Ejecutar el bot
    application.run_polling()

if __name__ == "__main__":
    main()