# Open WebUI Tools Guide

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
