"""Severity Assessor Agent for compliance finding prioritization.

This agent handles Phase 3 of governance analysis:
- Review violations from guideline checker
- Assign/verify severity levels
- Add effort estimates for remediation
- Prioritize findings
"""

from typing import Any

from app.agents.base import Agent
from app.logging_config import get_logger

logger = get_logger(__name__)


class SeverityAssessorAgent(Agent):
    """Agent that assigns severity and effort estimates to findings."""

    def __init__(self):
        super().__init__(agent_type="severity_assessor")

    def execute(
        self,
        input_data: dict[str, Any],
        user_id_hash: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Assess severity and effort for compliance findings.

        Input format:
        {
            "findings": [...],  # From GuidelineCheckerAgent
            "ruleset_id": "FDA-DK-2024-1.0"
        }

        Returns:
            Dict with assessed findings:
            {
                "output": {
                    "findings": [... with severity and effort_estimate added ...],
                    "prioritized_violations": [...],  # CRITICAL first, then MAJOR, etc.
                    "summary": {
                        "critical": 1,
                        "major": 2,
                        "minor": 0,
                        "info": 1
                    }
                },
                "usage": {...}
            }
        """
        findings = input_data.get("findings", [])

        if not findings:
            return self._empty_response()

        try:
            # MVP: Severity is already assigned by guideline checker based on rule defaults
            # This agent verifies and can adjust based on context

            assessed_findings = []
            severity_counts = {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0}

            for finding in findings:
                # For MVP, keep the severity from rule default
                # Add effort estimate based on severity
                assessed_finding = finding.copy()

                if finding["status"] == "VIOLATION":
                    # Assign effort based on severity
                    assessed_finding["effort_estimate"] = self._estimate_effort(
                        finding["severity"], finding["check_id"]
                    )
                    severity_counts[finding["severity"]] += 1
                else:
                    assessed_finding["effort_estimate"] = None

                assessed_findings.append(assessed_finding)

            # Prioritize violations by severity
            violations = [f for f in assessed_findings if f["status"] == "VIOLATION"]
            prioritized_violations = sorted(
                violations,
                key=lambda f: {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}[f["severity"]],
            )

            logger.info(
                "severity_assessment_complete",
                total_findings=len(assessed_findings),
                critical=severity_counts["CRITICAL"],
                major=severity_counts["MAJOR"],
            )

            return {
                "output": {
                    "findings": assessed_findings,
                    "prioritized_violations": prioritized_violations,
                    "summary": severity_counts,
                },
                "usage": {
                    "model_used": None,  # No LLM for severity assessment (MVP)
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "generation_id": None,
                },
            }

        except Exception as e:
            logger.error("severity_assessment_failed", error=str(e), exc_info=True)
            return self._error_response(f"Severity assessment failed: {e}")

    def _estimate_effort(self, severity: str, check_id: str) -> str:
        """Estimate remediation effort based on severity and check type."""
        # MVP: Simple heuristic based on severity
        # Future: Use LLM to analyze specific violation context

        effort_map = {
            "CRITICAL": "MEDIUM",  # Security/core issues require careful fixes
            "MAJOR": "MEDIUM",
            "MINOR": "LOW",
            "INFO": "LOW",
        }

        # Special cases
        if "versioning" in check_id.lower():
            return "LOW"  # Just update version string
        if "security" in check_id.lower():
            return "HIGH"  # Security fixes need testing

        return effort_map.get(severity, "MEDIUM")

    def _empty_response(self) -> dict[str, Any]:
        """Response when no findings provided."""
        return {
            "output": {
                "findings": [],
                "prioritized_violations": [],
                "summary": {"CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0},
            },
            "usage": {
                "model_used": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "generation_id": None,
            },
        }

    def _error_response(self, error_message: str) -> dict[str, Any]:
        """Build error response."""
        return {
            "output": {
                "findings": [],
                "prioritized_violations": [],
                "summary": {
                    "CRITICAL": 0,
                    "MAJOR": 0,
                    "MINOR": 0,
                    "INFO": 0,
                    "error": error_message,
                },
            },
            "usage": {
                "model_used": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "generation_id": None,
            },
        }
