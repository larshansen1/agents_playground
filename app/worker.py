import contextlib
import os
import socket
import time
from pathlib import Path
from typing import Any

import psycopg2
import requests
import urllib3
from opentelemetry import trace
from opentelemetry import trace as otel_trace
from opentelemetry.trace import Status, StatusCode
from psycopg2.extras import Json, RealDictCursor

from app.audit import log_audit_event
from app.config import settings
from app.db_sync import get_connection
from app.instance import get_instance_name
from app.logging_config import configure_logging, get_logger
from app.metrics import (
    active_leases,
    worker_heartbeat,
    worker_poll_interval_seconds,
)
from app.orchestrator import is_agent_task, is_workflow_task
from app.tasks import execute_task
from app.trace_utils import extract_trace_context, get_current_trace_id
from app.tracing import setup_tracing
from app.worker_helpers import _process_agent_task, _process_subtask, _process_workflow_task

# Suppress InsecureRequestWarning since we're using self-signed certs internally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure structured logging
configure_logging(log_level="INFO", json_logs=True)
logger = get_logger(__name__)

# API endpoint (internal Docker network)
API_URL = "https://task-api:8443"

# Worker Identity (hostname:pid)
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"

# Configure Prometheus multiprocess directory per instance to avoid PID collisions
# All Docker containers have PID 1, so they would overwrite each other's metrics
# Using separate subdirectories ensures each container writes to unique files
if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    base_dir = Path(os.environ["PROMETHEUS_MULTIPROC_DIR"])
    instance_dir = base_dir / get_instance_name()
    instance_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(instance_dir)
    logger.info(f"Prometheus multiprocess directory: {instance_dir}")

# Set up tracing for worker
setup_tracing(
    app=None,  # No FastAPI app in worker
    service_name="task-worker",
    use_console=True,  # Keep console for debugging
    otlp_endpoint="tempo:4317",  # Send to Tempo
    instrument_sql=False,  # Disable SQL tracing to reduce noise from lease queries
)
tracer = trace.get_tracer(__name__)


def notify_api_async(
    task_id: str, status: str, output: dict | None = None, error: str | None = None
) -> None:
    """
    Notify API of task update (best-effort, non-blocking).
    This triggers metrics recording and WebSocket broadcasting.
    Failures are logged but don't affect task completion.

    Args:
        task_id: UUID of the task
        status: Task status
        output: Task output dict (optional)
        error: Error message (optional)
    """
    url = f"{API_URL}/tasks/{task_id}"
    payload: dict[str, Any] = {"status": status}

    if output is not None:
        payload["output"] = output
    if error is not None:
        payload["error"] = error

    try:
        # Use verify=False for internal communication with self-signed certs
        response = requests.patch(url, json=payload, timeout=5, verify=False)  # nosec B501
        response.raise_for_status()
        logger.debug("api_notified", task_id=task_id, status=status)
    except Exception as e:
        # Log but don't fail - DB already updated
        logger.warning("api_notification_failed", task_id=task_id, error=str(e)[:100])


def run_worker_legacy():  # noqa: PLR0915
    """
    DEPRECATED: Use run_worker() instead.
    Main worker loop to process tasks with lease-based acquisition.
    """
    logger.warning(
        "Using deprecated run_worker_legacy(). This will be removed in a future release."
    )
    logger.info(
        "worker_started",
        worker_id=WORKER_ID,
        instance=get_instance_name(),
        poll_interval=settings.worker_poll_min_interval_seconds,
        lease_duration=settings.worker_lease_duration_seconds,
    )

    # Update heartbeat on startup
    worker_heartbeat.labels(service="worker", instance=get_instance_name()).set_to_current_time()

    # Adaptive polling state
    poll_interval = settings.worker_poll_min_interval_seconds
    last_recovery_check = time.time()

    # Connection reuse state
    conn = None
    cur = None

    while True:
        task_found = False

        try:
            # Establish connection if needed
            if conn is None or conn.closed:
                try:
                    conn = get_connection()
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    logger.info("worker_db_connected", worker_id=WORKER_ID)
                except Exception as e:
                    logger.error("worker_db_connection_failed", error=str(e))
                    time.sleep(5)
                    continue

            # Periodic lease recovery check
            if time.time() - last_recovery_check >= settings.worker_recovery_interval_seconds:
                from app.worker_lease import recover_expired_leases

                recover_expired_leases(conn, WORKER_ID)
                last_recovery_check = time.time()

            # Find and claim next task
            from app.worker_helpers import claim_next_task

            row = claim_next_task(conn, cur, WORKER_ID, settings)

            if row:
                task_found = True
                poll_interval = settings.worker_poll_min_interval_seconds

                # Process the task
                _process_task_row_legacy(conn, cur, row)

                # Decrement active leases after processing
                active_leases.labels(worker_id=WORKER_ID).dec()

            else:
                # No tasks found - apply adaptive backoff
                poll_interval = min(
                    poll_interval * settings.worker_poll_backoff_multiplier,
                    settings.worker_poll_max_interval_seconds,
                )

        except psycopg2.Error as e:
            logger.error("database_error", error=str(e), worker_id=WORKER_ID)
            # Force reconnection on DB error
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()
            conn = None
            time.sleep(5)
            poll_interval = settings.worker_poll_min_interval_seconds  # Reset on error
        except Exception as e:
            logger.error("unexpected_error", error=str(e), worker_id=WORKER_ID)
            time.sleep(5)
            poll_interval = settings.worker_poll_min_interval_seconds  # Reset on error

        # Note: We do NOT close the connection in finally block anymore
        # It stays open for reuse

        # Update metrics
        worker_poll_interval_seconds.labels(service="worker", instance=get_instance_name()).set(
            poll_interval
        )

        # Log polling state periodically (only when backing off)
        if not task_found and poll_interval > settings.worker_poll_min_interval_seconds:
            logger.debug(
                "worker_idle",
                poll_interval=poll_interval,
                worker_id=WORKER_ID,
            )

        # Sleep using current poll interval
        # Optimization: If we processed a task, don't sleep (or sleep very briefly)
        # to immediately pick up the next task (e.g., subtask just created).
        if not task_found:
            time.sleep(poll_interval)
        else:
            # Yield briefly to prevent CPU hogging but stay responsive
            time.sleep(0.01)


def _process_task_row_legacy(conn, cur, row):  # noqa: PLR0915, PLR0912
    """
    DEPRECATED: Use WorkerStateMachine instead.
    Process a single task or subtask row from the database.
    """
    source_type = row.get("source_type", "task")

    # Route to appropriate handler based on source type
    if source_type == "subtask":
        return _process_subtask(conn, cur, row)

    # For regular tasks, check task type
    task_type = row["type"]

    # Check if it's an agent task (agent:*)
    if is_agent_task(task_type):
        return _process_agent_task(conn, cur, row)

    # Check if it's a workflow task
    if is_workflow_task(task_type):
        return _process_workflow_task(conn, cur, row)

    # Regular task - existing behavior
    task_id = str(row["id"])
    task_input = row["input"]
    task_start_time = time.time()

    # Extract trace context from task input to continue the trace
    trace_ctx, cleaned_input = extract_trace_context(task_input)

    logger.info(
        "task_picked",
        task_id=task_id,
        task_type=task_type,
        trace_id=get_current_trace_id() or "none",
    )

    # Update heartbeat
    worker_heartbeat.labels(service="worker", instance=get_instance_name()).set_to_current_time()

    # Create span for task processing, using extracted context
    with tracer.start_as_current_span(
        f"process_task:{task_type}", context=trace_ctx, kind=trace.SpanKind.CONSUMER
    ) as span:
        # Add span attributes
        span.set_attribute("task.id", task_id)
        span.set_attribute("task.type", task_type)

        try:
            # Mark as running in DB (immediate, reliable)
            cur.execute(
                "UPDATE tasks SET status = 'running', updated_at = now() WHERE id = %s",
                (task_id,),
            )
            conn.commit()

            # Notify API (best-effort)
            notify_api_async(task_id, "running")

            # Extract user_id_hash from input (if present)
            user_id_hash = cleaned_input.pop("_user_id_hash", None)

            # Audit Log: Task Started
            log_audit_event(
                conn,
                "task_started",
                resource_id=task_id,
                user_id_hash=user_id_hash,
                meta={"task_type": task_type},
            )
            conn.commit()  # Commit audit log

            # Execute the task (this will create child spans for OpenRouter calls)
            result = execute_task(task_type, cleaned_input, user_id_hash)
            task_duration = time.time() - task_start_time

            # Handle result format - could be dict with 'output' and 'usage' or just output
            if isinstance(result, dict) and "usage" in result:
                output = result["output"]
                usage = result["usage"]
            else:
                # Backward compatibility - treat entire result as output
                output = result
                usage = None

            # Inject trace ID into output for UI linking
            current_trace_id = get_current_trace_id()
            if current_trace_id:
                if isinstance(output, dict):
                    output["_trace_id"] = current_trace_id
                elif isinstance(output, str):
                    # If output is a string, we can't easily add a key, so we wrap it
                    # or just rely on the UI checking input context as fallback.
                    # But for better UX, let's try to wrap it if it looks like JSON,
                    # otherwise we might need a separate column or just accept it.
                    # For now, let's only inject if it's already a dict to avoid breaking changes.
                    pass

            # Mark as done in DB with cost tracking
            if usage:
                cur.execute(
                    """
                    UPDATE tasks
                    SET status = 'done',
                        output = %s,
                        user_id_hash = %s,
                        model_used = %s,
                        input_tokens = %s,
                        output_tokens = %s,
                        total_cost = %s,
                        generation_id = %s,
                        updated_at = now()
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
                        task_id,
                    ),
                )
            else:
                # No usage data - update output only
                cur.execute(
                    """
                    UPDATE tasks
                    SET status = 'done', output = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (Json(output), task_id),
                )
            conn.commit()

            # Audit Log: Task Completed
            log_audit_event(
                conn,
                "task_completed",
                resource_id=task_id,
                user_id_hash=user_id_hash,
                meta={
                    "total_cost": float(usage.get("total_cost", 0)) if usage else 0,
                    "input_tokens": usage.get("input_tokens", 0) if usage else 0,
                    "output_tokens": usage.get("output_tokens", 0) if usage else 0,
                    "model_used": usage.get("model_used") if usage else None,
                    "duration_seconds": task_duration,
                },
            )
            conn.commit()

            # Notify API for metrics and WebSocket (best-effort)
            notify_api_async(task_id, "done", output=output)

            # Set span status to OK
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("task.duration_seconds", task_duration)

            logger.info(
                "task_completed",
                task_id=task_id,
                task_type=task_type,
                status="done",
                duration_seconds=f"{task_duration:.3f}",
                trace_id=get_current_trace_id(),
            )

        except Exception as e:
            # Mark as error in DB (immediate, reliable)
            error_msg = str(e)
            task_duration = time.time() - task_start_time

            cur.execute(
                """
                UPDATE tasks
                SET status = 'error', error = %s, updated_at = now()
                WHERE id = %s
                """,
                (error_msg, task_id),
            )
            conn.commit()

            # Audit Log: Task Failed
            # We need to try to get user_id_hash if we can, but it might not be extracted yet if error happened early
            # In this flow, we extracted it early, so we should have it if it was in input.
            # However, user_id_hash variable is local to the try block.
            # We need to ensure it's available in except block or re-extract.
            # For simplicity in this patch, we'll re-extract or use None if not available easily.
            # Actually, let's just use what we have. 'user_id_hash' might be unbound if error before assignment.
            try:
                uid_hash = user_id_hash if "user_id_hash" in locals() else None
            except UnboundLocalError:
                uid_hash = None

            log_audit_event(
                conn,
                "task_failed",
                resource_id=task_id,
                user_id_hash=uid_hash,
                meta={"error": error_msg, "duration_seconds": task_duration},
            )
            conn.commit()

            # Notify API for metrics (best-effort)
            notify_api_async(task_id, "error", error=error_msg)

            # Set span status to ERROR
            span.set_status(Status(StatusCode.ERROR, error_msg))
            span.set_attribute("task.duration_seconds", task_duration)
            span.record_exception(e)

            logger.error(
                "task_failed",
                task_id=task_id,
                task_type=task_type,
                error=error_msg,
                duration_seconds=f"{task_duration:.3f}",
                trace_id=get_current_trace_id(),
            )

    # Force flush spans to ensure they're exported to Tempo immediately
    # Without this, spans are buffered and may never be sent
    try:
        provider = otel_trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush(timeout_millis=5000)
            logger.debug("trace_flushed", task_id=task_id)
    except Exception as e:
        logger.warning("trace_flush_failed", error=str(e))


def run_worker() -> None:
    """Main entry point for worker process."""
    from app.worker_state import WorkerStateMachine

    worker_id = get_instance_name()
    state_machine = WorkerStateMachine(worker_id=worker_id)
    state_machine.run()


if __name__ == "__main__":
    run_worker()
