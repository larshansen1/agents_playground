#!/usr/bin/env python3
"""Test script for creating and monitoring a workflow task."""

import json
import time

import requests

API_URL = "http://localhost:8000"


def create_workflow_task():
    """Create a research-assessment workflow task."""
    url = f"{API_URL}/tasks"
    payload = {
        "type": "workflow:research_assessment",
        "input": {"topic": "What are the main benefits of microservices architecture?"},
    }

    print("Creating workflow task...")
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    task = response.json()

    print(f"✅ Workflow task created: {task['id']}")
    print(f"   Type: {task['type']}")
    print(f"   Status: {task['status']}")
    return task["id"]


def check_task_status(task_id):
    """Check the status of a task."""
    url = f"{API_URL}/tasks/{task_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def check_subtasks(task_id):
    """Check subtasks for a workflow (if API endpoint exists)."""
    url = f"{API_URL}/tasks/{task_id}/subtasks"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None


def monitor_workflow(task_id, max_wait=120):
    """Monitor workflow progress."""
    print(f"\nMonitoring workflow {task_id}...")
    print("=" * 60)

    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        task = check_task_status(task_id)
        status = task["status"]

        if status != last_status:
            print(f"\n[{time.strftime('%H:%M:%S')}] Status: {status}")
            if task.get("total_cost"):
                print(f"   Cost so far: ${task['total_cost']:.6f}")
            last_status = status

        if status in ("done", "error"):
            print("\n" + "=" * 60)
            print("✅ WORKFLOW COMPLETED" if status == "done" else "❌ WORKFLOW FAILED")
            print("=" * 60)

            if status == "done" and task.get("output"):
                print("\nFinal output:")
                print(json.dumps(task["output"], indent=2))

            if status == "error" and task.get("error"):
                print(f"\nError: {task['error']}")

            print("\nCost Summary:")
            print(f"  Input tokens:  {task.get('input_tokens', 0)}")
            print(f"  Output tokens: {task.get('output_tokens', 0)}")
            print(f"  Total cost:    ${task.get('total_cost', 0):.6f}")
            print(f"  Model(s) used: {task.get('model_used', 'N/A')}")

            return task

        time.sleep(2)

    print("\n⏱️  Timeout reached")
    return task


def main():
    """Main test function."""
    try:
        # Create workflow
        task_id = create_workflow_task()

        # Monitor progress
        final_task = monitor_workflow(task_id)

        print(f"\nFinal task ID: {final_task['id']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")


if __name__ == "__main__":
    main()
