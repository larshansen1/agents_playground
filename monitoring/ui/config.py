"""Configuration for the management UI."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://openwebui:password@postgres:5432/openwebui"
    )

    # API endpoints
    TASK_API_URL = os.getenv("TASK_API_URL", "http://task-api:8000")

    # UI settings
    REFRESH_INTERVAL = int(os.getenv("UI_REFRESH_INTERVAL", "10"))  # seconds
    MAX_TASKS_DISPLAY = int(os.getenv("UI_MAX_TASKS_DISPLAY", "100"))
    COST_ALERT_THRESHOLD = float(os.getenv("UI_COST_ALERT_THRESHOLD", "100.0"))

    # Page configuration
    PAGE_TITLE = "Task Backend Manager"
    PAGE_ICON = "📊"
    LAYOUT = "wide"


config = Config()
