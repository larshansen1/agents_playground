-- Migration: Add lease-based task acquisition columns
-- This allows multiple workers to safely claim tasks with automatic recovery from failures

-- Add lease columns to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS locked_by VARCHAR(100);  -- worker_id (hostname:pid)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS lease_timeout TIMESTAMP WITH TIME ZONE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS try_count INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS max_tries INTEGER DEFAULT 3;

-- Add lease columns to subtasks table
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS locked_by VARCHAR(100);
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS lease_timeout TIMESTAMP WITH TIME ZONE;
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS try_count INTEGER DEFAULT 0;
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS max_tries INTEGER DEFAULT 3;

-- Add partial indexes for fast pending task lookup
-- These indexes only include rows that need processing (pending status)
-- Note: Can't use NOW() in partial index predicate (must be immutable function)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_pending_lease
  ON tasks(created_at)
  WHERE status = 'pending';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subtasks_pending_lease
  ON subtasks(created_at)
  WHERE status = 'pending';

-- Add indexes for lease recovery (finding expired leases)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_expired_leases
  ON tasks(lease_timeout)
  WHERE status = 'running' AND lease_timeout IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subtasks_expired_leases
  ON subtasks(lease_timeout)
  WHERE status = 'running' AND lease_timeout IS NOT NULL;

-- Add index for monitoring which workers are processing tasks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_locked_by
  ON tasks(locked_by)
  WHERE locked_by IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subtasks_locked_by
  ON subtasks(locked_by)
  WHERE locked_by IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN tasks.locked_at IS 'Timestamp when task was claimed by a worker';
COMMENT ON COLUMN tasks.locked_by IS 'Worker ID (hostname:pid) that claimed this task';
COMMENT ON COLUMN tasks.lease_timeout IS 'Timestamp when lease expires; task becomes available if worker fails';
COMMENT ON COLUMN tasks.try_count IS 'Number of times this task has been attempted';
COMMENT ON COLUMN tasks.max_tries IS 'Maximum number of retry attempts before marking as permanently failed';

COMMENT ON COLUMN subtasks.locked_at IS 'Timestamp when subtask was claimed by a worker';
COMMENT ON COLUMN subtasks.locked_by IS 'Worker ID (hostname:pid) that claimed this subtask';
COMMENT ON COLUMN subtasks.lease_timeout IS 'Timestamp when lease expires; subtask becomes available if worker fails';
COMMENT ON COLUMN subtasks.try_count IS 'Number of times this subtask has been attempted';
COMMENT ON COLUMN subtasks.max_tries IS 'Maximum number of retry attempts before marking as permanently failed';
