"""Spec Parser Agent for OpenAPI validation and parsing.

This agent handles Phase 1 of FDA/governance analysis:
- Parse OpenAPI spec (JSON/YAML)
- Validate OpenAPI structure
- Extract metadata for downstream analysis
"""

import json
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from openapi_spec_validator import validate

from app.agents.base import Agent
from app.logging_config import get_logger

logger = get_logger(__name__)


class SpecParserAgent(Agent):
    """Agent that parses and validates OpenAPI specifications."""

    def __init__(self):
        super().__init__(agent_type="spec_parser")

    def execute(
        self,
        input_data: dict[str, Any],
        user_id_hash: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Parse and validate OpenAPI specification.

        Input format:
        {
            "spec_content": "...",  # OpenAPI spec as string (JSON or YAML)
            "spec_format": "json" | "yaml" | "auto",  # Optional, default: auto
            "spec_source": "inline" | "url" | "file"  # Optional, for tracking
        }

        Returns:
            Dict with parsed spec and validation results:
            {
                "output": {
                    "parsed_spec": {...},  # Parsed OpenAPI spec as dict
                    "spec_version": "3.0.3",
                    "spec_title": "My API",
                    "endpoint_count": 10,
                    "validation_status": "valid" | "invalid",
                    "validation_errors": []  # If invalid
                },
                "usage": {
                    "model_used": None,  # No LLM used for parsing
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0
                }
            }
        """
        spec_content = input_data.get("spec_content", "")
        spec_format = input_data.get("spec_format", "auto")

        if not spec_content:
            return self._error_response("spec_content is required")

        try:
            # Parse spec
            spec_dict = self._parse_spec(spec_content, spec_format)

            # Validate OpenAPI structure
            validation_errors = self._validate_spec(spec_dict)

            # Extract metadata
            metadata = self._extract_metadata(spec_dict)

            # Build output
            output = {
                "parsed_spec": spec_dict,
                "spec_version": metadata["version"],
                "spec_title": metadata["title"],
                "endpoint_count": metadata["endpoint_count"],
                "validation_status": "valid" if not validation_errors else "invalid",
                "validation_errors": validation_errors,
            }

            logger.info(
                "spec_parsed",
                spec_version=metadata["version"],
                spec_title=metadata["title"],
                endpoint_count=metadata["endpoint_count"],
                validation_status=output["validation_status"],
            )

            return {
                "output": output,
                "usage": {
                    "model_used": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "generation_id": None,
                },
            }

        except json.JSONDecodeError as e:
            return self._error_response(f"JSON parse error: {e}")
        except Exception as e:
            logger.error("spec_parse_failed", error=str(e), exc_info=True)
            return self._error_response(f"Spec parsing failed: {e}")

    def _parse_spec(self, content: str, format_hint: str) -> dict:
        """Parse OpenAPI spec from string."""
        if format_hint == "json" or (format_hint == "auto" and content.strip().startswith("{")):
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        # YAML parsing
        if yaml is None:
            msg = "YAML parsing not available - install PyYAML"
            raise ImportError(msg)
        try:
            parsed = yaml.safe_load(content)
            return parsed if isinstance(parsed, dict) else {}
        except yaml.YAMLError as e:
            msg = f"YAML parsing failed: {e}"
            raise ValueError(msg) from e

    def _validate_spec(self, spec_dict: dict) -> list[str]:
        """Validate OpenAPI spec using openapi-spec-validator."""
        errors = []

        try:
            # Validate against OpenAPI schema
            validate(spec_dict)
        except Exception as e:
            # Collect validation errors
            error_msg = str(e)
            # openapi-spec-validator raises ValidationError with detailed messages
            errors.append(error_msg)
            logger.warning("spec_validation_failed", error=error_msg)

        return errors

    def _extract_metadata(self, spec_dict: dict) -> dict:
        """Extract metadata from parsed spec."""
        info = spec_dict.get("info", {})
        paths = spec_dict.get("paths", {})

        # Count endpoints (paths x methods)
        endpoint_count = sum(
            len(
                [
                    k
                    for k in path_obj
                    if k in ["get", "post", "put", "patch", "delete", "options", "head"]
                ]
            )
            for path_obj in paths.values()
            if isinstance(path_obj, dict)
        )

        return {
            "version": spec_dict.get("openapi", spec_dict.get("swagger", "unknown")),
            "title": info.get("title", "Untitled API"),
            "endpoint_count": endpoint_count,
        }

    def _error_response(self, error_message: str) -> dict[str, Any]:
        """Build error response."""
        return {
            "output": {
                "parsed_spec": None,
                "spec_version": None,
                "spec_title": None,
                "endpoint_count": 0,
                "validation_status": "error",
                "validation_errors": [error_message],
            },
            "usage": {
                "model_used": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "generation_id": None,
            },
        }
