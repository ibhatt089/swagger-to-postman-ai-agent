"""
Schema Parser Utility

Provides detailed analysis of OpenAPI schema objects for use in test case generation.

Features:
- Required vs optional fields
- Type extraction and format tagging
- Enum and boolean field recognition
- Flattened schema insights for embedding and scenario generation
"""

from typing import Dict, List, Tuple, Any


def parse_schema_properties(
    schema: Dict[str, Any],
    required_fields: List[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses a Swagger schema object and returns required/optional fields with type metadata.

    Args:
        schema (Dict): OpenAPI schema object with 'properties'
        required_fields (List[str], optional): List of required field names

    Returns:
        Tuple[List[Dict], List[Dict]]: Required and optional fields with metadata
    """
    required_fields = required_fields or []
    required_props, optional_props = [], []

    properties = schema.get("properties", {})
    for prop_name, prop_schema in properties.items():
        field_info = {
            "name": prop_name,
            "type": prop_schema.get("type", "object"),
            "format": prop_schema.get("format"),
            "enum": prop_schema.get("enum", []),
            "description": prop_schema.get("description", ""),
            "is_boolean": prop_schema.get("type") == "boolean",
            "is_enum": "enum" in prop_schema,
            "example": prop_schema.get("example"),
            "default": prop_schema.get("default")
        }

        if prop_name in required_fields:
            required_props.append(field_info)
        else:
            optional_props.append(field_info)

    return required_props, optional_props


def flatten_schema_to_summary(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flattens the schema for quick ingestion and high-level summary.

    Args:
        schema (Dict): OpenAPI schema definition

    Returns:
        Dict: Summary of types, booleans, enums, required/optional lists
    """
    parsed = {
        "required_fields": [],
        "optional_fields": [],
        "types": {},
        "booleans": [],
        "enums": {}
    }

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field_name, field_schema in properties.items():
        f_type = field_schema.get("type", "object")
        parsed["types"][field_name] = f_type

        if field_name in required:
            parsed["required_fields"].append(field_name)
        else:
            parsed["optional_fields"].append(field_name)

        if f_type == "boolean":
            parsed["booleans"].append(field_name)

        if "enum" in field_schema:
            parsed["enums"][field_name] = field_schema["enum"]

    return parsed
