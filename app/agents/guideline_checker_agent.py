"""Guideline Checker Agent for compliance validation.

This agent handles Phase 2 of governance analysis:
- Load ruleset from database
- Run structural checks using validators
- Create findings with evidence
- Log decisions for audit trail
"""

from typing import Any

from app.agents.base import Agent
from app.governance.validators import (
    ValidationContext,
    validate_exists,
    validate_exists_and_non_empty,
    validate_regex,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


class GuidelineCheckerAgent(Agent):
    """Agent that checks specs against governance guidelines."""

    def __init__(self):
        super().__init__(agent_type="guideline_checker")

    def execute(
        self,
        input_data: dict[str, Any],
        user_id_hash: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Check OpenAPI spec against governance guidelines.

        Input format:
        {
            "parsed_spec": {...},  # From SpecParserAgent
            "ruleset_id": "FDA-DK-2024-1.0",  # Which ruleset to use
            "rules": [...],  # Optional: specific rules to check (default: all)
        }

        Returns:
            Dict with findings:
            {
                "output": {
                    "findings": [
                        {
                            "rule_id": "R06",
                            "check_id": "R06-01",
                            "status": "COMPLIANT" | "VIOLATION" | "NOT_APPLICABLE",
                            "severity": "CRITICAL" | "MAJOR" | "MINOR" | "INFO",
                            "confidence": 1.0,  # Structural checks are deterministic
                            "evidence": {...},
                            "reasoning": "...",
                            "recommendation": "..." | null
                        },
                        ...
                    ],
                    "summary": {
                        "total_checks": 7,
                        "compliant": 5,
                        "violations": 2,
                        "not_applicable": 0
                    }
                },
                "decisions": [
                    {
                        "decision_point": "R06-compliance",
                        "selected_option": "VIOLATION",
                        "selected_reasoning": "...",
                        "alternatives": [{...}],
                        "confidence": 1.0
                    },
                    ...
                ],
                "usage": {...}
            }
        """
        parsed_spec = input_data.get("parsed_spec")
        ruleset_id = input_data.get("ruleset_id", "FDA-DK-2024-1.0")
        # Check if we have parsed spec
        if not parsed_spec:
            msg = "Parsed spec is required for guideline checking"
            raise ValueError(msg)

        try:
            # Run checks for MVP structural rules
            findings = []
            decisions = []

            # MVP: Check R06-01 (OpenAPI version declared)
            ctx = ValidationContext(
                spec=parsed_spec,
                check_config={
                    "check_id": "R06-01",
                    "spec_path": "$.openapi",
                    "validation": {"type": "exists"},
                    "severity": "CRITICAL",
                    "evidence_template": "OpenAPI version field '{value}' is present",
                },
            )
            result = validate_exists(ctx)
            finding, decision = self._result_to_finding_and_decision(
                result, "R06", "OpenAPI version field must be present"
            )
            findings.append(finding)
            decisions.append(decision)

            # MVP: Check R06-02 (Service title present)
            ctx = ValidationContext(
                spec=parsed_spec,
                check_config={
                    "check_id": "R06-02",
                    "spec_path": "$.info.title",
                    "validation": {"type": "exists_and_non_empty"},
                    "severity": "CRITICAL",
                    "evidence_template": "Service title '{value}' is present and non-empty",
                },
            )
            result = validate_exists_and_non_empty(ctx)
            finding, decision = self._result_to_finding_and_decision(
                result, "R06", "Service must have a non-empty title"
            )
            findings.append(finding)
            decisions.append(decision)

            # MVP: Check R11-01 (Semantic versioning)
            ctx = ValidationContext(
                spec=parsed_spec,
                check_config={
                    "check_id": "R11-01",
                    "spec_path": "$.info.version",
                    "validation": {
                        "type": "regex",
                        "pattern": r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
                    },
                    "severity": "MAJOR",
                    "evidence_template": "Version '{value}' follows semantic versioning format",
                },
            )
            result = validate_regex(ctx)
            finding, decision = self._result_to_finding_and_decision(
                result, "R11", "Version must follow semantic versioning (X.Y.Z)"
            )
            findings.append(finding)
            decisions.append(decision)

            # Calculate summary
            summary = {
                "total_checks": len(findings),
                "compliant": sum(1 for f in findings if f["status"] == "COMPLIANT"),
                "violations": sum(1 for f in findings if f["status"] == "VIOLATION"),
                "not_applicable": sum(1 for f in findings if f["status"] == "NOT_APPLICABLE"),
            }

            logger.info(
                "guideline_checks_complete",
                ruleset_id=ruleset_id,
                total_checks=summary["total_checks"],
                violations=summary["violations"],
            )

            return {
                "output": {"findings": findings, "summary": summary},
                "decisions": decisions,
                "usage": {
                    "model_used": None,  # No LLM for structural checks
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "generation_id": None,
                },
            }

        except Exception as e:
            logger.error("guideline_check_failed", error=str(e), exc_info=True)
            return self._error_response(f"Guideline checking failed: {e}")

    def _result_to_finding_and_decision(
        self, result: Any, rule_id: str, reasoning_template: str
    ) -> tuple[dict, dict]:
        """Convert validator CheckResult to Finding and Decision."""
        finding = {
            "rule_id": rule_id,
            "check_id": result.check_id,
            "status": result.status.value,
            "severity": result.severity.value,
            "confidence": 1.0,  # Structural checks are deterministic
            "evidence": {
                "spec_paths": result.spec_paths_checked,
                "evidence_text": result.evidence,
                "details": result.details or {},
            },
            "reasoning": reasoning_template,
            "recommendation": None
            if result.status.value == "COMPLIANT"
            else "Review and fix the issue",
        }

        decision = {
            "decision_point": f"{result.check_id}-compliance",
            "selected_option": result.status.value,
            "selected_reasoning": reasoning_template,
            "alternatives": [
                {"option": "COMPLIANT", "reason_rejected": "Evidence shows non-compliance"}
                if result.status.value != "COMPLIANT"
                else {"option": "VIOLATION", "reason_rejected": "Evidence shows compliance"}
            ],
            "confidence": 1.0,
            "context": {"check_id": result.check_id, "evidence": result.evidence},
        }

        return finding, decision

    def _error_response(self, error_message: str) -> dict[str, Any]:
        """Build error response."""
        return {
            "output": {
                "findings": [],
                "summary": {
                    "total_checks": 0,
                    "compliant": 0,
                    "violations": 0,
                    "not_applicable": 0,
                    "error": error_message,
                },
            },
            "decisions": [],
            "usage": {
                "model_used": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "generation_id": None,
            },
        }
