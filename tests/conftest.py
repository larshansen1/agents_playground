"""Pytest configuration and fixtures."""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import JSON, Column, String, Text, DateTime, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import declarative_base
from httpx import AsyncClient
import uuid

from app.main import app
from app.database import get_db


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
    model_used = Column(String(100))
    input_tokens = Column(postgresql.INTEGER)
    output_tokens = Column(postgresql.INTEGER)
    total_cost = Column(postgresql.NUMERIC(10, 6))
    generation_id = Column(String(100))


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
    from httpx import ASGITransport
    
    async def override_get_db():
        yield async_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_task_data():
    """Sample task creation data."""
    return {
        "type": "summarize_document",
        "input": {"text": "Sample document for testing purposes."}
    }


@pytest.fixture
def sample_task_update():
    """Sample task update data."""
    return {
        "status": "done",
        "output": {
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"]
        }
    }
