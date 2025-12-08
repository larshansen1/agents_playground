"""
FDA API Guidelines Checker

Loads the FDA ruleset and runs all checks against an OpenAPI spec.
Produces findings with evidence and severity.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from fda_validators import CheckStatus, run_check


@dataclass
class Finding:
    """A compliance finding for one guideline check."""

    finding_id: str
    guideline_id: str
    check_id: str
    status: str
    severity: str
    evidence: str
    spec_paths: list[str]
    details: dict[str, Any] | None
    guideline_name_en: str
    guideline_name_da: str
    category: str
    priority: str


@dataclass
class AnalysisReport:
    """Complete analysis report."""

    spec_title: str
    spec_version: str
    ruleset_id: str
    ruleset_version: str
    analyzed_at: str
    summary: dict[str, int]
    compliance_score: float
    findings: list[Finding]


def load_ruleset(path: str | Path) -> dict:
    """Load FDA ruleset from JSON file."""
    with Path(path).open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def load_spec(path: str | Path) -> dict:
    """Load OpenAPI spec from JSON or YAML file."""
    path = Path(path)
    with path.open() as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)  # type: ignore[no-any-return]
        return json.load(f)  # type: ignore[no-any-return]


def parse_spec_string(content: str, format: str = "auto") -> dict:
    """Parse OpenAPI spec from string content."""
    if format == "auto":
        # Try JSON first, then YAML
        try:
            return json.loads(content)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            return yaml.safe_load(content)  # type: ignore[no-any-return]
    elif format == "json":
        return json.loads(content)  # type: ignore[no-any-return]
    else:
        return yaml.safe_load(content)  # type: ignore[no-any-return]


def analyze_spec(spec: dict, ruleset: dict) -> AnalysisReport:
    """Run all checks from ruleset against spec."""
    findings: list[Finding] = []
    finding_counter = 0

    # Summary counters
    summary = {
        "COMPLIANT": 0,
        "VIOLATION": 0,
        "NOT_APPLICABLE": 0,
        "UNABLE_TO_DETERMINE": 0,
        "CRITICAL": 0,
        "MAJOR": 0,
        "MINOR": 0,
        "INFO": 0,
    }

    for rule in ruleset.get("rules", []):
        for check in rule.get("checks", []):
            finding_counter += 1
            result = run_check(spec, check)

            finding = Finding(
                finding_id=f"F{finding_counter:04d}",
                guideline_id=rule["id"],
                check_id=check["check_id"],
                status=result.status.value,
                severity=result.severity.value,
                evidence=result.evidence,
                spec_paths=result.spec_paths_checked,
                details=result.details,
                guideline_name_en=rule["name_en"],
                guideline_name_da=rule["name_da"],
                category=rule["category"],
                priority=rule["priority"],
            )
            findings.append(finding)

            # Update summary
            summary[result.status.value] += 1
            if result.status == CheckStatus.VIOLATION:
                summary[result.severity.value] += 1

    # Calculate compliance score
    total_applicable = summary["COMPLIANT"] + summary["VIOLATION"]
    if total_applicable > 0:
        # Weight by severity
        max_score = total_applicable * 4  # All critical
        violation_score = (
            summary["CRITICAL"] * 4
            + summary["MAJOR"] * 3
            + summary["MINOR"] * 2
            + summary["INFO"] * 1
        )
        compliance_score = max(0, (max_score - violation_score) / max_score * 100)
    else:
        compliance_score = 100.0

    # Extract spec metadata
    spec_title = spec.get("info", {}).get("title", "Unknown")
    spec_version = spec.get("info", {}).get("version", "Unknown")

    return AnalysisReport(
        spec_title=spec_title,
        spec_version=spec_version,
        ruleset_id=ruleset["ruleset_id"],
        ruleset_version=ruleset["version"],
        analyzed_at=datetime.now(UTC).isoformat(),
        summary=summary,
        compliance_score=round(compliance_score, 1),
        findings=findings,
    )


def report_to_json(report: AnalysisReport) -> str:
    """Convert report to JSON string."""
    return json.dumps(asdict(report), indent=2)


def report_to_markdown(report: AnalysisReport) -> str:
    """Convert report to Markdown string."""
    lines = [
        "# FDA API Compliance Report",
        "",
        "## Summary",
        "",
        "| Attribute | Value |",
        "|-----------|-------|",
        f"| **API** | {report.spec_title} |",
        f"| **Version** | {report.spec_version} |",
        f"| **Ruleset** | {report.ruleset_id} v{report.ruleset_version} |",
        f"| **Analyzed** | {report.analyzed_at} |",
        f"| **Compliance Score** | {report.compliance_score}% |",
        "",
        "## Results",
        "",
        "| Status | Count |",
        "|--------|-------|",
        f"| ✅ Compliant | {report.summary['COMPLIANT']} |",
        f"| ❌ Violation | {report.summary['VIOLATION']} |",
        f"| ⬜ Not Applicable | {report.summary['NOT_APPLICABLE']} |",
        f"| ❓ Unable to Determine | {report.summary['UNABLE_TO_DETERMINE']} |",
        "",
    ]

    if report.summary["VIOLATION"] > 0:
        lines.extend(
            [
                "### Violations by Severity",
                "",
                "| Severity | Count |",
                "|----------|-------|",
                f"| 🔴 Critical | {report.summary['CRITICAL']} |",
                f"| 🟠 Major | {report.summary['MAJOR']} |",
                f"| 🟡 Minor | {report.summary['MINOR']} |",
                f"| 🔵 Info | {report.summary['INFO']} |",
                "",
            ]
        )

    # Group findings by status
    violations = [f for f in report.findings if f.status == "VIOLATION"]
    compliant = [f for f in report.findings if f.status == "COMPLIANT"]

    if violations:
        lines.extend(
            [
                "## Violations",
                "",
            ]
        )

        # Sort by severity
        severity_order = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}
        violations.sort(key=lambda f: severity_order.get(f.severity, 99))

        for finding in violations:
            severity_icon = {"CRITICAL": "🔴", "MAJOR": "🟠", "MINOR": "🟡", "INFO": "🔵"}
            lines.extend(
                [
                    f"### {severity_icon.get(finding.severity, '⚪')} [{finding.guideline_id}] {finding.guideline_name_en}",
                    "",
                    f"**Check:** {finding.check_id}",
                    "",
                    f"**Evidence:** {finding.evidence}",
                    "",
                    f"**Category:** {finding.category} | **Priority:** {finding.priority}",
                    "",
                    "---",
                    "",
                ]
            )

    lines.extend(
        [
            f"## Compliant Checks ({len(compliant)})",
            "",
        ]
    )

    for finding in compliant:
        lines.append(f"- ✅ [{finding.guideline_id}] {finding.check_id}: {finding.evidence}")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fda_checker.py <openapi_spec.yaml|json> [--format json|markdown]")
        print("")
        print("Example:")
        print("  python fda_checker.py my_api.yaml")
        print("  python fda_checker.py my_api.json --format markdown")
        sys.exit(1)

    spec_path = sys.argv[1]
    output_format = "markdown"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    # Load ruleset (assumes it's in same directory)
    ruleset_path = Path(__file__).parent / "fda_ruleset_v1.json"
    ruleset = load_ruleset(ruleset_path)

    # Load and analyze spec
    spec = load_spec(spec_path)
    report = analyze_spec(spec, ruleset)

    # Output
    if output_format == "json":
        print(report_to_json(report))
    else:
        print(report_to_markdown(report))
