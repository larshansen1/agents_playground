"""Main entry point for the management UI."""

import asyncio

import streamlit as st
from config import config
from data.database import get_db_client

# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main page content
st.title("🎯 Task Backend Manager")
st.markdown("---")

st.markdown("""
### Welcome to the Task Backend Management UI

This dashboard provides real-time monitoring and analytics for your task processing system.

**Available Pages:**
- 📊 **Dashboard**: Real-time task monitoring and system status
- 💰 **Costs**: Cost tracking and analysis
- 📈 **Analytics**: Historical trends and insights
- 🔍 **Task Search**: Find and inspect individual tasks

**Getting Started:**
1. Use the sidebar to navigate between pages
2. All pages auto-refresh to show the latest data
3. Filter and search to find specific information

---

#### System Overview
""")

# Database client import moved to top
db = get_db_client()

# Use asyncio to run async functions
try:
    stats = asyncio.run(db.get_task_stats())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tasks", f"{stats.get('total', 0):,}")

    with col2:
        st.metric("Pending", f"{stats.get('pending', 0):,}", delta=None)

    with col3:
        st.metric("Completed", f"{stats.get('done', 0):,}", delta=None)

    with col4:
        st.metric("Failed", f"{stats.get('error', 0):,}", delta=None)

    st.success("✅ Database connection successful")

except Exception as e:
    st.error(f"❌ Database connection failed: {e!s}")
    st.info(
        "💡 Make sure the database is running and environment variables are configured correctly."
    )

st.markdown("---")
st.markdown("*Select a page from the sidebar to get started*")
