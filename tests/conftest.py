"""Pytest configuration and fixtures."""

import asyncio
import os
import sqlite3
import uuid
from collections.abc import AsyncGenerator, Generator

# Set environment variables for testing BEFORE importing app modules
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["OPENROUTER_API_KEY"] = "test"
os.environ["OPENAI_API_KEY"] = "test"  # Required by OpenAI client in app.tasks

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, Column, DateTime, String, Text, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test-specific base
TestBase = declarative_base()


class TestTask(TestBase):
    """Test Task model compatible with SQLite."""

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    input = Column(JSON, nullable=False)
    output = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Cost tracking fields
    user_id_hash = Column(String(64))
    tenant_id = Column(String(100))
    model_used = Column(String(100))
    input_tokens = Column(postgresql.INTEGER)
    output_tokens = Column(postgresql.INTEGER)
    total_cost = Column(postgresql.NUMERIC(10, 6))
    generation_id = Column(String(100))

    # Lease-based task acquisition fields
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(String(100))
    lease_timeout = Column(DateTime(timezone=True))
    try_count = Column(postgresql.INTEGER, default=0)
    max_tries = Column(postgresql.INTEGER, default=3)


class TestSubtask(TestBase):
    """Test Subtask model compatible with SQLite."""

    __tablename__ = "subtasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_task_id = Column(String(36), nullable=False)
    agent_type = Column(String, nullable=False)
    iteration = Column(postgresql.INTEGER, nullable=False, default=1)
    status = Column(String, nullable=False, default="pending")
    input = Column(JSON, nullable=False)
    output = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Cost tracking fields
    user_id_hash = Column(String(64))
    tenant_id = Column(String(100))
    model_used = Column(String(100))
    input_tokens = Column(postgresql.INTEGER)
    output_tokens = Column(postgresql.INTEGER)
    total_cost = Column(postgresql.NUMERIC(10, 6))
    generation_id = Column(String(100))

    # Lease-based task acquisition fields
    locked_at = Column(DateTime(timezone=True))
    locked_by = Column(String(100))
    lease_timeout = Column(DateTime(timezone=True))
    try_count = Column(postgresql.INTEGER, default=0)
    max_tries = Column(postgresql.INTEGER, default=3)


class TestWorkflowState(TestBase):
    """Test WorkflowState model compatible with SQLite."""

    __tablename__ = "workflow_state"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_task_id = Column(String(36), nullable=False, unique=True)
    workflow_type = Column(String, nullable=False)
    current_iteration = Column(postgresql.INTEGER, nullable=False, default=1)
    max_iterations = Column(postgresql.INTEGER, nullable=False, default=3)
    current_state = Column(String, nullable=False)
    state_data = Column(JSON)
    tenant_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TestAuditLog(TestBase):
    """Test AuditLog model compatible with SQLite."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    event_type = Column(String, nullable=False)
    user_id_hash = Column(String(64))
    tenant_id = Column(String(100))
    resource_id = Column(String(36))
    metadata_ = Column("metadata", JSON)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_task_data():
    """Sample task creation data."""
    return {
        "type": "summarize_document",
        "input": {"text": "Sample document for testing purposes."},
    }


@pytest.fixture
def sample_task_update():
    """Sample task update data."""
    return {
        "status": "done",
        "output": {"summary": "Test summary", "key_points": ["Point 1", "Point 2"]},
    }


# Synchronous DB fixtures for workflow integration tests


class SyncDBConnection:
    """SQLite connection wrapper that mimics psycopg2 interface for testing."""

    def __init__(self, engine):
        self.engine = engine
        self._connection = None
        self._in_transaction = False

    def __enter__(self):
        # Create a sync connection from the async engine
        # We use a simple SQLite connection for testing
        db_path = ":memory:"
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._connection:
            self._connection.close()

    def cursor(self):
        """Get a cursor (RealDictCursor-like behavior via Row)."""
        return self._connection.cursor()

    def commit(self):
        """Commit the transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self):
        """Rollback the transaction."""
        if self._connection:
            self._connection.rollback()

    def execute(self, query, params=None):
        """Execute a query directly on connection."""
        cursor = self.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor


@pytest.fixture
def sync_db_engine(async_engine):
    """Create a synchronous database engine for workflow tests."""
    # Create in-memory SQLite connection
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Create tables (simplified schema for testing)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            input TEXT,
            output TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id_hash TEXT,
            tenant_id TEXT,
            model_used TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            generation_id TEXT,
            locked_at TIMESTAMP,
            locked_by TEXT,
            lease_timeout TIMESTAMP,
            try_count INTEGER DEFAULT 0,
            max_tries INTEGER DEFAULT 3
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id TEXT PRIMARY KEY,
            parent_task_id TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            iteration INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending',
            input TEXT,
            output TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id_hash TEXT,
            tenant_id TEXT,
            model_used TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            generation_id TEXT,
            locked_at TIMESTAMP,
            locked_by TEXT,
            lease_timeout TIMESTAMP,
            try_count INTEGER DEFAULT 0,
            max_tries INTEGER DEFAULT 3
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflow_state (
            id TEXT PRIMARY KEY,
            parent_task_id TEXT NOT NULL UNIQUE,
            workflow_type TEXT NOT NULL,
            current_iteration INTEGER NOT NULL DEFAULT 1,
            max_iterations INTEGER NOT NULL DEFAULT 3,
            current_state TEXT NOT NULL,
            state_data TEXT,
            tenant_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            user_id_hash TEXT,
            tenant_id TEXT,
            resource_id TEXT,
            metadata TEXT
        )
    """)

    conn.commit()

    yield conn

    conn.close()


# Mock agents for workflow integration tests


class MockResearchAgent:
    """Mock research agent for testing."""

    def __init__(self, predetermined_output=None, should_fail=False):
        self.agent_type = "research"
        self.predetermined_output = predetermined_output
        self.should_fail = should_fail
        self.call_count = 0

    def execute(self, input_data, user_id_hash=None):
        """Execute mock research task."""
        self.call_count += 1

        if self.should_fail:
            msg = "Mock research agent failed"
            raise RuntimeError(msg)

        # Default output if none provided
        if self.predetermined_output:
            output = self.predetermined_output
        else:
            iteration_suffix = f" (iteration {self.call_count})"
            topic = input_data.get("topic", "default topic")
            output = {
                "findings": f"Research findings for {topic}{iteration_suffix}",
                "sources": ["source1.com", "source2.com"],
                "key_insights": [f"Insight {self.call_count}"],
                "confidence_level": "high",
            }

        return {
            "output": output,
            "usage": {
                "model_used": "mock-research-model",
                "input_tokens": 100,
                "output_tokens": 200,
                "total_cost": 0.0001,
                "generation_id": f"mock-gen-{self.call_count}",
            },
        }


class MockAssessmentAgent:
    """Mock assessment agent for testing."""

    def __init__(self, predetermined_output=None, should_fail=False, approve_on_iteration=None):
        self.agent_type = "assessment"
        self.predetermined_output = predetermined_output
        self.should_fail = should_fail
        self.approve_on_iteration = approve_on_iteration
        self.call_count = 0

    def execute(self, input_data, user_id_hash=None):
        """Execute mock assessment task."""
        self.call_count += 1

        if self.should_fail:
            msg = "Mock assessment agent failed"
            raise RuntimeError(msg)

        # Default output if none provided
        if self.predetermined_output:
            output = self.predetermined_output
        else:
            # Approve based on iteration count
            approved = False
            if self.approve_on_iteration is not None:
                approved = self.call_count >= self.approve_on_iteration
            else:
                # Default: approve on first call
                approved = True

            output = {
                "approved": approved,
                "quality_score": 85 if approved else 60,
                "feedback": "Good work"
                if approved
                else f"Needs improvement (assessment {self.call_count})",
                "suggestions": [] if approved else ["Add more detail", "Cite sources"],
            }

        return {
            "output": output,
            "usage": {
                "model_used": "mock-assessment-model",
                "input_tokens": 150,
                "output_tokens": 100,
                "total_cost": 0.00008,
                "generation_id": f"mock-assess-gen-{self.call_count}",
            },
        }


@pytest.fixture
def mock_research_agent():
    """Fixture for mock research agent."""
    return MockResearchAgent()


@pytest.fixture
def mock_assessment_agent():
    """Fixture for mock assessment agent."""
    return MockAssessmentAgent()


@pytest.fixture
def mock_agent_registry():
    """Fixture that provides a mock agent registry."""

    def _get_mock_agent(agent_type, **kwargs):
        if agent_type == "research":
            return MockResearchAgent(**kwargs)
        if agent_type == "assessment":
            return MockAssessmentAgent(**kwargs)
        msg = f"Unknown mock agent type: {agent_type}"
        raise ValueError(msg)

    return _get_mock_agent
