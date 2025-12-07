# API Reference

Complete API documentation for the multi-agent task orchestration system.

## Base URL

```
http://localhost:8000
```

For production, use HTTPS with mTLS certificate authentication.

## Authentication

### mTLS (Mutual TLS)

API requires client certificate authentication:

```bash
curl https://localhost:8443/tasks \
  --cacert certs/ca-cert.pem \
  --cert certs/client-cert.pem \
  --key certs/client-key.pem
```

**Development:** Use HTTP on port 8000 (no auth required)
**Production:** Use HTTPS on port 8443 with certificates

## Core Endpoints

### Health Check

Check API and database health.

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected",
  "websocket_connections": 3
}
```

---

### Create Task

Submit a new task for execution.

```http
POST /tasks
Content-Type: application/json

{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "renewable energy",
    "user_email": "user@example.com"
  }
}
```

**Request Fields:**
- `type` (string, required): Task type - `workflow:name`, `agent:type`, or `tool:name`
- `input` (object, required): Input data for the task
  - `user_email` (string, optional): User's email (hashed for privacy)
  - `tenant_id` (string, optional): Tenant identifier
  - `_trace_context` (object, optional): Distributed tracing context

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow:research_assessment",
  "status": "pending",
  "input": {
    "topic": "renewable energy"
  },
  "output": null,
  "error": null,
  "user_id_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "tenant_id": null,
  "model_used": null,
  "input_tokens": null,
  "output_tokens": null,
  "total_cost": null,
  "generation_id": null,
  "created_at": "2025-12-07T15:30:00Z",
  "updated_at": "2025-12-07T15:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `422 Unprocessable Entity`: Validation error

---

### Get Task

Retrieve task status and results.

```http
GET /tasks/{task_id}
```

**Path Parameters:**
- `task_id` (UUID): Task identifier

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow:research_assessment",
  "status": "done",
  "input": {
    "topic": "renewable energy"
  },
  "output": {
    "findings": "Renewable energy sources include...",
    "approved": true,
    "iterations": 1
  },
  "error": null,
  "model_used": "openai/gpt-4o-mini",
  "input_tokens": 1250,
  "output_tokens": 830,
  "total_cost": 0.002145,
  "created_at": "2025-12-07T15:30:00Z",
  "updated_at": "2025-12-07T15:32:15Z"
}
```

**Error Responses:**
- `404 Not Found`: Task does not exist

---

### List Tasks

Query tasks with filters.

```http
GET /tasks?status_filter=pending&limit=50&user_id_hash=abc123
```

**Query Parameters:**
- `status_filter` (string, optional): Filter by status - `pending`, `running`, `done`, `error`
- `limit` (integer, optional): Maximum results (default: 50, max: 100)
- `user_id_hash` (string, optional): Filter by user hash
- `tenant_id` (string, optional): Filter by tenant

**Response** (200 OK):
```json
{
  "tasks": [
    { "id": "...", "type": "...", "status": "pending", ... },
    { "id": "...", "type": "...", "status": "running", ... }
  ],
  "count": 2
}
```

---

### Update Task

Manually update task status (admin use).

```http
PATCH /tasks/{task_id}
Content-Type: application/json

{
  "status": "done",
  "output": {"result": "completed"}
}
```

**Request Fields:**
- `status` (string, optional): New status
- `output` (object, optional): Task output
- `error` (string, optional): Error message

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "done",
  "output": {"result": "completed"},
  ...
}
```

**Error Responses:**
- `404 Not Found`: Task does not exist
- `422 Unprocessable Entity`: Invalid status transition

---

## Registry Endpoints

### List Agents

Get all registered agents.

```http
GET /admin/agents
```

**Response** (200 OK):
```json
{
  "agents": [
    {
      "type": "research",
      "description": "Conducts research on topics",
      "tools": ["web_search"],
      "config": {"model": "gpt-4-turbo"}
    },
    {
      "type": "assessment",
      "description": "Assesses research quality",
      "tools": ["fact_checker"],
      "config": {"model": "gpt-4-turbo"}
    }
  ]
}
```

---

### List Tools

Get all registered tools.

```http
GET /admin/tools
```

**Response** (200 OK):
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web using Brave API",
      "config": {"api_key_env": "BRAVE_API_KEY"}
    }
  ]
}
```

---

### List Workflows

Get all registered workflows.

```http
GET /admin/workflows
```

**Response** (200 OK):
```json
{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with quality feedback loop",
      "coordination_type": "iterative_refinement",
      "max_iterations": 3,
      "steps": [
        {"agent_type": "research", "name": "conduct_research"},
        {"agent_type": "assessment", "name": "assess_quality"}
      ]
    }
  ]
}
```

---

### Execute Agent Directly

Bypass task queue and execute agent synchronously.

```http
POST /tasks/agent
Content-Type: application/json

{
  "agent_type": "research",
  "input": {
    "topic": "climate change"
  }
}
```

**Request Fields:**
- `agent_type` (string, required): Agent type to execute
- `input` (object, required): Input data for agent

**Response** (200 OK):
```json
{
  "output": {
    "findings": "Climate change refers to...",
    "sources": ["https://..."]
  },
  "usage": {
    "input_tokens": 450,
    "output_tokens": 320,
    "total_cost": 0.001234
  }
}
```

**Error Responses:**
- `404 Not Found`: Agent type not registered
- `500 Internal Server Error`: Agent execution failed

---

## WebSocket API

Real-time task updates via WebSocket.

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
  ws.send('ping');  // Keep-alive
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
};
```

### Message Format

**Server → Client:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "done",
  "output": {...},
  "timestamp": "2025-12-07T15:32:15Z"
}
```

**Events:**
- `task_created`: New task submitted
- `task_updated`: Status or output changed
- `task_completed`: Task finished (done or error)

### Keep-Alive

Send ping every 30 seconds to keep connection alive:
```javascript
setInterval(() => ws.send('ping'), 30000);
```

---

## Task Types

### Workflow Tasks

Execute multi-agent workflows defined in YAML.

**Format:** `workflow:{workflow_name}`

**Example:**
```json
{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "artificial intelligence"
  }
}
```

See [WORKFLOWS.md](WORKFLOWS.md) for workflow definitions.

---

### Agent Tasks

Execute single agents directly.

**Format:** `agent:{agent_type}`

**Example:**
```json
{
  "type": "agent:research",
  "input": {
    "topic": "quantum computing"
  }
}
```

---

### Tool Tasks

Execute tools directly.

**Format:** `tool:{tool_name}`

**Example:**
```json
{
  "type": "tool:web_search",
  "input": {
    "query": "best practices for REST APIs"
  }
}
```

---

## Task Status Values

Tasks follow this lifecycle:

| Status | Description |
|--------|-------------|
| `pending` | Waiting for worker to claim |
| `running` | Being processed by worker |
| `done` | Successfully completed |
| `error` | Failed with error message |

**State transitions:**
```
pending → running → done
pending → running → error
running → pending (on lease expiry)
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "INVALID_AGENT_TYPE",
  "status_code": 404
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TASK_TYPE` | 400 | Unknown task type format |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `AGENT_NOT_FOUND` | 404 | Agent type not registered |
| `WORKFLOW_NOT_FOUND` | 404 | Workflow not found |
| `TASK_NOT_FOUND` | 404 | Task ID does not exist |
| `EXECUTION_ERROR` | 500 | Agent/workflow execution failed |

---

## Rate Limiting

**Current:** No rate limiting implemented

**Best practices:**
- Limit to 100 tasks/minute per client
- Use WebSocket for updates instead of polling
- Poll at maximum once per 2 seconds if using REST

---

## Distributed Tracing

Include trace context for unified observability:

```json
{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "machine learning",
    "_trace_context": {
      "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
      "span_id": "00f067aa0ba902b7"
    }
  }
}
```

The system propagates this context through all subtasks and agent executions.

See [MONITORING.md](MONITORING.md) for trace visualization.

---

## Examples

### Python Client

```python
import requests
import time

# Create task
response = requests.post('http://localhost:8000/tasks', json={
    'type': 'workflow:research_assessment',
    'input': {'topic': 'blockchain technology'}
})
task = response.json()
task_id = task['id']

# Poll for completion
while True:
    response = requests.get(f'http://localhost:8000/tasks/{task_id}')
    task = response.json()

    if task['status'] in ['done', 'error']:
        print(f"Result: {task['output']}")
        break

    time.sleep(2)
```

### cURL Examples

```bash
# Create task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"type": "agent:research", "input": {"topic": "solar energy"}}'

# Get task
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000

# List pending tasks
curl "http://localhost:8000/tasks?status_filter=pending&limit=10"

# List workflows
curl http://localhost:8000/admin/workflows
```

---

## See Also

- [Workflows Guide](WORKFLOWS.md) - Create declarative workflows
- [Architecture](ARCHITECTURE.md) - System design and data flow
- [Monitoring](MONITORING.md) - Observability and debugging
