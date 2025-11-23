-- Add multi-agent orchestration support
-- This migration adds tables for subtasks and workflow state tracking

-- Subtasks table to track individual agent executions within a workflow
CREATE TABLE IF NOT EXISTS subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    iteration INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Cost tracking fields (same as tasks table)
    user_id_hash VARCHAR(64),
    model_used VARCHAR(100),
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10,6) DEFAULT 0,
    generation_id VARCHAR(100)
);

-- Indexes for efficient subtask queries
CREATE INDEX IF NOT EXISTS idx_subtasks_parent ON subtasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_status ON subtasks(status);
CREATE INDEX IF NOT EXISTS idx_subtasks_agent_type ON subtasks(agent_type);
CREATE INDEX IF NOT EXISTS idx_subtasks_iteration ON subtasks(parent_task_id, iteration);

-- Workflow state table to manage workflow progression
CREATE TABLE IF NOT EXISTS workflow_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_task_id UUID NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
    workflow_type TEXT NOT NULL,
    current_iteration INTEGER NOT NULL DEFAULT 1,
    max_iterations INTEGER NOT NULL DEFAULT 3,
    current_state TEXT NOT NULL,
    state_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for workflow state queries
CREATE INDEX IF NOT EXISTS idx_workflow_state_parent ON workflow_state(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_state_type ON workflow_state(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflow_state_current_state ON workflow_state(current_state);

-- Comment
COMMENT ON TABLE subtasks IS 'Individual agent executions within multi-agent workflows';
COMMENT ON TABLE workflow_state IS 'State machine tracking for multi-agent workflows';

-- Verify the changes
SELECT
    'subtasks' AS table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'subtasks'
UNION ALL
SELECT
    'workflow_state' AS table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'workflow_state';
