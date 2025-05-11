"""
Vector Store Module for Swagger-to-Postman AI Agent

- Uses ChromaDB with duckdb+parquet backend
- SentenceTransformer embedding function: bge-large-en-v1.5
- Full support for add, upsert, clear, persist, query
- Handles custom metadata tagging (origin, filename, type, hash)
"""

from uuid import uuid4
from typing import List, Dict, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from backend.utils.logger import logger
from backend.utils.constants import (
    VectorStoreCollections,
    DEFAULT_VECTOR_DB_PATH,
    EMBEDDING_MODEL_NAME,
    METADATA_FIELD_FILENAME,
    METADATA_FIELD_ORIGIN,
    METADATA_FIELD_TYPE,
    METADATA_FIELD_HASH,
)


class VectorStore:
    """
    Wrapper for ChromaDB persistent vector store with semantic embeddings.

    Responsibilities:
    - Collection creation
    - Add/Upsert documents
    - Similarity query
    - Full persistence
    """

    def __init__(self, persist_directory: str = DEFAULT_VECTOR_DB_PATH):
        """
        Initializes the ChromaDB client with embedding function and persistence.
        """
        self.persist_directory = persist_directory
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.persist_directory
        ))
        self.embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        self._collections: Dict[str, Collection] = {}

        logger.success(f"✅ Initialized VectorStore at: {self.persist_directory}")

    def _load_or_create_collection(self, name: VectorStoreCollections) -> Collection:
        """
        Loads a ChromaDB collection or creates it if not found.

        Args:
            name (VectorStoreCollections): Enum collection name.

        Returns:
            Collection: ChromaDB collection instance.
        """
        name_str = name.value
        if name_str not in self._collections:
            logger.info(f"📦 Creating/loading collection: {name_str}")
            self._collections[name_str] = self.client.get_or_create_collection(
                name=name_str,
                embedding_function=self.embedding_function
            )
        return self._collections[name_str]

    def get_collection(self, name: VectorStoreCollections) -> Collection:
        """
        External accessor for a loaded collection.

        Args:
            name (VectorStoreCollections): Enum collection name.

        Returns:
            Collection: Loaded collection.
        """
        return self._load_or_create_collection(name)

    def add_documents(
        self,
        collection_name: VectorStoreCollections,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, str]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Adds precomputed embeddings with documents to vector store.

        Args:
            collection_name (VectorStoreCollections): Target collection.
            documents (List[str]): Raw texts.
            embeddings (List[List[float]]): Corresponding embeddings.
            metadatas (Optional[List[Dict]]): Metadata tags.
            ids (Optional[List[str]]): Optional UUIDs.
        """
        if len(documents) != len(embeddings):
            raise ValueError("Mismatch: documents and embeddings count.")

        ids = ids or [str(uuid4()) for _ in documents]
        if len(ids) != len(documents):
            raise ValueError("Mismatch: documents and IDs count.")

        enriched_metadatas = []
        for i, doc in enumerate(documents):
            base_meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            enriched_metadatas.append({
                METADATA_FIELD_TYPE: base_meta.get(METADATA_FIELD_TYPE, "text"),
                METADATA_FIELD_ORIGIN: base_meta.get(METADATA_FIELD_ORIGIN, "unknown"),
                METADATA_FIELD_FILENAME: base_meta.get(METADATA_FIELD_FILENAME, "unknown"),
                METADATA_FIELD_HASH: base_meta.get(METADATA_FIELD_HASH, str(uuid4())),
                **base_meta
            })

        collection = self._load_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=enriched_metadatas,
            ids=ids
        )

        logger.success(f"✅ Added {len(documents)} documents to collection: {collection_name.value}")

    def upsert_embeddings(
        self,
        collection_name: VectorStoreCollections,
        documents: List[str],
        metadatas: Optional[List[Dict[str, str]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Computes embeddings and upsert documents.

        Args:
            collection_name (VectorStoreCollections): Target collection.
            documents (List[str]): Raw texts.
            metadatas (Optional[List[Dict]]): Metadata tags.
            ids (Optional[List[str]]): Optional UUIDs.
        """
        if not documents:
            logger.warning("⚠️ No documents provided for upsert.")
            return

        ids = ids or [str(uuid4()) for _ in documents]
        if len(ids) != len(documents):
            raise ValueError("Mismatch: documents and IDs count.")

        enriched_metadatas = []
        for i, doc in enumerate(documents):
            base_meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            enriched_metadatas.append({
                METADATA_FIELD_TYPE: base_meta.get(METADATA_FIELD_TYPE, "text"),
                METADATA_FIELD_ORIGIN: base_meta.get(METADATA_FIELD_ORIGIN, "unknown"),
                METADATA_FIELD_FILENAME: base_meta.get(METADATA_FIELD_FILENAME, "unknown"),
                METADATA_FIELD_HASH: base_meta.get(METADATA_FIELD_HASH, str(uuid4())),
                **base_meta
            })

        embeddings = self.embedding_function(documents)
        collection = self._load_or_create_collection(collection_name)

        collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=enriched_metadatas,
            ids=ids
        )
        logger.success(f"🔁 Successful upsert of {len(documents)} documents into: {collection_name.value}")

    def query_similar(
        self,
        collection_name: VectorStoreCollections,
        query_texts: List[str],
        n_results: int = 5
    ) -> List[Dict]:
        """
        Performs semantic similarity search against stored vectors.

        Args:
            collection_name (VectorStoreCollections): Target collection.
            query_texts (List[str]): Input queries.
            n_results (int): Top-N results.

        Returns:
            List[Dict]: Matches for each query.
        """
        collection = self._load_or_create_collection(collection_name)
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        for i, query in enumerate(query_texts):
            matches = []
            for j in range(len(results["documents"][i])):
                matches.append({
                    "id": results["ids"][i][j],
                    "document": results["documents"][i][j],
                    "metadata": results["metadatas"][i][j],
                    "distance": results["distances"][i][j]
                })
            output.append({"query": query, "matches": matches})

        return output

    def clear(self, collection_name: VectorStoreCollections) -> None:
        """
        Clears all documents from the collection (soft delete).

        Args:
            collection_name (VectorStoreCollections): Target collection.
        """
        collection = self._load_or_create_collection(collection_name)
        collection.delete(where={})
        logger.warning(f"🧨 Cleared collection: {collection_name.value}")

    def reset_collection(self, collection_name: VectorStoreCollections) -> None:
        """
        Destroys and recreates a fresh collection.

        Args:
            collection_name (VectorStoreCollections): Target collection.
        """
        logger.warning(f"♻️ Resetting collection: {collection_name.value}")
        self.client.delete_collection(name=collection_name.value)
        self._collections.pop(collection_name.value, None)

    def list_collections(self) -> List[str]:
        """
        Lists all current vector collections.

        Returns:
            List[str]: Collection names.
        """
        return [col.name for col in self.client.list_collections()]

    def size(self, collection_name: VectorStoreCollections) -> int:
        """
        Returns number of documents in a collection.

        Args:
            collection_name (VectorStoreCollections): Target collection.

        Returns:
            int: Count of documents.
        """
        collection = self._load_or_create_collection(collection_name)
        return collection.count()
