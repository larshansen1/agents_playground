"""FDA Analysis Orchestrator for governance review workflows.

Coordinates the 4-phase analysis process:
1. SpecParserAgent - Parse and validate OpenAPI spec
2. GuidelineCheckerAgent - Run compliance checks
3. SeverityAssessorAgent - Assess violations
4. ReportGeneratorAgent - Generate reports

Stores findings in compliance_findings table and decisions in governance_decisions table.
"""

from typing import Any
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from app.governance_metrics import (
    analysis_tasks_total,
    compliance_findings_total,
    compliance_score_distribution,
    decision_confidence,
    finding_confidence,
    governance_decisions_total,
)
from app.logging_config import get_logger
from app.orchestrator.base import Orchestrator

logger = get_logger(__name__)


class FDAAnalysisOrchestrator(Orchestrator):
    """Orchestrator for FDA API governance analysis."""

    def __init__(self):
        super().__init__(workflow_type="analysis:fda")
        self.phases = [
            "spec_parser",
            "guideline_checker",
            "severity_assessor",
            "report_generator",
        ]

    def get_max_iterations(self) -> int:
        """Fixed 4-phase pipeline, no iterations."""
        return 1

    def create_workflow(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Initialize FDA analysis workflow.

        Creates workflow_state and first subtask (SpecParserAgent).

        Args:
            parent_task_id: UUID of parent task
            input_data: {"spec_content": "...", "ruleset_id": "FDA-DK-2024-1.0"}
            conn: Database connection
            user_id_hash: Optional user ID
            tenant_id: Optional tenant ID
        """
        logger.info(
            "fda_analysis_workflow_create",
            parent_task_id=parent_task_id,
            ruleset_id=input_data.get("ruleset_id", "FDA-DK-2024-1.0"),
        )

        # Create workflow state
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO workflow_state (parent_task_id, workflow_type, current_iteration, current_state, state_data)
                VALUES (%s, %s, 0, %s, %s)
                """,
                (
                    parent_task_id,
                    "analysis:fda",
                    "spec_parser",  # current_state maps to current phase
                    Json(
                        {
                            "current_phase": "spec_parser",
                            "phase_index": 0,
                            "spec_metadata": None,
                            "findings": [],
                            "decisions": [],
                            "ruleset_id": input_data.get("ruleset_id", "FDA-DK-2024-1.0"),
                        }
                    ),
                ),
            )

            # Create first subtask: SpecParserAgent
            subtask_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO subtasks (
                    id, parent_task_id, agent_type, status, input,
                    user_id_hash, tenant_id
                )
                VALUES (%s, %s, %s, 'pending', %s, %s, %s)
                """,
                (
                    subtask_id,
                    parent_task_id,
                    "spec_parser",
                    Json(input_data),
                    user_id_hash,
                    tenant_id,
                ),
            )

            conn.commit()

        logger.info(
            "fda_analysis_subtask_created",
            subtask_id=subtask_id,
            agent_type="spec_parser",
        )

    def process_subtask_completion(
        self,
        parent_task_id: str,
        subtask_id: str,
        output: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process completion of an analysis phase and trigger next phase.

        Pipeline:
        spec_parser → guideline_checker → severity_assessor → report_generator → complete

        Args:
            parent_task_id: UUID of parent task
            subtask_id: UUID of completed subtask
            output: Output from completed subtask
            conn: Database connection
            user_id_hash: Optional user ID hash
            tenant_id: Optional tenant ID

        Returns:
            {"action": "continue" | "complete", "output": {...}}
        """
        # Get workflow state
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT state_data FROM workflow_state WHERE parent_task_id = %s",
                (parent_task_id,),
            )
            row = cur.fetchone()
            if not row:
                msg = f"Workflow state not found for task {parent_task_id}"
                raise ValueError(msg)
            state_data = row["state_data"]

        current_phase = state_data["current_phase"]
        phase_index = state_data["phase_index"]

        logger.info(
            "fda_analysis_phase_complete",
            parent_task_id=parent_task_id,
            phase=current_phase,
            phase_index=phase_index,
        )

        # Update state based on completed phase
        if current_phase == "spec_parser":
            # Store parsed spec, create guideline_checker subtask
            state_data["spec_metadata"] = {
                "spec_title": output.get("spec_title"),
                "spec_version": output.get("spec_version"),
                "endpoint_count": output.get("endpoint_count"),
            }

            if output.get("validation_status") == "error":
                # Spec parsing failed, abort workflow
                return {
                    "action": "complete",
                    "output": {"error": "Spec parsing failed", "details": output},
                }

            next_input = {
                "parsed_spec": output.get("parsed_spec"),
                "ruleset_id": state_data["ruleset_id"],
            }
            next_phase = "guideline_checker"

        elif current_phase == "guideline_checker":
            # Store findings and decisions
            state_data["findings"] = output.get("findings", [])

            # Store decisions in governance_decisions table
            decisions = output.get("decisions", [])
            self._store_decisions(parent_task_id, decisions, "guideline_checker", conn)

            next_input = {
                "findings": state_data["findings"],
                "ruleset_id": state_data["ruleset_id"],
            }
            next_phase = "severity_assessor"

        elif current_phase == "severity_assessor":
            # Update findings with severity/effort
            state_data["findings"] = output.get("findings", [])
            state_data["severity_summary"] = output.get("summary", {})

            next_input = {
                "spec_metadata": state_data["spec_metadata"],
                "findings": state_data["findings"],
                "ruleset_id": state_data["ruleset_id"],
                "severity_summary": state_data["severity_summary"],
            }
            next_phase = "report_generator"

        elif current_phase == "report_generator":
            # Final phase - store findings and complete
            self._store_findings(
                parent_task_id,
                state_data["findings"],
                state_data["ruleset_id"],
                conn,
            )

            # Record compliance score metric
            compliance_score = output.get("compliance_score", 0.0)
            compliance_score_distribution.labels(ruleset_id=state_data["ruleset_id"]).observe(
                compliance_score
            )

            # Record analysis completion
            analysis_tasks_total.labels(framework="FDA", status="completed").inc()

            logger.info(
                "fda_analysis_complete",
                parent_task_id=parent_task_id,
                compliance_score=compliance_score,
                violations=output.get("summary", {}).get("violations", 0),
            )

            # Update workflow state with final output
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE workflow_state
                       SET state_data = %s, current_state = 'completed'
                       WHERE parent_task_id = %s""",
                    (Json(state_data), parent_task_id),
                )
                conn.commit()

            return {"action": "complete", "output": output}

        else:
            logger.error("unknown_phase", phase=current_phase)
            return {"action": "failed"}

        # Create next subtask
        phase_index += 1
        state_data["current_phase"] = next_phase
        state_data["phase_index"] = phase_index

        with conn.cursor() as cur:
            # Update workflow state and create next subtask
            cur.execute(
                """UPDATE workflow_state
                   SET state_data = %s, current_state = %s
                   WHERE parent_task_id = %s""",
                (Json(state_data), next_phase, parent_task_id),
            )

            next_subtask_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO subtasks (
                    id, parent_task_id, agent_type, status, input,
                    user_id_hash, tenant_id
                )
                VALUES (%s, %s, %s, 'pending', %s, %s, %s)
                """,
                (
                    next_subtask_id,
                    parent_task_id,
                    next_phase,
                    Json(next_input),
                    user_id_hash,
                    tenant_id,
                ),
            )

            conn.commit()

        logger.info(
            "fda_analysis_next_subtask_created",
            subtask_id=subtask_id,
            next_phase=next_phase,
        )

        return {"action": "continue"}

    def _store_findings(
        self,
        task_id: str,
        findings: list[dict],
        ruleset_id: str,
        conn: psycopg2.extensions.connection,
    ) -> None:
        """Store findings in compliance_findings table."""
        logger.info(
            "storing_findings",
            task_id=task_id,
            finding_count=len(findings),
            ruleset_id=ruleset_id,
        )

        with conn.cursor() as cur:
            for finding in findings:
                cur.execute(
                    """
                    INSERT INTO compliance_findings (
                        task_id, ruleset_id, rule_id, check_id, status, severity,
                        confidence, evidence, reasoning, recommendation, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        task_id,
                        ruleset_id,
                        finding["rule_id"],
                        finding["check_id"],
                        finding["status"],
                        finding["severity"],
                        finding["confidence"],
                        Json(finding["evidence"]),
                        finding["reasoning"],
                        finding.get("recommendation"),
                        Json({"effort_estimate": finding.get("effort_estimate")}),
                    ),
                )

            conn.commit()

        # Record metrics for findings
        for finding in findings:
            compliance_findings_total.labels(
                ruleset_id=ruleset_id,
                status=finding["status"],
                severity=finding["severity"],
            ).inc()

            finding_confidence.labels(
                check_id=finding["check_id"],
                status=finding["status"],
            ).observe(finding["confidence"])

        logger.info("findings_stored", task_id=task_id, finding_count=len(findings))

    def _store_decisions(
        self,
        task_id: str,
        decisions: list[dict],
        agent_type: str,
        conn: psycopg2.extensions.connection,
    ) -> None:
        """Store decisions in governance_decisions table."""
        with conn.cursor() as cur:
            for decision in decisions:
                cur.execute(
                    """
                    INSERT INTO governance_decisions (
                        task_id, agent_type, decision_point, selected_option,
                        selected_reasoning, alternatives, confidence, context
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        task_id,
                        agent_type,
                        decision["decision_point"],
                        decision["selected_option"],
                        decision["selected_reasoning"],
                        Json(decision["alternatives"]),
                        decision["confidence"],
                        Json(decision.get("context", {})),
                    ),
                )

            conn.commit()

        # Record metrics for decisions
        for decision in decisions:
            governance_decisions_total.labels(
                agent_type=agent_type,
                decision_point=decision["decision_point"],
            ).inc()

            decision_confidence.labels(
                decision_point=decision["decision_point"],
            ).observe(decision["confidence"])

        logger.info(
            "decisions_stored",
            task_id=task_id,
            agent_type=agent_type,
            decision_count=len(decisions),
        )
