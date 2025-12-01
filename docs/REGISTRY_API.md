# Registry API Documentation

## Endpoints

### GET /admin/agents
Returns all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "research",
      "description": "Research agent for gathering information",
      "capabilities": ["web_search", "summarization"]
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/agents \
  --cert client.pem \
  --key client.key
```

### GET /admin/tools
Returns all registered tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information",
      "parameters": { ... }
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/tools \
  --cert client.pem \
  --key client.key
```

### GET /admin/workflows
Returns all registered workflows.

**Response:**
```json
{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with iterative assessment",
      "steps": ["research", "assessment"]
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/workflows \
  --cert client.pem \
  --key client.key
```

### POST /tasks/agent
Execute an agent directly.

**Request Body:**
```json
{
  "agent_name": "research",
  "input": "quantum computing trends"
}
```

**Response:**
```json
{
  "task_id": "12345",
  "status": "pending"
}
```

**Example:**
```bash
curl -X POST https://localhost:8000/tasks/agent \
  -H "Content-Type: application/json" \
  --cert client.pem \
  --key client.key \
  -d '{"agent_name": "research", "input": "quantum computing trends"}'
```
