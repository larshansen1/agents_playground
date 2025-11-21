"""Task search and detail viewer."""

import asyncio
import json

import streamlit as st
from data.database import get_db_client

st.title("🔍 Task Search")

# Database client
db = get_db_client()

# Search input
st.markdown("### Search by Task ID")
task_id = st.text_input(
    "Enter Task ID (UUID)",
    placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000",
    help="Enter the full UUID of the task to view details",
)

if task_id:
    try:
        # Fetch task details
        task = asyncio.run(db.get_task_by_id(task_id))

        if task is None:
            st.warning(f"❌ Task with ID `{task_id}` not found.")
        else:
            st.success("✅ Task found!")

            # Display task information
            st.markdown("---")
            st.markdown("### Task Details")

            # Basic info
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Status", task["status"].upper())

            with col2:
                st.metric("Type", task["type"])

            with col3:
                if task["model_used"]:
                    st.metric("Model", task["model_used"])
                else:
                    st.metric("Model", "N/A")

            # Timestamps
            st.markdown("#### Timeline")
            col1, col2 = st.columns(2)

            with col1:
                st.text(f"Created: {task['created_at']}")

            with col2:
                st.text(f"Updated: {task['updated_at']}")

            # Duration
            if task["created_at"] and task["updated_at"]:
                duration = (task["updated_at"] - task["created_at"]).total_seconds()
                st.text(f"Duration: {duration:.2f} seconds")

            # Cost information
            if task["total_cost"] and task["total_cost"] > 0:
                st.markdown("#### Cost Breakdown")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Cost", f"${task['total_cost']:.4f}")

                with col2:
                    st.metric("Input Tokens", f"{task['input_tokens']:,}")

                with col3:
                    st.metric("Output Tokens", f"{task['output_tokens']:,}")

                with col4:
                    total_tokens = task["input_tokens"] + task["output_tokens"]
                    st.metric("Total Tokens", f"{total_tokens:,}")

            # User information
            if task["user_id_hash"]:
                st.markdown("#### User Information")
                st.text(f"User Hash: {task['user_id_hash']}")

            # Input/Output
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Input")
                if task["input"]:
                    st.json(task["input"])
                else:
                    st.info("No input data")

            with col2:
                st.markdown("#### Output")
                if task["output"]:
                    st.json(task["output"])
                else:
                    st.info("No output data yet")

            # Error (if any)
            if task["error"]:
                st.markdown("---")
                st.markdown("#### Error")
                st.error(task["error"])

            # Trace link (if Grafana is available)
            st.markdown("---")
            st.markdown("#### Distributed Tracing")

            # Check if trace context is available (in output or input)
            trace_id = "N/A"

            # Check output first (most reliable for completed tasks)
            if (
                task["output"]
                and isinstance(task["output"], dict)
                and "_trace_id" in task["output"]
            ):
                trace_id = task["output"]["_trace_id"]
            # Fallback to input context
            elif task["input"] and "_trace_context" in task["input"]:
                trace_context = task["input"]["_trace_context"]
                trace_id = trace_context.get("trace_id", "N/A")

            if trace_id != "N/A":
                # Display trace ID
                st.code(trace_id, language=None)

                # Calculate time range based on task timestamp
                if task["created_at"]:
                    # Use task creation time to set search range
                    from datetime import timedelta

                    task_time = task["created_at"]
                    # Search 5 minutes before and after task creation
                    from_time = int((task_time - timedelta(minutes=5)).timestamp() * 1000)
                    to_time = int((task_time + timedelta(minutes=30)).timestamp() * 1000)

                    # Link to Grafana Tempo (using TraceQL)
                    # Link to Grafana Tempo (using TraceQL)
                    import json
                    import urllib.parse

                    # TraceQL query: { traceID = "..." }
                    traceql_query = f'{{ traceID = "{trace_id}" }}'

                    # Construct Grafana state object
                    # We use a simpler structure that Grafana accepts reliably
                    explore_state = {
                        "datasource": "tempo",
                        "queries": [
                            {
                                "refId": "A",
                                "datasource": {"type": "tempo", "uid": "tempo"},
                                "queryType": "traceql",
                                "query": traceql_query,
                            }
                        ],
                        "range": {"from": str(from_time), "to": str(to_time)},
                    }

                    # Encode the state object properly
                    # Grafana expects: /explore?left={"datasource":"Tempo",...}
                    state_json = json.dumps(explore_state)
                    encoded_state = urllib.parse.quote(state_json)

                    grafana_url = f"http://localhost:3002/explore?orgId=1&left={encoded_state}"

                    st.markdown(f"[🔗 View in Grafana Tempo]({grafana_url})")

                    st.info(f"""
                    **Troubleshooting**: If trace is not visible in Grafana:
                    - Traces are only available for tasks that completed recently
                    - This task was created at: {task_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    - Check that Tempo is receiving traces: `docker-compose logs tempo`
                    - Verify worker is sending traces: `docker-compose logs task-worker | grep trace`
                    """)
                else:
                    st.warning("Cannot generate time-specific link (missing task timestamp)")
            else:
                st.info("No distributed tracing information available for this task.")

    except Exception as e:
        st.error(f"❌ Error fetching task: {e!s}")

else:
    st.info("👆 Enter a task ID above to view details")

    st.markdown("---")
    st.markdown("""
    ### Tips

    - Task IDs are UUIDs (e.g., `550e8400-e29b-41d4-a716-446655440000`)
    - You can find task IDs in the **Dashboard** page
    - Copy the full ID from the recent tasks table
    - Distributed tracing links will appear if the task has trace context
    """)
