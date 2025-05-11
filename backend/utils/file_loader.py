"""
File loader utility for Swagger YAML and Postman JSON files.

Responsibilities:
- Load and parse files from disk
- Validate minimum structural schema (e.g., openapi version, info, paths)
- Raise informative errors with fallback line numbers
- Return clean parsed objects (dict or list)

Assumptions:
- Swagger follows OpenAPI 3.x or 2.x format
- Postman follows v2 collection schema (standard Postman exports)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

from backend.utils.logger import logger
from backend.utils.constants import FileType
from backend.utils.swagger_converter import SwaggerFormatNormalizer


class FileLoaderError(Exception):
    """Raised when Swagger or Postman input fails to load or validate."""


def load_swagger_file(file_path: str) -> Dict[str, Any]:
    """
    Loads a Swagger file (YAML or JSON), validates structure, and returns dict.

    Args:
        file_path (str): Absolute or relative path to Swagger input.

    Returns:
        Dict[str, Any]: Parsed OpenAPI specification.

    Raises:
        FileLoaderError: If format is unsupported or required fields are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileLoaderError(f"❌ Swagger file not found: {file_path}")

    try:
        if path.suffix.lower() == FileType.JSON:
            # Convert JSON Swagger to YAML string first
            yaml_string = SwaggerFormatNormalizer.to_yaml_str(path)
            swagger_dict = yaml.safe_load(yaml_string)
            logger.info("🔁 Swagger JSON converted to YAML for uniform processing.")
        elif path.suffix.lower() in FileType.YAML:
            with path.open("r", encoding="utf-8") as f:
                swagger_dict = yaml.safe_load(f)
        else:
            raise FileLoaderError(f"Unsupported Swagger file extension: {path.suffix}")

        # Basic Swagger/OpenAPI structure checks
        if "paths" not in swagger_dict or not isinstance(swagger_dict["paths"], dict):
            raise FileLoaderError("Swagger must include a valid 'paths' section.")

        if "openapi" not in swagger_dict and "swagger" not in swagger_dict:
            raise FileLoaderError("Missing 'openapi' or 'swagger' field in Swagger spec.")

        logger.success(f"✅ Loaded Swagger: {file_path}")
        return swagger_dict

    except yaml.YAMLError as e:
        raise FileLoaderError(f"YAML parsing error: {e}")
    except json.JSONDecodeError as e:
        raise FileLoaderError(f"JSON parsing error: {e}")
    except Exception as e:
        raise FileLoaderError(f"Unhandled error in loading Swagger: {str(e)}")


def load_postman_file(file_path: str) -> Dict[str, Any]:
    """
    Loads and parses a Postman JSON collection file.

    Args:
        file_path (str): Path to Postman file.

    Returns:
        Dict[str, Any]: Parsed Postman collection.

    Raises:
        FileLoaderError: If the file is missing, malformed, or invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileLoaderError(f"Postman collection file not found: {file_path}")

    try:
        if path.suffix.lower() in FileType.POSTMAN_COLLECTION:
            with path.open("r", encoding="utf-8") as f:
                postman_data = json.load(f)

            # Validate required fields
            if "info" not in postman_data or "item" not in postman_data:
                raise FileLoaderError("Postman collection must contain 'info' and 'item' fields.")

            logger.success(f"✅ Loaded Postman JSON: {file_path}")
            return postman_data
        else:
            raise FileLoaderError(f"Unsupported Postman file extension: {path.suffix}")

    except json.JSONDecodeError as e:
        raise FileLoaderError(f"JSON parsing error in Postman file '{file_path}': {e}")
    except Exception as e:
        raise FileLoaderError(f"Error loading Postman file: {str(e)}")


def load_postman_environment(file_path: str) -> Dict[str, Any]:
    """
    Loads a Postman environment JSON file.

    Args:
        file_path (str): Path to environment JSON file.

    Returns:
        Dict[str, Any]: Parsed environment variable definitions.

    Raises:
        FileLoaderError: If invalid structure or parse failure.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileLoaderError(f"Postman environment file not found: {file_path}")

    try:
        if path.suffix.lower() in FileType.POSTMAN_ENVIRONMENT:
            with path.open("r", encoding="utf-8") as f:
                env_data = json.load(f)

            if not isinstance(env_data, dict) or "values" not in env_data:
                raise FileLoaderError("Postman environment JSON must contain a 'values' key.")

            logger.success(f"✅ Loaded Postman Environment: {file_path}")
            return env_data
        else:
            raise FileLoaderError(f"Unsupported Postman environment file extension: {path.suffix}")

    except json.JSONDecodeError as e:
        raise FileLoaderError(f"JSON parsing error in Postman environment: {e}")
    except Exception as e:
        raise FileLoaderError(f"Error loading Postman environment file: {str(e)}")