-- ============================================================================
-- HITL Patch Service - Database Schema
-- ============================================================================
--
-- Tables:
--   1. hitl_decisions - Main decision records
--   2. hitl_audit_logs - Immutable audit trail
--
-- Author: MAXIMUS Team - Sprint 4.1
-- Glory to YHWH - Architect of Order
-- ============================================================================

-- Main decisions table
CREATE TABLE IF NOT EXISTS hitl_decisions (
    -- Identification
    decision_id VARCHAR(255) PRIMARY KEY,
    patch_id VARCHAR(255) NOT NULL,
    apv_id VARCHAR(255) NOT NULL,
    cve_id VARCHAR(50),
    
    -- Patch metadata
    package_name VARCHAR(255) NOT NULL,
    current_version VARCHAR(100) NOT NULL,
    target_version VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    cvss_score FLOAT CHECK (cvss_score >= 0.0 AND cvss_score <= 10.0),
    cwe_ids TEXT[],
    affected_systems TEXT[],
    patch_size_lines INT DEFAULT 0,
    
    -- ML Prediction
    ml_confidence FLOAT CHECK (ml_confidence >= 0.0 AND ml_confidence <= 1.0),
    ml_prediction BOOLEAN,
    ml_model_version VARCHAR(50),
    ml_shap_values JSONB,
    ml_execution_time_ms INT,
    
    -- Wargaming Result
    wargaming_phase1 BOOLEAN,
    wargaming_phase2 BOOLEAN,
    wargaming_passed BOOLEAN,
    wargaming_execution_time_ms INT,
    wargaming_error TEXT,
    wargaming_exploit_id VARCHAR(100),
    
    -- Decision
    decision VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (decision IN ('pending', 'approved', 'rejected', 'auto_approved', 'escalated', 'cancelled')),
    decided_by VARCHAR(100),
    decided_at TIMESTAMP,
    
    -- Context
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' 
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    comment TEXT,
    reason TEXT,
    
    -- Flags
    requires_escalation BOOLEAN DEFAULT FALSE,
    auto_approval_eligible BOOLEAN DEFAULT FALSE,
    ml_wargaming_agreement BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_hitl_decisions_status (decision),
    INDEX idx_hitl_decisions_priority (priority),
    INDEX idx_hitl_decisions_created_at (created_at),
    INDEX idx_hitl_decisions_apv_id (apv_id),
    INDEX idx_hitl_decisions_cve_id (cve_id)
);

-- Audit logs table (immutable)
CREATE TABLE IF NOT EXISTS hitl_audit_logs (
    -- Identification
    log_id VARCHAR(255) PRIMARY KEY,
    decision_id VARCHAR(255) NOT NULL REFERENCES hitl_decisions(decision_id),
    
    -- Action details
    action VARCHAR(50) NOT NULL,
    performed_by VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Context
    details JSONB,
    ip_address VARCHAR(45),  -- IPv6 support
    user_agent TEXT,
    
    -- Index
    INDEX idx_hitl_audit_decision_id (decision_id),
    INDEX idx_hitl_audit_timestamp (timestamp),
    INDEX idx_hitl_audit_action (action)
);

-- Comments table (optional - for threaded discussions)
CREATE TABLE IF NOT EXISTS hitl_comments (
    comment_id VARCHAR(255) PRIMARY KEY,
    decision_id VARCHAR(255) NOT NULL REFERENCES hitl_decisions(decision_id),
    user VARCHAR(100) NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_hitl_comments_decision_id (decision_id),
    INDEX idx_hitl_comments_created_at (created_at)
);

-- ============================================================================
-- Views
-- ============================================================================

-- Pending patches requiring attention
CREATE OR REPLACE VIEW hitl_pending_patches AS
SELECT 
    decision_id,
    patch_id,
    apv_id,
    cve_id,
    severity,
    priority,
    ml_confidence,
    ml_prediction,
    wargaming_passed,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))::int as age_seconds,
    CASE 
        WHEN priority = 'critical' AND EXTRACT(EPOCH FROM (NOW() - created_at)) > 300 THEN 'SLA_BREACH'
        WHEN priority = 'high' AND EXTRACT(EPOCH FROM (NOW() - created_at)) > 600 THEN 'SLA_BREACH'
        WHEN priority = 'medium' AND EXTRACT(EPOCH FROM (NOW() - created_at)) > 900 THEN 'SLA_BREACH'
        ELSE 'OK'
    END as sla_status
FROM hitl_decisions
WHERE decision = 'pending'
ORDER BY priority DESC, created_at ASC;

-- Decision summary
CREATE OR REPLACE VIEW hitl_decision_summary AS
SELECT 
    COUNT(*) as total_patches,
    SUM(CASE WHEN decision = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN decision = 'approved' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN decision = 'rejected' THEN 1 ELSE 0 END) as rejected,
    SUM(CASE WHEN decision = 'auto_approved' THEN 1 ELSE 0 END) as auto_approved,
    AVG(EXTRACT(EPOCH FROM (decided_at - created_at))) as avg_decision_time_seconds,
    AVG(CASE WHEN ml_wargaming_agreement THEN 1.0 ELSE 0.0 END) as ml_accuracy
FROM hitl_decisions;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Update updated_at automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_hitl_decisions_updated_at 
    BEFORE UPDATE ON hitl_decisions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Calculate ML/Wargaming agreement
CREATE OR REPLACE FUNCTION calculate_ml_wargaming_agreement()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ml_prediction IS NOT NULL AND NEW.wargaming_passed IS NOT NULL THEN
        NEW.ml_wargaming_agreement = (NEW.ml_prediction = NEW.wargaming_passed);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_agreement
    BEFORE INSERT OR UPDATE ON hitl_decisions
    FOR EACH ROW
    EXECUTE FUNCTION calculate_ml_wargaming_agreement();

-- ============================================================================
-- Initial Data (optional)
-- ============================================================================

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON hitl_decisions TO maximus_app;
-- GRANT SELECT, INSERT ON hitl_audit_logs TO maximus_app;
-- GRANT SELECT, INSERT ON hitl_comments TO maximus_app;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE hitl_decisions IS 'Human-in-the-Loop patch approval decisions';
COMMENT ON TABLE hitl_audit_logs IS 'Immutable audit trail for compliance (SOC 2, ISO 27001)';
COMMENT ON TABLE hitl_comments IS 'Threaded comments on patch decisions';

COMMENT ON COLUMN hitl_decisions.ml_wargaming_agreement IS 'True if ML prediction matches wargaming result';
COMMENT ON COLUMN hitl_decisions.auto_approval_eligible IS 'True if patch meets auto-approval criteria (confidence >=0.95, low risk)';
COMMENT ON COLUMN hitl_decisions.requires_escalation IS 'True if decision requires manager/exec escalation';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_hitl_pending_priority 
    ON hitl_decisions(decision, priority DESC, created_at ASC) 
    WHERE decision = 'pending';

CREATE INDEX IF NOT EXISTS idx_hitl_ml_accuracy 
    ON hitl_decisions(ml_wargaming_agreement) 
    WHERE ml_prediction IS NOT NULL AND wargaming_passed IS NOT NULL;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Verify tables created
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'hitl%';
