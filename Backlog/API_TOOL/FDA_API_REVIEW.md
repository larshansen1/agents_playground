# FDA API Governance Review - Requirements Specification

## Overview

**Purpose:** AI-assisted API governance review system that analyzes OpenAPI specifications against Danish FDA (Fællesoffentlig Digital Arkitektur) guidelines and produces auditable compliance reports with traceable reasoning.

**Actors:** User (submits specs), System (orchestrates analysis), Auditor (reviews decisions post-hoc)

**Core domains:** Analysis (spec parsing, guideline checking), Governance (decision audit, traceability), Reporting (findings, recommendations)

**APIs:**
- Task API (submit analysis requests) - existing
- Governance API (query audit trail) - new

**Tech stack:** Python 3.11+, FastAPI, PostgreSQL, OpenTelemetry, existing orchestration platform

**Timeline goal:** 2-3 weeks to MVP with full governance instrumentation

---

## Actors

### Actor: User

**Can:**
- Submit OpenAPI specification for analysis (URL, file upload, or paste)
- Request analysis against FDA guidelines
- View analysis results and compliance report
- Download report in multiple formats (JSON, Markdown, PDF)
- Re-run analysis on same spec with different options

**Cannot:**
- Modify guideline definitions
- Override compliance findings
- Access other users' analysis results
- Query raw audit data directly

**Sends:**
- `AnalysisRequest` - OpenAPI spec + options
- `ReportRequest` - request formatted output

**Receives:**
- `AnalysisStarted` - task ID for tracking
- `AnalysisProgress` - phase updates during processing
- `AnalysisComplete` - findings summary with report link
- `AnalysisError` - failure with explanation

---

### Actor: Auditor

**Can:**
- Query decision audit trail for any analysis
- Filter decisions by confidence threshold
- View reasoning chain for any finding
- Compare findings across analysis runs
- Export audit data for compliance reporting
- Query aggregate patterns across analyses

**Cannot:**
- Modify historical decisions
- Delete audit records
- Trigger new analyses (uses User role for that)
- Access analysis results without audit justification

**Sends:**
- `AuditQuery` - criteria for decision lookup
- `TraceRequest` - request full execution trace
- `ComparisonRequest` - compare two analysis runs

**Receives:**
- `DecisionRecords` - matching audit entries with reasoning
- `ExecutionTrace` - complete state/decision/tool trace
- `ComparisonReport` - delta between runs

---

### Actor: System (Internal)

**Can:**
- Parse OpenAPI specifications
- Retrieve guideline rules from ruleset
- Execute analysis agents
- Record all state transitions
- Log all decisions with reasoning
- Generate compliance reports

**Cannot:**
- Skip decision logging (hard requirement)
- Transition without recording (observability is mandatory)
- Produce finding without evidence citation
- Delete or modify historical records

**Sends:**
- `StateTransition` - to observability
- `DecisionRecord` - to audit log
- `ToolInvocation` - to execution trace

**Receives:**
- `AnalysisTask` - from task queue
- `GuidelineRules` - from ruleset store

---

## Entities & States

### Entity: AnalysisTask

**Purpose:** Represents a single API governance review request.

**Key attributes:**
- `task_id`: UUID - unique identifier
- `spec_source`: string - URL, file path, or "inline"
- `spec_content`: text - raw OpenAPI spec
- `spec_version`: string - detected OpenAPI version (2.0, 3.0, 3.1)
- `ruleset_version`: string - FDA guidelines version used
- `options`: JSON - analysis configuration
- `created_at`: timestamp
- `completed_at`: timestamp (nullable)

**Has state machine:** Yes

**States:**
- `PENDING`: Task created, awaiting processing
- `PARSING`: Extracting and validating OpenAPI spec
- `ANALYZING`: Running guideline checks
- `EVALUATING`: Assessing severity and confidence
- `REPORTING`: Generating output report
- `COMPLETED`: Analysis finished successfully
- `FAILED`: Analysis terminated with error

**State Diagram:**
```
[PENDING] → [PARSING] → [ANALYZING] → [EVALUATING] → [REPORTING] → [COMPLETED]
              ↓              ↓              ↓              ↓
           [FAILED]      [FAILED]      [FAILED]      [FAILED]
```

**Transitions:**

| From | To | Trigger | Actor | Conditions |
|------|----|---------|-------|------------|
| PENDING | PARSING | TASK_CLAIMED | System | Worker available |
| PARSING | ANALYZING | SPEC_VALID | System | OpenAPI parsed successfully |
| PARSING | FAILED | SPEC_INVALID | System | Parse error or unsupported format |
| ANALYZING | EVALUATING | CHECKS_COMPLETE | System | All guideline checks executed |
| ANALYZING | FAILED | CHECK_ERROR | System | Unrecoverable analysis error |
| EVALUATING | REPORTING | EVALUATION_COMPLETE | System | All findings scored |
| EVALUATING | FAILED | EVALUATION_ERROR | System | Scoring failure |
| REPORTING | COMPLETED | REPORT_GENERATED | System | Output files created |
| REPORTING | FAILED | REPORT_ERROR | System | Report generation failure |

**Terminal states:** COMPLETED, FAILED

---

### Entity: AnalysisAgent

**Purpose:** Represents an agent executing a specific analysis phase.

**Key attributes:**
- `agent_id`: UUID - unique per execution
- `agent_type`: enum - SPEC_PARSER, GUIDELINE_CHECKER, SEVERITY_ASSESSOR, REPORT_GENERATOR
- `task_id`: UUID - parent analysis task
- `started_at`: timestamp
- `completed_at`: timestamp (nullable)

**Has state machine:** Yes

**States:**
- `INITIALIZING`: Agent created, loading context
- `GATHERING`: Collecting input data (spec sections, guidelines)
- `REASONING`: Applying rules, making assessments
- `DECIDING`: Selecting options, assigning values
- `PRODUCING`: Generating output artifacts
- `COMPLETE`: Agent finished successfully
- `ERROR`: Agent terminated with error

**State Diagram:**
```
[INITIALIZING] → [GATHERING] → [REASONING] → [DECIDING] → [PRODUCING] → [COMPLETE]
       ↓              ↓             ↓             ↓             ↓
    [ERROR]       [ERROR]       [ERROR]       [ERROR]       [ERROR]
```

**Transitions:**

| From | To | Trigger | Actor | Conditions |
|------|----|---------|-------|------------|
| INITIALIZING | GATHERING | CONTEXT_LOADED | System | Dependencies available |
| INITIALIZING | ERROR | INIT_FAILED | System | Missing dependencies |
| GATHERING | REASONING | DATA_COLLECTED | System | Required inputs present |
| GATHERING | ERROR | GATHER_FAILED | System | Data unavailable |
| REASONING | DECIDING | ANALYSIS_COMPLETE | System | Rules applied |
| REASONING | ERROR | REASONING_FAILED | System | Analysis error |
| DECIDING | PRODUCING | DECISIONS_MADE | System | All decisions logged |
| DECIDING | ERROR | DECISION_FAILED | System | Unable to decide |
| PRODUCING | COMPLETE | OUTPUT_READY | System | Artifacts generated |
| PRODUCING | ERROR | OUTPUT_FAILED | System | Generation error |

**Terminal states:** COMPLETE, ERROR

---

### Entity: Finding

**Purpose:** A single compliance assessment for one guideline check.

**Key attributes:**
- `finding_id`: UUID
- `task_id`: UUID - parent analysis
- `guideline_id`: string - e.g., "R06", "R11", "BILAG1-3.2"
- `guideline_version`: string - ruleset version
- `status`: enum - COMPLIANT, VIOLATION, NOT_APPLICABLE, UNABLE_TO_DETERMINE
- `severity`: enum (nullable) - CRITICAL, MAJOR, MINOR, INFO
- `confidence`: float - 0.0 to 1.0
- `evidence`: JSON - spec locations supporting finding
- `reasoning`: text - explanation of assessment
- `recommendation`: text (nullable) - remediation guidance
- `effort_estimate`: enum (nullable) - LOW, MEDIUM, HIGH

**Has state machine:** No (immutable once created)

---

### Entity: Decision

**Purpose:** Audit record of a choice made during analysis.

**Key attributes:**
- `decision_id`: UUID
- `task_id`: UUID - parent analysis
- `agent_id`: UUID - agent that made decision
- `decision_point`: string - identifier for type of decision
- `selected_option`: string - what was chosen
- `selected_reasoning`: text - why this option
- `alternatives`: JSON array - other options considered with rejection reasons
- `confidence`: float - 0.0 to 1.0
- `context`: JSON - input data at decision time
- `created_at`: timestamp

**Has state machine:** No (immutable audit record)

---

### Entity: Ruleset

**Purpose:** Versioned collection of FDA guideline rules.

**Key attributes:**
- `ruleset_id`: string - e.g., "FDA-2023-1.0"
- `version`: string - semantic version
- `effective_date`: date
- `rules`: JSON array - individual rule definitions
- `checksum`: string - integrity verification

**Has state machine:** No (immutable reference data)

---

## Work Item Types

| Type | Storage | Created By | Processed By | Can Create Children |
|------|---------|------------|--------------|---------------------|
| AnalysisTask | tasks table | User | AnalysisOrchestrator | Yes (agent executions) |
| AgentExecution | agent_executions table | AnalysisOrchestrator | Individual agents | No |

**Hierarchy:**

```
AnalysisTask
  └── creates → AgentExecution (SPEC_PARSER)
                  └── produces → ParsedSpec
  └── creates → AgentExecution (GUIDELINE_CHECKER)
                  └── produces → Finding[]
  └── creates → AgentExecution (SEVERITY_ASSESSOR)
                  └── produces → ScoredFinding[]
  └── creates → AgentExecution (REPORT_GENERATOR)
                  └── produces → Report
```

---

## Invariants

| ID | Rule | Scope | Enforcement |
|----|------|-------|-------------|
| INV-1 | Every state transition MUST be logged with timestamp and trace_id | AnalysisTask, AnalysisAgent | Hard block |
| INV-2 | Every Decision MUST have at least one alternative recorded | Decision | Hard block |
| INV-3 | Every Finding with status=VIOLATION MUST have severity assigned | Finding | Hard block |
| INV-4 | Every Finding MUST have non-empty evidence | Finding | Hard block |
| INV-5 | Every Finding MUST cite specific guideline_id from active ruleset | Finding | Hard block |
| INV-6 | AnalysisTask in COMPLETED state MUST have at least one Finding | AnalysisTask | Hard block |
| INV-7 | Confidence values MUST be in range [0.0, 1.0] | Decision, Finding | Hard block |
| INV-8 | Agent MUST log Decision before transitioning from DECIDING state | AnalysisAgent | Hard block |
| INV-9 | Task cannot transition to COMPLETED if any agent is in ERROR | AnalysisTask | Hard block |
| INV-10 | Audit records (Decision, StateTransition) are append-only, never modified | System | Hard block |
| INV-11 | Ruleset version used MUST be recorded on AnalysisTask at PARSING start | AnalysisTask | Hard block |

---

## Behaviors

### Behavior: Submit Analysis

**Actor:** User

**Input:**
- `spec`: string - OpenAPI spec content OR URL
- `spec_format`: enum - JSON, YAML, URL (optional, auto-detect)
- `options`: object (optional)
  - `include_info_findings`: boolean - include INFO severity (default: true)
  - `output_formats`: array - requested report formats (default: ["json"])

**Preconditions:**
- Spec is non-empty
- If URL, must be reachable

**State changes:**
- Creates: AnalysisTask in PENDING state
- Emits: TaskCreated event

**Output:**
- Success: `{ task_id, status: "PENDING", poll_url }`
- INVALID_SPEC_FORMAT: 400 - Cannot detect or parse format
- SPEC_TOO_LARGE: 413 - Exceeds size limit (1MB)
- URL_UNREACHABLE: 400 - Cannot fetch from URL

**Side effects:**
- Log: `analysis_submitted` with task_id, spec_size, source_type
- Metric: `analysis_requests_total` counter incremented

---

### Behavior: Execute Analysis

**Actor:** System (triggered by worker)

**Input:**
- `task_id`: UUID - task to process

**Preconditions:**
- Task exists and is in PENDING state
- Worker has claimed lease on task

**State changes:**
- AnalysisTask: PENDING → PARSING → ANALYZING → EVALUATING → REPORTING → COMPLETED
- Creates: AgentExecution records for each phase
- Creates: Decision records for each choice made
- Creates: Finding records for each guideline checked
- Creates: StateTransition records for each state change

**Output:**
- Success: Task in COMPLETED state with findings
- PARSE_ERROR: Task in FAILED state, error recorded
- ANALYSIS_ERROR: Task in FAILED state, partial results preserved

**Side effects:**
- Log: State transitions, decisions, tool invocations
- Metric: `analysis_duration_seconds` histogram
- Metric: `findings_total` counter by severity
- Trace: Full OpenTelemetry trace with spans per agent/state

---

### Behavior: Get Analysis Results

**Actor:** User

**Input:**
- `task_id`: UUID

**Preconditions:**
- Task exists
- Task belongs to requesting user (if auth enabled)

**State changes:**
- None (read-only)

**Output:**
- Success (COMPLETED): Full findings report
- Success (PENDING/PARSING/ANALYZING/EVALUATING/REPORTING): Progress status
- Success (FAILED): Error details with partial results if available
- NOT_FOUND: 404 - Task does not exist

**Side effects:**
- Log: `analysis_results_viewed` with task_id

---

### Behavior: Query Decisions

**Actor:** Auditor

**Input:**
- `task_id`: UUID (optional) - filter to specific analysis
- `confidence_lt`: float (optional) - findings below threshold
- `confidence_gt`: float (optional) - findings above threshold
- `decision_point`: string (optional) - specific decision type
- `limit`: int (default: 100, max: 1000)
- `offset`: int (default: 0)

**Preconditions:**
- At least one filter provided OR task_id specified

**State changes:**
- None (read-only)

**Output:**
- Success: Array of Decision records with pagination metadata
- INVALID_QUERY: 400 - Invalid filter combination
- TOO_BROAD: 400 - Query would return too many results without filters

**Side effects:**
- Log: `audit_query_executed` with query parameters and result count

---

### Behavior: Get Execution Trace

**Actor:** Auditor

**Input:**
- `task_id`: UUID
- `include_tool_invocations`: boolean (default: true)
- `include_decisions`: boolean (default: true)
- `include_state_transitions`: boolean (default: true)

**Preconditions:**
- Task exists

**State changes:**
- None (read-only)

**Output:**
- Success: Complete execution trace with:
  - All state transitions with timestamps and durations
  - All decisions with alternatives and reasoning
  - All tool invocations with inputs/outputs
  - Hierarchical structure by agent
- NOT_FOUND: 404 - Task does not exist

**Side effects:**
- Log: `execution_trace_retrieved` with task_id, requesting_user

---

### Behavior: Check Guideline Compliance

**Actor:** System (internal to GUIDELINE_CHECKER agent)

**Input:**
- `parsed_spec`: ParsedSpec - structured OpenAPI data
- `rule`: GuidelineRule - single rule to check

**Preconditions:**
- Spec is valid and parsed
- Rule is from active ruleset

**State changes:**
- Creates: Finding record
- Creates: Decision record for compliance assessment
- Creates: Decision record for severity assignment (if violation)

**Output:**
- Finding with status, evidence, reasoning

**Side effects:**
- Log: `guideline_checked` with rule_id, status, confidence
- Metric: `guideline_checks_total` counter by rule_id, status

**Decision Points:**

| Decision Point | Options | Selection Criteria |
|----------------|---------|-------------------|
| compliance_status | COMPLIANT, VIOLATION, NOT_APPLICABLE, UNABLE_TO_DETERMINE | Evidence presence and rule applicability |
| severity_level | CRITICAL, MAJOR, MINOR, INFO | Rule priority + context |
| confidence_score | 0.0-1.0 | Evidence strength, ambiguity level |

---

## API Contract

### API Structure

| API | Actors | Base Path | Auth |
|-----|--------|-----------|------|
| Analysis API | User | /api/v1/analysis | API key (existing) |
| Governance API | Auditor | /api/v1/governance | API key + AUDITOR role |

### Analysis API Endpoints

```yaml
POST /api/v1/analysis
  summary: Submit OpenAPI spec for analysis
  request_body:
    spec: string (required)
    spec_format: enum [json, yaml, url] (optional)
    options: object (optional)
  responses:
    201: { task_id, status, poll_url }
    400: { error: INVALID_SPEC_FORMAT | SPEC_TOO_LARGE }

GET /api/v1/analysis/{task_id}
  summary: Get analysis status and results
  responses:
    200: { task_id, status, progress?, findings?, report_url? }
    404: { error: NOT_FOUND }

GET /api/v1/analysis/{task_id}/report
  summary: Download formatted report
  query_params:
    format: enum [json, markdown, pdf] (default: json)
  responses:
    200: Report content (varies by format)
    404: { error: NOT_FOUND }
    409: { error: ANALYSIS_NOT_COMPLETE }
```

### Governance API Endpoints

```yaml
GET /api/v1/governance/tasks/{task_id}/trace
  summary: Get complete execution trace
  query_params:
    include_decisions: boolean (default: true)
    include_tools: boolean (default: true)
    include_states: boolean (default: true)
  responses:
    200: ExecutionTrace
    404: { error: NOT_FOUND }

GET /api/v1/governance/tasks/{task_id}/decisions
  summary: Get decisions for specific task
  query_params:
    confidence_lt: float (optional)
    decision_point: string (optional)
  responses:
    200: { decisions: Decision[], total, offset, limit }
    404: { error: NOT_FOUND }

GET /api/v1/governance/decisions
  summary: Query decisions across all tasks
  query_params:
    confidence_lt: float (optional)
    confidence_gt: float (optional)
    decision_point: string (optional)
    from_date: datetime (optional)
    to_date: datetime (optional)
    limit: int (default: 100)
    offset: int (default: 0)
  responses:
    200: { decisions: Decision[], total, offset, limit }
    400: { error: INVALID_QUERY | TOO_BROAD }

GET /api/v1/governance/findings
  summary: Query findings across all tasks
  query_params:
    status: enum [COMPLIANT, VIOLATION, NOT_APPLICABLE, UNABLE_TO_DETERMINE]
    severity: enum [CRITICAL, MAJOR, MINOR, INFO]
    guideline_id: string (optional)
    confidence_lt: float (optional)
    limit: int (default: 100)
  responses:
    200: { findings: Finding[], total, offset, limit }

POST /api/v1/governance/reviews
  summary: Record auditor review of findings
  request_body:
    task_id: UUID
    findings_reviewed: UUID[]
    review_outcome: enum [ACCEPTED, DISPUTED, REQUIRES_CLARIFICATION]
    notes: string (optional)
  responses:
    201: { review_id }
    404: { error: TASK_NOT_FOUND }
```

### Seed Data

| User | Role(s) | API Key | Purpose |
|------|---------|---------|---------|
| demo_user | USER | demo-user-key | Testing analysis submission |
| demo_auditor | AUDITOR | demo-auditor-key | Testing governance queries |
| test_user | USER | test-key-user | Automated tests |
| test_auditor | AUDITOR | test-key-auditor | Automated tests |

---

## Non-Functional Requirements

### NFR1: Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis latency (≤50 endpoints) | < 30 seconds | p95 |
| Analysis latency (≤100 endpoints) | < 60 seconds | p95 |
| Governance query latency | < 500ms | p95 |
| Report generation | < 5 seconds | p95 |

### NFR2: Accuracy

| Metric | Target | Measurement |
|--------|--------|-------------|
| Precision on documentation rules (R06-R10) | > 95% | vs expert review |
| Precision on versioning rules (R11-R12) | > 98% | vs expert review |
| False positive rate | < 5% | on compliant specs |
| Low-confidence finding rate | < 20% | findings with confidence < 0.7 |

### NFR3: Reliability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis completion rate | > 99% | successful / total |
| Audit log completeness | 100% | no missing state transitions or decisions |
| Data retention | 90 days | audit records |

### NFR4: Scalability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Concurrent analyses | 10 | simultaneous tasks |
| Specs per day | 100 | sustained |
| Audit query performance | O(log n) | indexed queries |

---

## Observability

### Log Events

| Event | Level | When | Fields |
|-------|-------|------|--------|
| `analysis_submitted` | INFO | Task created | task_id, spec_size, source_type |
| `analysis_started` | INFO | Worker claims task | task_id, worker_id |
| `state_transition` | INFO | Any state change | task_id, agent_id?, from_state, to_state, event, duration_ms |
| `decision_made` | INFO | Decision logged | task_id, agent_id, decision_point, selected_option, confidence |
| `guideline_checked` | INFO | Single rule evaluated | task_id, guideline_id, status, severity?, confidence |
| `tool_invoked` | DEBUG | External tool called | task_id, agent_id, tool_name, duration_ms, success |
| `analysis_completed` | INFO | Task reaches terminal | task_id, final_status, duration_ms, finding_count |
| `analysis_failed` | ERROR | Task fails | task_id, error_type, error_message, phase |
| `audit_query_executed` | INFO | Governance query | query_type, filters, result_count, user_id |
| `low_confidence_decision` | WARN | confidence < 0.7 | task_id, decision_point, confidence, reasoning |

### Metrics

```python
# Counters
analysis_requests_total = Counter(
    "fda_analysis_requests_total",
    "Total analysis requests",
    ["source_type"]  # url, file, inline
)

guideline_checks_total = Counter(
    "fda_guideline_checks_total",
    "Guideline checks performed",
    ["guideline_id", "status"]  # R06, COMPLIANT
)

findings_total = Counter(
    "fda_findings_total",
    "Findings generated",
    ["severity", "status"]
)

state_transitions_total = Counter(
    "fda_state_transitions_total",
    "State transitions",
    ["entity_type", "from_state", "to_state"]
)

# Histograms
analysis_duration_seconds = Histogram(
    "fda_analysis_duration_seconds",
    "Analysis duration",
    ["final_status"],
    buckets=[5, 10, 30, 60, 120, 300]
)

agent_phase_duration_seconds = Histogram(
    "fda_agent_phase_duration_seconds",
    "Time spent in each agent phase",
    ["agent_type", "state"]
)

decision_confidence = Histogram(
    "fda_decision_confidence",
    "Decision confidence distribution",
    ["decision_point"],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# Gauges
active_analyses = Gauge(
    "fda_active_analyses",
    "Currently running analyses"
)
```

### Traces

```python
# Trace structure
with tracer.start_as_current_span("analysis_task", attributes={"task_id": task_id}) as task_span:

    with tracer.start_as_current_span("agent_spec_parser") as parser_span:
        with tracer.start_as_current_span("state_gathering"):
            # ...
        with tracer.start_as_current_span("state_producing"):
            # ...

    with tracer.start_as_current_span("agent_guideline_checker") as checker_span:
        for rule in rules:
            with tracer.start_as_current_span(f"check_{rule.id}") as check_span:
                check_span.set_attribute("guideline_id", rule.id)
                check_span.set_attribute("status", finding.status)
                check_span.set_attribute("confidence", finding.confidence)
```

---

## Test Cases

### Authorization Tests (from Actor.Cannot)

```python
def test_user_cannot_access_governance_endpoints()
def test_user_cannot_modify_guideline_definitions()
def test_user_cannot_access_other_users_analysis()
def test_auditor_cannot_modify_historical_decisions()
def test_auditor_cannot_delete_audit_records()
```

### State Transition Tests (from Transitions table)

```python
# AnalysisTask transitions
def test_task_pending_to_parsing_on_claim()
def test_task_parsing_to_analyzing_on_valid_spec()
def test_task_parsing_to_failed_on_invalid_spec()
def test_task_analyzing_to_evaluating_on_checks_complete()
def test_task_evaluating_to_reporting_on_evaluation_complete()
def test_task_reporting_to_completed_on_report_generated()

# AnalysisAgent transitions
def test_agent_initializing_to_gathering_on_context_loaded()
def test_agent_gathering_to_reasoning_on_data_collected()
def test_agent_reasoning_to_deciding_on_analysis_complete()
def test_agent_deciding_to_producing_on_decisions_made()
def test_agent_producing_to_complete_on_output_ready()
def test_agent_any_to_error_on_failure()
```

### Invalid Transition Tests (NOT in Transitions table)

```python
def test_task_cannot_pending_to_completed()
def test_task_cannot_completed_to_analyzing()
def test_task_cannot_failed_to_completed()
def test_agent_cannot_complete_to_gathering()
def test_agent_cannot_skip_deciding_state()
```

### Invariant Tests

```python
def test_inv1_state_transition_always_logged()
def test_inv2_decision_has_at_least_one_alternative()
def test_inv3_violation_has_severity()
def test_inv4_finding_has_evidence()
def test_inv5_finding_cites_valid_guideline()
def test_inv6_completed_task_has_findings()
def test_inv7_confidence_in_valid_range()
def test_inv8_decision_logged_before_state_change()
def test_inv9_task_not_completed_if_agent_error()
def test_inv10_audit_records_immutable()
def test_inv11_ruleset_version_recorded_at_parsing()
```

### Behavior Tests

```python
# Submit Analysis
def test_submit_analysis_success()
def test_submit_analysis_invalid_spec_format()
def test_submit_analysis_spec_too_large()
def test_submit_analysis_url_unreachable()

# Execute Analysis
def test_execute_analysis_success_all_compliant()
def test_execute_analysis_success_with_violations()
def test_execute_analysis_parse_error()
def test_execute_analysis_partial_failure_preserves_results()

# Get Analysis Results
def test_get_results_completed()
def test_get_results_in_progress()
def test_get_results_failed()
def test_get_results_not_found()

# Query Decisions
def test_query_decisions_by_task()
def test_query_decisions_by_confidence()
def test_query_decisions_pagination()
def test_query_decisions_too_broad_rejected()

# Check Guideline Compliance
def test_check_guideline_compliant()
def test_check_guideline_violation()
def test_check_guideline_not_applicable()
def test_check_guideline_unable_to_determine()
```

### Decision Audit Tests

```python
def test_decision_records_all_alternatives()
def test_decision_includes_context()
def test_decision_reasoning_non_empty()
def test_decision_confidence_justified()
def test_multiple_decisions_per_finding_logged()
```

### Integration Tests

```python
def test_end_to_end_compliant_spec()
def test_end_to_end_spec_with_violations()
def test_end_to_end_governance_query_after_analysis()
def test_trace_reconstruction_matches_execution()
def test_findings_queryable_by_severity()
def test_low_confidence_findings_flagged()
```

### Structural Tests

```python
def test_all_agent_states_have_handlers()
def test_all_task_states_have_handlers()
def test_state_machine_dispatch_complexity_under_budget()
def test_all_decision_points_documented()
def test_all_guidelines_have_check_implementation()
```

---

## Implementation Phases

### Phase 1: Core State Machines (Est: 3 days)

**Creates:**
- `app/analysis_state.py` - AnalysisTaskState, AnalysisTaskEvent, transitions
- `app/agent_state.py` - AgentState, AgentEvent, transitions
- `app/state_base.py` - StateMachine base class with logging
- `tests/test_analysis_state.py`
- `tests/test_agent_state.py`

**Implements:**
- AnalysisTask state machine with handler dispatch
- AnalysisAgent state machine with handler dispatch
- State transition logging (INV-1)
- OpenTelemetry span creation per transition

**Tests:**
- All state transition tests
- All invalid transition tests
- Structural tests for handlers

**Verification Gate:**
```bash
pytest tests/test_analysis_state.py tests/test_agent_state.py -v
ruff check app/*_state.py
mypy app/*_state.py
radon cc app/*_state.py -s  # complexity < 5 for run methods
```

**Exit criteria:**
- [ ] All state transition tests pass
- [ ] State transitions emit OpenTelemetry spans
- [ ] Complexity under budget

---

### Phase 2: Decision Audit Infrastructure (Est: 3 days)

**Creates:**
- `app/models/decision.py` - Decision model
- `app/models/finding.py` - Finding model
- `app/services/decision_logger.py` - Decision logging service
- `migrations/xxx_create_decisions_table.py`
- `migrations/xxx_create_findings_table.py`
- `tests/test_decision_logger.py`

**Implements:**
- Decision model with alternatives (INV-2)
- Finding model with evidence (INV-4)
- log_decision() function enforcing INV-8
- Immutable audit records (INV-10)

**Tests:**
- Invariant tests INV-2, INV-4, INV-8, INV-10
- Decision logging tests

**Verification Gate:**
```bash
pytest tests/test_decision_logger.py -v
alembic upgrade head  # migrations apply cleanly
```

**Exit criteria:**
- [ ] Decisions persist with alternatives
- [ ] Findings persist with evidence
- [ ] Audit records cannot be modified (test)

---

### Phase 3: Guideline Checker Agent (Est: 4 days)

**Creates:**
- `app/agents/guideline_checker.py` - GuidelineCheckerAgent
- `app/rulesets/fda_guidelines.py` - Parsed FDA rules
- `app/services/openapi_parser.py` - Spec parsing utilities
- `tests/test_guideline_checker.py`
- `tests/fixtures/sample_specs/` - Test OpenAPI specs

**Implements:**
- GuidelineCheckerAgent with state machine
- FDA guideline rules (R06, R11, R24, R29, R34, R37 as initial set)
- Decision logging for compliance_status, severity_level, confidence_score
- Evidence extraction from spec

**Tests:**
- Behavior tests for Check Guideline Compliance
- Tests with known-compliant spec
- Tests with known-violation spec

**Verification Gate:**
```bash
pytest tests/test_guideline_checker.py -v
# Verify decisions logged
pytest -k "decision" --tb=short
```

**Exit criteria:**
- [ ] 6+ guidelines implemented with checks
- [ ] Each check logs decision with alternatives
- [ ] Evidence points to spec locations

---

### Phase 4: Analysis Orchestration (Est: 3 days)

**Creates:**
- `app/workflows/api_analysis.py` - Analysis workflow definition
- `app/agents/spec_parser.py` - Spec parsing agent
- `app/agents/report_generator.py` - Report generation agent
- `tests/test_api_analysis_workflow.py`

**Implements:**
- Full analysis workflow (PARSING → ANALYZING → EVALUATING → REPORTING)
- AnalysisTask state machine integration
- Ruleset version recording (INV-11)
- Report generation in JSON format

**Tests:**
- End-to-end integration tests
- Failure handling tests (parse error, analysis error)

**Verification Gate:**
```bash
pytest tests/test_api_analysis_workflow.py -v
# End-to-end with sample spec
python -c "from app.workflows.api_analysis import run_analysis; ..."
```

**Exit criteria:**
- [ ] Full workflow executes on sample spec
- [ ] All state transitions logged
- [ ] JSON report generated

---

### Phase 5: Governance API (Est: 3 days)

**Creates:**
- `app/api/governance.py` - Governance endpoints
- `app/services/audit_query.py` - Audit query service
- `tests/test_governance_api.py`

**Implements:**
- GET /governance/tasks/{id}/trace
- GET /governance/tasks/{id}/decisions
- GET /governance/decisions (with filters)
- GET /governance/findings (with filters)

**Tests:**
- All Query Decisions behavior tests
- Authorization tests (auditor role required)
- Pagination tests

**Verification Gate:**
```bash
pytest tests/test_governance_api.py -v
# Manual: query decisions for completed analysis
curl -H "X-API-Key: demo-auditor-key" localhost:8000/api/v1/governance/tasks/{id}/decisions
```

**Exit criteria:**
- [ ] All governance endpoints functional
- [ ] Auditor role enforced
- [ ] Trace reconstruction works

---

### Phase 6: Extended Guidelines & Reporting (Est: 4 days)

**Creates:**
- Additional guideline implementations (R07, R08, R09, R10, R12, etc.)
- `app/services/report_formatter.py` - Multi-format reports
- `tests/test_report_formats.py`

**Implements:**
- Remaining high-priority guidelines (target: 20 rules)
- Markdown report format
- PDF report format (optional)
- Compliance score calculation

**Tests:**
- Tests for each new guideline
- Report format tests

**Verification Gate:**
```bash
pytest tests/test_guideline_checker.py tests/test_report_formats.py -v
# Coverage check
pytest --cov=app/rulesets --cov-report=term-missing
```

**Exit criteria:**
- [ ] 20+ guidelines implemented
- [ ] Markdown reports generated
- [ ] Compliance score calculated

---

## Verification Checklist

- [ ] All tests pass (target: 100+ tests)
- [ ] Static analysis clean (ruff, mypy)
- [ ] Complexity under budget (radon cc < 10)
- [ ] Every Actor.Cannot has authorization test
- [ ] Every state Transition has test
- [ ] Every Invariant has test
- [ ] Every Decision logs alternatives
- [ ] Traces visible in observability stack
- [ ] Governance API returns complete audit trail
- [ ] Sample spec analysis produces valid report

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial requirements specification |
