"""Additional worker functions for multi-agent workflows."""

import time
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from psycopg2.extras import Json

from app.agents import get_agent
from app.db_utils import aggregate_subtask_costs, get_workflow_state
from app.instance import get_instance_name
from app.logging_config import get_logger
from app.orchestrator import extract_workflow_type, get_orchestrator
from app.trace_utils import extract_trace_context

# We need tracer - get it from opentelemetry directly

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_worker_deps():
    """Get worker dependencies to avoid circular import."""
    from app.worker import (
        notify_api_async,
        worker_heartbeat,
    )

    return notify_api_async, worker_heartbeat


def _handle_workflow_completion(action, parent_task_id, output, conn, cur, notify_api_async):
    """Handle workflow completion based on orchestrator action."""
    if action == "complete":
        cur.execute(
            "UPDATE tasks SET status = 'done', output = %s WHERE id = %s",
            (Json(output), parent_task_id),
        )
        conn.commit()
        notify_api_async(parent_task_id, "done", output=output)
    elif action == "failed":
        error_msg = "Workflow failed: max iterations or error"
        cur.execute(
            "UPDATE tasks SET status = 'error', error = %s WHERE id = %s",
            (error_msg, parent_task_id),
        )
        conn.commit()
        notify_api_async(parent_task_id, "error", error=error_msg)


def _process_subtask(conn, cur, row):  # noqa: PLR0915
    """Process a subtask by executing the appropriate agent."""
    notify_api_async, worker_heartbeat = _get_worker_deps()

    subtask_id = str(row["id"])
    parent_task_id = str(row["parent_task_id"])
    agent_type = row["agent_type"]
    subtask_input = row["input"]
    iteration = row["iteration"]
    task_start_time = time.time()

    trace_ctx, cleaned_input = extract_trace_context(subtask_input)

    logger.info(
        "subtask_picked",
        subtask_id=subtask_id,
        parent_task_id=parent_task_id,
        agent_type=agent_type,
        iteration=iteration,
    )

    worker_heartbeat.labels(service="worker", instance=get_instance_name()).set_to_current_time()

    with tracer.start_as_current_span(f"process_subtask:{agent_type}", context=trace_ctx) as span:
        span.set_attribute("subtask.id", subtask_id)
        span.set_attribute("subtask.parent_id", parent_task_id)
        span.set_attribute("subtask.agent_type", agent_type)
        span.set_attribute("workflow.iteration", iteration)

        # Add workflow-specific context from trace
        if trace_ctx and hasattr(trace_ctx, "get"):
            root_op = trace_ctx.get("root_operation")
            if root_op:
                span.set_attribute("workflow.root_operation", root_op)

        try:
            cur.execute(
                "UPDATE subtasks SET status = 'running' WHERE id = %s",
                (subtask_id,),
            )
            conn.commit()

            user_id_hash = cleaned_input.pop("_user_id_hash", None)
            tenant_id = cleaned_input.pop("_tenant_id", None)

            agent = get_agent(agent_type)
            result = agent.execute(cleaned_input, user_id_hash)
            task_duration = time.time() - task_start_time

            output = result["output"]
            usage = result.get("usage")

            if usage:
                cur.execute(
                    """
                    UPDATE subtasks
                    SET status = 'done', output = %s, user_id_hash = %s, tenant_id = %s,
                        model_used = %s, input_tokens = %s, output_tokens = %s,
                        total_cost = %s, generation_id = %s
                    WHERE id = %s
                    """,
                    (
                        Json(output),
                        user_id_hash,
                        tenant_id,
                        usage.get("model_used"),
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                        usage.get("total_cost", 0),
                        usage.get("generation_id"),
                        subtask_id,
                    ),
                )
            else:
                cur.execute(
                    "UPDATE subtasks SET status = 'done', output = %s, user_id_hash = %s, tenant_id = %s WHERE id = %s",
                    (Json(output), user_id_hash, tenant_id, subtask_id),
                )
            conn.commit()

            aggregate_subtask_costs(parent_task_id, conn)

            workflow_state = get_workflow_state(parent_task_id, conn)
            if workflow_state:
                workflow_type = workflow_state["workflow_type"]
                orchestrator = get_orchestrator(workflow_type)

                result_action = orchestrator.process_subtask_completion(
                    parent_task_id, subtask_id, output, conn, user_id_hash, tenant_id
                )

                action = result_action.get("action")
                final_output = result_action.get("output", output)
                _handle_workflow_completion(
                    action, parent_task_id, final_output, conn, cur, notify_api_async
                )

            span.set_status(Status(StatusCode.OK))
            logger.info("subtask_completed", subtask_id=subtask_id, duration=f"{task_duration:.3f}")

        except Exception as e:
            error_msg = str(e)
            cur.execute(
                "UPDATE subtasks SET status = 'error', error = %s WHERE id = %s",
                (error_msg, subtask_id),
            )
            cur.execute(
                "UPDATE tasks SET status = 'error', error = %s WHERE id = %s",
                (f"Subtask failed: {error_msg}", parent_task_id),
            )
            conn.commit()
            notify_api_async(parent_task_id, "error", error=error_msg)
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error("subtask_failed", subtask_id=subtask_id, error=error_msg)


def _process_agent_task(conn, cur, row):
    """Process an agent task by directly executing the specified agent."""
    notify_api_async, worker_heartbeat = _get_worker_deps()

    task_id = str(row["id"])
    task_type = row["type"]
    task_input = row["input"]
    task_start_time = time.time()

    from app.orchestrator import extract_agent_type

    agent_type = extract_agent_type(task_type)  # Extract 'research' from 'agent:research'
    trace_ctx, cleaned_input = extract_trace_context(task_input)

    logger.info("agent_task_picked", task_id=task_id, agent_type=agent_type)

    worker_heartbeat.labels(service="worker", instance=get_instance_name()).set_to_current_time()

    with tracer.start_as_current_span(
        f"process_agent_task:{agent_type}", context=trace_ctx
    ) as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.type", task_type)
        span.set_attribute("agent.type", agent_type)

        try:
            cur.execute(
                "UPDATE tasks SET status = 'running' WHERE id = %s",
                (task_id,),
            )
            conn.commit()
            notify_api_async(task_id, "running")

            user_id_hash = cleaned_input.pop("_user_id_hash", None)
            tenant_id = cleaned_input.pop("_tenant_id", None)

            # Execute agent directly
            agent = get_agent(agent_type)
            result = agent.execute(cleaned_input, user_id_hash)
            task_duration = time.time() - task_start_time

            output = result["output"]
            usage = result.get("usage")

            if usage:
                cur.execute(
                    """
                    UPDATE tasks
                    SET status = 'done', output = %s, user_id_hash = %s, tenant_id = %s,
                        model_used = %s, input_tokens = %s, output_tokens = %s,
                        total_cost = %s, generation_id = %s
                    WHERE id = %s
                    """,
                    (
                        Json(output),
                        user_id_hash,
                        tenant_id,
                        usage.get("model_used"),
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                        usage.get("total_cost", 0),
                        usage.get("generation_id"),
                        task_id,
                    ),
                )
            else:
                cur.execute(
                    "UPDATE tasks SET status = 'done', output = %s, user_id_hash = %s, tenant_id = %s WHERE id = %s",
                    (Json(output), user_id_hash, tenant_id, task_id),
                )
            conn.commit()
            notify_api_async(task_id, "done", output=output)

            span.set_status(Status(StatusCode.OK))
            logger.info(
                "agent_task_completed",
                task_id=task_id,
                agent_type=agent_type,
                duration=f"{task_duration:.3f}",
            )

        except Exception as e:
            error_msg = str(e)
            cur.execute(
                "UPDATE tasks SET status = 'error', error = %s WHERE id = %s",
                (error_msg, task_id),
            )
            conn.commit()
            notify_api_async(task_id, "error", error=error_msg)
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error(
                "agent_task_failed", task_id=task_id, agent_type=agent_type, error=error_msg
            )


def _process_workflow_task(conn, cur, row):
    """Process a workflow task by delegating to orchestrator."""
    notify_api_async, worker_heartbeat = _get_worker_deps()

    task_id = str(row["id"])
    task_type = row["type"]
    task_input = row["input"]
    task_start_time = time.time()

    trace_ctx, cleaned_input = extract_trace_context(task_input)

    logger.info("workflow_task_picked", task_id=task_id, task_type=task_type)

    worker_heartbeat.labels(service="worker", instance=get_instance_name()).set_to_current_time()

    with tracer.start_as_current_span(f"process_workflow:{task_type}", context=trace_ctx) as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.type", task_type)

        try:
            cur.execute(
                "UPDATE tasks SET status = 'running' WHERE id = %s",
                (task_id,),
            )
            conn.commit()
            notify_api_async(task_id, "running")

            user_id_hash = cleaned_input.pop("_user_id_hash", None)
            tenant_id = cleaned_input.pop("_tenant_id", None)

            workflow_type = extract_workflow_type(task_type)
            orchestrator = get_orchestrator(workflow_type)
            # Pass original task_input (not cleaned_input) to preserve trace context
            orchestrator.create_workflow(task_id, task_input, conn, user_id_hash, tenant_id)

            task_duration = time.time() - task_start_time
            span.set_status(Status(StatusCode.OK))
            logger.info("workflow_initialized", task_id=task_id, duration=f"{task_duration:.3f}")

        except Exception as e:
            error_msg = str(e)
            cur.execute(
                "UPDATE tasks SET status = 'error', error = %s WHERE id = %s",
                (error_msg, task_id),
            )
            conn.commit()
            notify_api_async(task_id, "error", error=error_msg)
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.record_exception(e)
            logger.error("workflow_initialization_failed", task_id=task_id, error=error_msg)


def claim_next_task(conn, cur, worker_id: str, settings: Any) -> dict[str, Any] | None:
    """
    Find and claim the next available task or subtask.

    Args:
        conn: Database connection
        cur: Database cursor
        worker_id: ID of the worker claiming the task
        settings: Application settings

    Returns:
        Task row dict if found and claimed, None otherwise
    """
    from datetime import UTC, datetime, timedelta

    from app.metrics import active_leases, tasks_acquired_total

    # Calculate lease timeout for new tasks
    lease_duration = timedelta(seconds=settings.worker_lease_duration_seconds)
    lease_timeout = datetime.now(UTC) + lease_duration

    # Find a pending subtask (priority to keep workflows moving)
    # Include lease timeout check to recover stalled tasks
    cur.execute(
        """
        SELECT id, parent_task_id, agent_type, iteration, status, input,
               try_count, max_tries, 'subtask' as source_type
        FROM subtasks
        WHERE status = 'pending'
          AND try_count < max_tries
          AND (lease_timeout IS NULL OR lease_timeout < NOW())
        ORDER BY created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
        """
    )

    row = cur.fetchone()

    # If no subtasks, try regular tasks
    if not row:
        cur.execute(
            """
            SELECT id, type, input, NULL as parent_task_id, NULL as agent_type,
                   NULL as iteration, try_count, max_tries, 'task' as source_type
            FROM tasks
            WHERE status = 'pending'
              AND try_count < max_tries
              AND (lease_timeout IS NULL OR lease_timeout < NOW())
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """
        )
        row = cur.fetchone()

    if not row:
        return None

    # Claim the task
    task_id = str(row["id"])
    source_type = row.get("source_type", "task")
    try_count = row.get("try_count", 0)

    # Claim the task with lease  # nosec B608
    table = "tasks" if source_type == "task" else "subtasks"
    cur.execute(
        f"""
        UPDATE {table}
        SET status = 'running',
            locked_at = NOW(),
            locked_by = %s,
            lease_timeout = %s,
            try_count = try_count + 1,
            updated_at = NOW()
        WHERE id = %s
        """,
        (worker_id, lease_timeout, task_id),
    )
    conn.commit()

    # Record metrics
    task_type = row.get("type") or row.get("agent_type", "unknown")
    tasks_acquired_total.labels(worker_id=worker_id, task_type=task_type).inc()
    active_leases.labels(worker_id=worker_id).inc()

    logger.info(
        "task_acquired",
        task_id=task_id,
        source_type=source_type,
        worker_id=worker_id,
        try_count=try_count + 1,
        max_tries=row.get("max_tries", 3),
        lease_timeout=lease_timeout.isoformat(),
    )

    return dict(row)
