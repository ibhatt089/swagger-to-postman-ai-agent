# backend/__init__.py

"""
Entry module for the `backend` package of the Swagger-to-Postman AI Agent.

This package contains the core logic and orchestration components of the entire system,
including LLM interfacing, embeddings, chunking, memory management, prompt building,
and multiprocessing support for large-scale processing.

Modules:
- agents: LLM-driven orchestration of Swagger -> Postman test generation.
- llm_provider: Modular support for OpenAI, local models (DeepSeek), and org API endpoints.
- embeddings: Embedding engine and vector store handling (ChromaDB + caching).
- chunking: Smart, file-aware document chunkers for Swagger, Postman, and free text.
- prompt_engine: Builds structured prompt inputs for inference.
- multiprocessing: Enables concurrent execution for high-throughput use.
- utils: Configs, logging, file I/O, constants.

This file ensures that relative imports across submodules work properly,
especially during multiprocessing and CLI execution.

Usage:
    This module is imported automatically when initializing the backend layer.
"""

# Explicitly import important high-level components for easier access
from backend.utils import config, logger
from backend.agents.swagger_agent import SwaggerToPostmanAgent

__all__ = [
    "config",
    "logger",
    "SwaggerToPostmanAgent"
]