"""FDA API Governance - Report Generator Agent.

Creates compliance reports in JSON and Markdown formats.
Responsibilities:
- Generate structured JSON report
- Generate markdown report with executive summary
- Provide executive summary
"""

from datetime import UTC, datetime
from typing import Any

from app.agents.base import Agent
from app.logging_config import get_logger

logger = get_logger(__name__)


class ReportGeneratorAgent(Agent):
    """Agent that generates compliance reports in multiple formats."""

    def __init__(self):
        super().__init__(agent_type="report_generator")

    def execute(
        self,
        input_data: dict[str, Any],
        user_id_hash: str | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """
        Generate compliance report.

        Input format:
        {
            "spec_metadata": {...},  # From SpecParserAgent
            "findings": [...],  # From Severity AssessorAgent
            "ruleset_id": "FDA-DK-2024-1.0",
            "severity_summary": {...},
            "output_formats": ["json", "markdown"]  # Default: both
        }

        Returns:
            Dict with generated reports:
            {
                "output": {
                    "report_json": {...},
                    "report_markdown": "...",
                    "compliance_score": 0.71,  # 0-1
                    "summary": {
                        "spec_title": "My API",
                        "total_checks": 7,
                        "violations": 2,
                        "compliance_percentage": 71
                    }
                },
                "usage": {...}
            }
        """
        spec_metadata = input_data.get("spec_metadata", {})
        findings = input_data.get("findings", [])
        ruleset_id = input_data.get("ruleset_id", "FDA-DK-2024-1.0")
        severity_summary = input_data.get("severity_summary", {})
        output_formats = input_data.get("output_formats", ["json", "markdown"])

        try:
            # Calculate compliance score
            total_checks = len(findings)
            compliant = sum(1 for f in findings if f["status"] == "COMPLIANT")
            compliance_score = compliant / total_checks if total_checks > 0 else 0.0

            # Build report data
            report_data = {
                "spec_title": spec_metadata.get("spec_title", "Unknown API"),
                "spec_version": spec_metadata.get("spec_version", "unknown"),
                "ruleset_id": ruleset_id,
                "ruleset_version": ruleset_id.split("-")[-1] if "-" in ruleset_id else "1.0",
                "analyzed_at": datetime.now(UTC).isoformat(),
                "summary": {
                    "total_checks": total_checks,
                    "compliant": compliant,
                    "violations": sum(1 for f in findings if f["status"] == "VIOLATION"),
                    "not_applicable": sum(1 for f in findings if f["status"] == "NOT_APPLICABLE"),
                    "compliance_score": round(compliance_score, 2),
                    "compliance_percentage": round(compliance_score * 100),
                    "severity_breakdown": severity_summary,
                },
                "findings": findings,
            }

            # Generate formats
            output: dict[str, Any] = {}

            if "json" in output_formats:
                output["report_json"] = report_data

            if "markdown" in output_formats:
                # Generate markdown report
                output["report_markdown"] = self._generate_markdown(report_data)

            # Add summary for quick reference
            output["compliance_score"] = compliance_score
            output["summary"] = report_data["summary"]

            logger.info(
                "report_generated",
                spec_title=report_data["spec_title"],
                compliance_score=compliance_score,
                violations=report_data["summary"]["violations"],
                formats=output_formats,
            )

            return {
                "output": output,
                "usage": {
                    "model_used": None,  # No LLM for report generation
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost": 0.0,
                    "generation_id": None,
                },
            }

        except Exception as e:
            logger.error("report_generation_failed", error=str(e), exc_info=True)
            return self._error_response(f"Report generation failed: {e}")

    def _generate_markdown(self, report_data: dict) -> str:
        """Generate Markdown format report."""
        summary = report_data["summary"]
        findings = report_data["findings"]

        md = f"""# API Governance Compliance Report

**API:** {report_data["spec_title"]} (v{report_data["spec_version"]})
**Ruleset:** {report_data["ruleset_id"]}
**Analysis Date:** {report_data["analyzed_at"]}

## Executive Summary

- **Compliance Score:** {summary["compliance_percentage"]}% ({summary["compliant"]}/{summary["total_checks"]} checks passed)
- **Violations:** {summary["violations"]}
  - Critical: {summary["severity_breakdown"].get("CRITICAL", 0)}
  - Major: {summary["severity_breakdown"].get("MAJOR", 0)}
  - Minor: {summary["severity_breakdown"].get("MINOR", 0)}

## Findings

"""

        # Group findings by status
        violations = [f for f in findings if f["status"] == "VIOLATION"]
        compliant = [f for f in findings if f["status"] == "COMPLIANT"]

        if violations:
            md += "### ❌ Violations\n\n"
            for finding in violations:
                md += f"""#### {finding["check_id"]} - {finding["severity"]}

**Status:** {finding["status"]}
**Confidence:** {finding["confidence"]}
**Effort:** {finding.get("effort_estimate", "N/A")}

**Evidence:** {finding["evidence"].get("evidence_text", "N/A")}

**Reasoning:** {finding["reasoning"]}

**Recommendation:** {finding.get("recommendation", "N/A")}

---

"""

        if compliant:
            md += f"\n### ✅ Compliant ({len(compliant)} checks passed)\n\n"
            for finding in compliant[:5]:  # Show first 5
                md += f"- **{finding['check_id']}:** {finding['reasoning']}\n"

            if len(compliant) > 5:
                md += f"\n*... and {len(compliant) - 5} more compliant checks*\n"

        md += "\n---\n*Generated by API Governance Review System*\n"

        return md

    def _error_response(self, error_message: str) -> dict[str, Any]:
        """Build error response."""
        return {
            "output": {
                "report_json": None,
                "report_markdown": None,
                "compliance_score": 0.0,
                "summary": {
                    "total_checks": 0,
                    "compliant": 0,
                    "violations": 0,
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
