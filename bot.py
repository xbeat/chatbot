import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from database import Database
from llm_handler import LLMHandler
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione server web per Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot Telegram attivo e funzionante!"

def run_server():
    app.run(host='0.0.0.0', port=10000)

class TelegramBot:
    def __init__(self):
        self.db = Database()
        self.llm = LLMHandler()
        self.app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
        
        # Registra gli handler
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, _):
        await update.message.reply_text("Ciao! Sono il tuo assistente virtuale. Chiedimi qualsiasi cosa!")

    async def handle_message(self, update: Update, _):
        user_id = update.message.from_user.id
        user_message = update.message.text
        
        try:
            response = self.llm.generate_response(user_message)
            self.db.save_message(user_id, user_message, response)
            await update.message.reply_text(response)
        except Exception as e:
            await update.message.reply_text("❌ Si è verificato un errore. Riprova più tardi.")
            print(f"Errore: {e}")

    def run(self):
        self.app.run_polling()

if __name__ == "__main__":
    # Avvia il server web solo in produzione
    if os.getenv('RENDER'):
        threading.Thread(target=run_server, daemon=True).start()
    
    # Avvia il bot Telegram
    bot = TelegramBot()
    bot.run()