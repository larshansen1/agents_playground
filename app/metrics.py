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

tasks_in_flight = Gauge("tasks_in_flight", "Current number of tasks being processed")

task_duration_seconds = Histogram(
    "task_duration_seconds",
    "Task processing duration in seconds",
    ["task_type", "status"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

# Worker Metrics
worker_heartbeat = Gauge("worker_heartbeat_timestamp", "Timestamp of last worker heartbeat")

worker_tasks_processed = Counter(
    "worker_tasks_processed_total", "Total tasks processed by worker", ["status"]
)

# Database Metrics
db_connections_active = Gauge("db_connections_active", "Number of active database connections")

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds", "Database query duration in seconds", ["operation"]
)

# WebSocket Metrics
websocket_connections_active = Gauge(
    "websocket_connections_active", "Number of active WebSocket connections"
)

websocket_messages_sent = Counter(
    "websocket_messages_sent_total", "Total WebSocket messages sent", ["message_type"]
)

# Application Info
app_info = Info("app_info", "Application information")
