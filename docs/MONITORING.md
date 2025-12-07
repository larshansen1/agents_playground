# Monitoring & Observability

Comprehensive guide to monitoring, tracing, and debugging the multi-agent orchestration system.

## Overview

The system provides three layers of observability:

1. **Management UI** - User-friendly dashboard for task monitoring and cost analytics
2. **Distributed Tracing** - End-to-end request tracing with Grafana Tempo
3. **Metrics** - Time-series metrics with Prometheus

## Management UI

**Access:** http://localhost:8501

The Streamlit-based management interface provides four main views:

### 📊 Dashboard

Real-time overview of system activity.

**Features:**
- Recent tasks (auto-refreshes every 5 seconds)
- Task status distribution pie chart
- Active tasks by type
- Error rate trends
- Click any task ID to see details

**Use cases:**
- Monitor system health at a glance
- Spot error patterns
- Track workload distribution

---

### 🔍 Task Search

Search and inspect individual tasks.

**Features:**
- Search by task ID
- View complete input/output
- See error messages and stack traces
- Cost breakdown (tokens, model used)
- **Direct link to Grafana trace** (with time range pre-set)
- Parent/child task relationships for workflows

**Use cases:**
- Debug specific task failures
- Analyze workflow execution flow
- Review agent responses
- Check cost for individual executions

**Example workflow:**
1. User reports: "@flow command failed"
2. Get task ID from Open WebUI
3. Search in Management UI
4. Click "View Trace in Grafana"
5. See exact failure point in distributed trace

---

### 👤 User Search

Find all activity for a specific user.

**Features:**
- Search by email address (privacy-preserving hash lookup)
- View all user's tasks across tenants
- Per-user cost analytics
- Audit log trail
- Aggregate statistics (total tasks, success rate, costs)

**Use cases:**
- User support ("Why did my task fail?")
- Cost analysis per user
- Audit compliance
- Usage pattern analysis

**Privacy:** Email is hashed with SHA-256 before lookup. Only the hash is stored in the database.

---

### 💰 Cost Analytics

Cost tracking and analysis.

**Features:**
- Per-user cost breakdown
- Per-tenant cost aggregation
- Model usage statistics
- Time-series cost trends
- Token usage details (input/output)
- Workflow cost aggregation (parent + all subtasks)

**Metrics tracked:**
- `input_tokens` - Tokens sent to LLM
- `output_tokens` - Tokens received from LLM
- `total_cost` - Calculated cost based on model pricing
- `model_used` - LLM model name

**Use cases:**
- Budget monitoring
- Cost allocation by tenant
- Identify expensive workflows
- Optimize model selection

---

## Distributed Tracing

**Access:** http://localhost:3002 (Grafana)

### What is Tracing?

Distributed tracing tracks requests across multiple services, showing:
- Complete execution timeline
- Nested operations (spans)
- Duration of each step
- LLM API calls
- Iteration breakdowns for multi-step workflows

### Trace Hierarchy

Example trace for `@flow research_assessment`:

```
openwebui_tool.at_flow (28.3s)
├─ task-api.create_task (15ms)
├─ task-worker.process_workflow (28.1s)
│  ├─ orchestrator.initialize_workflow (50ms)
│  ├─ orchestrator.process_subtask:research (7.6s, iteration=1)
│  │  ├─ agent.research.execute (7.5s)
│  │  │  └─ llm.openrouter.chat_completion (7.2s)
│  │  │     ├─ input_tokens: 1250
│  │  │     ├─ output_tokens: 830
│  │  │     └─ cost: $0.002145
│  │  └─ task-worker.update_subtask (45ms)
│  ├─ orchestrator.process_subtask:assessment (1.8s, iteration=1)
│  │  ├─ agent.assessment.execute (1.7s)
│  │  │  └─ llm.openrouter.chat_completion (1.6s)
│  │  │     ├─ input_tokens: 980
│  │  │     ├─ output_tokens: 120
│  │  │     └─ cost: $0.000850
│  │  └─ task-worker.update_subtask (30ms)
│  └─ task-worker.finalize_workflow (35ms)
└─ task-api.complete_task (10ms)
```

### Finding Traces

**Method 1: From Management UI**
1. Go to Task Search
2. Enter task ID
3. Click "View Trace in Grafana" button
4. Grafana opens with trace pre-loaded

**Method 2: Direct Search in Grafana**
1. Open http://localhost:3002
2. Go to **Explore** (compass icon)
3. Select **Tempo** data source
4. Search by:
   - **Trace ID** (from task's `generation_id` field)
   - **Service** (`task-worker`, `task-api`)
   - **Time range** (task created_at to completed_at)

### Trace Context Propagation

The system propagates trace context through all layers:

```
1. Open WebUI Tool
   ↓ generates trace_id
   ↓ injects into task.input._trace_context

2. Task API
   ↓ stores task with trace context
   ↓ returns task_id

3. Worker
   ↓ claims task
   ↓ extracts trace_id from input
   ↓ creates root span with trace_id

4. Orchestrator
   ↓ creates child span for each subtask

5. Agent
   ↓ creates nested span for LLM call
   ↓ exports to OpenTelemetry Collector

6. OTel Collector
   ↓ forwards to Grafana Tempo

7. User views unified trace in Grafana
```

**Key benefit:** One trace ID links the entire request flow from Open WebUI to final result.

---

## Metrics

**Access:** http://localhost:9090 (Prometheus)

### Available Metrics

#### Task Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `tasks_created_total` | Counter | Total tasks created by type |
| `tasks_completed_total` | Counter | Completed tasks by type and status |
| `tasks_pending` | Gauge | Queue depth (pending tasks) |
| `tasks_in_flight` | Gauge | Currently processing tasks |
| `task_duration_seconds` | Histogram | Task processing time |

#### Worker Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `worker_heartbeat_timestamp` | Gauge | Last heartbeat time |
| `worker_tasks_processed_total` | Counter | Tasks processed by worker |
| `tasks_acquired_total` | Counter | Tasks claimed with lease |
| `active_leases_total` | Gauge | Number of active task leases |

#### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `db_connections_active` | Gauge | Active database connections |
| `websocket_connections_active` | Gauge | Active WebSocket connections |

### Example Queries

**Queue depth over time:**
```promql
tasks_pending
```

**Task completion rate:**
```promql
rate(tasks_completed_total[5m])
```

**Average task duration by type:**
```promql
avg(task_duration_seconds) by (task_type)
```

**Worker throughput:**
```promql
rate(worker_tasks_processed_total[1m])
```

**Error rate:**
```promql
rate(tasks_completed_total{status="error"}[5m]) /
rate(tasks_completed_total[5m])
```

---

## Audit Logging

### What Gets Logged

All operations are tracked in the `audit_logs` table:

| Event Type | Triggered When |
|------------|----------------|
| `task_created` | POST /tasks |
| `task_updated` | Task status/output changes |
| `task_completed` | Task reaches done/error state |
| `workflow_initialized` | Multi-agent workflow starts |
| `subtask_completed` | Subtask finishes |

### Querying Audit Logs

**Via Database:**
```sql
-- User's activity log
SELECT event_type, timestamp, metadata
FROM audit_logs
WHERE user_id_hash = 'abc123...'
ORDER BY timestamp DESC
LIMIT 50;

-- Tenant audit trail (last 7 days)
SELECT event_type, resource_id, timestamp, metadata
FROM audit_logs
WHERE tenant_id = 'production'
  AND timestamp > NOW() - INTERVAL '7 days';
```

**Via Management UI:**
User Search view shows related audit logs automatically.

---

## Debugging Workflows

### Multi-Agent Workflow Visibility

For workflow tasks (e.g., `workflow:research_assessment`):

**In Management UI:**
1. Search for parent task ID
2. View "Subtasks" section
3. See all iterations and agent executions
4. Click trace link to see timeline

**In Grafana:**
- Parent span shows total workflow duration
- Child spans show each subtask/iteration
- LLM calls nested within agent spans
- Clear visual timeline of execution

**Example: Research-Assessment Loop**

Trace shows:
- Iteration 1: Research → Assessment (not approved)
- Iteration 2: Research (with feedback) → Assessment (approved)
- Total: 2 iterations, 4 agent calls, ~15 seconds

---

## Troubleshooting with Traces

### Scenario 1: Task Stuck in "Running"

**Symptoms:** Task status = "running" for > 5 minutes

**Debug steps:**
1. Check worker logs: `docker-compose logs task-worker`
2. Look for task_id in logs
3. Check if worker crashed mid-task
4. In trace, check for incomplete spans

**Resolution:** Lease will expire after 5 minutes, task becomes reclaimable

---

### Scenario 2: High Latency

**Symptoms:** Task takes 30+ seconds

**Debug steps:**
1. View trace in Grafana
2. Identify slow span (usually LLM API call)
3. Check span tags for:
   - `input_tokens` - Large context?
   - `output_tokens` - Long response?
   - `model_used` - Slow model?

**Resolution:** Optimize prompt, reduce context, or switch model

---

### Scenario 3: Iterative Workflow Not Converging

**Symptoms:** Workflow hits max_iterations without approval

**Debug steps:**
1. View subtasks in Management UI
2. Check each iteration's output
3. Look for assessment feedback
4. Review convergence criteria

**Resolution:** Adjust assessment criteria or increase max_iterations

---

## Accessing Observability Services

### Local Development

```bash
# View worker logs
docker-compose logs -f task-worker

# View API logs
docker-compose logs -f task-api

# Access Grafana
open http://localhost:3002

# Access Prometheus
open http://localhost:9090

# Access Management UI
open http://localhost:8501

# Query database directly
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui
```

### Useful Database Queries

```sql
-- Recent tasks with trace context
SELECT id, type, status,
       input->'_trace_context'->>'trace_id' as trace_id
FROM tasks
ORDER BY created_at DESC
LIMIT 10;

-- Tasks by status
SELECT status, COUNT(*)
FROM tasks
GROUP BY status;

-- Expensive tasks (by token count)
SELECT id, type, input_tokens + output_tokens as total_tokens, total_cost
FROM tasks
WHERE status = 'done'
ORDER BY total_cost DESC
LIMIT 10;

-- Workflow iterations
SELECT parent_task_id, iteration, agent_type, status, total_cost
FROM subtasks
WHERE parent_task_id = 'abc123...'
ORDER BY iteration, created_at;
```

---

## OpenTelemetry Collector

### Configuration

The OTel Collector aggregates traces and metrics:

```yaml
# monitoring/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  tempo:
    endpoint: tempo:4317
  prometheus:
    endpoint: prometheus:9090

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [tempo]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

### Checking Collector Status

```bash
# View collector logs
docker-compose logs otel-collector

# Check if receiving traces
docker-compose logs otel-collector | grep -i "trace"
```

---

## Best Practices

### For Development
- ✅ Keep Management UI open while testing
- ✅ Use trace links for debugging failures
- ✅ Check worker logs for detailed execution info
- ✅ Monitor queue depth to spot backlog

### For Production
- ✅ Set up alerts on error rate metrics
- ✅ Monitor queue depth (high = need more workers)
- ✅ Track cost metrics by tenant
- ✅ Retain audit logs for compliance (7-90 days)
- ✅ Export traces to long-term storage

### Cost Optimization
- 📊 Review top 10 expensive tasks weekly
- 📊 Identify prompt optimization opportunities
- 📊 Consider cheaper models for non-critical tasks
- 📊 Track cost per tenant for billing

---

## See Also

- [Architecture](ARCHITECTURE.md) - System design and data flow
- [API Reference](API_REFERENCE.md) - API endpoints for programmatic access
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
