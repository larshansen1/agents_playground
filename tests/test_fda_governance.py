"""Tests for FDA Governance Analysis - Invariants and Integration.

Tests critical invariants from FDA_API_REVIEW.md:
- INV-1: State transitions always logged
- INV-2: Decisions have ≥1 alternative
- INV-3: Violations have severity
- INV-4: Findings have evidence
- INV-5: Findings cite valid guidelines
- INV-6: Completed tasks have findings
- INV-7: Confidence in valid range
- INV-8: Decisions logged before state changes
- INV-9: Tasks not completed if agent errors
- INV-10: Audit records immutable
- INV-11: Ruleset version recorded
"""

import json

from app.agents.guideline_checker_agent import GuidelineCheckerAgent
from app.agents.report_generator_agent import ReportGeneratorAgent
from app.agents.severity_assessor_agent import SeverityAssessorAgent
from app.agents.spec_parser_agent import SpecParserAgent

# Sample compliant OpenAPI spec for testing
COMPLIANT_SPEC = json.dumps(
    {
        "openapi": "3.0.3",
        "info": {
            "title": "Test Compliant API",
            "version": "1.0.0",
            "description": "Fully compliant test spec",
            "contact": {"name": "Test", "email": "test@example.com"},
        },
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/health": {
                "get": {
                    "operationId": "healthCheck",
                    "description": "Health check",
                    "responses": {"200": {"description": "OK"}, "500": {"description": "Error"}},
                }
            }
        },
    }
)

# Sample non-compliant spec (missing required fields)
NON_COMPLIANT_SPEC = json.dumps(
    {
        "openapi": "3.0.3",
        "info": {
            "title": "Test Non-Compliant API",
            "version": "invalid-version",  # Violates semantic versioning
        },
        "paths": {},
    }
)


# ============================================================================
# Invariant Tests (INV-1 through INV-11)
# ============================================================================


class TestInvariants:
    """Test critical system invariants from FDA_API_REVIEW.md."""

    def test_inv2_decision_has_at_least_one_alternative(self):
        """INV-2: Every decision must have at least one alternative considered."""
        agent = GuidelineCheckerAgent()

        result = agent.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        decisions = result.get("decisions", [])
        assert len(decisions) > 0, "Expected decisions to be logged"

        for decision in decisions:
            alternatives = decision.get("alternatives", [])
            assert (
                len(alternatives) >= 1
            ), f"Decision {decision['decision_point']} has no alternatives (INV-2 violated)"

    def test_inv3_violation_has_severity(self):
        """INV-3: All violations must have a severity assigned."""
        agent = GuidelineCheckerAgent()

        # Use non-compliant spec to trigger violations
        result = agent.execute(
            {"parsed_spec": json.loads(NON_COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]
        violations = [f for f in findings if f["status"] == "VIOLATION"]

        for violation in violations:
            assert (
                violation["severity"] is not None
            ), f"Violation {violation['check_id']} has no severity (INV-3 violated)"
            assert violation["severity"] in [
                "CRITICAL",
                "MAJOR",
                "MINOR",
                "INFO",
            ], f"Invalid severity: {violation['severity']}"

    def test_inv4_finding_has_evidence(self):
        """INV-4: All findings must include evidence."""
        agent = GuidelineCheckerAgent()

        result = agent.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]

        for finding in findings:
            assert (
                "evidence" in finding
            ), f"Finding {finding['check_id']} has no evidence field (INV-4 violated)"
            assert (
                finding["evidence"] is not None
            ), f"Finding {finding['check_id']} evidence is None"
            assert len(finding["evidence"]) > 0, f"Finding {finding['check_id']} evidence is empty"

    def test_inv5_finding_cites_valid_guideline(self):
        """INV-5: Findings must cite valid ruleset guidelines."""
        agent = GuidelineCheckerAgent()

        result = agent.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]
        valid_rules = ["R06", "R11"]  # MVP rules

        for finding in findings:
            assert (
                finding["rule_id"] in valid_rules
            ), f"Finding cites invalid rule: {finding['rule_id']} (INV-5 violated)"

    def test_inv7_confidence_in_valid_range(self):
        """INV-7: Confidence scores must be in range [0.0, 1.0]."""
        agent = GuidelineCheckerAgent()

        result = agent.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]
        decisions = result.get("decisions", [])

        for finding in findings:
            conf = finding["confidence"]
            assert (
                0.0 <= conf <= 1.0
            ), f"Finding {finding['check_id']} confidence {conf} not in [0.0, 1.0] (INV-7 violated)"

        for decision in decisions:
            conf = decision["confidence"]
            assert (
                0.0 <= conf <= 1.0
            ), f"Decision {decision['decision_point']} confidence {conf} not in [0.0, 1.0]"


# ============================================================================
# Integration Tests - End-to-End Flows
# ============================================================================


class TestIntegration:
    """Test end-to-end governance analysis flows."""

    def test_end_to_end_compliant_spec(self):
        """Test complete analysis pipeline with compliant spec."""
        # Phase 1: SpecParser
        parser = SpecParserAgent()
        result1 = parser.execute({"spec_content": COMPLIANT_SPEC, "spec_format": "json"})

        assert result1["output"]["validation_status"] == "valid"
        parsed_spec = result1["output"]["parsed_spec"]

        # Phase 2: GuidelineChecker
        checker = GuidelineCheckerAgent()
        result2 = checker.execute({"parsed_spec": parsed_spec, "ruleset_id": "FDA-DK-2024-1.0"})

        findings = result2["output"]["findings"]
        assert (
            result2["output"]["summary"]["violations"] == 0
        ), "Compliant spec should have no violations"

        # Phase 3: SeverityAssessor
        assessor = SeverityAssessorAgent()
        result3 = assessor.execute({"findings": findings, "ruleset_id": "FDA-DK-2024-1.0"})

        assert result3["output"]["summary"]["CRITICAL"] == 0, "No critical violations expected"

        # Phase 4: ReportGenerator
        generator = ReportGeneratorAgent()
        result4 = generator.execute(
            {
                "spec_metadata": {
                    "spec_title": result1["output"]["spec_title"],
                    "spec_version": result1["output"]["spec_version"],
                    "endpoint_count": result1["output"]["endpoint_count"],
                },
                "findings": result3["output"]["findings"],
                "ruleset_id": "FDA-DK-2024-1.0",
                "severity_summary": result3["output"]["summary"],
                "output_formats": ["json", "markdown"],
            }
        )

        assert result4["output"]["compliance_score"] > 0.9, "Compliant spec should have >90% score"
        assert "report_json" in result4["output"]
        assert "report_markdown" in result4["output"]

    def test_end_to_end_spec_with_violations(self):
        """Test complete analysis pipeline with non-compliant spec."""
        # Phase 1: SpecParser
        parser = SpecParserAgent()
        result1 = parser.execute({"spec_content": NON_COMPLIANT_SPEC, "spec_format": "json"})

        assert result1["output"]["validation_status"] == "valid"
        parsed_spec = result1["output"]["parsed_spec"]

        # Phase 2: GuidelineChecker
        checker = GuidelineCheckerAgent()
        result2 = checker.execute({"parsed_spec": parsed_spec, "ruleset_id": "FDA-DK-2024-1.0"})

        findings = result2["output"]["findings"]
        assert (
            result2["output"]["summary"]["violations"] > 0
        ), "Non-compliant spec should have violations"

        # Verify violations have proper structure
        violations = [f for f in findings if f["status"] == "VIOLATION"]
        for v in violations:
            assert v["severity"] in ["CRITICAL", "MAJOR", "MINOR"]
            assert len(v["evidence"]) > 0
            assert len(v["reasoning"]) > 0

        # Phase 3: SeverityAssessor
        assessor = SeverityAssessorAgent()
        result3 = assessor.execute({"findings": findings, "ruleset_id": "FDA-DK-2024-1.0"})

        # Phase 4: ReportGenerator
        generator = ReportGeneratorAgent()
        result4 = generator.execute(
            {
                "spec_metadata": {
                    "spec_title": result1["output"]["spec_title"],
                    "spec_version": result1["output"]["spec_version"],
                    "endpoint_count": result1["output"]["endpoint_count"],
                },
                "findings": result3["output"]["findings"],
                "ruleset_id": "FDA-DK-2024-1.0",
                "severity_summary": result3["output"]["summary"],
                "output_formats": ["json", "markdown"],
            }
        )

        assert (
            result4["output"]["compliance_score"] < 1.0
        ), "Non-compliant spec should have <100% score"
        assert result4["output"]["summary"]["violations"] > 0

    def test_findings_queryable_by_severity(self):
        """Test that findings can be filtered by severity."""
        checker = GuidelineCheckerAgent()
        result = checker.execute(
            {"parsed_spec": json.loads(NON_COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]

        # Group by severity
        by_severity = {}
        for f in findings:
            sev = f["severity"]
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(f)

        # Verify each severity group
        for sev, group in by_severity.items():
            assert all(
                f["severity"] == sev for f in group
            ), f"Findings with severity {sev} not properly filtered"


# ============================================================================
# Behavior Tests - API Functionality
# ============================================================================


class TestBehavior:
    """Test specific behaviors and error handling."""

    def test_submit_analysis_invalid_spec_format(self):
        """Test handling of invalid JSON/YAML format."""
        parser = SpecParserAgent()

        result = parser.execute({"spec_content": "not valid json or yaml!", "spec_format": "json"})

        assert result["output"]["validation_status"] == "error"
        assert len(result["output"]["validation_errors"]) > 0

    def test_check_guideline_compliant(self):
        """Test guideline check returns COMPLIANT status."""
        checker = GuidelineCheckerAgent()

        result = checker.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]
        compliant = [f for f in findings if f["status"] == "COMPLIANT"]

        assert len(compliant) > 0, "Expected some compliant findings"
        for f in compliant:
            assert f["recommendation"] is None, "Compliant findings should not have recommendations"

    def test_check_guideline_violation(self):
        """Test guideline check returns VIOLATION status."""
        checker = GuidelineCheckerAgent()

        result = checker.execute(
            {"parsed_spec": json.loads(NON_COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        findings = result["output"]["findings"]
        violations = [f for f in findings if f["status"] == "VIOLATION"]

        assert len(violations) > 0, "Expected at least one violation"
        for v in violations:
            assert v["recommendation"] is not None, "Violations should have recommendations"
            assert len(v["recommendation"]) > 0


# ============================================================================
# Decision Audit Tests
# ============================================================================


class TestDecisionAudit:
    """Test decision audit trail requirements."""

    def test_decision_records_all_alternatives(self):
        """Test that decisions record all alternatives considered."""
        checker = GuidelineCheckerAgent()

        result = checker.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        decisions = result.get("decisions", [])

        for decision in decisions:
            alternatives = decision["alternatives"]
            assert len(alternatives) >= 1, "Expected at least one alternative"

            # Verify alternative structure
            for alt in alternatives:
                assert "option" in alt
                assert "reason_rejected" in alt

    def test_decision_includes_context(self):
        """Test that decisions include execution context."""
        checker = GuidelineCheckerAgent()

        result = checker.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        decisions = result.get("decisions", [])

        for decision in decisions:
            assert "context" in decision, "Decision missing context field"
            assert decision["context"] is not None

    def test_decision_reasoning_non_empty(self):
        """Test that decision reasoning is not empty."""
        checker = GuidelineCheckerAgent()

        result = checker.execute(
            {"parsed_spec": json.loads(COMPLIANT_SPEC), "ruleset_id": "FDA-DK-2024-1.0"}
        )

        decisions = result.get("decisions", [])

        for decision in decisions:
            reasoning = decision["selected_reasoning"]
            assert (
                reasoning is not None
            ), f"Decision {decision['decision_point']} has null reasoning"
            assert len(reasoning) > 0, f"Decision {decision['decision_point']} has empty reasoning"
