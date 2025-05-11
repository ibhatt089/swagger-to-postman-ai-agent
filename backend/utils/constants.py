"""
Centralized constants and enums for the Swagger-to-Postman AI Agent solution.

Includes:
- LLM provider modes
- Document chunk types
- Prompt template keys
- Logging levels
- Directory paths
- Embedding & vector store settings
"""

from enum import Enum, IntEnum
from pathlib import Path
from typing import Final


# === Model Provider Modes ===

class LLMMode(str, Enum):
    """Supported LLM modes for the inference engine."""
    OPENAI = "openai"
    LOCAL_DEEPSEEK = "local_deepseek"
    TR_PLATFORM = "tr_platform"


# === Chunk Metadata Types ===

class ChunkType(str, Enum):
    """Chunk origin types for embedding metadata."""
    SWAGGER = "swagger"  # Legacy fallback
    POSTMAN = "postman"
    TEXT = "free_text"
    ENDPOINT_DESCRIPTION = "endpoint_description"
    PARAMETER = "parameter"
    REQUEST_BODY_SCHEMA = "request_body_schema"
    RESPONSE_SCHEMA = "response_schema"
    ENUM_TEST_CASE = "enum_test_case"
    BOOLEAN_FLAG_TEST_CASE = "boolean_flag_test_case"
    ERROR_CODE_CASE = "error_code_case"

    @classmethod
    def values(cls) -> list[str]:
        """
        Returns a list of all valid chunk type values.
        """
        return [str(member) for member in cls]

    @classmethod
    def value(cls) -> str:
        """
        Returns the string value of the enum instance.
        """
        return str(cls)


class FileType(str, Enum):
    """Supported input file types."""
    JSON = ".json"
    YAML = [".yaml", ".yml"]
    POSTMAN_COLLECTION = ".postman_collection.json"
    POSTMAN_ENVIRONMENT = ".postman_environment.json"


class PromptTemplateKey(str, Enum):
    """Keys to fetch prompt templates from the YAML template store."""
    SWAGGER_TO_TEST = "swagger_to_postman"
    SINGLE_ENDPOINT = "single_endpoint_test"
    MULTI_CASE_GENERATION = "multi_test_generation"


class VectorStoreCollections(str, Enum):
    """Named collections in ChromaDB for persistent embedding storage."""
    SWAGGER_EMBEDDINGS = "swagger_embeddings"
    POSTMAN_EMBEDDINGS = "postman_embeddings"
    GENERIC_TEXT_EMBEDDINGS = "text_embeddings"


# === Custom Logging Levels ===
class LogLevel(IntEnum):
    """Logging levels including custom SUCCESS level (25)."""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


# === Paths ===

DATA_DIR = Path("backend/data")
OUTPUT_DIR = Path("backend/output")
LOG_DIR = OUTPUT_DIR / "logs"
VECTOR_CACHE_DIR = DATA_DIR / "vector_cache"
SWAGGER_INPUT_DIR = DATA_DIR / "swagger"
POSTMAN_INPUT_DIR = DATA_DIR / "postman"
POSTMAN_OUTPUT_DIR = OUTPUT_DIR / "postman_collections"


# === Vector Store Settings ===

EMBEDDING_MODEL_NAME = "bge-large-en-v1.5"
CHROMA_COLLECTION_NAME = "swagger_postman_vectors"
CHROMA_PERSIST_DIR = VECTOR_CACHE_DIR.as_posix()

DEFAULT_LLM_MODEL = {
    LLMMode.OPENAI: "gpt-4o",
    LLMMode.LOCAL_DEEPSEEK: "deepseek-coder:6.7b-instruct",
    LLMMode.TR_PLATFORM: "anthropic.claude-v3.7-sonnet"
}

# File system paths or flags
DEFAULT_VECTOR_DB_PATH: Final[str] = "./backend/data/vector_cache"
DEFAULT_CHUNK_OVERLAP: Final[int] = 32
DEFAULT_CHUNK_SIZE: Final[int] = 512

# Metadata keys
METADATA_FIELD_ORIGIN: Final[str] = "chunk_origin"
METADATA_FIELD_FILENAME: Final[str] = "source_file"
METADATA_FIELD_TYPE: Final[str] = "chunk_type"
METADATA_FIELD_HASH: Final[str] = "hash_id"
