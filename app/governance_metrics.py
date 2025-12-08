"""Governance-specific Prometheus metrics.

Metrics for FDA API compliance analysis and governance decisions.
"""

from prometheus_client import Counter, Histogram

# ============================================================================
# Compliance Analysis Metrics
# ============================================================================

compliance_findings_total = Counter(
    "governance_compliance_findings_total",
    "Total compliance findings by status and severity",
    ["ruleset_id", "status", "severity"],
)

governance_decisions_total = Counter(
    "governance_decisions_total",
    "Total governance decisions logged",
    ["agent_type", "decision_point"],
)

# ============================================================================
# Agent Performance Metrics
# ============================================================================

agent_phase_duration_seconds = Histogram(
    "governance_agent_phase_duration_seconds",
    "Time spent in each agent phase",
    ["agent_type", "phase"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

# ============================================================================
# Decision Quality Metrics
# ============================================================================

decision_confidence = Histogram(
    "governance_decision_confidence",
    "Decision confidence score distribution",
    ["decision_point"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
)

finding_confidence = Histogram(
    "governance_finding_confidence",
    "Finding confidence score distribution",
    ["check_id", "status"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
)

# ============================================================================
# Analysis Volume Metrics
# ============================================================================

analysis_tasks_total = Counter(
    "governance_analysis_tasks_total",
    "Total analysis tasks by framework and outcome",
    ["framework", "status"],
)

compliance_score_distribution = Histogram(
    "governance_compliance_score",
    "Compliance score distribution",
    ["ruleset_id"],
    buckets=[0.0, 0.25, 0.5, 0.75, 0.85, 0.9, 0.95, 0.99, 1.0],
)
