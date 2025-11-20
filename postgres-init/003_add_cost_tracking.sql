-- Add cost tracking columns to tasks table
-- This migration adds OpenRouter API usage tracking

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id_hash VARCHAR(64);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS model_used VARCHAR(100);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS input_tokens INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS output_tokens INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS total_cost DECIMAL(10,6) DEFAULT 0;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS generation_id VARCHAR(100);

-- Add indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_tasks_user_hash ON tasks(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_tasks_cost ON tasks(total_cost) WHERE total_cost > 0;
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'tasks' 
ORDER BY ordinal_position;
