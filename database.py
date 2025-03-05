# database.py
import os
import json
import psycopg2
from typing import Dict, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class Database:
	def __init__(self):
		self.conn = self._connect()
		self._init_tables()
	
	def _connect(self):
		"""Gestisce la connessione per ambiente locale e Render"""
		if os.getenv('RENDER'):
			# Modalità produzione (Render)
			db_url = urlparse(os.getenv('DATABASE_URL'))
			return psycopg2.connect(
				dbname=db_url.path[1:],
				user=db_url.username,
				password=db_url.password,
				host=db_url.hostname,
				port=db_url.port,
				sslmode='require'
			)
		else:
			# Modalità sviluppo locale
			return psycopg2.connect(
				host=os.getenv('DB_HOST'),
				database=os.getenv('DB_NAME'),
				user=os.getenv('DB_USER'),
				password=os.getenv('DB_PASSWORD')
			)

	def _init_tables(self):
		"""Crea le tabelle se non esistono"""
		with self.conn.cursor() as cur:
			# Tabella sessioni
			cur.execute("""
				CREATE TABLE IF NOT EXISTS chat_sessions (
					user_id BIGINT PRIMARY KEY,
					history JSONB NOT NULL,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				)
			""")
			
			# Tabella cronologia messaggi
			cur.execute("""
				CREATE TABLE IF NOT EXISTS message_history (
					id SERIAL PRIMARY KEY,
					user_id BIGINT NOT NULL,
					message TEXT NOT NULL,
					response TEXT NOT NULL,
					timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				)
			""")
			self.conn.commit()

	# --- Gestione Sessioni ---
	def init_user_session(self, user_id: int):
		with self.conn.cursor() as cur:
			cur.execute("""
				INSERT INTO chat_sessions (user_id, history)
				VALUES (%s, '[]'::JSONB)
				ON CONFLICT (user_id) DO NOTHING
			""", (user_id,))
			self.conn.commit()

	def get_session(self, user_id: int) -> dict:
	    """Restituisce la sessione in formato corretto"""
	    with self.conn.cursor() as cur:
	        cur.execute("""
	            SELECT history FROM chat_sessions
	            WHERE user_id = %s
	        """, (user_id,))
	        result = cur.fetchone()
	    
	    # Converti direttamente il JSONB di PostgreSQL
	    return {
	        'history': result[0] if result else [],  # Rimossa la deserializzazione
	        'metadata': {}
    }

	def save_session(self, user_id: int, session_data: Dict):
	    """Serializza correttamente i dati per PostgreSQL"""
	    with self.conn.cursor() as cur:
	        cur.execute("""
	            INSERT INTO chat_sessions (user_id, history)
	            VALUES (%s, %s::JSONB)
	            ON CONFLICT (user_id) 
	            DO UPDATE SET history = EXCLUDED.history
	        """, (user_id, json.dumps(session_data['history'])))  # Serializza esplicitamente
	        self.conn.commit()

	def clear_session(self, user_id: int):
		with self.conn.cursor() as cur:
			cur.execute("""
				DELETE FROM chat_sessions
				WHERE user_id = %s
			""", (user_id,))
			self.conn.commit()

	# --- Cronologia Messaggi (Vecchio metodo mantenuto per retrocompatibilità) ---
	def save_message(self, user_id: int, message: str, response: str):
		"""Vecchio metodo mantenuto per transizione"""
		final_response = response.strip().replace("'", "''")
		with self.conn.cursor() as cur:
			# Salva nella nuova tabella
			cur.execute("""
				INSERT INTO message_history (user_id, message, response)
				VALUES (%s, %s, %s)
			""", (user_id, message, final_response))
			self.conn.commit()

	# --- Metodi aggiuntivi per nuova funzionalità ---
	def log_message(self, user_id: int, message: str, response: str):
	    with self.conn.cursor() as cur:
	        # Assicurati che la tabella message_history esista
	        cur.execute("""
	            INSERT INTO message_history (user_id, message, response)
	            VALUES (%s, %s, %s)
	        """, (user_id, message, response))
	        self.conn.commit()

	def __del__(self):
		"""Chiude la connessione alla distruzione dell'oggetto"""
		if self.conn and not self.conn.closed:
			self.conn.close()