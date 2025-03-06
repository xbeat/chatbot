# pinecone_handler.py
from dotenv import load_dotenv
import os
from pinecone import Pinecone
from typing import List, Dict, Optional

# Carica le variabili d'ambiente dal file .env
load_dotenv()

class PineconeManager:
    def __init__(self):
        # Configura Pinecone
        self.pc = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY")
        )
        self.index_name = os.getenv("PINECONE_INDEX", "telegram-rag")
        self.index = self.pc.Index(self.index_name)

    def ingest_pdf(self, filename: str = "mio_file.pdf", chunk_size: int = 1000) -> bool:
        """Carica un PDF dalla cartella docs, suddividendo il testo in chunk"""
        try:
            # Percorso completo del file
            import os
            filepath = os.path.join("docs", filename)

            # Converti il PDF in testo
            from PyPDF2 import PdfReader
            import io

            with open(filepath, "rb") as f:
                pdf_file = io.BytesIO(f.read())
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"

            # Suddividi il testo in chunk
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

            # Inserisci i chunk in Pinecone
            for i, chunk in enumerate(chunks):
                # Usa l'embedding integrato di Pinecone
                self.index.upsert(
                    vectors=[{
                        "id": f"doc1_chunk_{i}",  # ID univoco per il chunk
                        "values": [],  # Vettore vuoto (Pinecone gestisce l'embedding)
                        "metadata": {"text": chunk}
                    }],
                    namespace="pdf_content"
                )
            return True
        except Exception as e:
            print(f"Errore caricamento PDF: {str(e)}")
            return False

    def query_index(self, question: str, top_k: int = 3) -> List[str]:
        """Esegue una ricerca contestuale sui chunk"""
        try:
            # Usa un vettore placeholder di dimensione 1024
            query_vector = [0.0] * 1024  # Vettore di zeri (Pinecone gestisce l'embedding)

            # Esegui la query
            result = self.index.query(
                vector=query_vector,  # Vettore placeholder
                top_k=top_k,
                include_metadata=True,
                namespace="pdf_content"
            )

            # Debug: Stampa i risultati della query
            print(f"Risultati della query ({len(result.matches)} match trovati):")
            for match in result.matches:
                print(f"- ID: {match.id}, Punteggio: {match.score}, Testo: {match.metadata['text'][:100]}...")

            return [match.metadata["text"] for match in result.matches]
        except Exception as e:
            print(f"Errore ricerca Pinecone: {str(e)}")
            return []