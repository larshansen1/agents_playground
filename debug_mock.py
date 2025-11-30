import json
from unittest.mock import MagicMock

try:
    m = MagicMock()
    print(f"Mock: {m}")
    res = json.loads(m)
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")

try:
    m = MagicMock()
    # If content is a mock
    content = m.choices[0].message.content
    print(f"Content: {content}")
    res = json.loads(content)
    print(f"Result from content: {res}")
except Exception as e:
    print(f"Error from content: {e}")
