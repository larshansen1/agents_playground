#!/usr/bin/env python3
"""
Test script for the FastAPI Task Management Service.

This script demonstrates:
1. Creating a task
2. Retrieving task status
3. Updating task status
4. Listing tasks

Note: Requires the service to be running with mTLS enabled.
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "https://localhost:8443"
CA_CERT = "certs/ca-cert.pem"
CLIENT_CERT = "certs/client-cert.pem"
CLIENT_KEY = "certs/client-key.pem"


def create_task():
    """Create a new task."""
    print("\n1. Creating a new task...")
    
    task_data = {
        "type": "summarize_document",
        "input": {
            "text": """
            Artificial Intelligence (AI) has emerged as one of the most transformative technologies 
            of the 21st century. Machine learning, a subset of AI, enables computers to learn from 
            data without being explicitly programmed. Deep learning, which uses neural networks with 
            multiple layers, has achieved remarkable success in image recognition, natural language 
            processing, and game playing.
            
            The applications of AI span across various industries. In healthcare, AI systems assist 
            doctors in diagnosing diseases and predicting patient outcomes. In finance, algorithms 
            detect fraudulent transactions and optimize trading strategies. Autonomous vehicles use 
            AI to navigate roads and make split-second decisions. Virtual assistants like Siri and 
            Alexa rely on natural language processing to understand and respond to user queries.
            
            However, AI also raises important ethical concerns. Bias in training data can lead to 
            discriminatory outcomes. Privacy issues arise from the collection and analysis of vast 
            amounts of personal data. Job displacement due to automation is a growing concern. 
            The potential misuse of AI in surveillance and autonomous weapons poses risks to 
            civil liberties and international security.
            
            As AI continues to advance, it is crucial to develop frameworks for responsible AI 
            development and deployment. This includes ensuring transparency in AI decision-making, 
            protecting individual privacy, addressing algorithmic bias, and establishing guidelines 
            for AI safety and ethics.
            """
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tasks",
        json=task_data,
        cert=(CLIENT_CERT, CLIENT_KEY),
        verify=CA_CERT
    )
    
    if response.status_code == 201:
        task = response.json()
        print(f"✓ Task created successfully!")
        print(f"  Task ID: {task['id']}")
        print(f"  Type: {task['type']}")
        print(f"  Status: {task['status']}")
        return task['id']
    else:
        print(f"✗ Failed to create task: {response.status_code}")
        print(f"  {response.text}")
        return None


def get_task(task_id):
    """Get task status by ID."""
    print(f"\n2. Retrieving task status...")
    
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}",
        cert=(CLIENT_CERT, CLIENT_KEY),
        verify=CA_CERT
    )
    
    if response.status_code == 200:
        task = response.json()
        print(f"✓ Task retrieved successfully!")
        print(f"  ID: {task['id']}")
        print(f"  Type: {task['type']}")
        print(f"  Status: {task['status']}")
        print(f"  Created: {task['created_at']}")
        return task
    else:
        print(f"✗ Failed to get task: {response.status_code}")
        print(f"  {response.text}")
        return None


def update_task(task_id):
    """Update task status."""
    print(f"\n3. Updating task status...")
    
    update_data = {
        "status": "completed",
        "output": {
            "summary": "AI is a transformative 21st-century technology with applications in healthcare, finance, and autonomous systems, but raises ethical concerns about bias, privacy, and job displacement.",
            "key_points": [
                "Machine learning enables computers to learn from data without explicit programming",
                "Deep learning has achieved success in image recognition, NLP, and game playing",
                "AI applications span healthcare, finance, autonomous vehicles, and virtual assistants",
                "Ethical concerns include bias, privacy issues, job displacement, and potential misuse"
            ],
            "missing_info": [
                "Specific examples of AI bias incidents",
                "Quantitative data on job displacement",
                "Current regulatory frameworks for AI"
            ],
            "suggested_next_questions": [
                "What are the current regulations for AI development?",
                "How can we mitigate algorithmic bias?",
                "What jobs are most at risk from AI automation?"
            ]
        }
    }
    
    response = requests.patch(
        f"{BASE_URL}/tasks/{task_id}",
        json=update_data,
        cert=(CLIENT_CERT, CLIENT_KEY),
        verify=CA_CERT
    )
    
    if response.status_code == 200:
        task = response.json()
        print(f"✓ Task updated successfully!")
        print(f"  Status: {task['status']}")
        print(f"  Output: {task['output']}")
        return task
    else:
        print(f"✗ Failed to update task: {response.status_code}")
        print(f"  {response.text}")
        return None


def list_tasks():
    """List all tasks."""
    print(f"\n4. Listing all tasks...")
    
    response = requests.get(
        f"{BASE_URL}/tasks?limit=10",
        cert=(CLIENT_CERT, CLIENT_KEY),
        verify=CA_CERT
    )
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"✓ Retrieved {len(tasks)} task(s)")
        for task in tasks:
            print(f"  - {task['id']}: {task['type']} ({task['status']})")
        return tasks
    else:
        print(f"✗ Failed to list tasks: {response.status_code}")
        print(f"  {response.text}")
        return None


def test_health():
    """Test health endpoint."""
    print("\n0. Testing health endpoint...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            cert=(CLIENT_CERT, CLIENT_KEY),
            verify=CA_CERT,
            timeout=5
        )
        
        if response.status_code == 200:
            health = response.json()
            print(f"✓ Service is healthy!")
            print(f"  Database: {health.get('database')}")
            print(f"  WebSocket connections: {health.get('websocket_connections')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL Error: {e}")
        print("\nTip: Make sure the certificates are properly generated and the paths are correct.")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Could not connect to the service: {e}")
        return False
    except Exception as e:
        print(f"✗ Error ({type(e).__name__}): {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("FastAPI Task Management Service - Test Script")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("\n⚠ Service is not running. Please start it first:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8443 \\")
        print("    --ssl-keyfile certs/server-key.pem \\")
        print("    --ssl-certfile certs/server-cert.pem \\")
        print("    --ssl-ca-certs certs/ca-cert.pem \\")
        print("    --ssl-cert-reqs 2")
        sys.exit(1)
    
    # Create task
    task_id = create_task()
    if not task_id:
        sys.exit(1)
    
    # Small delay
    time.sleep(0.5)
    
    # Get task
    get_task(task_id)
    
    # Update task
    update_task(task_id)
    
    # List tasks
    list_tasks()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
