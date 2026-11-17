import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from langchain_community.embeddings import HuggingFaceEmbeddings
from app.utils.logger import logger

class EmbeddingManager:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self._embeddings = None

    def get_embeddings(self):
        if self._embeddings is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}...")
                self._embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {str(e)}")
                raise e
        return self._embeddings

embedding_manager = EmbeddingManager()