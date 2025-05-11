"""
Prompt Builder Utility

Loads YAML-based prompt templates and injects runtime variables using Jinja2.
Provides:
- Strict prompt retrieval using PromptTemplateKey Enum
- Safe, typed prompt injection with Jinja2 templating
- YAML parsing with internal caching
"""

from typing import Dict, Any
from pathlib import Path
import yaml
from jinja2 import Template, TemplateError

from backend.utils.constants import PromptTemplateKey
from backend.utils.logger import logger

PROMPT_TEMPLATE_PATH = Path("backend/prompt_engine/prompt_templates.yaml")


class PromptBuilder:
    """
    Centralized class for fetching and rendering LLM prompt templates.
    Prompts are stored in Jinja2-compatible YAML and selected via Enum keys.
    """

    def __init__(self, template_path: Path = PROMPT_TEMPLATE_PATH):
        """
        Initializes the prompt builder and loads all templates from disk.

        Args:
            template_path (Path): Path to the YAML prompt template file.
        """
        self._raw_templates: Dict[str, str] = self._load_templates(template_path)

    def _load_templates(self, path: Path) -> Dict[str, str]:
        """
        Loads YAML prompt templates from disk.

        Args:
            path (Path): Path to YAML file.

        Returns:
            Dict[str, str]: Mapping of prompt name -> template string.

        Raises:
            RuntimeError: If YAML parsing fails.
        """
        if not path.exists():
            raise FileNotFoundError(f"Prompt template file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("Prompt template YAML must be a dictionary at the top level.")
                logger.success(f"✅ Loaded prompt templates from {path}")
                return data
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse prompt YAML: {e}")

    def render(self, key: PromptTemplateKey, variables: Dict[str, Any]) -> str:
        """
        Renders a prompt by injecting variables into a Jinja2 template.

        Args:
            key (PromptTemplateKey): Enum key of the prompt to render.
            variables (Dict[str, Any]): Dictionary of substitution variables.

        Returns:
            str: Final rendered prompt string ready for LLM consumption.

        Raises:
            KeyError: If the prompt key is not found.
            TemplateError: If Jinja2 rendering fails.
        """
        raw_template = self._raw_templates.get(key.value)
        if raw_template is None:
            raise KeyError(f"Prompt template '{key.value}' not found.")

        try:
            template = Template(raw_template)
            rendered = template.render(**variables)
            logger.debug(f"🧠 Rendered prompt for key [{key.value}] with {len(variables)} variable(s)")
            return rendered
        except TemplateError as e:
            raise TemplateError(f"Error rendering template [{key.value}]: {e}")

    def available_keys(self) -> Dict[str, str]:
        """
        Returns a list of available keys for UI/debug purposes.

        Returns:
            Dict[str, str]: Key name -> truncated preview
        """
        return {
            k: v[:80].strip().replace("\n", " ") + "..."
            for k, v in self._raw_templates.items()
        }
