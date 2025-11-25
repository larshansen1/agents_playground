"""Prometheus metrics configuration."""

from prometheus_client import Counter, Gauge, Histogram, Info

# API Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

# Task Metrics
tasks_created_total = Counter("tasks_created_total", "Total tasks created", ["task_type"])

tasks_completed_total = Counter(
    "tasks_completed_total", "Total tasks completed", ["task_type", "status"]
)

tasks_pending = Gauge(
    "tasks_pending", "Number of tasks waiting to be processed", ["service", "instance"]
)

tasks_in_flight = Gauge(
    "tasks_in_flight", "Current number of tasks being processed", ["service", "instance"]
)

task_duration_seconds = Histogram(
    "task_duration_seconds",
    "Task processing duration in seconds",
    ["task_type", "status"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

# Worker Metrics
worker_heartbeat = Gauge(
    "worker_heartbeat_timestamp", "Timestamp of last worker heartbeat", ["service", "instance"]
)

worker_tasks_processed = Counter(
    "worker_tasks_processed_total", "Total tasks processed by worker", ["status"]
)

# Lease-based acquisition metrics
tasks_acquired_total = Counter(
    "tasks_acquired_total", "Tasks acquired with lease", ["worker_id", "task_type"]
)

tasks_lease_renewed_total = Counter("tasks_lease_renewed_total", "Lease renewals", ["worker_id"])

tasks_recovered_total = Counter(
    "tasks_recovered_total", "Tasks recovered from expired leases", ["task_type"]
)

tasks_retry_exhausted_total = Counter(
    "tasks_retry_exhausted_total", "Tasks that exceeded max retries", ["task_type"]
)

worker_poll_interval_seconds = Gauge(
    "worker_poll_interval_seconds", "Current polling interval in seconds", ["service", "instance"]
)

active_leases = Gauge(
    "active_leases_total", "Number of active task leases", ["service", "instance"]
)

# Database Metrics
db_connections_active = Gauge(
    "db_connections_active", "Number of active database connections", ["service", "instance"]
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds", "Database query duration in seconds", ["operation"]
)

# WebSocket Metrics
websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Number of active WebSocket connections",
    ["service", "instance"],
)

websocket_messages_sent = Counter(
    "websocket_messages_sent_total", "Total WebSocket messages sent", ["message_type"]
)

# Application Info
app_info = Info("app_info", "Application information")
