import os
from huggingface_hub import InferenceClient

class LLMHandler:
	def __init__(self):
		self.client = InferenceClient(token=os.getenv('HF_API_KEY'))
	
	# In llm_handler.py
	def generate_response(self, prompt):
		raw_response = self.client.text_generation(
			prompt,
			model="mistralai/Mistral-7B-Instruct-v0.3",  # Modello gratuito
			max_new_tokens=750,  # Aumentato da 150 a 750
			truncate=500  # Taglia il prompt se supera 500 token
		)
		# Pulizia aggressiva della risposta
		cleaned_response = raw_response.strip().lstrip('�').lstrip(' ')  # Rimuove spazi e caratteri invisibili
		#return cleaned_response[:2000]  # Limite di sicurezza
		return cleaned_response