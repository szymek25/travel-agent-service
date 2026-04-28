"""
Placeholder module for embedding generation.
Will be integrated with a vector store and LLM provider in future iterations.
"""
from typing import List


class EmbeddingService:
    """
    Placeholder embedding service.
    Future implementation will use the configured LLM_PROVIDER to generate embeddings.
    """

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError("Embedding service is not yet implemented.")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Batch embedding service is not yet implemented.")
