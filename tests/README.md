# Test Suite

Comprehensive test coverage for the Task Management API.

## Running Tests

### All Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Specific Test File
```bash
pytest tests/test_api.py
```

### Specific Test Class or Function
```bash
pytest tests/test_api.py::TestTaskEndpoints::test_create_task
```

### By Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_schemas.py       # Pydantic schema tests
├── test_models.py        # SQLAlchemy model tests
├── test_api.py           # API endpoint tests
└── test_websocket.py     # WebSocket functionality tests
```

## Test Coverage

### test_schemas.py
- ✅ TaskStatus enum validation
- ✅ TaskCreate schema validation
- ✅ TaskUpdate schema validation
- ✅ TaskResponse schema validation
- ✅ TaskStatusUpdate schema validation
- ✅ Complex nested data structures

### test_models.py
- ✅ Task model creation
- ✅ JSONB field handling
- ✅ Database queries by ID
- ✅ Database queries by status
- ✅ Task updates
- ✅ Complex nested JSON storage

### test_api.py
- ✅ Health check endpoint
- ✅ Root endpoint
- ✅ Create task (POST /tasks)
- ✅ Get task by ID (GET /tasks/{id})
- ✅ List tasks (GET /tasks)
- ✅ Filter tasks by status
- ✅ Limit task results
- ✅ Update task (PATCH /tasks/{id})
- ✅ 404 error handling
- ✅ Validation error handling
- ✅ Complete task lifecycle (create → update → complete)
- ✅ Task error flow

### test_websocket.py
- ✅ WebSocket connection manager
- ✅ WebSocket endpoint connection
- ✅ Ping/pong functionality
- ✅ Task creation broadcasts
- ✅ Task update broadcasts

## Fixtures

### async_engine
In-memory SQLite database engine for fast tests.

### async_session
Async database session with automatic cleanup.

### client
Async HTTP client with database dependency override.

### sample_task_data
Sample task creation payload.

### sample_task_update
Sample task update payload.

## Test Database

Tests use an in-memory SQLite database with async support:
- Fast execution (no disk I/O)
- Clean state for each test
- No impact on production/development databases

## Continuous Integration

Tests are configured to:
- Run automatically on commit (when CI is set up)
- Generate coverage reports
- Fail on coverage below threshold (can be configured)

## Writing New Tests

1. Create test file: `tests/test_<feature>.py`
2. Import fixtures from conftest: `from conftest import client, async_session`
3. Mark tests appropriately:
   - `@pytest.mark.unit` for unit tests
   - `@pytest.mark.integration` for integration tests
   - `@pytest.mark.asyncio` for async tests
4. Use descriptive test names: `test_<what>_<scenario>()`

Example:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_success_case(client: AsyncClient):
    response = await client.get("/endpoint")
    assert response.status_code == 200
```
