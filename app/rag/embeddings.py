import google.generativeai as genai
from typing import List
from app.config import settings
from app.utils.logger import logger

try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    class Embeddings:  # type: ignore
        pass


class GeminiAPIEmbeddings(Embeddings):
    """
    Lightweight cloud-based Gemini API embeddings.
    Eliminates heavy PyTorch/HuggingFace RAM overhead (~400MB saved on Render).
    """

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model_name = self._detect_embedding_model()
        logger.info(f"Initialized lightweight Gemini API Embeddings: {self.model_name}")

    def _detect_embedding_model(self) -> str:
        try:
            for m in genai.list_models():
                methods = getattr(m, "supported_generation_methods", [])
                if "embedContent" in methods:
                    return m.name
        except Exception as e:
            logger.warning(f"Could not auto-list embedding models: {str(e)}")
        return "models/text-embedding-004"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            clean_text = (text or " ").strip()[:8000]
            res = genai.embed_content(
                model=self.model_name,
                content=clean_text,
                task_type="retrieval_document",
            )
            vectors.append(res["embedding"])
        return vectors

    def embed_query(self, text: str) -> List[float]:
        clean_text = (text or " ").strip()[:8000]
        res = genai.embed_content(
            model=self.model_name,
            content=clean_text,
            task_type="retrieval_query",
        )
        return res["embedding"]


class EmbeddingManager:
    def __init__(self):
        self._embeddings = None

    def get_embeddings(self):
        if self._embeddings is None:
            try:
                if not settings.gemini_api_key:
                    raise ValueError("GEMINI_API_KEY is not configured for embeddings.")
                self._embeddings = GeminiAPIEmbeddings(api_key=settings.gemini_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API embeddings: {str(e)}")
                raise e
        return self._embeddings


embedding_manager = EmbeddingManager()