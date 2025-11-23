"""Cost tracking and analysis page."""

import asyncio

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config import config
from data.database import get_db_client

st.title("💰 Cost Tracking")

# Time range selector in sidebar
st.sidebar.markdown("### Time Range")
time_range = st.sidebar.selectbox(
    "Analysis Period",
    options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
    index=2,
)

# Map selection to days
time_range_days = {
    "Last 24 Hours": 1,
    "Last 7 Days": 7,
    "Last 30 Days": 30,
    "All Time": 9999,  # Large number for all-time
}
days = time_range_days[time_range]

# Database client
db = get_db_client()


# Fetch data with caching
@st.cache_data(ttl=60)
def fetch_cost_summary(days: int):
    """Fetch cost summary."""
    return asyncio.run(db.get_cost_summary(days=days))


@st.cache_data(ttl=60)
def fetch_cost_trends(days: int):
    """Fetch daily cost trends."""
    return asyncio.run(db.get_cost_trends(days=min(days, 30)))


@st.cache_data(ttl=60)
def fetch_top_users(limit: int = 10):
    """Fetch top users by cost."""
    return asyncio.run(db.get_top_users_by_cost(limit=limit))


try:
    # Get cost summary
    summary = fetch_cost_summary(days)

    # Cost overview metrics
    st.markdown(f"### Cost Overview - {time_range}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_cost = summary["total_cost"]
        st.metric("💵 Total Cost", f"${total_cost:.2f}", help="Total cost for selected period")

    with col2:
        avg_cost = summary["avg_cost_per_task"]
        st.metric("📊 Avg Cost/Task", f"${avg_cost:.4f}", help="Average cost per task")

    with col3:
        total_tasks = summary["total_tasks"]
        st.metric("📋 Tasks with Cost", f"{total_tasks:,}", help="Number of tasks with cost data")

    with col4:
        unique_users = summary["unique_users"]
        st.metric("👥 Active Users", f"{unique_users:,}", help="Number of unique users")

    # Token usage metrics
    st.markdown("### Token Usage")

    col1, col2, col3 = st.columns(3)

    with col1:
        input_tokens = summary["total_input_tokens"]
        st.metric("⬇️ Input Tokens", f"{input_tokens:,}")

    with col2:
        output_tokens = summary["total_output_tokens"]
        st.metric("⬆️ Output Tokens", f"{output_tokens:,}")

    with col3:
        total_tokens = input_tokens + output_tokens
        cost_per_1k = (total_cost / total_tokens * 1000) if total_tokens > 0 else 0
        st.metric("💎 Cost/1K Tokens", f"${cost_per_1k:.4f}")

    st.markdown("---")

    # Cost trends chart
    if days <= 30:
        st.markdown("### Daily Cost Trends")

        trends_df = fetch_cost_trends(days)

        if not trends_df.empty:
            # Create dual-axis chart: cost + task count
            fig = go.Figure()

            # Add cost line
            fig.add_trace(
                go.Scatter(
                    x=trends_df["date"],
                    y=trends_df["daily_cost"],
                    name="Daily Cost",
                    mode="lines+markers",
                    line={"color": "#2ecc71", "width": 3},
                    yaxis="y1",
                )
            )

            # Add task count bars
            fig.add_trace(
                go.Bar(
                    x=trends_df["date"],
                    y=trends_df["task_count"],
                    name="Task Count",
                    marker={"color": "#3498db", "opacity": 0.6},
                    yaxis="y2",
                )
            )

            # Update layout for dual axes
            fig.update_layout(
                title="Cost and Task Volume Over Time",
                xaxis={"title": "Date"},
                yaxis={
                    "title": {"text": "Cost ($)", "font": {"color": "#2ecc71"}},
                    "tickfont": {"color": "#2ecc71"},
                },
                yaxis2={
                    "title": {"text": "Task Count", "font": {"color": "#3498db"}},
                    "tickfont": {"color": "#3498db"},
                    "overlaying": "y",
                    "side": "right",
                },
                hovermode="x unified",
                height=400,
            )

            st.plotly_chart(fig, width="stretch")

            # Cost projection
            if len(trends_df) >= 3:
                recent_avg = trends_df.tail(7)["daily_cost"].mean()
                projected_monthly = recent_avg * 30

                st.info(
                    f"📈 **Projected Monthly Cost**: ${projected_monthly:.2f} (based on last 7 days average: ${recent_avg:.2f}/day)"
                )

                if projected_monthly > config.COST_ALERT_THRESHOLD:
                    st.warning(
                        f"⚠️ Projected monthly cost exceeds alert threshold of ${config.COST_ALERT_THRESHOLD:.2f}"
                    )
        else:
            st.info("No cost data available for the selected period.")

    st.markdown("---")

    # Top spenders
    st.markdown("### Top Spenders")

    top_users_df = fetch_top_users(limit=10)

    if not top_users_df.empty:
        # Display as two columns
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### By Total Cost")

            # Format the dataframe
            display_df = top_users_df.copy()
            display_df["user_id_hash"] = (
                display_df["user_id_hash"].fillna("Anonymous").str[:16] + "..."
            )
            display_df["total_cost"] = display_df["total_cost"].apply(lambda x: f"${x:.4f}")
            display_df["avg_cost"] = display_df["avg_cost"].apply(lambda x: f"${x:.4f}")

            display_df = display_df.rename(
                columns={
                    "user_id_hash": "User Hash",
                    "task_count": "Tasks",
                    "total_cost": "Total Cost",
                    "avg_cost": "Avg Cost",
                }
            )

            st.dataframe(display_df, width="stretch", hide_index=True)

        with col2:
            st.markdown("#### Cost Distribution")

            # Pie chart of top users
            fig = px.pie(
                top_users_df,
                values="total_cost",
                names=top_users_df["user_id_hash"].fillna("Anonymous").str[:8] + "...",
                title="Cost Share by User",
                hole=0.4,
            )

            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(height=400)

            st.plotly_chart(fig, width="stretch")
    else:
        st.info("No user cost data available.")

    st.markdown("---")

    # Token efficiency analysis
    st.markdown("### Token Efficiency")

    if summary["total_input_tokens"] > 0 and summary["total_output_tokens"] > 0:
        col1, col2 = st.columns(2)

        with col1:
            # Token distribution pie chart
            token_data = pd.DataFrame(
                {
                    "Type": ["Input Tokens", "Output Tokens"],
                    "Count": [summary["total_input_tokens"], summary["total_output_tokens"]],
                }
            )

            fig = px.pie(
                token_data,
                values="Count",
                names="Type",
                title="Token Distribution",
                color_discrete_sequence=["#3498db", "#e74c3c"],
            )

            st.plotly_chart(fig, width="stretch")

        with col2:
            # Token ratio
            ratio = summary["total_output_tokens"] / summary["total_input_tokens"]

            st.metric(
                "Output/Input Ratio", f"{ratio:.2f}x", help="Ratio of output tokens to input tokens"
            )

            st.markdown(f"""
            **Token Statistics:**
            - Input: {summary["total_input_tokens"]:,} tokens
            - Output: {summary["total_output_tokens"]:,} tokens
            - Total: {summary["total_input_tokens"] + summary["total_output_tokens"]:,} tokens
            """)

except Exception as e:
    st.error(f"❌ Error loading cost data: {e!s}")
    st.info("Check database connection and configuration.")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
