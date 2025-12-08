"""Governance API Router - Audit trail and decision tracking.

Provides endpoints for querying governance analysis audit trails,
decisions, and compliance findings.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/governance", tags=["governance"])


# ============================================================================
# Response Models
# ============================================================================


class Finding(BaseModel):
    """Single compliance finding."""

    id: str
    rule_id: str
    check_id: str
    status: str
    severity: str
    confidence: float
    evidence: dict[str, Any]
    reasoning: str
    recommendation: str | None
    metadata: dict[str, Any] | None


class Decision(BaseModel):
    """Single governance decision."""

    id: str
    agent_type: str
    decision_point: str
    selected_option: str
    selected_reasoning: str
    alternatives: list[dict[str, Any]]
    confidence: float
    context: dict[str, Any] | None
    created_at: str


class ExecutionTrace(BaseModel):
    """Execution trace for a task."""

    task_id: str
    task_type: str
    task_status: str
    created_at: str
    completed_at: str | None
    phases: list[dict[str, Any]]
    findings_count: int
    decisions_count: int


class DecisionAuditTrail(BaseModel):
    """Complete decision audit trail for a task."""

    task_id: str
    task_type: str
    decisions: list[Decision]
    total_decisions: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/tasks/{task_id}/trace", response_model=ExecutionTrace)
async def get_execution_trace(
    task_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ExecutionTrace:
    """
    Get execution trace for a governance analysis task.

    Shows the complete execution flow: which agents ran, in what order,
    and what each phase produced.

    Args:
        task_id: UUID of the analysis task
        db: Database session

    Returns:
        ExecutionTrace with phase execution details

    Raises:
        HTTPException: 404 if task not found or not a governance task
    """
    # Get task details
    async with db.begin():
        result = await db.execute(
            text("""
                SELECT id, type, status, created_at, updated_at
                FROM tasks
                WHERE id = :task_id
            """),
            {"task_id": task_id},
        )
        task_row = result.fetchone()

    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task_row.type.startswith("analysis:"):
        raise HTTPException(
            status_code=400,
            detail=f"Task type '{task_row.type}' is not a governance analysis task",
        )

    # Get subtasks (phases)
    async with db.begin():
        result = await db.execute(
            text("""
                SELECT id, agent_type, status, created_at, updated_at,
                       input_tokens, output_tokens, total_cost
                FROM subtasks
                WHERE parent_task_id = :task_id
                ORDER BY created_at ASC
            """),
            {"task_id": task_id},
        )
        subtask_rows = result.fetchall()

    phases = [
        {
            "phase": row.agent_type,
            "status": row.status,
            "started_at": row.created_at.isoformat() if row.created_at else None,
            "completed_at": row.updated_at.isoformat() if row.updated_at else None,
            "cost": float(row.total_cost) if row.total_cost else 0.0,
        }
        for row in subtask_rows
    ]

    # Get counts
    async with db.begin():
        findings_result = await db.execute(
            text("SELECT COUNT(*) FROM compliance_findings WHERE task_id = :task_id"),
            {"task_id": task_id},
        )
        findings_count = findings_result.scalar() or 0

        decisions_result = await db.execute(
            text("SELECT COUNT(*) FROM governance_decisions WHERE task_id = :task_id"),
            {"task_id": task_id},
        )
        decisions_count = decisions_result.scalar() or 0

    return ExecutionTrace(
        task_id=str(task_row.id),
        task_type=task_row.type,
        task_status=task_row.status,
        created_at=task_row.created_at.isoformat() if task_row.created_at else "",
        completed_at=task_row.updated_at.isoformat()
        if task_row.updated_at and task_row.status == "done"
        else None,
        phases=phases,
        findings_count=findings_count,
        decisions_count=decisions_count,
    )


@router.get("/tasks/{task_id}/decisions", response_model=DecisionAuditTrail)
async def get_decision_audit_trail(
    task_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> DecisionAuditTrail:
    """
    Get complete decision audit trail for a task.

    Returns all governance decisions made during analysis,
    including alternatives considered and reasoning.

    Args:
        task_id: UUID of the analysis task
        db: Database session

    Returns:
        DecisionAuditTrail with all decisions

    Raises:
        HTTPException: 404 if task not found
    """
    # Verify task exists
    async with db.begin():
        task_result = await db.execute(
            text("SELECT type FROM tasks WHERE id = :task_id"),
            {"task_id": task_id},
        )
        task_row = task_result.fetchone()

    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get all decisions
    async with db.begin():
        result = await db.execute(
            text("""
                SELECT id, agent_type, decision_point, selected_option,
                       selected_reasoning, alternatives, confidence,
                       context, created_at
                FROM governance_decisions
                WHERE task_id = :task_id
                ORDER BY created_at ASC
            """),
            {"task_id": task_id},
        )
        decision_rows = result.fetchall()

    decisions = [
        Decision(
            id=str(row.id),
            agent_type=row.agent_type,
            decision_point=row.decision_point,
            selected_option=row.selected_option,
            selected_reasoning=row.selected_reasoning,
            alternatives=row.alternatives if row.alternatives else [],
            confidence=float(row.confidence) if row.confidence else 0.0,
            context=row.context if row.context else None,
            created_at=row.created_at.isoformat() if row.created_at else "",
        )
        for row in decision_rows
    ]

    return DecisionAuditTrail(
        task_id=task_id,
        task_type=task_row.type,
        decisions=decisions,
        total_decisions=len(decisions),
    )


@router.get("/tasks/{task_id}/findings", response_model=list[Finding])
async def get_compliance_findings(
    task_id: str,
    severity: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[Finding]:
    """
    Get compliance findings for a task.

    Args:
        task_id: UUID of the analysis task
        severity: Optional filter by severity (CRITICAL, MAJOR, MINOR, INFO)
        status: Optional filter by status (COMPLIANT, VIOLATION, NOT_APPLICABLE)
        db: Database session

    Returns:
        List of compliance findings

    Raises:
        HTTPException: 404 if task not found
    """
    # Verify task exists
    async with db.begin():
        task_result = await db.execute(
            text("SELECT id FROM tasks WHERE id = :task_id"),
            {"task_id": task_id},
        )
        if not task_result.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

    # Build query with optional filters
    query = """
        SELECT id, ruleset_id, rule_id, check_id, status, severity,
               confidence, evidence, reasoning, recommendation, metadata
        FROM compliance_findings
        WHERE task_id = :task_id
    """
    params: dict[str, Any] = {"task_id": task_id}

    if severity:
        query += " AND severity = :severity"
        params["severity"] = severity.upper()

    if status:
        query += " AND status = :status"
        params["status"] = status.upper()

    query += " ORDER BY severity DESC, check_id ASC"

    async with db.begin():
        result = await db.execute(text(query), params)
        finding_rows = result.fetchall()

    return [
        Finding(
            id=str(row.id),
            rule_id=row.rule_id,
            check_id=row.check_id,
            status=row.status,
            severity=row.severity,
            confidence=float(row.confidence) if row.confidence else 0.0,
            evidence=row.evidence if row.evidence else {},
            reasoning=row.reasoning,
            recommendation=row.recommendation,
            metadata=row.metadata if row.metadata else None,
        )
        for row in finding_rows
    ]
