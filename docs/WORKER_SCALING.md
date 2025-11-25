# Task Management API - Worker Scaling Guide

## Horizontal Scaling with Lease-Based Acquisition

The system supports running multiple worker instances concurrently using a lease-based task acquisition mechanism. Workers safely claim tasks with time-limited leases and automatically recover tasks from failed instances.

### Quick Start

**Single Worker (Default)**:
```bash
docker-compose up -d
```

**Multiple Workers**:
```bash
# Scale to 3 worker instances
docker-compose up -d --scale task-worker=3

# Verify all workers are running
docker-compose ps task-worker
```

### How It Works

- **Worker Identity**: Each worker has a unique ID (hostname:pid)
- **Lease-Based Claims**: Tasks are claimed with 5-minute leases by default
- **Automatic Recovery**: Expired leases are recovered every 30 seconds
- **Adaptive Polling**: Workers back off from 0.2s to 10s when idle
- **Retry Logic**: Failed tasks retry up to 3 times (configurable)

### Configuration

Set via environment variables in `.env` or `docker-compose.yml`:

```bash
# Lease duration (for long-running tasks)
WORKER_LEASE_DURATION_SECONDS=600  # 10 minutes

# Recovery interval
WORKER_RECOVERY_INTERVAL_SECONDS=30  # Check every 30s

# Polling intervals
WORKER_POLL_MIN_INTERVAL_SECONDS=0.2
WORKER_POLL_MAX_INTERVAL_SECONDS=10.0

# Retry settings
WORKER_MAX_RETRIES=5
```

### Monitoring

**View Active Workers**:
```sql
SELECT locked_by, COUNT(*) as active_tasks
FROM tasks
WHERE status = 'running' AND lease_timeout > NOW()
GROUP BY locked_by;
```

**Check Task Retry Status**:
```sql
SELECT id, type, try_count, max_tries, status
FROM tasks
WHERE try_count > 0
ORDER BY try_count DESC;
```

**View Stale Leases** (should be auto-recovered):
```sql
SELECT id, type, locked_by, lease_timeout
FROM tasks
WHERE status = 'running' AND lease_timeout < NOW();
```

### Metrics

Access Prometheus metrics at `http://localhost:8000/metrics`:

- `tasks_acquired_total` - Tasks claimed by each worker
- `tasks_recovered_total` - Tasks recovered from failed workers
- `worker_poll_interval_seconds` - Current polling interval
- `active_leases_total` - Active leases per worker

See full implementation details in the walkthrough documentation.
