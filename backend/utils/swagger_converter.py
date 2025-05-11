"""
Swagger Format Normalizer

Utility class that accepts Swagger/OpenAPI files in either JSON or YAML,
and converts them to a unified YAML string format for consistent downstream usage.

Usage:
    SwaggerFormatNormalizer.to_yaml_str(file_path: str) -> str
"""

import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any

from backend.utils.constants import FileType
from backend.utils.logger import logger


class SwaggerFormatNormalizer:
    """
    Converts Swagger input (JSON or YAML) to a normalized YAML string.

    Helps ensure a uniform YAML format regardless of original source format.
    """

    @staticmethod
    def to_yaml_str(file_path: Union[str, Path]) -> str:
        """
        Converts a Swagger file (.json or .yaml/.yml) into a unified YAML string.

        Args:
            file_path (str | Path): Path to the Swagger file.

        Returns:
            str: YAML-formatted Swagger content as string.

        Raises:
            FileNotFoundError: If file is not found.
            ValueError: If unsupported extension or parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Swagger file not found: {file_path}")

        ext = path.suffix.lower()
        try:
            with path.open("r", encoding="utf-8") as f:
                if ext == FileType.JSON:
                    json_data: Dict[str, Any] = json.load(f)
                    logger.debug(f"🔄 Converted JSON Swagger to YAML for: {file_path}")
                    return yaml.safe_dump(json_data, sort_keys=False)
                elif ext in FileType.YAML:
                    content = yaml.safe_load(f)
                    logger.debug(f"✅ Loaded YAML Swagger directly: {file_path}")
                    return yaml.safe_dump(content, sort_keys=False)
                else:
                    raise ValueError(f"Unsupported file format: {ext}")

        except Exception as e:
            raise RuntimeError(f"Failed to convert Swagger file '{file_path}' to YAML: {e}")
