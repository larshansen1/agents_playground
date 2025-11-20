import os

import psycopg2
from psycopg2.extras import RealDictCursor

# Construct database URL from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "openwebui")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
if not POSTGRES_PASSWORD:
    msg = "POSTGRES_PASSWORD environment variable must be set"
    raise ValueError(msg)
POSTGRES_DB = os.getenv("POSTGRES_DB", "openwebui")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
