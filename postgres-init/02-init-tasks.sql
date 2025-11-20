-- Enable pgcrypto so we can use gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Core tasks table for the LLM task runner
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending|running|done|error
  input JSONB NOT NULL,
  output JSONB,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Optional: dynamic task types storage
CREATE TABLE IF NOT EXISTS task_types (
  name TEXT PRIMARY KEY,
  system_prompt TEXT NOT NULL,
  enabled BOOLEAN DEFAULT TRUE
);
