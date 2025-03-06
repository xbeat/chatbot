import os
import google.generativeai as genai
from typing import List, Dict, Optional
from pinecone_handler import PineconeManager

class GeminiHandler:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro-002')
        self.chat_sessions = {}
        self.rag = PineconeManager()  # Aggiungi questa linea

    # llm_handler.py - Modifica al metodo generate_response
    def generate_response(self, chat_id: int, prompt: str, history: list = None) -> str:
        try:
            # Genera risposta LLM
            if chat_id not in self.chat_sessions:
                self.chat_sessions[chat_id] = self.model.start_chat(history=[])
            
            response = self.chat_sessions[chat_id].send_message(prompt)

            # Ricerca Pinecone
            context_results = self.rag.query_index(prompt)
            
            # Formattazione avanzata risultati
            context_str = ""
            if context_results:
                context_str += "\n\n📚 **Contesto rilevante:**"
                for i, result in enumerate(context_results, 1):
                    context_str += f"\n\n▸ **Risultato {i}** (affidabilità: {result['score']:.2f})\n"
                    context_str += f"_{result['source']}_\n{result['text'][:250]}..."
            else:
                context_str = "\n\n⚠️ Nessun risultato contestuale trovato"

            return f"🤖 **Risposta AI:**\n{response.text}{context_str}"

        except Exception as e:
            return f"⚠️ Errore: {str(e)}"        