# Task Management API with mTLS & WebSocket

A modern, async FastAPI-based task management service with mutual TLS authentication, PostgreSQL database, real-time WebSocket updates, and Open WebUI integration.

## Features

- **Async Architecture** - SQLAlchemy async ORM with asyncpg driver
- **mTLS Authentication** - Secure client authentication using mutual TLS
- **PostgreSQL Database** - Task storage with connection pooling
- **REST API** - Full CRUD operations for task management
- **WebSocket Support** - Real-time task status updates
- **Background Worker** - Async task processing with OpenTelemetry instrumentation
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

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## Code Quality

This project uses modern Python tooling for maintaining code quality:

- **🚀 Ruff** - Fast linting and formatting
- **🔍 Mypy** - Static type checking
- **🔒 Bandit** - Security vulnerability scanning
- **🪝 Pre-commit** - Automated git hooks

**Quick Setup:**
```bash
# Install development tools
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run all quality checks
make validate
```

See [docs/CODE_QUALITY.md](docs/CODE_QUALITY.md) for comprehensive setup guide and [docs/CODE_QUALITY_REPORT.md](docs/CODE_QUALITY_REPORT.md) for initial scan results.

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_tasks_status ON tasks(status);
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

## Observability

The system is fully instrumented with OpenTelemetry for comprehensive observability:

- **OpenTelemetry**: Captures traces and metrics from API and Worker services.
- **Tempo**: Stores distributed traces, allowing end-to-end visualization of task processing.
- **Prometheus**: Collects metrics from the OpenTelemetry collector.
- **Grafana**: Visualizes traces and metrics in a unified dashboard.

The worker automatically creates spans for each task, including child spans for external API calls (OpenRouter), providing detailed insights into latency and errors.

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
