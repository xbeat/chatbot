from dotenv import load_dotenv
import os
import pinecone
from pinecone import ServerlessSpec
from PyPDF2 import PdfReader
from typing import List
import time
import random

load_dotenv()

class PineconeManager:
    def __init__(self):
        # Inizializzazione client Pinecone v6
        self.pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX", "telegram-rag")
        self._setup_index()

    def _setup_index(self):
        """Configura l'indice per il modello llama-text-embed-v2"""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            time.sleep(20)  # Attesa per la propagazione dell'indice
        self.index = self.pc.Index(self.index_name)

    def _get_embedding(self, text: str, is_query: bool = False):
        """Genera embedding usando l'API Inference"""
        try:
            if not text.strip():
                raise ValueError("Testo vuoto")

            # Utilizza l'endpoint inference
            response = self.pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[text.strip()],
                parameters={
                    "input_type": "query" if is_query else "passage",
                    "truncate": "END"
                }
            )

            embedding = response.data[0].values

            if all(abs(v) < 0.0001 for v in embedding):
                raise ValueError("Embedding non valido")

            return embedding

        except Exception as e:
            print(f"ERRORE EMBEDDING: {str(e)} - Testo: '{text[:50]}'...")
            return [random.gauss(0, 0.01) for _ in range(1024)]

    def ingest_pdf(self, filename: str, chunk_size: int = 1024) -> bool:
        try:
            filepath = os.path.join("docs", filename)
            
            # Estrazione testo da PDF
            with open(filepath, "rb") as f:
                reader = PdfReader(f)
                text = "".join(page.extract_text() or "\n" for page in reader.pages)

            # Pulizia e suddivisione in chunk
            chunks = [text[i:i+chunk_size].strip() for i in range(0, len(text), chunk_size)]
            chunks = [chunk for chunk in chunks if chunk and len(chunk) > 50]  # Filtra chunk troppo corti

            if not chunks:
                raise ValueError("Nessun contenuto testuale valido nel PDF")

            # Elaborazione a batch
            batch_size = 50  # Ottimizzato per performance
            total_batches = (len(chunks) + batch_size - 1) // batch_size

            for batch_num, i in enumerate(range(0, len(chunks), batch_size), 1):
                batch_chunks = chunks[i:i+batch_size]
                vectors = []
                
                for j, chunk in enumerate(batch_chunks):
                    chunk_id = f"{filename[:15]}_chunk_{i+j}"
                    embedding = self._get_embedding(chunk)
                    
                    vectors.append({
                        "id": chunk_id,
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "source": filename
                        }
                    })

                if vectors:
                    self.index.upsert(
                        vectors=vectors,
                        namespace="legal_docs"  # Namespace specifico
                    )
                    print(f"Batch {batch_num}/{total_batches} elaborato ({len(vectors)} vettori)")

                # Ritardo tra batch per evitare rate limiting
                time.sleep(0.3)

            return True
            
        except Exception as e:
            print(f"ERRORE GLOBALE: {str(e)}")
            return False

    # pinecone_handler.py (versione corretta)
    def query_index(self, question: str, top_k: int = 5) -> List[str]:
        try:
            # 1. Genera l'embedding della query
            query_embedding = self._get_embedding(question, is_query=True)
            
            # 2. Esegui la query senza filtri aggiuntivi
            result = self.index.query(
                vector=query_embedding,
                namespace="legal_docs",
                top_k=top_k,
                include_metadata=True
            )

            # 3. Log di debug
            print(f"\n🔍 DEBUG QUERY:")
            print(f"Query: '{question}'")
            print(f"Risultati grezzi: {len(result.matches)}")
            print(f"Scores: {[m.score for m in result.matches]}")

            # 4. Filtra e formatta i risultati
            return [{
                "text": match.metadata["text"],
                "score": match.score,
                "source": match.metadata.get("source", "sconosciuto")
            } for match in result.matches if match.score > 0.3]

        except Exception as e:
            print(f"ERRORE QUERY: {str(e)}")
            return []