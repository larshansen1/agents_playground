from app.agents.base import extract_json


def test_extract_json_standard():
    """Test extracting standard JSON."""
    text = '{"key": "value"}'
    result = extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_markdown():
    """Test extracting JSON from markdown."""
    text = 'Here is the result:\n```json\n{"key": "value"}\n```'
    result = extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_sse_prefix():
    """Test extracting JSON with SSE data: prefix."""
    text = 'data: {"key": "value"}'
    result = extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_sse_prefix_with_newlines():
    """Test extracting JSON with SSE data: prefix and newlines."""
    text = 'data: \n{"key": "value"}\n'
    result = extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_embedded_sse():
    """Test extracting JSON where data: is inside text but regex finds JSON."""
    # This mimics if the model outputs "data: " then the JSON block
    text = 'data: {"key": "value"}'
    result = extract_json(text)
    assert result == {"key": "value"}
