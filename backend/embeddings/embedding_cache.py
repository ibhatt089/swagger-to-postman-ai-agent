"""
Embedding Cache Module

- Prevents redundant embedding computation
- Supports metadata-aware hashing
- Provides persistent caching using JSON
- Multiprocessing-safe with file locks
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, List
from filelock import FileLock


class EmbeddingCache:
    """
    A persistent + in-memory cache for storing text embeddings.
    Caches are hashed based on text + optional metadata, to avoid collisions
    between Swagger/Postman chunks that have same surface text but different source.

    Uses:
    - SHA-256 based deduplication
    - Persistent disk cache (index.json)
    - File locking to ensure multiprocessing safety
    """

    def __init__(self, cache_dir: str = "backend/data/vector_cache/.embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.cache_dir / "index.json"
        self.lock_file = self.cache_dir / "index.lock"
        self._cache: Dict[str, List[float]] = self._load_index()

    def _load_index(self) -> Dict[str, List[float]]:
        if not self.index_file.exists():
            return {}

        try:
            with FileLock(str(self.lock_file), timeout=10):
                with self.index_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, TimeoutError):
            return {}

    def _save_index(self) -> None:
        with FileLock(str(self.lock_file), timeout=10):
            with self.index_file.open("w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)

    @staticmethod
    def _compute_hash(text: str, metadata: Optional[Dict] = None) -> str:
        """
        Returns SHA-256 hash of the input text + metadata.
        """
        normalized = {
            "text": text.strip(),
            "metadata": metadata or {}
        }
        encoded = json.dumps(normalized, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get(self, text: str, metadata: Optional[Dict] = None) -> Optional[List[float]]:
        """
        Retrieves an embedding from the cache if available.

        Args:
            text (str): The text content to retrieve.
            metadata (Optional[Dict]): Optional metadata affecting uniqueness.

        Returns:
            Optional[List[float]]: The cached embedding, if found.
        """
        key = self._compute_hash(text, metadata)
        return self._cache.get(key)

    def add(self, text: str, embedding: List[float], metadata: Optional[Dict] = None) -> None:
        """
        Adds a new embedding to the cache and persists it.

        Args:
            text (str): Original input text.
            embedding (List[float]): Corresponding embedding vector.
            metadata (Optional[Dict]): Optional hash-affecting metadata.
        """
        key = self._compute_hash(text, metadata)
        self._cache[key] = embedding
        self._save_index()

    def clear(self) -> None:
        """
        Clears the in-memory and on-disk cache.
        """
        self._cache.clear()
        if self.index_file.exists():
            self.index_file.unlink()

    def size(self) -> int:
        """
        Returns the number of cached entries.
        """
        return len(self._cache)
