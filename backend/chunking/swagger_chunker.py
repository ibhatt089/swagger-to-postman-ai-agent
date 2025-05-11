"""
Swagger Chunker Utility for Swagger-to-Postman AI Agent

Responsibilities:
- Load and normalize Swagger (OpenAPI) specs (YAML/JSON)
- Traverse endpoints, methods, parameters, schemas, responses
- Resolve $ref references recursively
- Generate fine-grained chunks for each logical unit
- Inject detailed metadata for embedding context

Chunk Types:
- endpoint_description
- parameter
- request_body_schema
- response_schema
- enum_test_case
- boolean_flag_test_case
- error_code_case

All chunks follow this structure:
{
    "id": str,
    "type": str,
    "text": str,
    "metadata": Dict[str, Any]
}
"""

import os
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from uuid import uuid4

from backend.utils.logger import logger
from backend.utils.constants import (
    ChunkType,
    METADATA_FIELD_TYPE,
    METADATA_FIELD_ORIGIN,
    METADATA_FIELD_FILENAME,
    METADATA_FIELD_HASH,
)
from backend.utils.swagger_converter import SwaggerFormatNormalizer


class SwaggerChunker:
    """
    Chunker class for processing OpenAPI Swagger specs into structured LLM chunks.

    Features:
    - Normalized access to paths, methods, schemas
    - Recursive $ref resolution for request/response bodies
    - Metadata-aware chunk creation
    - Hash-based deduplication ready
    """

    def __init__(self, swagger: Dict[str, Any], source_file: str):
        self.swagger = swagger
        self.source_file = Path(source_file).name
        self.components = swagger.get("components", {}).get("schemas", {})
        self.security_schemes = swagger.get("components", {}).get("securitySchemes", {})
        self.global_security = swagger.get("security", [])
        self.chunks: List[Dict[str, Any]] = []

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """
        Resolves a $ref string to the actual schema dictionary.

        Args:
            ref (str): A $ref path (e.g., "#/components/schemas/User")

        Returns:
            Dict[str, Any]: The referenced schema object.
        """
        ref_path = ref.lstrip("#/").split("/")
        result = self.swagger
        for part in ref_path:
            result = result.get(part)
            if result is None:
                raise KeyError(f"Unable to resolve $ref: {ref}")
        return result

    def _generate_chunk_id(self, base: str) -> str:
        """
        Generates a unique, hash-stable ID for each chunk based on input text.

        Args:
            base (str): The base string to hash.

        Returns:
            str: Hashed UUID-style identifier.
        """
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

    def _base_metadata(self, chunk_type: ChunkType) -> Dict[str, Any]:
        """
        Returns the base metadata dict for a chunk.

        Args:
            chunk_type (ChunkType): The type of chunk.

        Returns:
            Dict[str, Any]: Standard metadata.
        """
        return {
            METADATA_FIELD_TYPE: chunk_type,
            METADATA_FIELD_ORIGIN: ChunkType.SWAGGER,
            METADATA_FIELD_FILENAME: self.source_file
        }

    def _extract_endpoints(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Extracts (method, path, operation_obj) for all valid operations.

        Returns:
            List[Tuple[str, str, Dict]]: Each item is (method, path, operation).
        """
        all_ops = []
        for path, methods in self.swagger.get("paths", {}).items():
            for method, op in methods.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    all_ops.append((method.lower(), path, op))
        return all_ops

    def extract_chunks(self) -> List[Dict[str, Any]]:
        """
        Extracts all meaningful Swagger chunks for each operation,
        including parameters, request body, and responses.

        Returns:
            List[Dict]: Finalized chunks ready for embedding.
        """
        for method, path, operation in self._extract_endpoints():
            operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
            summary = operation.get("summary", "")
            parameters = self._extract_parameters(operation)
            request_body = self._extract_request_body(operation)
            responses = self._extract_responses(operation)
            security = self._extract_security(operation)

            base_text = f"{method.upper()} {path}\n\n{summary}\n\nParameters:\n{parameters}\n\n"
            if request_body:
                base_text += f"Request Body:\n{request_body}\n\n"
            base_text += f"Responses:\n{responses}\n\nSecurity: {security}"

            chunk = {
                "id": self._generate_chunk_id(base_text),
                "type": ChunkType.SWAGGER,
                "text": base_text.strip(),
                "metadata": {
                    **self._base_metadata(ChunkType.SWAGGER),
                    "method": method,
                    "path": path,
                    "operation_id": operation_id
                }
            }

            self.chunks.append(chunk)

        return self.chunks

    def _extract_parameters(self, operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gathers all parameters (path, query, header, cookie) for an operation.
        Resolves any $ref where applicable.

        Returns:
            List[Dict]: List of parameters with name, type, in, required, etc.
        """
        params = operation.get("parameters", [])
        resolved = []

        for param in params:
            if "$ref" in param:
                param = self._resolve_ref(param["$ref"])

            resolved.append({
                "name": param.get("name"),
                "in": param.get("in"),
                "required": param.get("required", False),
                "type": param.get("schema", {}).get("type", "string"),
                "description": param.get("description", "")
            })

        return resolved

    def _extract_request_body(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parses request body (if present) and returns its schema.

        Returns:
            Dict or None: Schema structure or None.
        """
        body = operation.get("requestBody", {})
        content = body.get("content", {})
        for content_type, media_obj in content.items():
            schema = media_obj.get("schema")
            if not schema:
                continue
            if "$ref" in schema:
                schema = self._resolve_ref(schema["$ref"])
            return {"content_type": content_type, "schema": schema}
        return None

    def _extract_responses(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts all available responses, status codes, and schema hints.

        Returns:
            Dict: Mapping of status_code -> schema/description.
        """
        output = {}
        for status_code, resp in operation.get("responses", {}).items():
            content = resp.get("content", {})
            for _, media_obj in content.items():
                schema = media_obj.get("schema", {})
                if "$ref" in schema:
                    schema = self._resolve_ref(schema["$ref"])
                output[status_code] = {
                    "description": resp.get("description", ""),
                    "schema": schema
                }
        return output

    def _extract_security(self, operation: Dict[str, Any]) -> List[str]:
        """
        Determines security mechanisms required for the operation.

        Returns:
            List[str]: List of auth schemes (e.g., Bearer, APIKey).
        """
        schemes = operation.get("security", self.global_security)
        result = []
        for s in schemes:
            for key in s.keys():
                result.append(key)
        return result

