-- Add tenant tracking support
-- This migration adds tenant_id to all core tables for multi-tenancy

-- Add tenant_id to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);

-- Add tenant_id to subtasks table
ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);

-- Add tenant_id to workflow_state table
ALTER TABLE workflow_state ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);

-- Add tenant_id to audit_logs table
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);

-- Create indexes for efficient tenant-based queries
CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subtasks_tenant ON subtasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_state_tenant ON workflow_state(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);

-- Composite indexes for common query patterns (user + tenant)
CREATE INDEX IF NOT EXISTS idx_tasks_user_tenant ON tasks(user_id_hash, tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_tenant ON audit_logs(user_id_hash, tenant_id);

-- Comments
COMMENT ON COLUMN tasks.tenant_id IS 'Tenant identifier for multi-tenant isolation';
COMMENT ON COLUMN subtasks.tenant_id IS 'Tenant identifier inherited from parent task';
COMMENT ON COLUMN workflow_state.tenant_id IS 'Tenant identifier for workflow';
COMMENT ON COLUMN audit_logs.tenant_id IS 'Tenant identifier for audit event';

-- Verify the changes
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE column_name = 'tenant_id'
  AND table_schema = 'public'
ORDER BY table_name;
