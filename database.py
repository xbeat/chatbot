import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
    
    def save_message(self, user_id, message, response):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_history (user_id, message, response) VALUES (%s, %s, %s)",
                (user_id, message, response)
            )
            self.conn.commit()