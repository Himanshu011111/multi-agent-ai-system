import chromadb
from typing import List, Dict, Any
from app.config import settings
from app.rag.embeddings import embedding_manager
from app.utils.logger import logger


class VectorStoreManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_db_dir)
        self.collection_name = "agent_documents"
        # embedding_function=None prevents ChromaDB from loading heavy local ONNX models (~200MB saved)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
        )

    def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        try:
            embedding_model = embedding_manager.get_embeddings()
            embeddings = embedding_model.embed_documents(documents)

            try:
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
            except Exception as add_err:
                # Auto-reset collection if old 384-dim MiniLM vectors conflict with 768-dim Gemini vectors
                if "dimension" in str(add_err).lower():
                    logger.warning("Embedding dimension changed; resetting ChromaDB collection...")
                    self.client.delete_collection(name=self.collection_name)
                    self.collection = self.client.get_or_create_collection(
                        name=self.collection_name,
                        embedding_function=None,
                    )
                    self.collection.add(
                        documents=documents,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=ids,
                    )
                else:
                    raise add_err

            logger.info(f"Successfully added {len(documents)} document chunks to vector store.")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise e

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        try:
            embedding_model = embedding_manager.get_embeddings()
            query_embedding = embedding_model.embed_query(query)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
            )

            formatted_results = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]

            for doc, meta in zip(docs, metas):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                })
            return formatted_results
        except Exception as e:
            logger.error(f"Error during vector similarity search: {str(e)}")
            return []


vector_store_manager = VectorStoreManager()