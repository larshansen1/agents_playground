# Agent Registry

## Overview

The Agent Registry is a centralized system for managing, discovering, and configuring agents in the multi-agent workflow system. It provides three flexible approaches for agent registration:

1. **YAML Configuration** - Declarative agent definitions
2. **Auto-Discovery** - Automatic detection from filesystem
3. **Programmatic Registration** - Direct registration in code

## Quick Start

### Using the Registry

```python
from app.agents.registry_init import registry

# Get an agent (singleton)
agent = registry.get("research")

# Create a new instance
fresh_agent = registry.create_new("research")

# Check if agent exists
if registry.has("custom_agent"):
    agent = registry.get("custom_agent")

# List all agents
all_agents = registry.list_all()  # ['research', 'assessment']
```

### Worker Integration

The worker automatically uses the registry:

```python
# In app/worker_helpers.py
from app.agents import get_agent

agent = get_agent("research")  # Uses registry automatically
result = agent.execute(input_data)
```

## Configuration Methods

### 1. YAML Configuration (Recommended)

**Create `config/agents.yaml`:**
```yaml
agents:
  - name: research
    class: app.agents.research_agent.ResearchAgent
    config:
      model: gpt-4-turbo
      temperature: 0.7
    tools:
      - web_search
      - document_reader
    description: "Conducts deep research on topics"

  - name: assessment
    class: app.agents.assessment_agent.AssessmentAgent
    config:
      model: gpt-4-turbo
      temperature: 0.3
    tools:
      - fact_checker
    description: "Assesses research quality"
```

**Benefits:**
- ✅ Centralized configuration
- ✅ Version controlled
- ✅ Environment-specific configs (dev/staging/prod)
- ✅ No code changes needed

### 2. Auto-Discovery (Zero Config)

Agents are automatically discovered from `app/agents/` directory on startup.

**File naming convention:**
```
app/agents/
├── base.py              # ← Excluded (base class)
├── research_agent.py    # ← Discovered as "research"
├── assessment_agent.py  # ← Discovered as "assessment"
└── custom_agent.py      # ← Discovered as "custom"
```

**Agent type derived from filename:**
- `research_agent.py` → `"research"`
- `assessment_agent.py` → `"assessment"`
- Format: `{type}_agent.py` → `{type}`

**Benefits:**
- ✅ No configuration needed
- ✅ Just add file and restart
- ✅ Perfect for development

### 3. Programmatic Registration

Useful for testing or dynamic agent creation:

```python
from app.agents.registry_init import registry
from app.agents.research_agent import ResearchAgent

# Manual registration
registry.register(
    agent_type="custom",
    agent_class=ResearchAgent,
    config={"model": "gpt-4"},
    tools=["tool1", "tool2"],
    description="Custom agent"
)
```

## Registry Initialization

The registry initializes automatically on first import using this strategy:

```python
# app/agents/registry_init.py
# 1. Try loading from config/agents.yaml
# 2. Fall back to auto-discovery from app/agents/
# 3. Return empty registry as last resort
```

**Startup flow:**
```
Worker Starts
    ↓
Import registry_init module
    ↓
Auto-initialize registry
    ↓
Load from YAML (if exists)
    OR
Auto-discover from filesystem
    ↓
Registry ready
```

## Features

### Singleton Pattern

Agents are cached as singletons for performance:

```python
# First call creates instance
agent1 = registry.get("research")

# Second call returns same instance
agent2 = registry.get("research")

assert agent1 is agent2  # True - same object
```

**Benefits:**
- ✅ Better performance (no repeated initialization)
- ✅ Consistent state across requests
- ✅ Lower memory usage

**Create new instance when needed:**
```python
fresh_agent = registry.create_new("research")  # New instance
```

### Thread Safety

Registry operations are thread-safe:

```python
# Multiple workers can access simultaneously
with registry._lock:
    registry.register(...)  # Protected
```

### Observability

Registry emits structured logs:

```python
# On initialization
INFO: agents_discovered - agent_types=['research', 'assessment'] count=2

# On agent instantiation
INFO: agent_instantiated - agent_type=research instance_id=... is_singleton=true
```

## API Reference

### Registry Methods

#### `get(agent_type: str) -> Agent`
Get singleton agent instance.

```python
agent = registry.get("research")
```

**Raises:** `ValueError` if agent not found

#### `create_new(agent_type: str, **override_config) -> Agent`
Create fresh agent instance (not singleton).

```python
agent = registry.create_new("research", temperature=0.9)
```

#### `register(agent_type, agent_class, config=None, tools=None, description="")`
Manually register an agent.

```python
registry.register(
    agent_type="custom",
    agent_class=CustomAgent,
    config={"param": "value"},
    tools=["tool1"],
    description="Description"
)
```

#### `has(agent_type: str) -> bool`
Check if agent is registered.

```python
if registry.has("custom"):
    agent = registry.get("custom")
```

#### `list_all() -> List[str]`
List all registered agent types.

```python
agents = registry.list_all()  # ['research', 'assessment']
```

#### `get_metadata(agent_type: str) -> AgentMetadata`
Get agent metadata including config, tools, description.

```python
metadata = registry.get_metadata("research")
print(metadata.config)  # {'model': 'gpt-4-turbo', ...}
print(metadata.tools)   # ['web_search', ...]
```

#### `load_from_yaml(yaml_path: str | Path)`
Load agents from YAML file.

```python
registry.load_from_yaml("config/agents.yaml")
```

#### `discover_agents(search_path="app/agents", exclude_patterns=None)`
Auto-discover agents from filesystem.

```python
discovered = registry.discover_agents()
print(f"Found: {discovered}")  # ['research', 'assessment']
```

## Environment Configuration

### Development
```yaml
# config/agents_dev.yaml
agents:
  - name: research
    config:
      model: gpt-3.5-turbo  # Cheaper for dev
      temperature: 0.7
```

### Production
```yaml
# config/agents_prod.yaml
agents:
  - name: research
    config:
      model: gpt-4-turbo  # Best quality
      temperature: 0.7
```

### Loading Environment-Specific Config

```python
import os
env = os.getenv("ENV", "production")
registry.load_from_yaml(f"config/agents_{env}.yaml")
```

## Scaling Considerations

### Horizontal Scaling

**Multiple Workers:**
- Each worker has independent in-memory registry
- Discovered from same code on startup
- Rolling deploys create brief version skew (acceptable)

**Characteristics:**
- ✅ Self-contained workers
- ✅ No coordination needed
- ✅ Simple and reliable
- ⚠️ Brief version skew during deploys (~30-60s)

### Current Design Benefits

**Code-Based Approach:**
- ✅ **Version Control** - Git tracks all agent changes
- ✅ **Reproducible** - Code = source of truth
- ✅ **Testable** - Easy to write tests
- ✅ **Fast** - In-memory, no DB queries
- ✅ **Simple** - No database schema/migrations

## Performance

Registry operations are extremely fast:

| Operation | Latency | Notes |
|-----------|---------|-------|
| `get()` | < 0.1ms | Cached singleton |
| `create_new()` | < 1ms | New instance |
| YAML loading | ~5ms | One-time on startup |
| Auto-discovery | ~10ms | One-time on startup |

**No overhead:** Singleton pattern means zero per-request cost.

## Testing

### Unit Tests

```python
def test_agent_from_registry():
    from app.agents.registry_init import registry

    agent = registry.get("research")
    assert agent is not None

    # Test singleton
    agent2 = registry.get("research")
    assert agent is agent2
```

### Mock Agents

```python
# In tests
from tests.mocks import MockAgent

registry.register("research", MockAgent)
# Now all code using registry gets mock
```

## Troubleshooting

### "Agent not found" error
```python
ValueError: Unknown agent type: 'custom'
Available agents: ['research', 'assessment']
```

**Solutions:**
1. Check agent file exists: `app/agents/custom_agent.py`
2. Verify YAML config has agent defined
3. Check exclusion patterns in `discover_agents()`

### Agent not auto-discovered

**Check:**
- File named correctly: `{type}_agent.py`
- Class inherits from `Agent` base class
- File not in exclusion list (`base.py`, `__*`)

### Workers have different agent versions

**During deployment:**
- Normal with rolling deploys (~30-60s skew)
- Workers restart with new code version
- Eventually consistent

## Future Enhancements

Potential Phase 4 features:

- **Hot-reload** - Reload agents without restart
- **Database persistence** - Track agent usage/metadata
- **Per-tenant agents** - Custom agents per customer
- **Agent versioning** - Multiple versions simultaneously
- **Plugin marketplace** - User-uploaded agents

## Architecture

```
┌─────────────────────────────────────────────┐
│  Worker Process                             │
│  ┌───────────────────────────────────────┐  │
│  │  registry_init.py                     │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AgentRegistry                  │  │  │
│  │  │  ├── _agents: Dict[str, Meta]   │  │  │
│  │  │  ├── _lock: RLock              │  │  │
│  │  │  └── methods...                 │  │  │
│  │  └─────────────────────────────────┘  │  │
│  │           ↓                            │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AgentMetadata                  │  │  │
│  │  │  ├── agent_class                │  │  │
│  │  │  ├── config                     │  │  │
│  │  │  ├── tools                      │  │  │
│  │  │  ├── description                │  │  │
│  │  │  └── _instance (cached)         │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Summary

**Current State:**
- ✅ Phase 1: Programmatic registration
- ✅ Phase 2: YAML + Auto-discovery
- ✅ Phase 3: Worker integration
- ✅ Production-ready
- ✅ 52 tests, 96% coverage

**Key Features:**
- Three registration methods (YAML, auto-discovery, programmatic)
- Singleton pattern for performance
- Thread-safe operations
- Structured logging
- No database dependency
- Scales horizontally

**Best For:**
- Platform development (not SaaS customization)
- Code-driven agent definitions
- Version-controlled configurations
- Developer-centric workflows
