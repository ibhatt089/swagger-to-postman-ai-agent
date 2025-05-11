"""
Embedding Engine for Swagger-to-Postman AI Agent

- Embeds Swagger YAML, Postman JSON, and free-text chunks
- Uses bge-large-en-v1.5 (or other configurable model)
- Integrates with EmbeddingCache to prevent redundant computation
- Compatible with ChromaDB and other vector stores
"""

from typing import List, Dict, Any
import torch
from sentence_transformers import SentenceTransformer

from backend.utils.logger import logger
from backend.utils.config import config
from backend.utils.constants import ChunkType
from backend.embeddings.embedding_cache import EmbeddingCache


class EmbeddingEngine:
    """
    Central embedding processor using sentence-transformers compatible models.

    Applies normalization, batching, caching, and device optimization (CPU/GPU).
    """

    def __init__(self):
        self.model_name = config.embedding_model_name
        self.batch_size = config.embedding_batch_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache = EmbeddingCache()

        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.success(f"✅ Embedding model loaded: {self.model_name} on {self.device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model [{self.model_name}]: {e}")

    def embed_texts(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embeds a batch of text chunks and returns enriched output with embeddings.
        Utilizes caching to avoid re-computation.

        Args:
            chunks (List[Dict]): List of chunks with 'id', 'type', and 'text'

        Returns:
            List[Dict]: Enriched chunks with 'embedding' field added
        """
        validated_chunks = []

        for chunk in chunks:
            if not all(k in chunk for k in ("id", "type", "text")):
                logger.warning(f"⚠️ Skipping invalid chunk: {chunk}")
                continue

            if chunk["type"] not in ChunkType.values():
                logger.warning(f"⚠️ Unknown chunk type '{chunk['type']}' in {chunk['id']}, defaulting to 'text'")
                chunk["type"] = ChunkType.TEXT

            validated_chunks.append(chunk)

        # Split into cached and new
        to_embed = []
        enriched_chunks = []

        for chunk in validated_chunks:
            cached = self.cache.get(chunk["text"], metadata={"type": chunk["type"]})
            if cached:
                logger.debug(f"🧠 Using cached embedding for chunk: {chunk['id']}")
                chunk["embedding"] = cached
                enriched_chunks.append(chunk)
            else:
                to_embed.append(chunk)

        # Embed new ones
        if to_embed:
            logger.info(f"🔄 Embedding {len(to_embed)} new chunks...")
            texts = [c["text"] for c in to_embed]
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            for i, chunk in enumerate(to_embed):
                vector = embeddings[i].tolist()
                chunk["embedding"] = vector
                enriched_chunks.append(chunk)
                self.cache.add(chunk["text"], vector, metadata={"type": chunk["type"]})

            logger.success("✅ New embeddings computed and cached.")

        return enriched_chunks
