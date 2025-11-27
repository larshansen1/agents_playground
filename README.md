# Task Management API with mTLS & WebSocket

A modern, async FastAPI-based task management service with mutual TLS authentication, PostgreSQL database, real-time WebSocket updates, and Open WebUI integration.

## Features

- **Async Architecture** - SQLAlchemy async ORM with asyncpg driver
- **mTLS Authentication** - Secure client authentication using mutual TLS
- **PostgreSQL Database** - Task storage with connection pooling
- **REST API** - Full CRUD operations for task management
- **WebSocket Support** - Real-time task status updates
- **Background Worker** - Async task processing with OpenTelemetry instrumentation
- **Lease-Based Task Acquisition** - Multi-worker safe task claiming with automatic recovery from failures
- **User Tracking** - Privacy-preserving user tracking with SHA-256 hashed emails
- **Multi-Tenancy** - Tenant isolation for environment-based segmentation
- **Audit Logging** - Immutable audit trail for all operations
- **Management UI** - Streamlit dashboard with user search and analytics
- **Open WebUI Integration** - Pre-built tool for chat interface
- **Docker Compose** - Complete stack deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

```bash
# 1. Clone and navigate to project
git clone <repository>
cd agents_playground

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Generate SSL certificates
./utils/generate_certs.sh

# 4. Start the stack
docker-compose up -d

# 5. Test the API
curl http://localhost:8000/health
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for development workflow and code quality practices.

## Architecture

### Services

The docker-compose stack includes:

| Service | Port | Description |
|---------|------|-------------|
| **task-api** | 8000 | FastAPI REST API with async SQLAlchemy |
| **task-worker** | - | Background task processor |
| **postgres** | 5432 | PostgreSQL 18 with pgvector extension |
| **qdrant** | 6333 | Vector database for embeddings |
| **open-webui** | 3000 | Web UI for chat interface |

### Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with asyncpg
- **PostgreSQL** - Primary database with JSONB support
- **Pydantic Settings** - Environment-based configuration
- **WebSockets** - Real-time bidirectional communication
- **OpenTelemetry** - Distributed tracing and metrics
- **Qdrant** - Vector similarity search

## API Documentation

### Endpoints

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "websocket_connections": 0
}
```

#### Create Task
```http
POST /tasks
Content-Type: application/json

{
  "type": "summarize",
  "input": {"text": "Document to summarize..."}
}
```

Response:
```json
{
  "id": "uuid",
  "type": "summarize",
  "status": "pending",
  "input": {...},
  "output": null,
  "error": null,
  "created_at": "2025-11-18T20:15:48Z",
  "updated_at": "2025-11-18T20:15:48Z"
}
```

#### Get Task
```http
GET /tasks/{task_id}
```

#### List Tasks
```http
GET /tasks?status_filter=pending&limit=50
```

#### Update Task
```http
PATCH /tasks/{task_id}
Content-Type: application/json

{
  "status": "done",
  "output": {"summary": "..."}
}
```

### Task Status Values

Tasks progress through these states:
- `pending` - Task created, waiting for processing
- `running` - Currently being processed by worker
- `done` - Successfully completed
- `error` - Failed with error message

### WebSocket

Connect to `/ws` for real-time task updates:

```python
import asyncio
import websockets
import json

async def monitor_tasks():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        # Keep connection alive
        await ws.send('ping')

        # Receive updates
        while True:
            message = await ws.recv()
            data = json.loads(message)
            print(f"Task {data['task_id']}: {data['status']}")

asyncio.run(monitor_tasks())
```

Test with: `python utils/test_websocket.py`

## Testing

### Automated Tests

```bash
# Test REST API
python utils/test_api.py

# Test WebSocket connection
python utils/test_websocket.py
```

### Manual Testing

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"type": "summarize", "input": {"text": "test"}}'

# Get task by ID
curl http://localhost:8000/tasks/{task_id}

# List pending tasks
curl "http://localhost:8000/tasks?status_filter=pending"
```

## Project Structure

```
.
├── app/                       # Application code
│   ├── main.py               # FastAPI app with routers
│   ├── config.py             # Pydantic settings
│   ├── database.py           # Async SQLAlchemy engine
│   ├── db_sync.py            # Sync connection for worker
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic schemas
│   ├── tasks.py              # Task execution logic
│   ├── worker.py             # Background task processor
│   ├── websocket.py          # WebSocket manager
│   ├── middleware/
│   │   └── mtls.py           # mTLS authentication
│   └── routers/
│       └── tasks.py          # Task CRUD endpoints
├── certs/                     # SSL certificates (gitignored)
├── docs/
│   └── OPENWEBUI.md          # Open WebUI integration guide
├── postgres-init/             # Database initialization scripts
├── utils/
│   ├── generate_certs.sh     # Certificate generation
│   ├── test_api.py           # API test script
│   └── test_websocket.py     # WebSocket test script
├── docker-compose.yml         # Stack orchestration
├── Dockerfile                 # Task API container
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (gitignored)
├── .gitignore                # Git ignore rules
├── QUICKSTART.md             # Quick start guide
└── README.md                 # This file
```

## Database Schema

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    user_id_hash VARCHAR(64),      -- SHA-256 hashed user email
    tenant_id VARCHAR(100),          -- Environment identifier
    model_used VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_cost DECIMAL(10, 6),
    generation_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_user_hash ON tasks(user_id_hash);
CREATE INDEX idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX idx_tasks_user_tenant ON tasks(user_id_hash, tenant_id);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB
);

CREATE INDEX idx_audit_user ON audit_logs(user_id_hash);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_id);
```

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

```env
# Database
DATABASE_URL=postgresql://openwebui:openwebui_password@postgres:5432/openwebui

# OpenRouter API
OPENROUTER_API_KEY=your_key_here
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=gpt-4.1-mini

# Open WebUI
WEBUI_SECRET_KEY=your_secret_key
ENABLE_SIGNUP=true

# Task API (for Open WebUI)
TASK_API_URL=https://host.docker.internal:8443
CA_CERT_PATH=/app/backend/data/certs/ca-cert.pem
CLIENT_CERT_PATH=/app/backend/data/certs/client-cert.pem
CLIENT_KEY_PATH=/app/backend/data/certs/client-key.pem
```

### SSL Certificates

Generate test certificates:
```bash
./utils/generate_certs.sh
```

Creates:
- `ca-cert.pem`, `ca-key.pem` - Certificate Authority
- `server-cert.pem`, `server-key.pem` - Server certificate
- `client-cert.pem`, `client-key.pem` - Client certificate

**⚠️ For production**: Use properly signed certificates from a trusted CA.

## Open WebUI Integration

1. Access Open WebUI at http://localhost:3000
2. Install the Task Queue tool from `openwebui_task_tool.py`
3. Upload documents and use: `@queue summarize this document`

See [docs/OPENWEBUI.md](docs/OPENWEBUI.md) for complete integration guide.

## Declarative Workflows

Create multi-agent workflows using YAML without writing Python code:

```yaml
# app/workflows/my_workflow.yaml
name: my_workflow
coordination_type: sequential
steps:
  - agent_type: research
  - agent_type: assessment
```

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for complete workflow guide.

## Development

### Local Development

Run services individually:

```bash
# Start dependencies
docker-compose up -d postgres qdrant

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API locally
uvicorn app.main:app --reload --port 8000

# Run worker locally
python -m app.worker
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f task-api
docker-compose logs -f task-worker
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui

# View tasks
SELECT id, type, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 10;
```

## Security

- **mTLS**: Client certificate authentication for API
- **Certificate Storage**: Certs stored securely, gitignored
- **Database**: Strong passwords, internal network only
- **CORS**: Configure for production environment
- **Environment**: Secrets in `.env`, never committed

## Monitoring & Observability

The system provides comprehensive observability through distributed tracing, metrics, and a management UI:

### Distributed Tracing

Full end-to-end distributed tracing from OpenWebUI tool through workflow execution:

**Access Grafana**: http://localhost:3002

**What You Can See:**
- Complete trace timelines from `@queue` command to final result
- Multi-agent workflow execution with all iterations
- Individual agent spans (research, assessment)
- LLM API call duration and costs
- Iteration-level breakdown for complex workflows

**Trace Hierarchy Example:**
```
openwebui_tool.at_queue (28s)
├─ worker.process_workflow
├─ process_subtask:research (7.6s)
│  └─ llm.openrouter.chat_completion
└─ process_subtask:assessment (1.8s)
   └─ llm.openrouter.chat_completion
```

**How It Works:**
1. OpenWebUI tool generates a trace ID for each `@queue` command
2. Trace context propagates through API → Worker → Orchestrator → Agents
3. All spans link to the same trace ID for unified visibility
4. Grafana Tempo stores traces for querying and visualization

**Finding Traces:**
- Use Management UI Task Search to get direct Grafana links
- Search by trace ID in Grafana Explore
- Filter by service: `task-worker`, `task-api`

### Management UI

**Access Streamlit UI**: http://localhost:8501

The management UI provides three main views:

**1. Dashboard (📊)**
- Recent task activity with real-time updates
- Task status distribution (pending, running, done, error)
- Cost analytics by user and workflow type
- Quick navigation to task details

**2. Cost Analytics (💰)**
- Per-user cost breakdown with LLM token usage
- Model usage statistics
- Time-series cost trends
- Aggregated costs for multi-agent workflows

**3. Task Search (🔍)**
- Search tasks by ID
- View complete task details (input, output, error)
- Cost breakdown with token counts
- **Direct links to distributed traces in Grafana**
- Parent/child task relationships for workflows

**4. User Search (👤)**
- Search by email address to find all user's tasks
- Privacy-preserving (hashes email for lookup)
- View user's complete task history
- Cost analysis per user
- Audit log trail for troubleshooting

**Key Features:**
- Auto-refresh every 5 seconds on dashboard
```
- Click task IDs to navigate to detailed views
- Trace links automatically generated with correct time ranges
- Multi-agent workflow visibility with subtask breakdown

### Metrics & Alerts

**Prometheus**: http://localhost:9090

Available metrics:

| Metric Name | Type | Description |
|-------------|------|-------------|
| `tasks_created_total` | Counter | Total tasks created by type |
| `tasks_completed_total` | Counter | Total tasks completed by type and status |
| `tasks_pending` | Gauge | Number of tasks waiting to be processed (Queue Depth) |
| `tasks_in_flight` | Gauge | Current number of tasks being processed |
| `task_duration_seconds` | Histogram | Task processing duration in seconds |
| `worker_heartbeat_timestamp` | Gauge | Timestamp of last worker heartbeat |
| `worker_tasks_processed_total` | Counter | Total tasks processed by worker |
| `tasks_acquired_total` | Counter | Tasks acquired with lease |
| `active_leases_total` | Gauge | Number of active task leases |
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | HTTP request duration in seconds |
| `db_connections_active` | Gauge | Number of active database connections |
| `websocket_connections_active` | Gauge | Number of active WebSocket connections |

**OpenTelemetry Collector**: Aggregates traces and metrics from all services

### Accessing Services

```bash
# View live worker logs
docker-compose logs -f task-worker

# Check trace export
docker-compose logs -f otel-collector | grep -i tempo

# Query Prometheus metrics
curl http://localhost:9090/api/v1/query?query=tasks_created_total

# Database queries
docker exec -it postgres psql -U openwebui -d openwebui

# View recent tasks with trace context
SELECT id, type, status, input->'_trace_context'->>'trace_id' as trace_id
FROM tasks ORDER BY created_at DESC LIMIT 5;
```

### Multi-Agent Workflow Visibility

For workflow tasks (e.g., `workflow:research_assessment`):

1. **Task Hierarchy**: View parent task and all subtasks in Management UI
2. **Iteration Tracking**: See each research/assessment iteration clearly
3. **Cost Aggregation**: Parent task shows total cost across all iterations
4. **Unified Trace**: One trace ID links all agent executions together
5. **Timeline View**: Grafana shows complete workflow timeline with iteration spans

Example workflow trace shows:
- Initial research subtask (iteration 1)
- Assessment subtask (iteration 1)
- Revised research subtask (iteration 2) if needed
- Final assessment approval

All under one trace ID for complete visibility!

## User Tracking \u0026 Multi-Tenancy

The system implements privacy-preserving user tracking and tenant isolation for multi-environment deployments.

### User Privacy

**Email Hashing**: User emails are SHA-256 hashed before storage for privacy:
- Plain email sent to API (only in request body, never stored)
- API hashes email immediately: `user_id_hash = SHA256(email)`
- Only the hash is stored in database (tasks, subtasks, audit_logs)
- No plain emails in database or LLM prompts

**User Search**: Management UI allows searching by email:
1. Go to Management UI → **👤 User Search**
2. Enter email address (e.g., `user@example.com`)
3. System hashes it and queries `user_id_hash`
4. View all tasks, subtasks, and audit logs for that user

### Multi-Tenancy

**Tenant Isolation**: The `tenant_id` field identifies deployment environments:

**Configuration** (Open WebUI Tool):
```python
# In Open WebUI Admin → Workspace → Functions → Task Queue
# Set the valve:
tenant_id = "production"  # or "staging", "client-a", etc.
```

**Database Schema**:
```sql
-- All core tables have tenant_id
ALTER TABLE tasks ADD COLUMN tenant_id VARCHAR(100);
ALTER TABLE subtasks ADD COLUMN tenant_id VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN tenant_id VARCHAR(100);
ALTER TABLE workflow_state ADD COLUMN tenant_id VARCHAR(100);

-- Indexes for efficient querying
CREATE INDEX idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX idx_tasks_user_tenant ON tasks(user_id_hash, tenant_id);
```

**Querying by Tenant**:
```sql
-- Get all tasks for a tenant
SELECT * FROM tasks WHERE tenant_id = 'production';

-- Get user tasks within a tenant
SELECT * FROM tasks
WHERE tenant_id = 'production'
  AND user_id_hash = 'hash_value';
```

### Audit Logging

**Immutable Audit Trail**: All operations are logged to `audit_logs` table:

**Events Tracked**:
- `task_created` - When task is created via API
- `task_updated` - When task status or output changes
- `task_completed` - When task finishes (done or error)
- `workflow_initialized` - When multi-agent workflow starts
- `subtask_completed` - When subtask finishes

**Audit Log Schema**:
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,  -- Task/subtask ID
    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),
   timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB
);
```

**Query Examples**:
```sql
-- User's activity log
SELECT event_type, timestamp, metadata
FROM audit_logs
WHERE user_id_hash = 'hash_value'
ORDER BY timestamp DESC;

-- Tenant's audit trail
SELECT event_type, resource_id, timestamp
FROM audit_logs
WHERE tenant_id = 'production'
  AND timestamp \u003e NOW() - INTERVAL '7 days';
```

### Management UI Features

**1. Dashboard (📊)**
- Real-time task monitoring
- Tenant-based filtering (when configured)
- User activity summaries

**2. User Search (👤)**
- Search by email address
- View all user's tasks across tenants
- Cost analysis per user
- Complete audit trail

**3. Cost Analytics (💰)**
- Per-tenant cost breakdown
- Per-user cost within tenants
- Model usage by environment

**Troubleshooting Use Case**:
1. User reports: "My tasks are failing"
2. Go to Management UI → User Search
3. Enter their email
4. See all their tasks, errors, and audit logs
5. No need to search by hash manually!

## Troubleshooting

### Services won't start

```bash
docker-compose logs
docker-compose ps
```

### Database connection errors

Wait for PostgreSQL health check:
```bash
docker-compose logs postgres
```

### Worker not processing tasks

Check worker logs and task status:
```bash
docker-compose logs task-worker
curl http://localhost:8000/tasks
```

### Port conflicts

Modify ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change host port
```

## License

This project is provided as-is for demonstration purposes.

## Contributing

PRs welcome! Please ensure:
- Code follows existing patterns
- Tests pass
- Documentation is updated
- Commits are clear and atomic
