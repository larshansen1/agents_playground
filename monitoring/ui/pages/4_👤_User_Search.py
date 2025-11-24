"""User search page for troubleshooting."""

import asyncio
import hashlib

import streamlit as st
from data.database import get_db_client

st.set_page_config(page_title="User Search", page_icon="👤", layout="wide")

st.title("👤 User Search")
st.markdown("Search for tasks by user email for troubleshooting")
st.markdown("---")

# Email input
user_email = st.text_input(
    "Enter user email address:",
    placeholder="user@example.com",
    help="Enter the user's email address to find all their tasks",
)

if user_email:
    # Hash the email
    user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()

    st.info(f"🔍 **Searching for:** {user_email}")
    st.code(f"user_id_hash: {user_id_hash}", language="text")

    db = get_db_client()

    try:
        # Fetch tasks for this user
        tasks = asyncio.run(db.get_tasks_by_user(user_id_hash))

        if tasks:
            st.success(f"✅ Found {len(tasks)} task(s)")

            # Display task summary
            st.subheader("📊 Task Summary")
            col1, col2, col3, col4 = st.columns(4)

            total_tasks = len(tasks)
            done_tasks = sum(1 for t in tasks if t["status"] == "done")
            error_tasks = sum(1 for t in tasks if t["status"] == "error")
            total_cost = sum(float(t["total_cost"] or 0) for t in tasks)

            col1.metric("Total Tasks", total_tasks)
            col2.metric("Completed", done_tasks)
            col3.metric("Failed", error_tasks)
            col4.metric("Total Cost", f"${total_cost:.4f}")

            st.markdown("---")

            # Display tasks in expandable sections
            st.subheader("🔍 Task Details")

            for task in tasks:
                status_emoji = {"done": "✅", "error": "❌", "pending": "⏳", "running": "🔄"}.get(
                    task["status"], "❓"
                )

                with st.expander(
                    f"{status_emoji} {task['type']} - {task['id']} ({task['status']})",
                    expanded=False,
                ):
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.write("**Task ID:**", task["id"])
                        st.write("**Type:**", task["type"])
                        st.write("**Status:**", task["status"])
                        st.write("**Created:**", task["created_at"])

                    with col_b:
                        st.write("**Updated:**", task["updated_at"])
                        if task["total_cost"]:
                            st.write("**Cost:**", f"${float(task['total_cost']):.6f}")
                        if task["input_tokens"]:
                            st.write(
                                "**Tokens:**",
                                f"{task['input_tokens']:,} in / {task['output_tokens']:,} out",
                            )

                    # Fetch subtasks for this task
                    subtasks = asyncio.run(db.get_subtasks_by_task(task["id"]))

                    if subtasks:
                        st.write(f"**Subtasks:** {len(subtasks)}")
                        for subtask in subtasks:
                            st.text(
                                f"  • {subtask['agent_type']} (iter {subtask['iteration']}) - {subtask['status']}"
                            )

                    # Fetch audit logs for this task
                    audit_logs = asyncio.run(db.get_audit_logs_by_task(task["id"]))

                    if audit_logs:
                        st.write(f"**Audit Trail:** {len(audit_logs)} events")
                        for log in audit_logs:
                            st.text(f"  • {log['timestamp']}: {log['event_type']}")
        else:
            st.warning(f"⚠️ No tasks found for user: {user_email}")
            st.info("💡 Make sure the email address is correct and the user has created tasks.")

    except Exception as e:
        st.error(f"❌ Error querying database: {e!s}")
        st.exception(e)
else:
    st.info("👆 Enter a user email address above to search for their tasks")

    # Show example
    with st.expander("How it works"):
        st.markdown("""
        ### User Privacy & Search

        For privacy reasons, we don't store plain email addresses in the database. Instead:

        1. **Storage**: When a task is created, the user's email is hashed (SHA-256) and stored as `user_id_hash`
        2. **Search**: When you search by email, we hash it the same way and query by the hash
        3. **Matching**: This allows us to find all tasks for a user without storing their actual email

        ### Use Cases

        - **Troubleshooting**: User reports "my tasks are failing" - search their email to see what's happening
        - **Cost Analysis**: See how much a specific user is spending on tasks
        - **Support**: Investigate specific user issues

        ### SQL Query

        Behind the scenes, this page runs:
        ```sql
        SELECT * FROM tasks
        WHERE user_id_hash = SHA256('user@example.com')
        ORDER BY created_at DESC;
        ```
        """)
