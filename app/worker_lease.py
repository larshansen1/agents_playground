"""Helper functions for lease-based task acquisition in worker."""

from datetime import UTC, datetime, timedelta

import psycopg2

from app.config import settings
from app.logging_config import get_logger
from app.metrics import (
    tasks_lease_renewed_total,
    tasks_recovered_total,
    tasks_retry_exhausted_total,
)

logger = get_logger(__name__)


def recover_expired_leases(conn, worker_id: str) -> int:
    """
    Recover tasks/subtasks with expired leases.

    Returns number of tasks recovered.
    """
    cur = conn.cursor()
    recovered_count = 0

    try:
        # Recover expired task leases
        cur.execute(
            """
            UPDATE tasks
            SET status = 'pending',
                locked_at = NULL,
                locked_by = NULL,
                lease_timeout = NULL,
                updated_at = NOW()
            WHERE status = 'running'
              AND lease_timeout < NOW()
              AND try_count < max_tries
            RETURNING id, type, try_count, locked_by
            """
        )
        recovered_tasks = cur.fetchall()

        for task in recovered_tasks:
            task_id, task_type, try_count, old_worker = task
            logger.warning(
                "lease_expired_recovered",
                task_id=str(task_id),
                task_type=task_type,
                try_count=try_count,
                old_worker=old_worker,
                worker_id=worker_id,
            )
            tasks_recovered_total.labels(task_type=task_type).inc()
            recovered_count += 1

        # Mark tasks that exceeded max retries as error
        cur.execute(
            """
            UPDATE tasks
            SET status = 'error',
                error = 'Maximum retry attempts exceeded',
                locked_at = NULL,
                locked_by = NULL,
                lease_timeout = NULL,
                updated_at = NOW()
            WHERE status = 'running'
              AND lease_timeout < NOW()
              AND try_count >= max_tries
            RETURNING id, type
            """
        )
        exhausted_tasks = cur.fetchall()

        for task in exhausted_tasks:
            task_id, task_type = task
            logger.error(
                "task_retry_exhausted",
                task_id=str(task_id),
                task_type=task_type,
            )
            tasks_retry_exhausted_total.labels(task_type=task_type).inc()

        # Recover expired subtask leases
        cur.execute(
            """
            UPDATE subtasks
            SET status = 'pending',
                locked_at = NULL,
                locked_by = NULL,
                lease_timeout = NULL,
                updated_at = NOW()
            WHERE status = 'running'
              AND lease_timeout < NOW()
              AND try_count < max_tries
            RETURNING id, agent_type, try_count
            """
        )
        recovered_subtasks = cur.fetchall()

        for subtask in recovered_subtasks:
            subtask_id, agent_type, try_count = subtask
            logger.warning(
                "subtask_lease_expired_recovered",
                subtask_id=str(subtask_id),
                agent_type=agent_type,
                try_count=try_count,
            )
            tasks_recovered_total.labels(task_type=f"subtask:{agent_type}").inc()
            recovered_count += 1

        # Mark subtasks that exceeded max retries as error
        cur.execute(
            """
            UPDATE subtasks
            SET status = 'error',
                error = 'Maximum retry attempts exceeded',
                locked_at = NULL,
                locked_by = NULL,
                lease_timeout = NULL,
                updated_at = NOW()
            WHERE status = 'running'
              AND lease_timeout < NOW()
              AND try_count >= max_tries
            RETURNING id, agent_type
            """
        )
        exhausted_subtasks = cur.fetchall()

        for subtask in exhausted_subtasks:
            subtask_id, agent_type = subtask
            logger.error(
                "subtask_retry_exhausted",
                subtask_id=str(subtask_id),
                agent_type=agent_type,
            )
            tasks_retry_exhausted_total.labels(task_type=f"subtask:{agent_type}").inc()

        conn.commit()

        if recovered_count > 0:
            logger.info(
                "lease_recovery_completed",
                recovered_count=recovered_count,
                worker_id=worker_id,
            )

        return recovered_count

    except psycopg2.Error as e:
        logger.error("lease_recovery_failed", error=str(e))
        conn.rollback()
        return 0
    finally:
        cur.close()


def renew_lease(conn, task_id: str, source_type: str, worker_id: str) -> bool:
    """
    Renew lease timeout for a task being processed.

    Returns True if renewal succeeded, False otherwise.
    """
    cur = conn.cursor()

    try:
        lease_duration = timedelta(seconds=settings.worker_lease_duration_seconds)
        new_timeout = datetime.now(UTC) + lease_duration

        table = "tasks" if source_type == "task" else "subtasks"
        cur.execute(
            f"""  # nosec B608
            UPDATE {table}
            SET lease_timeout = %s,
                updated_at = NOW()
            WHERE id = %s
              AND locked_by = %s
              AND status = 'running'
            """,
            (new_timeout, task_id, worker_id),
        )

        if cur.rowcount > 0:
            conn.commit()
            tasks_lease_renewed_total.labels(worker_id=worker_id).inc()
            logger.debug(
                "lease_renewed",
                task_id=task_id,
                source_type=source_type,
                worker_id=worker_id,
            )
            return True
        logger.warning(
            "lease_renewal_failed",
            task_id=task_id,
            source_type=source_type,
            worker_id=worker_id,
            reason="task_not_found_or_wrong_owner",
        )
        return False

    except psycopg2.Error as e:
        logger.error(
            "lease_renewal_error",
            task_id=task_id,
            error=str(e),
        )
        conn.rollback()
        return False
    finally:
        cur.close()
