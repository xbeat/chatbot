# database.py
import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv('.env')  # Per sviluppo locale

class Database:
	def __init__(self):
		if os.getenv('RENDER'):
			# Modalità Render (produzione)
			db_url = urlparse(os.getenv('DATABASE_URL'))
			self.conn = psycopg2.connect(
				dbname=db_url.path[1:],
				user=db_url.username,
				password=db_url.password,
				host=db_url.hostname,
				port=db_url.port,
				sslmode='require'
			)
		else:
			# Modalità locale
			self.conn = psycopg2.connect(
				host=os.getenv('DB_HOST'),
				database=os.getenv('DB_NAME'),
				user=os.getenv('DB_USER'),
				password=os.getenv('DB_PASSWORD')
			)
	
	# In database.py
	def save_message(self, user_id, message, response):
		# Pulizia finale prima del salvataggio
		final_response = response.strip().replace("'", "''")  # Escape apici per SQL
		
		with self.conn.cursor() as cur:
			cur.execute(
				"INSERT INTO chat_history (user_id, message, response) VALUES (%s, %s, %s)",
				(user_id, message, final_response)
			)
			self.conn.commit()            