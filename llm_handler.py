import os
from huggingface_hub import InferenceClient

class LLMHandler:
	def __init__(self):
		self.client = InferenceClient(token=os.getenv('HF_API_KEY'))
	
	def generate_response(self, prompt):
		return self.client.text_generation(
			prompt,
			model="mistralai/Mistral-7B-Instruct-v0.3",  # Modello gratuito
			max_new_tokens=150
	)