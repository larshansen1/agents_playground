Dynamic Open WebUI Tools - Phased Requirements Document
Version: 1.0
Author: System Architecture
Date: 2024-11-30
Estimated Total Time: 16-20 hours (2-3 weeks part-time)

Executive Summary
Transform hardcoded Open WebUI tools into dynamic, registry-aware tools that automatically discover available agents, tools, and workflows. Split monolithic @queue tool into 4 specialized tools with comprehensive test coverage and distributed tracing.
Goals

Eliminate hardcoded task types - Query registry APIs dynamically
Improve user experience - Separate tools for different purposes
Enable discoverability - Users can explore available resources
Maintain observability - Full telemetry and test coverage
Production readiness - 80%+ test coverage, comprehensive tracing


System Architecture
┌─────────────────────────────────────────────────────┐
│              Open WebUI Tools Layer                 │
├─────────────────────────────────────────────────────┤
│  @discover  │  @queue  │  @agent  │  @workflow     │
│  (explore)  │  (smart) │ (direct) │  (direct)      │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│           Backend Registry APIs                     │
├─────────────────────────────────────────────────────┤
│  /admin/agents  │  /admin/tools  │  /admin/workflows│
│  /tasks/agent   │  /tasks (existing)                │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│              Registry Layer                         │
├─────────────────────────────────────────────────────┤
│  AgentRegistry  │  ToolRegistry  │  WorkflowRegistry│
└─────────────────────────────────────────────────────┘

Phase 1: Backend Registry APIs (4-5 hours)
Functional Requirements
FR1.1: Agent Registry Endpoint
Endpoint: GET /admin/agents
Response Format:
json{
  "agents": [
    {
      "name": "research",
      "description": "Research agent for deep topic investigation",
      "config": {
        "model": "gpt-4-turbo",
        "temperature": 0.7
      },
      "tools": ["web_search", "document_reader"]
    }
  ]
}
Requirements:

Returns all registered agents from agent_registry
Includes agent name, description, config, and tools
Returns empty list if no agents registered
Response time: < 100ms (no database queries)
Requires mTLS authentication


FR1.2: Tool Registry Endpoint
Endpoint: GET /admin/tools
Response Format:
json{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web using Brave Search API",
      "schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Search query"},
          "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
      }
    }
  ]
}
Requirements:

Returns all registered tools from tool_registry
Includes tool name, description, and JSON schema
Schema shows parameters, types, defaults, required fields
Returns empty list if no tools registered
Response time: < 100ms


FR1.3: Workflow Registry Endpoint
Endpoint: GET /admin/workflows
Response Format:
json{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with iterative assessment and refinement",
      "strategy": "iterative_refinement",
      "max_iterations": 3,
      "steps": [
        {
          "name": "research",
          "agent_type": "research",
          "description": "Conduct initial research",
          "tools": ["web_search"]
        },
        {
          "name": "assessment",
          "agent_type": "assessment",
          "description": "Assess research quality"
        }
      ]
    }
  ]
}
Requirements:

Returns all registered workflows from workflow_registry
Includes workflow name, description, strategy, max_iterations
Includes all steps with agent_type, tools, description
Returns empty list if no workflows registered
Response time: < 200ms (includes YAML parsing)


FR1.4: Direct Agent Execution Endpoint
Endpoint: POST /tasks/agent
Request Format:
json{
  "agent_type": "research",
  "input": {
    "topic": "AI safety governance"
  },
  "user_id": "user@example.com",
  "tenant_id": "production"
}
Response Format:
json{
  "id": "uuid-task-id",
  "status": "pending",
  "type": "agent:research",
  "created_at": "2024-11-30T12:00:00Z"
}
Requirements:

Creates task for single agent execution (no workflow)
Validates agent exists in registry
Returns 400 if agent not found (with available agents list)
Accepts same input format as workflow tasks
Creates task in database with status "pending"
Worker processes task using specified agent


Non-Functional Requirements
NFR1.1: Performance

All registry endpoints: < 200ms response time
No database queries (in-memory registry lookup only)
Support 100+ concurrent requests

NFR1.2: Security

All endpoints require mTLS authentication
Tenant isolation enforced
No sensitive data in responses (e.g., API keys in config)

NFR1.3: Caching

Registry data cached for 60 seconds
Cache invalidated on registry updates
Optional: ?refresh=true query param to bypass cache


Testing Requirements
TR1.1: Unit Tests (12 tests minimum)
File: tests/test_admin_registry_endpoints.py
pythonclass TestAgentRegistryEndpoint:
    def test_list_agents_success(self):
        """Test /admin/agents returns registered agents."""

    def test_list_agents_empty_registry(self):
        """Test /admin/agents with no agents registered."""

    def test_list_agents_includes_tools(self):
        """Test agent response includes tools list."""

    def test_list_agents_mTLS_required(self):
        """Test endpoint requires mTLS authentication."""

class TestToolRegistryEndpoint:
    def test_list_tools_success(self):
        """Test /admin/tools returns registered tools."""

    def test_list_tools_includes_schema(self):
        """Test tool response includes JSON schema."""

    def test_list_tools_empty_registry(self):
        """Test /admin/tools with no tools registered."""

class TestWorkflowRegistryEndpoint:
    def test_list_workflows_success(self):
        """Test /admin/workflows returns registered workflows."""

    def test_list_workflows_includes_steps(self):
        """Test workflow response includes all steps."""

    def test_list_workflows_empty_registry(self):
        """Test /admin/workflows with no workflows registered."""

class TestDirectAgentEndpoint:
    def test_create_agent_task_success(self):
        """Test POST /tasks/agent creates task."""

    def test_create_agent_task_unknown_agent(self):
        """Test error when agent not found."""
Coverage Target: 90%+ for admin endpoints

TR1.2: Integration Tests (4 tests minimum)
File: tests/test_registry_api_integration.py
pythonclass TestRegistryAPIIntegration:
    def test_discover_agents_tools_workflows(self):
        """Test complete registry discovery flow."""
        # Register agents, tools, workflows
        # Call all 3 endpoints
        # Verify all resources returned

    def test_agent_execution_uses_registry(self):
        """Test /tasks/agent uses agent from registry."""
        # Register agent
        # Create task via /tasks/agent
        # Verify task created with correct agent_type

    def test_registry_updates_reflected_in_api(self):
        """Test dynamic registration reflected in API."""
        # Call /admin/agents (empty)
        # Register new agent
        # Call /admin/agents again
        # Verify new agent present

    def test_workflow_references_valid_agents(self):
        """Test workflow steps reference registered agents."""
        # Call /admin/workflows
        # Extract all agent_types from steps
        # Call /admin/agents
        # Verify all agent_types exist
Coverage Target: 85%+ for integration scenarios

Telemetry Requirements
TM1.1: Distributed Tracing
Trace all registry API calls:
python# app/routers/admin.py

@router.get("/admin/agents")
async def list_agents():
    """List all registered agents."""
    with tracer.start_as_current_span(
        "admin.list_agents",
        attributes={
            "http.method": "GET",
            "http.route": "/admin/agents",
        }
    ) as span:
        agents = agent_registry.list_all()
        span.set_attribute("agent.count", len(agents))

        # ... build response ...

        return {"agents": agents}
Required attributes:

http.method - HTTP method
http.route - API route
agent.count / tool.count / workflow.count - Number of items
cache.hit - Whether response from cache
response.time_ms - Response generation time


TM1.2: Structured Logging
Log all registry queries:
pythonimport structlog

logger = structlog.get_logger(__name__)

@router.get("/admin/agents")
async def list_agents():
    logger.info(
        "registry.api.agents.list",
        agent_count=len(agents),
        response_time_ms=elapsed_ms,
        cache_hit=False,
    )
Required log fields:

event - Event name (e.g., "registry.api.agents.list")
agent_count / tool_count / workflow_count
response_time_ms
cache_hit (if caching implemented)
tenant_id (if multi-tenant)


TM1.3: Metrics
Prometheus metrics for registry APIs:
pythonfrom prometheus_client import Counter, Histogram

registry_requests = Counter(
    "registry_api_requests_total",
    "Total registry API requests",
    ["endpoint", "status"]
)

registry_response_time = Histogram(
    "registry_api_response_seconds",
    "Registry API response time",
    ["endpoint"]
)

@router.get("/admin/agents")
async def list_agents():
    with registry_response_time.labels(endpoint="agents").time():
        # ... handle request ...
        registry_requests.labels(endpoint="agents", status="success").inc()
Required metrics:

registry_api_requests_total{endpoint, status} - Request counter
registry_api_response_seconds{endpoint} - Response time histogram
registry_cache_hits_total{endpoint} - Cache hit counter (if caching)


Acceptance Criteria
Phase 1 is complete when:

✅ All 4 endpoints implemented (/admin/agents, /admin/tools, /admin/workflows, /tasks/agent)
✅ 12+ unit tests passing (90%+ coverage)
✅ 4+ integration tests passing (85%+ coverage)
✅ All endpoints traced with OpenTelemetry
✅ Structured logging on all endpoints
✅ Prometheus metrics exported
✅ Response time < 200ms for all endpoints
✅ Documentation updated (API docs, README)

Verification:
bash# Test endpoints
curl -X GET https://localhost:8000/admin/agents --cert client.pem --key client.key
curl -X GET https://localhost:8000/admin/tools --cert client.pem --key client.key
curl -X GET https://localhost:8000/admin/workflows --cert client.pem --key client.key

# Test direct agent execution
curl -X POST https://localhost:8000/tasks/agent \
  --cert client.pem --key client.key \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "research", "input": {"topic": "test"}, "user_id": "test@example.com"}'

# Verify metrics
curl http://localhost:8000/metrics | grep registry_api

# Run tests
pytest tests/test_admin_registry_endpoints.py -v --cov=app/routers/admin
pytest tests/test_registry_api_integration.py -v

Phase 2: @discover Tool (3-4 hours)
Functional Requirements
FR2.1: Tool Structure
File: openwebui_tools/discover.py
Tool metadata:
python"""
title: Registry Discovery Tool
author: system
version: 1.0
description: Discover available agents, tools, and workflows in the backend system
requirements: requests, asyncio
"""
Valves configuration:
pythonclass Valves(BaseModel):
    task_api_url: str = Field(
        default=os.getenv("TASK_API_URL", "http://task-api:8000"),
        description="Base URL for Task API"
    )
    # ... mTLS cert paths (same as existing queue tool) ...
    cache_ttl_seconds: int = Field(
        default=60,
        description="Cache registry data for N seconds"
    )

FR2.2: Discovery Commands
Command: @discover or @discover all
Output:
markdown# Available Resources

## Agents (3)
- **research**: Research agent for deep topic investigation
  - Tools: web_search, document_reader
  - Model: gpt-4-turbo
- **assessment**: Assessment agent for quality evaluation
  - Model: gpt-4-turbo
- **analysis**: Data analysis agent
  - Tools: calculator, database_query

## Tools (4)
- **web_search**: Search the web using Brave Search API
  - Parameters: query (required), max_results (optional)
- **calculator**: Safe mathematical expression evaluator
  - Parameters: expression (required)
- **document_reader**: Fetch and extract text from URLs
  - Parameters: url (required), max_length (optional)
- **database_query**: Query internal database
  - Parameters: query_type (required), limit (optional)

## Workflows (2)
- **research_assessment**: Research with iterative assessment
  - Strategy: iterative_refinement (max 3 iterations)
  - Steps: 2 agents (research → assessment)
- **simple_sequential**: Simple sequential workflow
  - Strategy: sequential
  - Steps: 2 agents

Command: @discover agents
Output:
markdown# Available Agents (3)

**research**
- Description: Research agent for deep topic investigation
- Tools: web_search, document_reader
- Model: gpt-4-turbo
- Temperature: 0.7

**assessment**
- Description: Assessment agent for quality evaluation
- Model: gpt-4-turbo
- Temperature: 0.3

**analysis**
- Description: Data analysis agent
- Tools: calculator, database_query
- Model: gpt-4-turbo

Command: @discover tools
Output:
markdown# Available Tools (4)

**web_search**
- Description: Search the web using Brave Search API
- Parameters:
  - query (string, required): Search query
  - max_results (integer, optional, default=5): Max results to return

**calculator**
- Description: Safe mathematical expression evaluator
- Parameters:
  - expression (string, required): Mathematical expression to evaluate

**document_reader**
- Description: Fetch and extract text from URLs
- Parameters:
  - url (string, required): URL to fetch
  - max_length (integer, optional, default=10000): Max text length

**database_query**
- Description: Query internal database safely
- Parameters:
  - query_type (string, required): Type of query (task_stats, cost_by_user, recent_tasks)
  - user_id_hash (string, optional): User ID for filtering
  - limit (integer, optional, default=10): Number of results

Command: @discover workflows
Output:
markdown# Available Workflows (2)

**research_assessment**
- Description: Research with iterative assessment and refinement
- Strategy: iterative_refinement
- Max Iterations: 3
- Steps:
  1. research (research agent)
     - Description: Conduct initial research
     - Tools: web_search
  2. assessment (assessment agent)
     - Description: Assess research quality
     - Convergence: Check approved=true

**simple_sequential**
- Description: Simple sequential two-agent workflow
- Strategy: sequential
- Steps:
  1. step_one (research agent)
  2. step_two (assessment agent)

---

**Usage:**
- Execute workflow: `@workflow research_assessment "your topic"`
- Execute agent: `@agent research "your query"`
- Queue task: `@queue "your task description"`

FR2.3: Error Handling
Scenario: Backend API unreachable
Output:
markdown❌ **Error: Cannot connect to backend**

The registry API is unavailable. Please check:
1. Backend service is running
2. mTLS certificates are configured correctly
3. Network connectivity

Error details: Connection refused to http://task-api:8000/admin/agents

Scenario: No resources registered
Output:
markdown# Available Resources

⚠️ **No agents registered**

⚠️ **No tools registered**

⚠️ **No workflows registered**

The system is running but no resources have been configured.
Please check the agent/tool/workflow registries.

FR2.4: Caching
Requirements:

Cache registry responses for cache_ttl_seconds (default: 60s)
Cache key: registry:{type} (e.g., registry:agents)
Cache invalidation: TTL-based (no manual invalidation)
Cache bypass: Internal flag (no user-facing option)

Implementation:
pythonclass Tools:
    def __init__(self):
        self.valves = self.Valves()
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, data)

    async def _get_cached_or_fetch(
        self,
        cache_key: str,
        fetch_func: Callable,
    ) -> Any:
        """Get from cache or fetch from API."""
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if now - timestamp < self.valves.cache_ttl_seconds:
                return data

        # Cache miss - fetch from API
        data = await fetch_func()
        self._cache[cache_key] = (now, data)
        return data

Non-Functional Requirements
NFR2.1: Performance

Total discovery time: < 3 seconds (all 3 API calls)
Cached discovery: < 100ms
UI status updates: Every 500ms during discovery

NFR2.2: User Experience

Real-time status updates via __event_emitter__
Clear formatting with markdown
Helpful error messages
Examples in output

NFR2.3: Maintainability

Separate formatting functions per resource type
Reusable API client methods
Comprehensive docstrings


Testing Requirements
TR2.1: Unit Tests (15 tests minimum)
File: tests/test_discover_tool.py
pythonclass TestDiscoverTool:
    def test_discover_all_formats_correctly(self, mock_api):
        """Test @discover all returns formatted output."""

    def test_discover_agents_only(self, mock_api):
        """Test @discover agents returns only agents."""

    def test_discover_tools_only(self, mock_api):
        """Test @discover tools returns only tools."""

    def test_discover_workflows_only(self, mock_api):
        """Test @discover workflows returns only workflows."""

    def test_discover_empty_registry(self, mock_api):
        """Test @discover with no resources registered."""

    def test_discover_api_error(self, mock_api):
        """Test @discover handles API errors gracefully."""

    def test_discover_network_error(self, mock_api):
        """Test @discover handles network errors."""

    def test_discover_invalid_response(self, mock_api):
        """Test @discover handles malformed API responses."""

class TestDiscoverCaching:
    def test_cache_hit(self, mock_api):
        """Test cached response returns quickly."""

    def test_cache_miss(self, mock_api):
        """Test cache miss fetches from API."""

    def test_cache_expiry(self, mock_api):
        """Test cache expires after TTL."""

    def test_cache_per_resource_type(self, mock_api):
        """Test separate cache per resource type."""

class TestDiscoverFormatting:
    def test_format_agent_with_tools(self):
        """Test agent formatting includes tools."""

    def test_format_tool_with_schema(self):
        """Test tool formatting includes parameter schema."""

    def test_format_workflow_with_steps(self):
        """Test workflow formatting includes all steps."""
Coverage Target: 85%+ for discover tool

TR2.2: Integration Tests (3 tests minimum)
File: tests/test_discover_tool_integration.py
pythonclass TestDiscoverToolIntegration:
    def test_discover_real_backend(self, test_backend):
        """Test @discover against real backend."""
        # Start test backend with real registries
        # Call @discover all
        # Verify all resources returned

    def test_discover_trace_propagation(self, test_backend):
        """Test @discover creates trace spans."""
        # Call @discover
        # Verify trace spans created
        # Verify span attributes set

    def test_discover_emits_status_updates(self, test_backend):
        """Test @discover emits UI status updates."""
        # Mock event emitter
        # Call @discover
        # Verify status updates emitted
Coverage Target: 80%+ for integration

Telemetry Requirements
TM2.1: Distributed Tracing
Trace @discover operations:
pythonasync def at_discover(
    self,
    query: str = "",
    __event_emitter__: Any = None,
) -> str:
    """Discover available resources."""

    # Create root span
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    with tracer.start_span(
        "openwebui.discover",
        attributes={
            "discover.query": query or "all",
            "discover.user_request": True,
        }
    ) as root_span:
        # Fetch agents
        with tracer.start_span(
            "openwebui.discover.fetch_agents",
            parent=root_span,
        ) as span:
            agents = await self._fetch_agents()
            span.set_attribute("discover.agents.count", len(agents))

        # Fetch tools
        with tracer.start_span(
            "openwebui.discover.fetch_tools",
            parent=root_span,
        ) as span:
            tools = await self._fetch_tools()
            span.set_attribute("discover.tools.count", len(tools))

        # Fetch workflows
        with tracer.start_span(
            "openwebui.discover.fetch_workflows",
            parent=root_span,
        ) as span:
            workflows = await self._fetch_workflows()
            span.set_attribute("discover.workflows.count", len(workflows))

        root_span.set_attribute("discover.total_resources",
                                len(agents) + len(tools) + len(workflows))

        return formatted_output
Required attributes:

discover.query - Query type (all, agents, tools, workflows)
discover.agents.count - Number of agents
discover.tools.count - Number of tools
discover.workflows.count - Number of workflows
discover.total_resources - Total resources found
discover.cache_hit - Whether response from cache
discover.response_time_ms - Total response time


TM2.2: Structured Logging
Log discovery operations:
pythonlogger.info(
    "openwebui.discover.complete",
    query=query or "all",
    agents_count=len(agents),
    tools_count=len(tools),
    workflows_count=len(workflows),
    cache_hit=cache_hit,
    response_time_ms=elapsed_ms,
)

Acceptance Criteria
Phase 2 is complete when:

✅ @discover tool implemented with all commands
✅ Supports @discover, @discover all, @discover agents, @discover tools, @discover workflows
✅ 15+ unit tests passing (85%+ coverage)
✅ 3+ integration tests passing (80%+ coverage)
✅ Caching implemented (60s TTL)
✅ Distributed tracing on all operations
✅ Structured logging on all operations
✅ Error handling for all failure modes
✅ User documentation (README, examples)

Verification:
bash# Test in Open WebUI
User: @discover
User: @discover agents
User: @discover tools
User: @discover workflows

# Run tests
pytest tests/test_discover_tool.py -v --cov=openwebui_tools/discover
pytest tests/test_discover_tool_integration.py -v

# Verify traces in Jaeger
# Verify logs in structured format

Phase 3: Enhanced @queue Tool (3-4 hours)
Functional Requirements
FR3.1: Dynamic Workflow Selection
Update: Replace _infer_task_type() with dynamic lookup
Old implementation (hardcoded):
pythondef _infer_task_type(self, user_message: str) -> str:
    """Infer task type from user message."""
    if "research" in message_lower:
        return "workflow:research_assessment"
    if "summarize" in message_lower:
        return "summarize_document"
    # etc...
New implementation (dynamic):
pythonasync def _smart_workflow_selection(
    self,
    instruction: str,
    __event_emitter__: Any = None,
) -> str | None:
    """
    Dynamically select workflow based on available workflows.

    Selection strategy:
    1. Exact workflow name match in instruction
    2. Keyword match in workflow descriptions
    3. Fallback to default workflow (research_assessment)
    """
    instruction_lower = instruction.lower()

    # Fetch available workflows (cached)
    workflows = await self._get_cached_or_fetch(
        "registry:workflows",
        self._fetch_workflows
    )

    if not workflows:
        return "workflow:research_assessment"  # Fallback

    # Strategy 1: Exact name match
    for workflow in workflows:
        if workflow['name'] in instruction_lower:
            await self._emit_status(
                __event_emitter__,
                f"Selected workflow: {workflow['name']}",
                False
            )
            return f"workflow:{workflow['name']}"

    # Strategy 2: Keyword matching
    matches = []
    for workflow in workflows:
        desc_lower = workflow.get('description', '').lower()
        keywords = set(desc_lower.split())
        user_words = set(instruction_lower.split())

        # Calculate keyword overlap
        overlap = len(keywords & user_words)
        if overlap > 0:
            matches.append((workflow, overlap))

    if matches:
        # Sort by overlap (best match first)
        matches.sort(key=lambda x: x[1], reverse=True)
        best_match = matches[0][0]

        await self._emit_status(
            __event_emitter__,
            f"Matched workflow: {best_match['name']}",
            False
        )
        return f"workflow:{best_match['name']}"

    # Strategy 3: Fallback
    await self._emit_status(
        __event_emitter__,
        "Using default workflow: research_assessment",
        False
    )
    return "workflow:research_assessment"

FR3.2: Workflow Suggestions
Enhancement: Show workflow suggestions on ambiguous input
Scenario: User query matches multiple workflows
Output:
markdown📋 **Multiple workflows match your query:**

1. **research_assessment** (3 keyword matches)
   - Research with iterative assessment and refinement
   - Use: `@workflow research_assessment "your topic"`

2. **deep_research** (2 keyword matches)
   - Deep research with multiple sources
   - Use: `@workflow deep_research "your topic"`

**Auto-selected:** research_assessment (best match)

Proceeding with research_assessment workflow...
```

---

#### FR3.3: Backward Compatibility

**Requirement:** Existing `@queue` commands continue to work

**Test cases:**
```
@queue summarize this document
  → Should still create summarize_document task

@queue analyze this table
  → Should still create analyze_table task

@queue research AI safety
  → Should dynamically select workflow (new behavior)

Non-Functional Requirements
NFR3.1: Performance

Workflow selection: < 500ms (including API call)
Cached workflow selection: < 50ms
No degradation for non-workflow tasks

NFR3.2: User Experience

Clear feedback on workflow selection
Show matched keywords (if multiple matches)
Graceful fallback to default workflow


Testing Requirements
TR3.1: Unit Tests (18 tests minimum)
File: tests/test_queue_tool_dynamic.py
pythonclass TestSmartWorkflowSelection:
    def test_exact_workflow_name_match(self, mock_api):
        """Test exact workflow name in instruction."""

    def test_keyword_matching(self, mock_api):
        """Test keyword-based workflow matching."""

    def test_multiple_matches_best_selected(self, mock_api):
        """Test best match selected with multiple options."""

    def test_no_match_uses_default(self, mock_api):
        """Test fallback to default workflow."""

    def test_empty_workflow_registry(self, mock_api):
        """Test behavior when no workflows registered."""

class TestBackwardCompatibility:
    def test_summarize_task_still_works(self):
        """Test @queue summarize creates summarize_document task."""

    def test_analyze_task_still_works(self):
        """Test @queue analyze creates analyze_table task."""

    def test_compare_task_still_works(self):
        """Test @queue compare creates compare_options task."""

class TestWorkflowSuggestions:
    def test_multiple_matches_shows_suggestions(self, mock_api):
        """Test suggestions shown for multiple matches."""

    def test_suggestion_format(self, mock_api):
        """Test suggestion output format."""

class TestQueueCaching:
    def test_workflow_list_cached(self, mock_api):
        """Test workflow list cached for performance."""

    def test_cache_ttl_respected(self, mock_api):
        """Test cache expires after TTL."""

class TestQueueErrorHandling:
    def test_api_error_fallback(self, mock_api):
        """Test fallback when API unavailable."""

    def test_invalid_workflow_response(self, mock_api):
        """Test handling of malformed API response."""

    def test_network_timeout(self, mock_api):
        """Test handling of network timeout."""

class TestQueueTracing:
    def test_trace_context_propagated(self, mock_tracer):
        """Test trace context passed to backend."""

    def test_workflow_selection_traced(self, mock_tracer):
        """Test workflow selection creates span."""

    def test_trace_attributes_set(self, mock_tracer):
        """Test trace attributes include workflow info."""
Coverage Target: 90%+ for queue tool

TR3.2: Integration Tests (5 tests minimum)
File: tests/test_queue_tool_integration.py
pythonclass TestQueueToolIntegration:
    def test_queue_dynamic_workflow_end_to_end(self, test_backend):
        """Test @queue with dynamic workflow selection."""

    def test_queue_backward_compatible(self, test_backend):
        """Test @queue with legacy task types."""

    def test_queue_workflow_suggestions(self, test_backend):
        """Test workflow suggestions on ambiguous input."""

    def test_queue_trace_propagation(self, test_backend):
        """Test trace propagation through workflow."""

    def test_queue_with_real_registries(self, test_backend):
        """Test @queue against real backend registries."""
Coverage Target: 85%+ for integration

Telemetry Requirements
TM3.1: Distributed Tracing
Trace workflow selection:
pythonasync def _smart_workflow_selection(
    self,
    instruction: str,
    __event_emitter__: Any = None,
) -> str | None:
    """Dynamically select workflow."""

    with tracer.start_span(
        "openwebui.queue.workflow_selection",
        attributes={
            "instruction": instruction[:100],
        }
    ) as span:
        # Fetch workflows
        with tracer.start_span(
            "openwebui.queue.fetch_workflows",
            parent=span,
        ) as fetch_span:
            workflows = await self._get_cached_or_fetch(...)
            fetch_span.set_attribute("workflows.count", len(workflows))

        # Match workflow
        selected = self._match_workflow(instruction, workflows)

        span.set_attribute("workflow.selected", selected)
        span.set_attribute("workflow.selection_strategy", strategy)

        return selected

TM3.2: Structured Logging
pythonlogger.info(
    "openwebui.queue.workflow_selected",
    instruction=instruction[:100],
    workflow_name=selected_workflow,
    selection_strategy=strategy,
    match_score=overlap_score,
    alternatives_count=len(matches),
)

Acceptance Criteria
Phase 3 is complete when:

✅ Dynamic workflow selection implemented
✅ Backward compatibility maintained
✅ Workflow suggestions on ambiguous input
✅ 18+ unit tests passing (90%+ coverage)
✅ 5+ integration tests passing (85%+ coverage)
✅ Distributed tracing on workflow selection
✅ Structured logging on all operations
✅ Performance: < 500ms workflow selection

Verification:
bash# Test dynamic workflow selection
User: @queue research quantum computing
  → Should auto-select research_assessment workflow

User: @queue deep_research AI safety
  → Should select deep_research workflow (if exists)

User: @queue summarize this document
  → Should create summarize_document task (backward compatible)

# Run tests
pytest tests/test_queue_tool_dynamic.py -v --cov
pytest tests/test_queue_tool_integration.py -v
```

---

## Phase 4: @agent Tool (2-3 hours)

### Functional Requirements

#### FR4.1: Direct Agent Execution

**Command:** `@agent <agent_name> <instruction>`

**Examples:**
```
@agent research "quantum computing trends 2024"
@agent assessment "review this research quality"
@agent analysis "calculate revenue projections"
Behavior:

Parse agent name from command
Verify agent exists in registry
Create task with type: "agent:{agent_name}"
Wait for task completion
Return formatted result


FR4.2: Agent Discovery
Command: @agent (no arguments)
Output:
markdown# Available Agents

You can execute any of these agents directly:

**research**
- Description: Research agent for deep topic investigation
- Tools: web_search, document_reader
- Usage: `@agent research "your query"`

**assessment**
- Description: Assessment agent for quality evaluation
- Usage: `@agent assessment "your evaluation request"`

**analysis**
- Description: Data analysis agent
- Tools: calculator, database_query
- Usage: `@agent analysis "your analysis task"`

---

**Examples:**
```
@agent research "AI safety governance"
@agent assessment "review the research above"
@agent analysis "calculate growth rate"
```

FR4.3: Agent Validation
Scenario: Unknown agent
Input: @agent unknown_agent "test query"
Output:
markdown❌ **Unknown agent: unknown_agent**

**Available agents:**
- research
- assessment
- analysis

**Usage:** `@agent <agent_name> <instruction>`

**Example:** `@agent research "your query"`

FR4.4: Error Handling
Scenario: Missing instruction
Input: @agent research
Output:
markdown❌ **Missing instruction**

**Usage:** `@agent <agent_name> <instruction>`

**Example:** `@agent research "quantum computing trends"`

Scenario: Agent execution error
Output:
markdown❌ **Agent Execution Error**

Agent: research
Error: LLM API rate limit exceeded

**Task ID:** `abc123-def456-...`

You can check task status: `@queue status abc123-def456-...`

Non-Functional Requirements
NFR4.1: Performance

Agent validation: < 100ms (cached)
Task creation: < 500ms
Total execution time: Same as workflow tasks

NFR4.2: User Experience

Clear agent selection
Helpful error messages
Examples in help text


Testing Requirements
TR4.1: Unit Tests (12 tests minimum)
File: tests/test_agent_tool.py
pythonclass TestAgentTool:
    def test_agent_execution_success(self, mock_api):
        """Test @agent executes agent successfully."""

    def test_agent_list_available(self, mock_api):
        """Test @agent with no args lists agents."""

    def test_agent_unknown_agent(self, mock_api):
        """Test @agent with unknown agent shows error."""

    def test_agent_missing_instruction(self, mock_api):
        """Test @agent with missing instruction shows error."""

    def test_agent_validation_cached(self, mock_api):
        """Test agent list cached for performance."""

class TestAgentToolFormatting:
    def test_agent_list_format(self):
        """Test agent list output format."""

    def test_agent_error_format(self):
        """Test error message format."""

    def test_agent_help_includes_examples(self):
        """Test help text includes examples."""

class TestAgentToolTracing:
    def test_agent_execution_traced(self, mock_tracer):
        """Test @agent creates trace spans."""

    def test_trace_includes_agent_name(self, mock_tracer):
        """Test trace includes agent name attribute."""

    def test_trace_propagates_to_backend(self, mock_tracer):
        """Test trace propagates to backend."""

class TestAgentToolIntegration:
    def test_agent_creates_correct_task_type(self, test_backend):
        """Test @agent creates agent:* task type."""

    def test_agent_waits_for_completion(self, test_backend):
        """Test @agent waits for task completion."""
Coverage Target: 85%+ for agent tool

Telemetry Requirements
TM4.1: Distributed Tracing
pythonasync def at_agent(
    self,
    command: str,
    __event_emitter__: Any = None,
) -> str:
    """Execute agent directly."""

    with tracer.start_span(
        "openwebui.agent.execute",
        attributes={
            "agent.command": command[:100],
        }
    ) as span:
        # Parse agent name
        agent_name = self._parse_agent_name(command)
        span.set_attribute("agent.name", agent_name)

        # Validate agent
        with tracer.start_span(
            "openwebui.agent.validate",
            parent=span,
        ) as validate_span:
            is_valid = await self._validate_agent(agent_name)
            validate_span.set_attribute("agent.valid", is_valid)

        # Execute
        task_id = await self._create_agent_task(...)
        span.set_attribute("task.id", task_id)

        return result
```

---

### Acceptance Criteria

**Phase 4 is complete when:**

1. ✅ `@agent` tool implemented
2. ✅ Supports agent execution and discovery
3. ✅ 12+ unit tests passing (85%+ coverage)
4. ✅ Distributed tracing on all operations
5. ✅ Structured logging
6. ✅ Documentation (README, examples)

---

## Phase 5: @workflow Tool (2-3 hours)

### Functional Requirements

#### FR5.1: Direct Workflow Execution

**Command:** `@workflow <workflow_name> <topic>`

**Examples:**
```
@workflow research_assessment "quantum computing"
@workflow simple_sequential "market analysis"
@workflow custom_workflow "user query"

FR5.2: Workflow Discovery
Command: @workflow (no arguments)
Output:
markdown# Available Workflows

**research_assessment**
- Description: Research with iterative assessment and refinement
- Strategy: iterative_refinement (max 3 iterations)
- Steps: research → assessment
- Usage: `@workflow research_assessment "your topic"`

**simple_sequential**
- Description: Simple sequential two-agent workflow
- Strategy: sequential
- Steps: step_one → step_two
- Usage: `@workflow simple_sequential "your topic"`

---

**Examples:**
```
@workflow research_assessment "AI safety governance"
@workflow simple_sequential "quarterly revenue analysis"
```

**Note:** You can also use `@queue` for smart workflow selection.

FR5.3: Workflow Validation
Similar to @agent validation - Show available workflows on error.

Testing Requirements
Similar to @agent tool - 12+ unit tests, 85%+ coverage, tracing, logging.

Acceptance Criteria
Phase 5 is complete when:

✅ @workflow tool implemented
✅ 12+ unit tests passing (85%+ coverage)
✅ Distributed tracing
✅ Documentation


Phase 6: Documentation & Polish (2 hours)
Documentation Requirements
DR6.1: API Documentation
File: docs/REGISTRY_API.md
Contents:
markdown# Registry API Documentation

## Endpoints

### GET /admin/agents
Returns all registered agents.

**Response:**
```json
{
  "agents": [...]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/agents \
  --cert client.pem \
  --key client.key
```

### GET /admin/tools
...

### GET /admin/workflows
...

### POST /tasks/agent
...

DR6.2: Open WebUI Tools Guide
File: docs/OPENWEBUI_TOOLS.md
Contents:
markdown# Open WebUI Tools Guide

## Available Tools

### @discover - Registry Explorer
Discover available agents, tools, and workflows.

**Usage:**
- `@discover` - Show all resources
- `@discover agents` - Show only agents
- `@discover tools` - Show only tools
- `@discover workflows` - Show only workflows

### @queue - Smart Task Queue
Submit tasks with automatic workflow selection.

**Usage:**
- `@queue research AI safety` - Auto-selects workflow
- `@queue summarize document` - Legacy task type

### @agent - Direct Agent Execution
Execute a specific agent directly.

**Usage:**
- `@agent research "your query"`
- `@agent assessment "your evaluation"`

### @workflow - Direct Workflow Execution
Execute a specific workflow by name.

**Usage:**
- `@workflow research_assessment "your topic"`
- `@workflow simple_sequential "your task"`

## Examples

### Research Workflow
```
User: @discover workflows
User: @workflow research_assessment "quantum computing trends"
  → Executes multi-agent research workflow
```

### Direct Agent Usage
```
User: @agent research "AI safety governance"
  → Executes research agent only
```
```

---

#### DR6.3: README Updates

Update main README with:
- New registry endpoints
- New Open WebUI tools
- Examples
- Architecture diagram

---

### Polish Requirements

#### PR6.1: Code Quality
- All files pass linting (ruff)
- Type hints on all functions
- Docstrings on all classes/methods
- No TODO/FIXME comments

#### PR6.2: Error Messages
- All errors have helpful messages
- Suggest corrections
- Include examples

#### PR6.3: Logging
- Consistent log levels
- Structured logging throughout
- No sensitive data in logs

---

### Acceptance Criteria

**Phase 6 is complete when:**

1. ✅ Complete API documentation
2. ✅ Complete Open WebUI tools guide
3. ✅ README updated
4. ✅ All code linted
5. ✅ All docstrings complete
6. ✅ Error messages polished

---

## Overall Success Criteria

### Test Coverage Requirements

**Target: 85%+ overall coverage**

| Component | Coverage Target | Tests Required |
|-----------|----------------|----------------|
| Backend Registry APIs | 90%+ | 16+ tests |
| @discover Tool | 85%+ | 15+ tests |
| @queue Tool | 90%+ | 18+ tests |
| @agent Tool | 85%+ | 12+ tests |
| @workflow Tool | 85%+ | 12+ tests |

**Total Tests Required:** 73+ tests

**Test Execution Time:** < 10 seconds

---

### Telemetry Requirements

#### Distributed Tracing Coverage

**All operations must be traced:**
- ✅ Registry API calls
- ✅ Tool executions (@discover, @queue, @agent, @workflow)
- ✅ Workflow selection logic
- ✅ Cache operations

**Required trace attributes:**
- `http.method`, `http.route` (API calls)
- `agent.name`, `tool.name`, `workflow.name` (execution)
- `cache.hit` (cache operations)
- `error.type`, `error.message` (errors)

---

#### Structured Logging Coverage

**All operations must log:**
- ✅ INFO: Successful operations
- ✅ WARN: Fallbacks, cache misses
- ✅ ERROR: Failures, exceptions

**Required log fields:**
- `event` - Event name
- `duration_ms` - Operation duration
- `cache_hit` - Cache status
- `error` - Error details (if applicable)

---

#### Metrics Coverage

**Required Prometheus metrics:**
```
registry_api_requests_total{endpoint, status}
registry_api_response_seconds{endpoint}
registry_cache_hits_total{endpoint}
openwebui_tool_executions_total{tool, status}
openwebui_tool_response_seconds{tool}
openwebui_workflow_selections_total{strategy}

Timeline Summary
PhaseTimeTestsCoverageDeliverablePhase 14-5h16+90%+Registry APIsPhase 23-4h15+85%+@discover toolPhase 33-4h18+90%+Enhanced @queuePhase 42-3h12+85%+@agent toolPhase 52-3h12+85%+@workflow toolPhase 62h--DocumentationTotal16-21h73+85%+Complete system

Verification Checklist
✅ Phase 1 Complete

 All 4 endpoints implemented
 16+ tests passing
 90%+ coverage
 Tracing implemented
 Metrics exported
 Documentation updated

✅ Phase 2 Complete

 @discover tool implemented
 15+ tests passing
 85%+ coverage
 Caching working
 Tracing implemented
 User guide updated

✅ Phase 3 Complete

 Dynamic workflow selection implemented
 18+ tests passing
 90%+ coverage
 Backward compatibility maintained
 Tracing implemented

✅ Phase 4 Complete

 @agent tool implemented
 12+ tests passing
 85%+ coverage
 Tracing implemented

✅ Phase 5 Complete

 @workflow tool implemented
 12+ tests passing
 85%+ coverage
 Tracing implemented

✅ Phase 6 Complete

 All documentation complete
 Code linted
 Error messages polished

✅ Overall System Complete

 73+ total tests passing
 85%+ overall coverage
 All telemetry working
 Production deployment ready


Out of Scope
Not included in this project:
❌ Agent/Tool/Workflow creation via Open WebUI
❌ Registry editing via Open WebUI
❌ Advanced workflow orchestration
❌ Multi-modal support
❌ Real-time registry updates (WebSocket)
❌ User-specific agent/tool customization
These can be added in future iterations.é
