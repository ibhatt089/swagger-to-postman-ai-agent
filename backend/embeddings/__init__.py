"""
Embeddings Package Init

This package handles:
- Text embedding using transformer models
- Embedding cache management (prevent re-computation)
- Vector DB operations (ChromaDB with DuckDB backend)

Exposed Classes:
- EmbeddingEngine
- EmbeddingCache
- VectorStore
"""

from backend.embeddings.embedding_engine import EmbeddingEngine
from backend.embeddings.embedding_cache import EmbeddingCache
from backend.embeddings.vector_store import VectorStore

__all__ = [
    "EmbeddingEngine",
    "EmbeddingCache",
    "VectorStore"
]
