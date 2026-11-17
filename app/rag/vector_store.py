import chromadb
from app.config import settings
from app.rag.embeddings import embedding_manager
from app.utils.logger import logger

class VectorStoreManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.collection_name = "agent_documents"
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        try:
            embedding_model = embedding_manager.get_embeddings()
            embeddings = embedding_model.embed_documents(documents)
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully added {len(documents)} document chunks to vector store.")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise e

    def similarity_search(self, query: str, k: int = 4) -> list[dict]:
        try:
            embedding_model = embedding_manager.get_embeddings()
            query_embedding = embedding_model.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            formatted_results = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            
            for doc, meta in zip(docs, metas):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta
                })
            return formatted_results
        except Exception as e:
            logger.error(f"Error during vector similarity search: {str(e)}")
            return []

vector_store_manager = VectorStoreManager()