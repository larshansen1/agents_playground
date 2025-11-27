# Declarative Workflow System

The task management system supports **declarative workflows** defined in YAML, allowing you to create multi-step agent orchestrations without writing Python code.

## Quick Start

### 1. Create a Workflow

Create a YAML file in `app/workflows/`:

```yaml
# app/workflows/my_workflow.yaml
name: my_workflow
description: Custom workflow for my use case
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: gather_info
  - agent_type: assessment
    name: verify_info
```

### 2. Use It

The workflow is **automatically loaded** at startup. Use it via Open WebUI or API:

```
@queue my_workflow analyze this document
```

Or via API:
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "workflow:my_workflow",
    "input": {"topic": "AI safety"}
  }'
```

## Workflow Schema

### Required Fields

```yaml
name: workflow_name          # Must match filename
description: Human-readable description
coordination_type: sequential | iterative_refinement
max_iterations: 3            # Only used for iterative_refinement
```

### Steps

Each step specifies an agent to execute:

```yaml
steps:
  - agent_type: research     # Maps to ResearchAgent
    name: gather_info        # Human-readable step name

  - agent_type: assessment   # Maps to AssessmentAgent
    name: verify_quality
```

## Coordination Types

### Sequential

Executes steps **one after another**. Simple pipelines.

```yaml
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: step1
  - agent_type: assessment
    name: step2
```

**Flow**: Research → Assessment → Done

**Use case**: Simple multi-step processing (research, then summarize, then format).

### Iterative Refinement

Executes steps in a **loop until approved** or max iterations reached.

```yaml
coordination_type: iterative_refinement
max_iterations: 3
convergence_check: assessment_approved

steps:
  - agent_type: research      # Creates initial output
    name: create_research
  - agent_type: assessment    # Evaluates quality
    name: quality_check
```

**Flow**: Research → Assessment → (if not approved) → Research (with feedback) → Assessment → ...

**Use case**: Quality control loops (generate, critique, improve).

## Available Agents

Agents are defined in `app/agents/`:

| Agent Type | Description | Input | Output |
|------------|-------------|-------|--------|
| `research` | Conducts research on a topic | `topic`, `previous_feedback` (optional) | `{"findings": "...", "sources": [...]}` |
| `assessment` | Evaluates research quality | `research_findings`, `original_topic` | `{"approved": bool, "feedback": "..."}` |

### Adding New Agents

1. **Create agent class** in `app/agents/my_agent.py`:
   ```python
   from app.agents.base import Agent

   class MyAgent(Agent):
       def __init__(self):
           super().__init__(agent_type="my_agent")

       def execute(self, input_data, user_id_hash=None):
           # Your logic here
           return {"output": result, "usage": {...}}
   ```

2. **Register in** `app/agents/__init__.py`:
   ```python
   from app.agents.my_agent import MyAgent

   AGENT_REGISTRY = {
       "research": ResearchAgent,
       "assessment": AssessmentAgent,
       "my_agent": MyAgent,  # Add this
   }
   ```

3. **Use in workflows**:
   ```yaml
   steps:
     - agent_type: my_agent
       name: custom_step
   ```

## Convergence Checks

For `iterative_refinement`, specify when to stop iterating:

```yaml
convergence_check: assessment_approved  # Default
```

Available checks:
- `assessment_approved`: Stop when `output.approved == true`
- `quality_threshold`: Stop when `output.quality_score >= 0.8`

## Data Flow

### Sequential

Each step receives the **previous step's output**:

```yaml
steps:
  - agent_type: research
    name: step1
    # Input: workflow input
    # Output: {"findings": "..."}

  - agent_type: assessment
    name: step2
    # Input: {"previous_output": {...}, "research_findings": {...}}
    # Output: {"approved": true}
```

### Iterative Refinement

Steps iterate with **feedback**:

**Iteration 1:**
- Research agent: Gets `topic`
- Assessment agent: Gets `research_findings`

**Iteration 2 (if not approved):**
- Research agent: Gets `topic` + `previous_feedback`
- Assessment agent: Gets new `research_findings`

## Examples

### Simple Sequential Pipeline

```yaml
# app/workflows/document_pipeline.yaml
name: document_pipeline
description: Process a document through multiple stages
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: extract_key_points
  - agent_type: assessment
    name: validate_extraction
```

### Quality Control Loop

```yaml
# app/workflows/research_assessment.yaml
name: research_assessment
description: Research with quality feedback loop
coordination_type: iterative_refinement
max_iterations: 3
convergence_check: assessment_approved

steps:
  - agent_type: research
    name: conduct_research
  - agent_type: assessment
    name: assess_quality
```

## Architecture

```
┌─────────────────┐
│  YAML Workflow  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ WorkflowRegistry    │ ← Auto-loads from app/workflows/
│ (Startup)           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ DeclarativeOrch.    │ ← Generic orchestrator
│ (Runtime)           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ CoordinationStrategy│ ← Sequential or IterativeRefinement
│                     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     Agents          │ ← ResearchAgent, AssessmentAgent, etc.
│                     │
└─────────────────────┘
```

## Monitoring

### View Workflow Execution

1. **Management UI** (http://localhost:8501)
   - Search for task by ID
   - See parent task + all subtasks
   - View iteration history

2. **Grafana Traces** (http://localhost:3002)
   - Full distributed trace
   - See timing for each step
   - Identify bottlenecks

### Database Queries

```sql
-- View workflow state
SELECT * FROM workflow_state
WHERE parent_task_id = 'task-uuid';

-- View all subtasks in a workflow
SELECT * FROM subtasks
WHERE parent_task_id = 'task-uuid'
ORDER BY iteration, created_at;
```

## Debugging

### Workflow Not Loading

Check logs at startup:
```bash
docker-compose logs task-api | grep -i workflow
docker-compose logs task-worker | grep -i workflow
```

Expected output:
```
INFO: Loaded declarative workflow: my_workflow
```

### Workflow Failing

1. Check YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('app/workflows/my_workflow.yaml'))"
   ```

2. View worker logs:
   ```bash
   docker-compose logs -f task-worker
   ```

3. Check database:
   ```sql
   SELECT * FROM tasks WHERE type LIKE 'workflow:%' ORDER BY created_at DESC LIMIT 5;
   ```

## Best Practices

1. **Keep steps focused**: Each step should do one thing well
2. **Name workflows clearly**: Use snake_case matching the filename
3. **Document your workflows**: Use descriptive `description` field
4. **Test iteratively**: Start with `max_iterations: 1` for debugging
5. **Monitor costs**: Iterative workflows can use multiple LLM calls

## Advanced Topics

### Custom Coordination Strategies

Create new strategies in `app/orchestrator/coordination_strategies.py`:

```python
class ParallelStrategy(CoordinationStrategy):
    def initialize(self, parent_task_id, input_data, conn, ...):
        # Create all subtasks at once
        pass

    def process_completion(self, parent_task_id, subtask_id, output, ...):
        # Wait for all to complete
        pass
```

Register in `create_strategy()`:
```python
if definition.coordination_type == "parallel":
    return ParallelStrategy(definition)
```

### Conditional Workflows

Not yet supported, but planned:
```yaml
# Future feature
steps:
  - agent_type: research
    name: gather
    condition: "input.type == 'detailed'"
```

## Migration from Coded Orchestrators

If you have an existing Python orchestrator:

1. **Identify the pattern**: Sequential or iterative?
2. **List the steps**: What agents are involved?
3. **Create YAML**: Map steps to agent types
4. **Test side-by-side**: Keep old orchestrator while validating new one
5. **Switch**: Update task type from `coded_name` to `workflow:declarative_name`

Example: `ResearchAssessmentOrchestrator` → `research_assessment.yaml`

## See Also

- [Adding Agents](../app/agents/README.md) *(if you create this)*
- [Worker Architecture](WORKER_SCALING.md)
- [Open WebUI Integration](OPENWEBUI.md)
