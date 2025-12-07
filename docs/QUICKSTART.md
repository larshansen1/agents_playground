# Quick Start Guide

Get your multi-agent task orchestration system running in under 10 minutes.

## Prerequisites

Before you begin, ensure you have:
- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Git**
- An **OpenRouter API key** ([get one here](https://openrouter.ai/))

### Verify Prerequisites

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version
# Docker Compose version v2.0.0 or higher
```

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository>
cd agents_playground

# Create environment file
cp .env.example .env
```

**Expected output:** `.env` file created

## Step 2: Configure API Keys

Edit `.env` and add your OpenRouter API key:

```bash
# Open in your editor
nano .env  # or vim, code, etc.
```

Set these required variables:
```env
OPENROUTER_API_KEY=your_key_here
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
```

**💡 Tip:** Keep other defaults as-is for your first run.

## Step 3: Generate SSL Certificates

```bash
./utils/generate_certs.sh
```

**Expected output:**
```
Generating CA certificate...
Generating server certificate...
Generating client certificate...
✅ Certificates generated successfully in ./certs/
```

## Step 4: Start the Stack

```bash
docker-compose up -d
```

**Expected output:**
```
Creating network "agents_playground_default"
Creating agents_playground-postgres-1 ... done
Creating agents_playground-qdrant-1   ... done
Creating agents_playground-task-api-1 ... done
Creating agents_playground-task-worker-1 ... done
Creating agents_playground-open-webui-1 ... done
```

Wait ~30 seconds for services to initialize.

## Step 5: Verify Installation

Check that services are healthy:

```bash
# Test the API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","websocket_connections":0}
```

Access the web interfaces:
- **Open WebUI**: http://localhost:3000 (chat interface)
- **Management UI**: http://localhost:8501 (monitoring dashboard)
- **Grafana**: http://localhost:3002 (distributed tracing)

## Step 6: Run Your First Workflow

### Option A: Via Open WebUI (Recommended)

1. Open http://localhost:3000
2. Create an account (or sign in)
3. Click **Workspace** → **Functions** in the sidebar
4. Search for "Task Queue Tool" and install it
5. In the chat, type:
   ```
   @flow research_assessment analyze the benefits of renewable energy
   ```
6. Watch the research agent gather information, then the assessment agent evaluate it!

### Option B: Via API

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "workflow:research_assessment",
    "input": {"topic": "benefits of renewable energy"}
  }'
```

**Response:**
```json
{
  "id": "abc123...",
  "type": "workflow:research_assessment",
  "status": "pending",
  ...
}
```

Check task status:
```bash
curl http://localhost:8000/tasks/abc123...
```

## Step 7: Monitor Execution

### Management UI
1. Open http://localhost:8501
2. Go to **🔍 Task Search**
3. Enter the task ID from step 6
4. View complete execution details, costs, and trace link

### Watch Worker Logs
```bash
docker-compose logs -f task-worker
```

You'll see:
- Task claimed by worker
- Research agent executing
- Assessment agent evaluating
- Final results

## What Just Happened?

You executed an **iterative refinement workflow** that:
1. **Research agent** gathered information about renewable energy
2. **Assessment agent** evaluated the research quality
3. If not approved, the cycle repeats with feedback (up to 3 iterations)
4. Results returned when quality threshold met

**Data flow:** OpenWebUI → API → PostgreSQL → Worker → Agent Registry → Research Agent → Assessment Agent → Results

## Next Steps

### Learn More
- **[Workflows Guide](WORKFLOWS.md)** - Create your own multi-agent workflows
- **[Agent Registry](AGENT_REGISTRY.md)** - Build custom agents
- **[Tool Registry](TOOL_REGISTRY.md)** - Add new tools
- **[API Reference](API_REFERENCE.md)** - Integrate programmatically

### Create Your First Workflow

```bash
# Create a new workflow file
cat > app/workflows/my_workflow.yaml << 'EOF'
name: my_workflow
description: My custom workflow
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: gather_info
  - agent_type: assessment
    name: verify_info
EOF

# Restart to load the new workflow
docker-compose restart task-api task-worker

# Use it
# In Open WebUI: @flow my_workflow analyze climate change
```

### Explore the System
- **View all workflows:** `curl http://localhost:8000/admin/workflows`
- **View all agents:** `curl http://localhost:8000/admin/agents`
- **View all tools:** `curl http://localhost:8000/admin/tools`

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose ps
```

### "Database connection error"
Wait for PostgreSQL to fully initialize (~30 seconds on first run):
```bash
docker-compose logs postgres
# Look for: "database system is ready to accept connections"
```

### Worker not processing tasks
```bash
# Check worker is running
docker-compose ps task-worker

# View worker logs
docker-compose logs task-worker

# Verify worker can connect to database
docker-compose logs task-worker | grep -i "connected"
```

### Port conflicts
If ports 8000, 3000, or 8501 are in use, modify `docker-compose.yml`:
```yaml
services:
  task-api:
    ports:
      - "8001:8000"  # Change host port
```

### More help
See [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

## Clean Up (Optional)

To stop and remove everything:
```bash
# Stop services
docker-compose down

# Remove volumes (deletes database data)
docker-compose down -v
```

---

**🎉 Congratulations!** You now have a working multi-agent orchestration system. Check out the [Workflows Guide](WORKFLOWS.md) to build your own agents and workflows.
