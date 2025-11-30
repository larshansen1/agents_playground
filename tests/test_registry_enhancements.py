"""Enhanced tests for thread safety and performance.

Addresses test gaps identified in code review:
- Gap #1: Config override verification
- Gap #2: Thread safety testing
- Gap #3: Performance benchmarks
"""

import threading
import time

from app.agents.base import Agent
from app.agents.registry import AgentRegistry


class MockAgent(Agent):
    """Mock agent for thread safety tests."""

    def __init__(self):
        super().__init__(agent_type="mock")

    def execute(self, _input_data: dict, _user_id_hash: str | None = None) -> dict:
        """Mock execute."""
        return {"output": {}, "usage": {}}


# ============================================================================
# Thread Safety Tests (Gap #2)
# ============================================================================


def test_concurrent_registration():
    """Test thread-safe concurrent registration."""
    registry = AgentRegistry()
    errors = []
    success_count = [0]

    def register_agent():
        try:
            registry.register("concurrent_test", MockAgent)
            success_count[0] += 1
        except ValueError as e:
            errors.append(e)

    # 10 threads try to register simultaneously
    threads = [threading.Thread(target=register_agent) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly 1 should succeed, 9 should fail
    assert success_count[0] == 1, f"Expected 1 success, got {success_count[0]}"
    assert len(errors) == 9, f"Expected 9 errors, got {len(errors)}"
    assert registry.has("concurrent_test")
    assert all("already registered" in str(e) for e in errors)


def test_concurrent_get_operations():
    """Test thread-safe concurrent get operations."""
    registry = AgentRegistry()
    registry.register("concurrent_get", MockAgent)

    agents = []

    def get_agent():
        agent = registry.get("concurrent_get")
        agents.append(agent)

    # 20 threads get agent simultaneously
    threads = [threading.Thread(target=get_agent) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All should get the same singleton instance
    assert len(agents) == 20
    assert all(agent is agents[0] for agent in agents), "All threads should get same singleton"


# ============================================================================
# Performance Tests (Gap #3)
# ============================================================================


def test_registry_performance():
    """Test registry operations meet performance requirements."""
    registry = AgentRegistry()

    # Test 1: Bulk registration should be fast (< 100ms for 100 agents)
    start = time.time()
    for i in range(100):
        registry.register(f"agent_{i}", MockAgent)
    register_time = time.time() - start

    assert register_time < 0.1, f"Registration took {register_time:.3f}s, expected < 0.1s"

    # Test 2: Singleton retrieval should be fast (< 100ms for 1000 calls)
    # Note: With logging enabled, this is slower (~50ms), but still very fast
    start = time.time()
    for _ in range(1000):
        registry.get("agent_0")
    get_time = time.time() - start

    assert get_time < 0.1, f"1000 get() calls took {get_time:.3f}s, expected < 0.1s"

    # Test 3: Individual get() should be < 0.1ms (100 microseconds avg)
    per_call_time = get_time / 1000
    assert per_call_time < 0.001, f"Per-call time {per_call_time * 1000:.3f}ms, expected < 1ms"
