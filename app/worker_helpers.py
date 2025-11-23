"""Additional worker functions for multi-agent workflows."""

import time

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from psycopg2.extras import Json

from app.agents import get_agent
from app.db_utils import aggregate_subtask_costs, get_workflow_state
from app.logging_config import get_logger
from app.orchestrator import extract_workflow_type, get_orchestrator
from app.trace_utils import extract_trace_context

# We need tracer - get it from opentelemetry directly

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _get_worker_deps():
    """Get worker dependencies to avoid circular import."""
    from app.worker import notify_api_async, worker_heartbeat

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

    worker_heartbeat.set_to_current_time()

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

            agent = get_agent(agent_type)
            result = agent.execute(cleaned_input, user_id_hash)
            task_duration = time.time() - task_start_time

            output = result["output"]
            usage = result.get("usage")

            if usage:
                cur.execute(
                    """
                    UPDATE subtasks
                    SET status = 'done', output = %s, user_id_hash = %s,
                        model_used = %s, input_tokens = %s, output_tokens = %s,
                        total_cost = %s, generation_id = %s
                    WHERE id = %s
                    """,
                    (
                        Json(output),
                        user_id_hash,
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
                    "UPDATE subtasks SET status = 'done', output = %s WHERE id = %s",
                    (Json(output), subtask_id),
                )
            conn.commit()

            aggregate_subtask_costs(parent_task_id, conn)

            workflow_state = get_workflow_state(parent_task_id, conn)
            if workflow_state:
                workflow_type = workflow_state["workflow_type"]
                orchestrator = get_orchestrator(workflow_type)

                result_action = orchestrator.process_subtask_completion(
                    parent_task_id, subtask_id, output, conn, user_id_hash
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


def _process_workflow_task(conn, cur, row):
    """Process a workflow task by delegating to orchestrator."""
    notify_api_async, worker_heartbeat = _get_worker_deps()

    task_id = str(row["id"])
    task_type = row["type"]
    task_input = row["input"]
    task_start_time = time.time()

    trace_ctx, cleaned_input = extract_trace_context(task_input)

    logger.info("workflow_task_picked", task_id=task_id, task_type=task_type)

    worker_heartbeat.set_to_current_time()

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

            workflow_type = extract_workflow_type(task_type)
            orchestrator = get_orchestrator(workflow_type)
            # Pass original task_input (not cleaned_input) to preserve trace context
            orchestrator.create_workflow(task_id, task_input, conn, user_id_hash)

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
