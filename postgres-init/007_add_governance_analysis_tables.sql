-- Add generic governance analysis tables for API compliance checking
-- Supports multiple frameworks: FDA, FHIR, GraphQL, custom standards

-- Table: compliance_findings
-- Stores compliance findings for any governance framework
CREATE TABLE IF NOT EXISTS compliance_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    ruleset_id VARCHAR(100) NOT NULL,
    rule_id VARCHAR(100) NOT NULL,
    check_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('COMPLIANT', 'VIOLATION', 'NOT_APPLICABLE', 'UNABLE_TO_DETERMINE')),
    severity VARCHAR(20) CHECK (severity IN ('CRITICAL', 'MAJOR', 'MINOR', 'INFO')),
    confidence DECIMAL(3, 2) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    evidence JSONB NOT NULL,
    reasoning TEXT NOT NULL,
    recommendation TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_findings_task ON compliance_findings(task_id);
CREATE INDEX idx_findings_status ON compliance_findings(status);
CREATE INDEX idx_findings_severity ON compliance_findings(severity);
CREATE INDEX idx_findings_ruleset ON compliance_findings(ruleset_id);
CREATE INDEX idx_findings_rule ON compliance_findings(rule_id);

COMMENT ON TABLE compliance_findings IS 'Generic compliance findings for any governance framework (FDA, FHIR, GraphQL, etc.)';
COMMENT ON COLUMN compliance_findings.ruleset_id IS 'Ruleset identifier, e.g., FDA-DK-2024-1.0, FHIR-R4-2023';
COMMENT ON COLUMN compliance_findings.metadata IS 'Framework-specific extras like effort_estimate for FDA';

-- Table: governance_decisions
-- Immutable audit trail of all agent decisions
CREATE TABLE IF NOT EXISTS governance_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL,
    decision_point VARCHAR(200) NOT NULL,
    selected_option VARCHAR(500) NOT NULL,
    selected_reasoning TEXT NOT NULL,
    alternatives JSONB NOT NULL,
    confidence DECIMAL(3, 2) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_decisions_task ON governance_decisions(task_id);
CREATE INDEX idx_decisions_agent ON governance_decisions(agent_type);
CREATE INDEX idx_decisions_confidence ON governance_decisions(confidence);
CREATE INDEX idx_decisions_created ON governance_decisions(created_at);

COMMENT ON TABLE governance_decisions IS 'Immutable audit trail of agent decisions during governance analysis';
COMMENT ON COLUMN governance_decisions.alternatives IS 'JSONB array of {option, reason_rejected} for alternatives considered';

-- Table: governance_rulesets
-- Versioned governance rulesets for any framework
CREATE TABLE IF NOT EXISTS governance_rulesets (
    ruleset_id VARCHAR(100) PRIMARY KEY,
    framework VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    effective_date DATE NOT NULL,
    rules JSONB NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rulesets_framework ON governance_rulesets(framework);
CREATE INDEX idx_rulesets_version ON governance_rulesets(version);

COMMENT ON TABLE governance_rulesets IS 'Versioned governance rulesets for multiple frameworks (FDA, FHIR, GraphQL, custom)';
COMMENT ON COLUMN governance_rulesets.rules IS 'Complete ruleset definition as JSONB';
COMMENT ON COLUMN governance_rulesets.checksum IS 'SHA-256 checksum for integrity verification';

-- Verify the changes
SELECT
    'compliance_findings' AS table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'compliance_findings'
UNION ALL
SELECT
    'governance_decisions' AS table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'governance_decisions'
UNION ALL
SELECT
    'governance_rulesets' AS table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_name = 'governance_rulesets';
