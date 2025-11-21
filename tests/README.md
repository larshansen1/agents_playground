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
open htmlcov/index.html
```

### Specific Tests
```bash
# Specific file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::TestTaskEndpoints::test_create_task

# By marker
pytest -m unit
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_schemas.py       # Pydantic schema tests
├── test_models.py        # SQLAlchemy model tests
├── test_api.py           # API endpoint tests
├── test_websocket.py     # WebSocket functionality tests
└── test_worker.py        # Background worker tests
```

## Fixtures

- `async_engine` - In-memory SQLite database
- `async_session` - Async database session
- `client` - Async HTTP client
- `sample_task_data` - Sample task creation payload

## Writing New Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_success(client: AsyncClient):
    response = await client.get("/endpoint")
    assert response.status_code == 200
```

See [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) for code quality standards.
