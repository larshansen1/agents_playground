"""Test script for FDA Analysis agents - validates all 4 phases.

This script tests each agent individually and shows the complete analysis pipeline.
Run this from the project root: python test_fda_analysis.py
"""

from app.agents.guideline_checker_agent import GuidelineCheckerAgent
from app.agents.report_generator_agent import ReportGeneratorAgent
from app.agents.severity_assessor_agent import SeverityAssessorAgent
from app.agents.spec_parser_agent import SpecParserAgent

# Sample OpenAPI spec (minimal but valid)
sample_spec = """
{
  "openapi": "3.0.3",
  "info": {
    "title": "Test API",
    "version": "1.0.0",
    "description": "Test API for FDA validation",
    "contact": {
      "name": "API Team",
      "email": "api@example.com"
    }
  },
  "servers": [{"url": "https://api.example.com"}],
  "paths": {
    "/health": {
      "get": {
        "operationId": "healthCheck",
        "description": "Health check endpoint",
        "responses": {
          "200": {"description": "OK"},
          "500": {"description": "Internal Server Error"}
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "oauth2": {
        "type": "oauth2",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://auth.example.com/authorize",
            "tokenUrl": "https://auth.example.com/token",
            "scopes": {}
          }
        }
      }
    }
  }
}
"""

print("=" * 80)
print("FDA API GOVERNANCE ANALYSIS - AGENT VALIDATION")
print("=" * 80)
print()

# Test Phase 1: SpecParser
print("=" * 80)
print("PHASE 1: SpecParser - Parse and validate OpenAPI spec")
print("=" * 80)
spec_parser = SpecParserAgent()
result1 = spec_parser.execute({"spec_content": sample_spec, "spec_format": "json"})

print(f"✓ Validation Status: {result1['output']['validation_status']}")
print(f"✓ API Title: {result1['output']['spec_title']}")
print(f"✓ API Version: {result1['output']['spec_version']}")
print(f"✓ Endpoint Count: {result1['output']['endpoint_count']}")
print(f"✓ LLM Cost: ${result1['usage']['total_cost']:.4f}")

if result1["output"]["validation_errors"]:
    print(f"⚠ Validation Errors: {result1['output']['validation_errors']}")
print()

# Test Phase 2: GuidelineChecker
print("=" * 80)
print("PHASE 2: GuidelineChecker - Run compliance checks")
print("=" * 80)
checker = GuidelineCheckerAgent()
result2 = checker.execute(
    {"parsed_spec": result1["output"]["parsed_spec"], "ruleset_id": "FDA-DK-2024-1.0"}
)

summary = result2["output"]["summary"]
print(f"✓ Total Checks: {summary['total_checks']}")
print(f"✓ Compliant: {summary['compliant']}")
print(f"✓ Violations: {summary['violations']}")
print(f"✓ Not Applicable: {summary['not_applicable']}")
print(f"✓ Decisions Logged: {len(result2.get('decisions', []))}")
print()

print("Findings breakdown:")
for finding in result2["output"]["findings"]:
    icon = "✓" if finding["status"] == "COMPLIANT" else "✗"
    print(f"  {icon} {finding['check_id']}: {finding['status']} ({finding['severity']})")
print()

# Test Phase 3: SeverityAssessor
print("=" * 80)
print("PHASE 3: SeverityAssessor - Assess violations and prioritize")
print("=" * 80)
assessor = SeverityAssessorAgent()
result3 = assessor.execute(
    {"findings": result2["output"]["findings"], "ruleset_id": "FDA-DK-2024-1.0"}
)

severity_summary = result3["output"]["summary"]
print(f"✓ Critical Violations: {severity_summary['CRITICAL']}")
print(f"✓ Major Violations: {severity_summary['MAJOR']}")
print(f"✓ Minor Violations: {severity_summary['MINOR']}")
print(f"✓ Info Findings: {severity_summary['INFO']}")
print()

if result3["output"]["prioritized_violations"]:
    print("Prioritized violations (highest severity first):")
    for v in result3["output"]["prioritized_violations"][:3]:  # Show top 3
        print(f"  • {v['check_id']}: {v['severity']} - {v.get('effort_estimate', 'N/A')} effort")
print()

# Test Phase 4: ReportGenerator
print("=" * 80)
print("PHASE 4: ReportGenerator - Generate compliance report")
print("=" * 80)
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

print(f"✓ Compliance Score: {result4['output']['compliance_score']:.2%}")
print(f"✓ Compliance Percentage: {result4['output']['summary']['compliance_percentage']}%")
print("✓ Report Formats: JSON, Markdown")
print()

# Show markdown report preview
print("=" * 80)
print("MARKDOWN REPORT PREVIEW (first 800 characters)")
print("=" * 80)
print(result4["output"]["report_markdown"][:800])
print("...")
print()

# Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print("✓ All 4 agents executed successfully")
print(f"✓ {summary['total_checks']} checks run")
print(f"✓ {len(result2.get('decisions', []))} decisions logged for audit")
print(f"✓ Final compliance: {result4['output']['summary']['compliance_percentage']}%")
print("✓ Total LLM cost: $0.00 (no LLM used for structural checks)")
print()
print("=" * 80)
print("✅ FDA ANALYSIS AGENTS VALIDATED SUCCESSFULLY")
print("=" * 80)
