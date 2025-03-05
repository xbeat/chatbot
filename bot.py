import os
import logging
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from telegram import Update
from telegram.ext import (
	Application,
	MessageHandler,
	filters,
	CommandHandler,
	ContextTypes,
	CallbackContext
)
from database import Database
from llm_handler import GeminiHandler

# Configurazione logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()
		self.wfile.write(b'OK')

class HealthServer:
	def __init__(self, port=10000):
		self.port = port
		self.server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
		self.thread = Thread(target=self.server.serve_forever)

	def start(self):
		self.thread.start()
		logger.info(f"Health check server avviato su porta {self.port}")

	def stop(self):
		self.server.shutdown()
		self.thread.join()
		logger.info("Health check server fermato")

class TelegramBot:
	def __init__(self):
		self.db = Database()
		self.llm = GeminiHandler()
		self.health_server = HealthServer() if os.getenv('RENDER') else None
		self.app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
		
		# Registra handler
		self.app.add_handler(CommandHandler("start", self.start))
		self.app.add_handler(CommandHandler("clear", self.clear_history))
		self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""Gestisce il comando /start"""
		user = update.effective_user
		await update.message.reply_text(
			f"Ciao {user.first_name}! Sono il tuo assistente IA.\n"
			"Scrivi /clear per resettare la conversazione."
		)
		self.db.init_user_session(user.id)

	async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		"""Resetta la cronologia conversazione"""
		user_id = update.message.from_user.id
		self.db.clear_session(user_id)
		await update.message.reply_text("✅ Cronologia resettata")

	async def handle_message(self, update: Update, context: CallbackContext):
		"""Gestisce i messaggi degli utenti"""
		user = update.effective_user
		message = update.message.text
		
		try:
			session = self.db.get_session(user.id)

			# Se la sessione non esiste, creane una nuova
			if not session:
				logger.info(f"Creazione nuova sessione per l'utente {user.id}")
				self.db.init_user_session(user.id)
				session = {'history': []}  # Struttura predefinita

			response = self.llm.generate_response(
			    chat_id=user.id,
			    prompt=message,
			    history=session['history']  # Passa direttamente la lista
			)
			
			new_history = session.get('history', []) + [
				{"role": "user", "content": message},
				{"role": "assistant", "content": response}
			]
			
			self.db.save_session(user.id, {
				"history": new_history[-10:],
				"metadata": {
					"last_interaction": str(update.message.date),
					"message_count": session.get('message_count', 0) + 1
				}
			})
			
			await update.message.reply_text(response)

		except Exception as e:
			logger.error(f"Errore: {str(e)}", exc_info=True)
			await update.message.reply_text("⚠️ Si è verificato un errore. Riprova più tardi.")

	def run(self):
		"""Avvia il bot"""
		if self.health_server:
			self.health_server.start()
			
		self.app.run_polling(
			allowed_updates=Update.ALL_TYPES,
			drop_pending_updates=True
		)

if __name__ == "__main__":
	from dotenv import load_dotenv
	load_dotenv()

	bot = TelegramBot()
	try:
		bot.run()
	finally:
		if bot.health_server:
			bot.health_server.stop()