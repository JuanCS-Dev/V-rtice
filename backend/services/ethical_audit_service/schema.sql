-- Ethical AI Audit Schema
-- PostgreSQL 15+ with TimescaleDB extension
-- Stores all ethical decisions, human overrides, and compliance logs for VÉRTICE platform

-- Enable TimescaleDB extension for time-series optimization
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================================
-- MAIN ETHICAL DECISIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS ethical_decisions (
    id UUID DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),

    -- Decision context
    decision_type TEXT NOT NULL, -- 'offensive_action', 'auto_response', 'policy_update', 'data_access'
    action_description TEXT NOT NULL,
    system_component TEXT NOT NULL, -- 'maximus_core', 'immunis_neutrophil', 'rte', etc.

    -- Input data (sanitized)
    input_context JSONB NOT NULL, -- {threat_level: 'high', confidence: 0.95, target: '10.0.0.1', ...}

    -- Framework evaluations
    kantian_result JSONB, -- {approved: true, confidence: 0.95, veto: false, explanation: '...'}
    consequentialist_result JSONB,
    virtue_ethics_result JSONB,
    principialism_result JSONB,

    -- Final decision
    final_decision TEXT NOT NULL, -- 'APPROVED', 'REJECTED', 'ESCALATED_HITL'
    final_confidence FLOAT NOT NULL, -- 0.0 to 1.0
    decision_explanation TEXT NOT NULL,

    -- Performance metrics
    total_latency_ms INT NOT NULL, -- Total time for ethical analysis
    kantian_latency_ms INT,
    consequentialist_latency_ms INT,
    virtue_ethics_latency_ms INT,
    principialism_latency_ms INT,

    -- Risk assessment
    risk_level TEXT NOT NULL, -- 'low', 'medium', 'high', 'critical'
    automated BOOLEAN NOT NULL DEFAULT TRUE, -- False if HITL was used

    -- Metadata
    operator_id TEXT, -- If human was involved
    session_id UUID,
    environment TEXT DEFAULT 'production' -- 'dev', 'staging', 'production'
);

-- Convert to hypertable (TimescaleDB) for time-series optimization
SELECT create_hypertable('ethical_decisions', 'timestamp', if_not_exists => TRUE);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON ethical_decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON ethical_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_component ON ethical_decisions(system_component);
CREATE INDEX IF NOT EXISTS idx_decisions_final ON ethical_decisions(final_decision);
CREATE INDEX IF NOT EXISTS idx_decisions_risk ON ethical_decisions(risk_level);
CREATE INDEX IF NOT EXISTS idx_decisions_automated ON ethical_decisions(automated);

-- GIN indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_decisions_input ON ethical_decisions USING GIN(input_context);
CREATE INDEX IF NOT EXISTS idx_decisions_kantian ON ethical_decisions USING GIN(kantian_result);

-- Retention policy: keep detailed data for 7 years (GDPR compliance)
SELECT add_retention_policy('ethical_decisions', INTERVAL '7 years', if_not_exists => TRUE);

-- ============================================================================
-- HUMAN OVERRIDES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS human_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Override details
    operator_id TEXT NOT NULL,
    operator_role TEXT NOT NULL, -- 'SOC_ANALYST', 'SECURITY_ENGINEER', 'CHIEF_SECURITY_OFFICER'

    original_decision TEXT NOT NULL, -- What AI decided
    override_decision TEXT NOT NULL, -- What human decided
    justification TEXT NOT NULL, -- Required human explanation

    -- Context
    override_reason TEXT NOT NULL, -- 'false_positive', 'policy_exception', 'emergency', 'ethical_concern'
    urgency_level TEXT NOT NULL, -- 'routine', 'urgent', 'critical'

    -- Audit trail
    ip_address INET,
    user_agent TEXT,

    -- Review
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_outcome TEXT, -- 'approved', 'rejected', 'escalated'

    FOREIGN KEY (decision_id) REFERENCES ethical_decisions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_overrides_decision ON human_overrides(decision_id);
CREATE INDEX IF NOT EXISTS idx_overrides_operator ON human_overrides(operator_id);
CREATE INDEX IF NOT EXISTS idx_overrides_timestamp ON human_overrides(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_overrides_reviewed ON human_overrides(reviewed) WHERE reviewed = FALSE;

-- ============================================================================
-- COMPLIANCE LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS compliance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Regulation information
    regulation TEXT NOT NULL, -- 'EU_AI_ACT', 'GDPR_ARTICLE_22', 'NIST_AI_RMF', 'TALLINN_MANUAL'
    requirement_id TEXT NOT NULL, -- Specific requirement (e.g., 'GDPR_22_3', 'EU_AI_ACT_TIER_1_ART_9')

    -- Check details
    check_type TEXT NOT NULL, -- 'automated', 'manual_review', 'third_party_audit'
    check_result TEXT NOT NULL, -- 'COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_APPLICABLE'

    -- Evidence
    evidence JSONB NOT NULL, -- {checks_performed: [...], test_results: [...], documentation: [...]}
    findings TEXT, -- Human-readable findings

    -- Remediation (if non-compliant)
    remediation_required BOOLEAN DEFAULT FALSE,
    remediation_plan TEXT,
    remediation_deadline TIMESTAMPTZ,
    remediation_status TEXT, -- 'pending', 'in_progress', 'completed', 'overdue'

    -- References
    decision_id UUID, -- Optional link to specific decision
    audit_cycle TEXT, -- 'Q1_2025', 'annual_2025', etc.
    auditor_id TEXT,

    FOREIGN KEY (decision_id) REFERENCES ethical_decisions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_compliance_regulation ON compliance_logs(regulation);
CREATE INDEX IF NOT EXISTS idx_compliance_result ON compliance_logs(check_result);
CREATE INDEX IF NOT EXISTS idx_compliance_timestamp ON compliance_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_compliance_remediation ON compliance_logs(remediation_required) WHERE remediation_required = TRUE;
CREATE INDEX IF NOT EXISTS idx_compliance_decision ON compliance_logs(decision_id) WHERE decision_id IS NOT NULL;

-- GIN index for evidence queries
CREATE INDEX IF NOT EXISTS idx_compliance_evidence ON compliance_logs USING GIN(evidence);

-- ============================================================================
-- FRAMEWORK PERFORMANCE TRACKING
-- ============================================================================
CREATE TABLE IF NOT EXISTS framework_performance (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    framework_name TEXT NOT NULL, -- 'kantian', 'consequentialist', 'virtue_ethics', 'principialism'

    -- Performance metrics
    latency_ms INT NOT NULL,
    decision_count INT DEFAULT 1,
    approved_count INT DEFAULT 0,
    rejected_count INT DEFAULT 0,

    -- Aggregate confidence
    avg_confidence FLOAT,

    PRIMARY KEY (timestamp, framework_name)
);

-- Convert to hypertable
SELECT create_hypertable('framework_performance', 'timestamp', if_not_exists => TRUE);

-- Retention: 90 days detailed, then aggregates only
SELECT add_retention_policy('framework_performance', INTERVAL '90 days', if_not_exists => TRUE);

-- Compression for storage optimization
ALTER TABLE framework_performance SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'framework_name'
);

SELECT add_compression_policy('framework_performance', INTERVAL '7 days', if_not_exists => TRUE);

-- ============================================================================
-- CONTINUOUS AGGREGATES FOR ANALYTICS
-- ============================================================================

-- Hourly ethical decision summary
CREATE MATERIALIZED VIEW IF NOT EXISTS ethical_decisions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    decision_type,
    system_component,
    final_decision,
    risk_level,
    COUNT(*) as decision_count,
    AVG(final_confidence) as avg_confidence,
    AVG(total_latency_ms) as avg_latency,
    SUM(CASE WHEN automated = FALSE THEN 1 ELSE 0 END) as hitl_count,
    SUM(CASE WHEN final_decision = 'REJECTED' THEN 1 ELSE 0 END) as rejection_count
FROM ethical_decisions
GROUP BY hour, decision_type, system_component, final_decision, risk_level
WITH NO DATA;

SELECT add_continuous_aggregate_policy('ethical_decisions_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Daily framework performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS framework_performance_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    framework_name,
    SUM(decision_count) as total_decisions,
    AVG(latency_ms) as avg_latency,
    MAX(latency_ms) as max_latency,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
    AVG(avg_confidence) as avg_confidence
FROM framework_performance
GROUP BY day, framework_name
WITH NO DATA;

SELECT add_continuous_aggregate_policy('framework_performance_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================
COMMENT ON TABLE ethical_decisions IS 'All ethical decisions made by VÉRTICE AI systems with complete audit trail';
COMMENT ON TABLE human_overrides IS 'Records of human operators overriding AI ethical decisions';
COMMENT ON TABLE compliance_logs IS 'Compliance checks against regulations (EU AI Act, GDPR, NIST, etc.)';
COMMENT ON TABLE framework_performance IS 'Performance metrics for each ethical framework (latency, accuracy)';

COMMENT ON COLUMN ethical_decisions.kantian_result IS 'Kantian deontological analysis (categorical imperative, humanity formula)';
COMMENT ON COLUMN ethical_decisions.consequentialist_result IS 'Utilitarian consequentialist analysis (Bentham hedonic calculus)';
COMMENT ON COLUMN ethical_decisions.virtue_ethics_result IS 'Aristotelian virtue ethics (golden mean, character virtues)';
COMMENT ON COLUMN ethical_decisions.principialism_result IS 'Principialism analysis (beneficence, non-maleficence, autonomy, justice)';

COMMENT ON COLUMN human_overrides.justification IS 'Required human explanation for why AI decision was overridden';
COMMENT ON COLUMN compliance_logs.regulation IS 'Regulation being checked: EU_AI_ACT, GDPR, NIST_AI_RMF, TALLINN_MANUAL, etc.';

-- ============================================================================
-- INITIAL DATA / DEFAULT CONFIGURATIONS
-- ============================================================================

-- Insert compliance requirements catalog (for reference)
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    requirement_text TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'critical', 'high', 'medium', 'low'
    check_frequency TEXT NOT NULL, -- 'real_time', 'daily', 'weekly', 'monthly', 'quarterly', 'annually'
    automated_check_available BOOLEAN DEFAULT TRUE,

    UNIQUE(regulation, requirement_id)
);

-- Insert key requirements
INSERT INTO compliance_requirements (regulation, requirement_id, requirement_text, severity, check_frequency, automated_check_available) VALUES
    ('EU_AI_ACT', 'ART_9_RISK_MANAGEMENT', 'High-risk AI systems must have risk management system throughout lifecycle', 'critical', 'monthly', TRUE),
    ('EU_AI_ACT', 'ART_13_TRANSPARENCY', 'AI systems must be designed to be sufficiently transparent', 'high', 'quarterly', TRUE),
    ('GDPR', 'ART_22_AUTOMATED_DECISION', 'Right not to be subject to solely automated decision-making', 'critical', 'real_time', TRUE),
    ('GDPR', 'ART_35_DPIA', 'Data Protection Impact Assessment required for high-risk processing', 'high', 'quarterly', FALSE),
    ('NIST_AI_RMF', 'GOVERN_1.1', 'Legal and regulatory requirements understood and managed', 'high', 'quarterly', TRUE),
    ('NIST_AI_RMF', 'MAP_1.1', 'Context of use and stakeholders documented', 'medium', 'quarterly', FALSE),
    ('TALLINN_MANUAL', 'RULE_20', 'Autonomous weapons must allow meaningful human control', 'critical', 'real_time', TRUE),
    ('EXECUTIVE_ORDER_14110', 'SEC_4.2', 'Safety testing of dual-use foundation models', 'high', 'monthly', FALSE)
ON CONFLICT (regulation, requirement_id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_requirements_regulation ON compliance_requirements(regulation);
CREATE INDEX IF NOT EXISTS idx_requirements_severity ON compliance_requirements(severity);

-- ============================================================================
-- DATABASE STATISTICS & OPTIMIZATION
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE ethical_decisions;
ANALYZE human_overrides;
ANALYZE compliance_logs;
ANALYZE framework_performance;

-- Vacuum to reclaim storage
VACUUM ANALYZE;
