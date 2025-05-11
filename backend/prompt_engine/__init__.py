"""
Initializer for the Prompt Engine subpackage.

Provides:
- Prompt template loading and rendering (Jinja2-based)
- Structured access via PromptTemplateKey enum

This module is responsible for dynamically shaping the inputs
given to the LLMs across various test-generation workflows.

Exposed components:
- PromptBuilder: Loads YAML templates and injects runtime variables.
"""

from .prompt_builder import PromptBuilder

__all__ = ["PromptBuilder"]
