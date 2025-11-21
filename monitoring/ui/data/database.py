"""Database client for querying task data."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
from config import config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


class DatabaseClient:
    """Client for querying the tasks database."""

    def __init__(self):
        """Initialize database connection."""
        # Use NullPool to avoid connection reuse issues with Streamlit caching
        self.engine = create_async_engine(
            config.DATABASE_URL,
            echo=False,
            poolclass=NullPool,  # Create new connection for each request
        )
        self.async_session = sessionmaker(  # type: ignore[call-overload]
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_recent_tasks(
        self, limit: int = 100, status_filter: str | None = None
    ) -> pd.DataFrame:
        """
        Get recent tasks as a pandas DataFrame.

        Args:
            limit: Maximum number of tasks to return
            status_filter: Optional status filter (pending, running, done, error)

        Returns:
            DataFrame with task data
        """
        query = """
            SELECT
                id,
                type,
                status,
                created_at,
                updated_at,
                user_id_hash,
                model_used,
                input_tokens,
                output_tokens,
                total_cost,
                error
            FROM tasks
        """

        if status_filter:
            query += " WHERE status = :status"

        query += " ORDER BY created_at DESC LIMIT :limit"

        async with self.async_session() as session:
            if status_filter:
                result = await session.execute(
                    text(query), {"status": status_filter, "limit": limit}
                )
            else:
                result = await session.execute(text(query), {"limit": limit})

            rows = result.fetchall()

            if not rows:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(
                [dict(row._mapping) for row in rows],
                columns=[
                    "id",
                    "type",
                    "status",
                    "created_at",
                    "updated_at",
                    "user_id_hash",
                    "model_used",
                    "input_tokens",
                    "output_tokens",
                    "total_cost",
                    "error",
                ],
            )

            # Calculate duration for completed tasks
            df["duration_seconds"] = (df["updated_at"] - df["created_at"]).dt.total_seconds()

            return df

    async def get_task_stats(self) -> dict[str, Any]:
        """
        Get overall task statistics.

        Returns:
            Dictionary with task counts by status
        """
        query = text("""
            SELECT
                status,
                COUNT(*) as count
            FROM tasks
            GROUP BY status
        """)

        async with self.async_session() as session:
            result = await session.execute(query)
            rows = result.fetchall()

            stats = {row.status: row.count for row in rows}

            # Add total
            stats["total"] = sum(stats.values())

            return stats

    async def get_cost_summary(self, days: int = 30) -> dict[str, Any]:
        """
        Get cost summary for the specified time period.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with cost statistics
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        query = text("""
            SELECT
                COUNT(*) as total_tasks,
                COUNT(DISTINCT user_id_hash) as unique_users,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(AVG(total_cost), 0) as avg_cost_per_task
            FROM tasks
            WHERE created_at >= :cutoff_date
              AND total_cost IS NOT NULL
        """)

        async with self.async_session() as session:
            result = await session.execute(query, {"cutoff_date": cutoff_date})
            row = result.first()

            if not row:
                return {
                    "total_tasks": 0,
                    "unique_users": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost": 0.0,
                    "avg_cost_per_task": 0.0,
                }

            return {
                "total_tasks": row.total_tasks,
                "unique_users": row.unique_users,
                "total_input_tokens": row.total_input_tokens,
                "total_output_tokens": row.total_output_tokens,
                "total_cost": float(row.total_cost),
                "avg_cost_per_task": float(row.avg_cost_per_task),
            }

    async def get_cost_trends(self, days: int = 7) -> pd.DataFrame:
        """
        Get daily cost trends.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with daily costs
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        query = text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as task_count,
                COALESCE(SUM(total_cost), 0) as daily_cost,
                COALESCE(SUM(input_tokens), 0) as input_tokens,
                COALESCE(SUM(output_tokens), 0) as output_tokens
            FROM tasks
            WHERE created_at >= :cutoff_date
              AND total_cost IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """)

        async with self.async_session() as session:
            result = await session.execute(query, {"cutoff_date": cutoff_date})
            rows = result.fetchall()

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame(
                [dict(row._mapping) for row in rows],
                columns=["date", "task_count", "daily_cost", "input_tokens", "output_tokens"],
            )

    async def get_top_users_by_cost(self, limit: int = 10) -> pd.DataFrame:
        """
        Get top users by total cost.

        Args:
            limit: Number of users to return

        Returns:
            DataFrame with user costs
        """
        query = text("""
            SELECT
                user_id_hash,
                COUNT(*) as task_count,
                COALESCE(SUM(total_cost), 0) as total_cost,
                COALESCE(AVG(total_cost), 0) as avg_cost
            FROM tasks
            WHERE user_id_hash IS NOT NULL
              AND total_cost IS NOT NULL
            GROUP BY user_id_hash
            ORDER BY total_cost DESC
            LIMIT :limit
        """)

        async with self.async_session() as session:
            result = await session.execute(query, {"limit": limit})
            rows = result.fetchall()

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame(
                [dict(row._mapping) for row in rows],
                columns=["user_id_hash", "task_count", "total_cost", "avg_cost"],
            )

    async def get_task_by_id(self, task_id: str) -> dict[str, Any] | None:
        """
        Get a single task by ID.

        Args:
            task_id: UUID of the task

        Returns:
            Task data as dictionary, or None if not found
        """
        query = text("""
            SELECT *
            FROM tasks
            WHERE id = :task_id
        """)

        async with self.async_session() as session:
            result = await session.execute(query, {"task_id": task_id})
            row = result.first()

            if not row:
                return None

            return dict(row._mapping)

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


# Singleton instance
_db_client = None


def get_db_client() -> DatabaseClient:
    """Get or create database client singleton."""
    global _db_client  # noqa: PLW0603
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client
