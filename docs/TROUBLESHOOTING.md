# Troubleshooting Guide

Common issues and solutions for the multi-agent orchestration system.

## Quick Diagnostic Commands

```bash
# Check all services status
docker-compose ps

# View all logs
docker-compose logs

# Check specific service health
docker-compose logs task-api | tail -50
docker-compose logs task-worker | tail -50
docker-compose logs postgres | tail -50

# Test API connectivity
curl http://localhost:8000/health

# Check database connectivity
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c "SELECT 1;"
```

---

## Services Won't Start

### Symptom
```bash
docker-compose up -d
# One or more services show "Exited" or "Restarting"
```

### Diagnosis

```bash
# Check which services are failing
docker-compose ps

# View logs for failed service
docker-compose logs <service-name>
```

### Common Causes

**1. Port conflicts**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using the port
lsof -i :8000  # or :3000, :5432, etc.

# Kill the process or change port in docker-compose.yml
vi docker-compose.yml
# Change: "8001:8000" instead of "8000:8000"
```

**2. Missing environment variables**
```
Error: OPENROUTER_API_KEY not set
```

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify required variables
grep OPENROUTER_API_KEY .env

# If missing, copy from template
cp .env.example .env
# Edit and add your API key
```

**3. Docker out of resources**
```
Error: failed to allocate memory
```

**Solution:**
```bash
# Increase Docker memory (Docker Desktop → Settings → Resources)
# Or prune old containers/images
docker system prune -a
```

---

## Database Connection Errors

### Symptom
```
ERROR: could not connect to database
psycopg2.OperationalError: could not connect to server
```

### Diagnosis

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres | grep -i ready

# Expected output:
# "database system is ready to accept connections"
```

### Solutions

**1. PostgreSQL still initializing**

First startup takes ~30 seconds. Wait and retry.

```bash
# Watch initialization
docker-compose logs -f postgres

# When ready, restart dependent services
docker-compose restart task-api task-worker
```

**2. Wrong database credentials**

```bash
# Verify DATABASE_URL in .env
grep DATABASE_URL .env

# Should match docker-compose.yml postgres config
# Format: postgresql://user:password@host:port/dbname
```

**3. Database corrupted**

```bash
# Stop all services
docker-compose down

# Remove database volume (⚠️ deletes all data)
docker volume rm agents_playground_postgres_data

# Recreate
docker-compose up -d postgres

# Wait for initialization, then start other services
docker-compose up -d
```

---

## Worker Not Processing Tasks

### Symptom
Tasks stuck in "pending" status indefinitely.

### Diagnosis

```bash
# Check worker is running
docker-compose ps task-worker

# View recent worker activity
docker-compose logs task-worker --tail=100

# Check for tasks in database
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui \
  -c "SELECT id, type, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;"
```

### Solutions

**1. Worker crashed or not running**

```bash
# Check worker status
docker-compose ps task-worker

# If "Exited", view logs
docker-compose logs task-worker

# Restart worker
docker-compose restart task-worker
```

**2. Worker can't claim tasks (database lock)**

```bash
# Check for long-running queries
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c \
  "SELECT pid, age(clock_timestamp(), query_start), query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# Kill stuck queries if needed
# SELECT pg_terminate_backend(pid);
```

**3. Worker stuck on previous task**

```bash
# Check worker logs for current task
docker-compose logs task-worker | grep "Processing task"

# If stuck > 5 minutes, restart worker
docker-compose restart task-worker

# Lease will expire and task will be reclaimed
```

**4. No API keys configured**

```bash
# Worker fails if LLM API key missing
docker-compose logs task-worker | grep -i "api key"

# Check .env has OPENROUTER_API_KEY
grep OPENROUTER_API_KEY .env

# Add key and restart
docker-compose restart task-worker
```

---

## Workflow Failures

### Symptom
Workflow task shows status="error" with error message.

### Diagnosis

**Via Management UI:**
1. Open http://localhost:8501 → Task Search
2. Enter task ID
3. View error message and subtasks
4. Click "View Trace in Grafana"

**Via Database:**
```sql
-- Get task details
SELECT id, type, status, error, output
FROM tasks
WHERE id = 'your-task-id';

-- Get subtask failures
SELECT id, agent_type, iteration, status, error
FROM subtasks
WHERE parent_task_id = 'your-task-id'
ORDER BY iteration, created_at;
```

### Common Errors

**1. "Agent not found"**
```
ERROR: Unknown agent type: 'custom_agent'
```

**Solution:**
```bash
# Check registered agents
curl http://localhost:8000/admin/agents

# If agent missing, verify file exists
ls app/agents/custom_agent.py

# Restart to reload agents
docker-compose restart task-api task-worker
```

**2. "LLM API error"**
```
ERROR: OpenAI API error: Insufficient credits
```

**Solution:**
- Check API key has credits
- Verify API key in .env is correct
- Try different model in config/agents.yaml

**3. "Max iterations exceeded"**
```
Workflow failed: Max iterations (3) reached without convergence
```

**Solution:**
- Review assessment criteria (too strict?)
- Increase max_iterations in workflow YAML
- Check assessment feedback in subtasks

**4. "Invalid workflow definition"**
```
ERROR: Workflow 'my_workflow' not found
```

**Solution:**
```bash
# Check workflow files
ls app/workflows/

# Verify workflow loaded
curl http://localhost:8000/admin/workflows

# Check for YAML syntax errors
python -c "import yaml; yaml.safe_load(open('app/workflows/my_workflow.yaml'))"

# Restart to reload workflows
docker-compose restart task-api task-worker
```

---

## SSL/Certificate Issues

### Symptom
```
SSL: CERTIFICATE_VERIFY_FAILED
```

### mTLS Not Working

**For development:**
```bash
# Use HTTP (no SSL)
curl http://localhost:8000/health

# Skip certificate verification (testing only)
curl -k https://localhost:8443/health
```

**For production:**
```bash
# Verify certificates exist
ls -la certs/

# Regenerate if missing
./utils/generate_certs.sh

# Test with certificates
curl --cacert certs/ca-cert.pem \
     --cert certs/client-cert.pem \
     --key certs/client-key.pem \
     https://localhost:8443/health
```

---

## WebSocket Connection Issues

### Symptom
WebSocket disconnects immediately or can't connect.

### Solutions

**1. CORS issues**

Check CORS settings in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Keep-alive not sent**

```javascript
// Send ping every 30 seconds
const ws = new WebSocket('ws://localhost:8000/ws');
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);
```

---

## High Memory Usage

### Diagnosis

```bash
# Check Docker memory usage
docker stats

# Check PostgreSQL memory
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c \
  "SELECT pg_size_pretty(pg_database_size('openwebui'));"
```

### Solutions

**1. Large task outputs**

```sql
-- Find large tasks
SELECT id, type, pg_column_size(output) as output_size
FROM tasks
WHERE output IS NOT NULL
ORDER BY output_size DESC
LIMIT 10;

-- Clean up old completed tasks
DELETE FROM tasks
WHERE status IN ('done', 'error')
  AND created_at < NOW() - INTERVAL '7 days';
```

**2. Too many WebSocket connections**

```bash
# Check connection count
curl http://localhost:8000/health | jq .websocket_connections

# Restart API to clear stale connections
docker-compose restart task-api
```

---

## Slow Performance

### Task Processing Slow

**Diagnosis:**
1. Check Grafana trace for the task
2. Identify slow span (usually LLM API call)
3. Review input_tokens count

**Solutions:**
- Reduce prompt length
- Use faster/cheaper model
- Optimize workflow (fewer iterations)

### Database Slow

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

**Solutions:**
- Add missing indexes
- Vacuum analyze: `VACUUM ANALYZE tasks;`
-Increase shared_buffers in PostgreSQL config

---

## Open WebUI Integration Issues

### @flow Command Not Working

**Diagnosis:**
```bash
# Check tool is installed in Open WebUI
# Go to: http://localhost:3000 → Workspace → Functions
# Search for "Task Queue Tool"
```

**Solutions:**
- Reinstall tool from `integrations/openwebui/`
- Check TASK_API_URL in tool config
- Verify certificates mounted correctly in docker-compose.yml

### Results Not Appearing

**Check WebSocket connection:**
```javascript
// In Open WebUI tool code
console.log('WebSocket connected:', ws.readyState);
```

**Check task status:**
```bash
# Get recent tasks
curl http://localhost:8000/tasks?limit=5 | jq .
```

---

## Reset Everything

If all else fails, complete reset:

```bash
# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Remove certificates
rm -rf certs/*

# Regenerate certificates
./utils/generate_certs.sh

# Fresh start
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

---

## Getting Help

**Check logs first:**
```bash
docker-compose logs --tail=100
```

**Gather diagnostic info:**
```bash
# Services status
docker-compose ps > diagnostics.txt

# Recent logs
docker-compose logs --tail=500 >> diagnostics.txt

# Environment check
cat .env | grep -v "API_KEY" >> diagnostics.txt

# Database state
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui \
  -c "\dt" >> diagnostics.txt
```

**Useful log searches:**
```bash
# Find errors
docker-compose logs | grep -i error

# Find specific task
docker-compose logs | grep "task-id-here"

# Find worker activity
docker-compose logs task-worker | grep "Processing task"
```

---

## See Also

- [Monitoring Guide](MONITORING.md) - Observability and debugging tools
- [Architecture](ARCHITECTURE.md) - System design documentation
- [Development Guide](DEVELOPMENT.md) - Local development setup
