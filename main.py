import logging
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

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
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bienvenido al bot avanzado de búsqueda de EntresHijos!\n\nComandos disponibles:\n/start - Mostrar este mensaje\n/buscar [palabra clave] - Buscar contenido\n/listar - Listar tus contenidos guardados\n/eliminar [ID] - Eliminar un contenido específico")

# Comando /buscar
def buscar(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    keyword = " ".join(context.args).strip()

    if not keyword:
        update.message.reply_text("Uso: /buscar [palabra clave]")
        return

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, contenido FROM contenidos WHERE user_id = ? AND contenido LIKE ?", (user_id, f"%{keyword}%"))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        update.message.reply_text("No se encontraron resultados.")
        return

    keyboard = [[InlineKeyboardButton(f"{r[0]} - {r[1][:30]}", callback_data=str(r[0]))] for r in resultados]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Resultados encontrados:", reply_markup=reply_markup)

# Manejador de callbacks
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    contenido_id = query.data

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contenido FROM contenidos WHERE id = ?", (contenido_id,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        query.edit_message_text(text=f"Contenido completo: {resultado[0]}")
    else:
        query.edit_message_text(text="El contenido ya no está disponible.")

# Comando /listar
def listar(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, contenido FROM contenidos WHERE user_id = ?", (user_id,))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        update.message.reply_text("No tienes contenido guardado.")
        return

    mensaje = "\n".join([f"{r[0]}: {r[1][:30]}..." for r in resultados])
    update.message.reply_text(f"Tu contenido guardado:\n{mensaje}")

# Comando /eliminar
def eliminar(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Uso: /eliminar [ID]")
        return

    contenido_id = context.args[0]
    user_id = update.message.from_user.id

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contenidos WHERE id = ? AND user_id = ?", (contenido_id, user_id))
    conn.commit()
    conn.close()

    update.message.reply_text("Contenido eliminado correctamente.")

# Función principal
def main():
    init_db()
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("buscar", buscar))
    dp.add_handler(CommandHandler("listar", listar))
    dp.add_handler(CommandHandler("eliminar", eliminar))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
