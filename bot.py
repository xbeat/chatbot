import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from database import Database
from llm_handler import LLMHandler

class TelegramBot:
    def __init__(self):
        self.db = Database()
        self.llm = LLMHandler()
        self.app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
        
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, _):
        await update.message.reply_text("Benvenuto! Sono un bot intelligente, chiedimi qualsiasi cosa!")
    
    async def handle_message(self, update: Update, _):
        user_id = update.message.from_user.id
        user_message = update.message.text
        
        response = self.llm.generate_response(user_message)
        self.db.save_message(user_id, user_message, response)
        
        await update.message.reply_text(response)
    
    def run(self):
        self.app.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()