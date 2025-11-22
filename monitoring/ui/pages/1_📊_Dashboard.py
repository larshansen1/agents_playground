"""Dashboard page showing real-time task monitoring."""

import asyncio
from datetime import datetime

import pandas as pd
import streamlit as st
from config import config
from data.database import get_db_client

st.title("📊 Task Dashboard")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
if auto_refresh:
    st.sidebar.info(f"Refreshing every {config.REFRESH_INTERVAL}s")

# Filters in sidebar
st.sidebar.markdown("### Filters")
status_filter = st.sidebar.selectbox(
    "Status",
    options=["All", "pending", "running", "done", "error"],
    index=0,
)
limit = st.sidebar.slider(
    "Max tasks to display",
    min_value=10,
    max_value=500,
    value=config.MAX_TASKS_DISPLAY,
    step=10,
)

# Database client
db = get_db_client()


# Fetch data
@st.cache_data(ttl=config.REFRESH_INTERVAL)
def fetch_task_stats():
    """Fetch task statistics."""
    return asyncio.run(db.get_task_stats())


@st.cache_data(ttl=config.REFRESH_INTERVAL)
def fetch_recent_tasks(status: str | None, limit: int):
    """Fetch recent tasks."""
    return asyncio.run(db.get_recent_tasks(limit=limit, status_filter=status))


try:
    # Get stats
    stats = fetch_task_stats()

    # Display metrics
    st.markdown("### System Status")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📋 Total Tasks", f"{stats.get('total', 0):,}")

    with col2:
        pending_count = stats.get("pending", 0)
        st.metric("⏳ Pending", f"{pending_count:,}")

    with col3:
        running_count = stats.get("running", 0)
        st.metric("🔄 Running", f"{running_count:,}")

    with col4:
        done_count = stats.get("done", 0)
        success_rate = (done_count / stats["total"] * 100) if stats.get("total", 0) > 0 else 0
        st.metric("✅ Done", f"{done_count:,}", delta=f"{success_rate:.1f}%")

    with col5:
        error_count = stats.get("error", 0)
        error_rate = (error_count / stats["total"] * 100) if stats.get("total", 0) > 0 else 0
        st.metric("❌ Failed", f"{error_count:,}", delta=f"-{error_rate:.1f}%")

    st.markdown("---")

    # Recent tasks
    st.markdown("### Recent Tasks")

    # Apply filter
    status_param = None if status_filter == "All" else status_filter
    df = fetch_recent_tasks(status_param, limit)

    if df.empty:
        st.info("No tasks found matching the selected filters.")
    else:
        # Store full task IDs before formatting
        full_task_ids = df["id"].astype(str).tolist()

        # Format the data for display
        display_df = df.copy()

        # Keep full task IDs for clickability
        display_df["id"] = display_df["id"].astype(str)

        # Format timestamps
        display_df["created_at"] = pd.to_datetime(display_df["created_at"])
        display_df["updated_at"] = pd.to_datetime(display_df["updated_at"])

        # Calculate relative time (ensure timezone-aware comparison)
        import pytz  # type: ignore[import-untyped]

        now = datetime.now(pytz.UTC)  # Use timezone-aware datetime
        display_df["age"] = (now - display_df["created_at"]).apply(
            lambda x: f"{int(x.total_seconds() // 60)}m"
            if x.total_seconds() < 3600
            else f"{int(x.total_seconds() // 3600)}h"
        )

        # Format cost
        display_df["cost"] = display_df["total_cost"].apply(
            lambda x: f"${x:.4f}" if pd.notna(x) and x > 0 else "-"
        )

        # Format duration
        display_df["duration"] = display_df["duration_seconds"].apply(
            lambda x: f"{x:.1f}s" if pd.notna(x) and x > 0 else "-"
        )

        # Select columns to display
        display_columns = [
            "id",
            "type",
            "status",
            "age",
            "duration",
            "model_used",
            "cost",
            "user_id_hash",
        ]

        # Rename for better display
        display_df = display_df[display_columns].rename(
            columns={
                "id": "Task ID",
                "type": "Type",
                "status": "Status",
                "age": "Age",
                "duration": "Duration",
                "model_used": "Model",
                "cost": "Cost",
                "user_id_hash": "User Hash",
            }
        )

        # Color-code status using styling
        def color_status(val):
            colors = {
                "pending": "background-color: #f0f0f0; color: #666",
                "running": "background-color: #e3f2fd; color: #1976d2",
                "done": "background-color: #e8f5e9; color: #388e3c",
                "error": "background-color: #ffebee; color: #d32f2f",
            }
            return colors.get(val, "")

        # Create clickable links for task IDs
        # Streamlit pages are accessed by their display name, URL-encoded
        # The page "3_🔍_Task_Search.py" is accessed as "Task_Search"
        display_df["Task ID"] = display_df["Task ID"].apply(
            lambda task_id: f"Task_Search?task_id={task_id}"
        )

        # Display dataframe with column config to make task IDs clickable
        st.info("💡 Click on a Task ID to view full details")

        st.dataframe(
            display_df,
            width="stretch",
            height=600,
            column_config={
                "Task ID": st.column_config.LinkColumn(
                    "Task ID",
                    help="Click to view task details",
                    display_text=r"^(.{8}).*",  # Show first 8 chars as display text
                ),
                "Status": st.column_config.Column(
                    "Status",
                    help="Task status",
                ),
            },
        )

        # Summary info
        st.caption(f"Showing {len(display_df)} tasks")

except Exception as e:
    st.error(f"❌ Error loading dashboard data: {e!s}")
    st.info("Check database connection and configuration.")

# Auto-refresh logic
if auto_refresh:
    import time

    time.sleep(config.REFRESH_INTERVAL)
    st.rerun()
