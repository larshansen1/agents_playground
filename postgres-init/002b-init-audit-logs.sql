-- Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(36),
    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id_hash);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_id);
