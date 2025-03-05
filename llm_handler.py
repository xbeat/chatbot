import os
import google.generativeai as genai
from typing import List, Dict, Optional

class GeminiHandler:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro-002')  # Usa la versione più recente
        self.chat_sessions = {}

    def generate_response(self, chat_id: int, prompt: str, history: list = None) -> str:
        try:
            # Converti la cronologia nel formato richiesto da Gemini 1.5
            formatted_history = []
            for msg in (history or []):
                role = 'user' if msg['role'] == 'user' else 'model'
                formatted_history.append({'role': role, 'parts': [msg['content']]})
            
            # Crea una nuova chat se non esiste o se la cronologia è cambiata
            if chat_id not in self.chat_sessions:
                self.chat_sessions[chat_id] = self.model.start_chat(history=formatted_history)
            else:
                self.chat_sessions[chat_id].history = formatted_history
                
            response = self.chat_sessions[chat_id].send_message(prompt)
            return response.text

        except Exception as e:
            return f"⚠️ Errore: {str(e)}"