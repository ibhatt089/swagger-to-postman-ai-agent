# backend/utils/config.py

"""
Configuration manager for the Swagger-to-Postman AI Agent.

Features:
- Loads structured config from backend/config/config.yaml
- Overrides values using .env (secure secrets)
- Provides validated, unified AppConfig object
- Supports UI- and CLI-level access to all runtime settings
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from dotenv import load_dotenv

from backend.utils.constants import (
    LLMMode,
    EMBEDDING_MODEL_NAME,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR
)

# === Paths ===
DOTENV_PATH = Path(".env")
YAML_CONFIG_PATH = Path("./backend/config/config.yaml")

# Load environment variables (highest precedence)
load_dotenv(DOTENV_PATH)


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse YAML config: {e}")


class AppConfig:
    """
    Unified runtime configuration loader with ENV override support.

    Priority Order:
    1. .env file
    2. config.yaml file
    3. Internal default
    """

    def __init__(self):
        # === Load from YAML first ===
        self.yaml_config = _load_yaml_config(YAML_CONFIG_PATH)

        # === Apply values with fallback priority ===
        self.llm_mode: LLMMode = LLMMode(self._get("LLM_MODE", LLMMode.OPENAI))

        # API keys
        self.openai_api_key: Optional[str] = self._get("OPENAI_API_KEY")
        self.tr_access_token: Optional[str] = self._get("TR_AUTH_TOKEN")

        # Model selection
        self.default_openai_model: str = self._get("OPENAI_MODEL", "gpt-4o")
        self.default_deepseek_model: str = self._get("LOCAL_MODEL", "deepseek-coder:6.7b-instruct")
        self.default_tr_model: str = self._get("TR_MODEL", "anthropic.claude-v3.7-sonnet")

        # Embedding
        self.embedding_model_name: str = self._get("EMBEDDING_MODEL", EMBEDDING_MODEL_NAME)
        self.embedding_batch_size: int = int(self._get("EMBEDDING_BATCH_SIZE", 8))

        # Vector store
        self.vector_store_path: str = self._get("CHROMA_PERSIST_DIR", CHROMA_PERSIST_DIR)
        self.vector_collection_name: str = self._get("CHROMA_COLLECTION", CHROMA_COLLECTION_NAME)

        # Logging
        self.log_level: str = self._get("AGENT_LOG_LEVEL", "INFO")

        # Multiprocessing
        self.max_parallel_processes: int = int(self._get("MAX_PARALLEL_PROCESSES", os.cpu_count() or 4))

    def _get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Load value from ENV or YAML config, falling back to default.

        Args:
            key (str): Configuration key name.
            default (Optional[Any]): Default fallback value.

        Returns:
            Any: Loaded or default value.
        """
        return os.getenv(key) or self.yaml_config.get(key) or default

    def as_dict(self) -> Dict[str, Any]:
        """
        Serializes the active config into a dictionary (safe for display).

        Returns:
            Dict[str, Any]: Config values as dictionary.
        """
        return {
            "llm_mode": self.llm_mode.value,
            "openai_api_key": "****" if self.openai_api_key else None,
            "tr_access_token": "****" if self.tr_access_token else None,
            "default_openai_model": self.default_openai_model,
            "default_deepseek_model": self.default_deepseek_model,
            "default_tr_model": self.default_tr_model,
            "embedding_model_name": self.embedding_model_name,
            "embedding_batch_size": self.embedding_batch_size,
            "vector_store_path": self.vector_store_path,
            "vector_collection_name": self.vector_collection_name,
            "log_level": self.log_level,
            "max_parallel_processes": self.max_parallel_processes,
        }


# === Singleton Config Instance ===
config = AppConfig()
