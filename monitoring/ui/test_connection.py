"""Quick test script to verify database connectivity."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from data.database import get_db_client

from config import config  # type: ignore[attr-defined]


async def test_connection():
    """Test database connection and basic queries."""
    print("=" * 60)
    print("Management UI - Database Connection Test")
    print("=" * 60)
    print()

    print(f"Database URL: {config.DATABASE_URL}")
    print()

    db = get_db_client()

    try:
        # Test 1: Get task stats
        print("Test 1: Fetching task statistics...")
        stats = await db.get_task_stats()
        print(f"✅ Success! Task stats: {stats}")
        print()

        # Test 2: Get recent tasks
        print("Test 2: Fetching recent tasks (limit 5)...")
        tasks_df = await db.get_recent_tasks(limit=5)
        print(f"✅ Success! Retrieved {len(tasks_df)} tasks")
        if not tasks_df.empty:
            print(f"   Columns: {list(tasks_df.columns)}")
        print()

        # Test 3: Get cost summary
        print("Test 3: Fetching cost summary (last 30 days)...")
        cost_summary = await db.get_cost_summary(days=30)
        print(f"✅ Success! Cost summary: {cost_summary}")
        print()

        print("=" * 60)
        print("✅ All tests passed! Database connection is working.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ Error: {e!s}")
        print()
        print("Troubleshooting:")
        print("1. Check that PostgreSQL is running: docker-compose ps postgres")
        print("2. Verify DATABASE_URL environment variable")
        print("3. Ensure database has tasks table")
        return False

    finally:
        await db.close()


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
