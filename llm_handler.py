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

	def generate_response(self, chat_id: int, prompt: str, history: list = None) -> str:
		try:
			# STEP 1: Genera la risposta con il modello LLM
			if chat_id not in self.chat_sessions:
				self.chat_sessions[chat_id] = self.model.start_chat(history=[])
			
			response = self.chat_sessions[chat_id].send_message(prompt)

			# STEP 2: Ricerca contestuale in Pinecone (sempre eseguita)
			context_chunks = self.rag.query_index(prompt)
			context = "\n\n".join(context_chunks)  # Unisci i chunk trovati

			# STEP 3: Costruzione della risposta finale
			if context:
				return f"🤖 **Risposta LLM:**\n{response.text}\n\n📚 **Contesto da Pinecone:**\n{context}"
			else:
				return f"🤖 **Risposta LLM:**\n{response.text}\n\n📚 **Nessun contesto rilevante trovato.**"

		except Exception as e:
			return f"⚠️ Errore RAG: {str(e)}"            