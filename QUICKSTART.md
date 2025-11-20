# Quick Start Guide

Get the Task Management API running in under 5 minutes using docker-compose.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)

## Getting Started

### 1. Environment Setup

Copy the environment template and configure:
```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work for local development):
```env
DATABASE_URL=postgresql://openwebui:openwebui_password@postgres:5432/openwebui
OPENROUTER_API_KEY=your_api_key_here
WEBUI_SECRET_KEY=your_secret_key
```

### 2. Generate SSL Certificates

For mTLS authentication:
```bash
./utils/generate_certs.sh
```

This creates certificates in `certs/`:
- `ca-cert.pem`, `ca-key.pem` (Certificate Authority)
- `server-cert.pem`, `server-key.pem` (Server certificate)
- `client-cert.pem`, `client-key.pem` (Client certificate)

### 3. Start the Stack

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** - Database (port 5432)
- **Qdrant** - Vector database (port 6333)
- **Task API** - FastAPI service (port 8000)
- **Task Worker** - Background task processor
- **Open WebUI** - Web interface (port 3000)

### 4. Verify Services

Check all services are running:
```bash
docker-compose ps
```

Test the API:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "websocket_connections": 0
}
```

## Testing the API

### Option 1: Using Test Scripts

```bash
# Test REST API
python utils/test_api.py

# Test WebSocket
python utils/test_websocket.py
```

### Option 2: Manual Testing

Create a task:
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "summarize",
    "input": {"text": "This is a test document"}
  }'
```

Get task status (use ID from response):
```bash
curl http://localhost:8000/tasks/{task_id}
```

List all tasks:
```bash
curl http://localhost:8000/tasks
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Open WebUI | http://localhost:3000 | Web interface |
| Task API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Database |
| Qdrant | http://localhost:6333 | Vector DB |

## Using Open WebUI

1. Open http://localhost:3000 in your browser
2. Create an account (first user becomes admin)
3. Install the Task Queue tool (see [docs/OPENWEBUI.md](docs/OPENWEBUI.md))
4. Upload a document and use: `@queue summarize this document`

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f task-api
docker-compose logs -f task-worker
docker-compose logs -f open-webui
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## Troubleshooting

### Services won't start

Check docker-compose logs:
```bash
docker-compose logs
```

### Database connection errors

Wait for PostgreSQL to be ready:
```bash
docker-compose logs postgres
```

### Worker not processing tasks

Check worker logs:
```bash
docker-compose logs task-worker
```

Ensure tasks table exists:
```bash
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c "\\d tasks"
```

### Port conflicts

If ports 3000, 5432, 6333, or 8000 are in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change host port
```

## Next Steps

- Read the [README.md](README.md) for detailed API documentation
- Set up Open WebUI integration: [docs/OPENWEBUI.md](docs/OPENWEBUI.md)
- Configure environment variables for your use case
- Add observability (Prometheus/Grafana) for production

## Development Mode

To run with live reload:
```bash
# Modify docker-compose.yml to add --reload flag
# Or run locally:
source .venv/bin/activate
uvicorn app.main:app --reload
```

See [README.md](README.md) for more details on local development.
