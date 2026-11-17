from app.rag.vector_store import vector_store_manager
from app.services.llm_service import llm_service
from app.utils.logger import logger

class RAGRetriever:
    def answer_query(self, query: str) -> dict:
        retrieved_docs = vector_store_manager.similarity_search(query, k=4)
        
        if not retrieved_docs:
            return {
                "answer": "No relevant documents found in the vector store.",
                "sources": []
            }
            
        context = "\n\n".join([doc["content"] for doc in retrieved_docs])
        sources = list(set([doc["metadata"].get("filename", "Unknown") for doc in retrieved_docs]))
        
        prompt = f"""You are an expert AI research assistant. Answer the user's question based strictly on the provided context. Include source references.

Context:
{context}

Question: {query}

Answer:"""

        answer = llm_service.generate_text(prompt, system_instruction="You are a precise RAG QA assistant.")
        
        return {
            "answer": answer,
            "sources": sources
        }

rag_retriever = RAGRetriever()