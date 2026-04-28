"""
Placeholder module for RAG document retrieval.
Will be integrated with a vector store (e.g. Chroma, Pinecone) in future iterations.
"""
from typing import List


class DocumentRetriever:
    """
    Placeholder retriever.
    Future implementation will query the configured VECTOR_STORE for relevant documents.
    """

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        raise NotImplementedError("Document retriever is not yet implemented.")
