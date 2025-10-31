-- PENELOPE (Christian Autonomous Healing Service) Schema Migration
-- Version: 1.0.0
-- Date: 2025-10-30
-- Author: Vértice Platform Team
-- Governance: 7 Biblical Articles

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For hashing

-- =============================================================================
-- ANOMALIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_anomalies (
    anomaly_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_type VARCHAR(100) NOT NULL, -- latency_spike, error_rate_increase, memory_leak, etc.
    service VARCHAR(255) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    severity VARCHAR(10) NOT NULL, -- P0, P1, P2, P3
    status VARCHAR(50) NOT NULL DEFAULT 'detected', -- detected, diagnosed, patched, resolved, ignored
    metrics JSONB NOT NULL,
    context JSONB DEFAULT '{}'::JSONB,
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_severity CHECK (severity IN ('P0', 'P1', 'P2', 'P3')),
    CONSTRAINT chk_anomaly_status CHECK (status IN ('detected', 'diagnosed', 'patched', 'resolved', 'ignored'))
);

CREATE INDEX idx_penelope_anomalies_type ON penelope_anomalies(anomaly_type, detected_at DESC);
CREATE INDEX idx_penelope_anomalies_service ON penelope_anomalies(service, detected_at DESC);
CREATE INDEX idx_penelope_anomalies_severity ON penelope_anomalies(severity);
CREATE INDEX idx_penelope_anomalies_status ON penelope_anomalies(status);

-- =============================================================================
-- DIAGNOSES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_diagnoses (
    diagnosis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_id UUID NOT NULL REFERENCES penelope_anomalies(anomaly_id) ON DELETE CASCADE,
    diagnosed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    root_cause TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    domain VARCHAR(100) NOT NULL, -- known, unknown
    causal_chain JSONB NOT NULL, -- Array of causal steps
    precedents JSONB DEFAULT '[]'::JSONB, -- Array of similar precedents

    -- Sophia Engine Decision
    sophia_recommendation VARCHAR(50) NOT NULL, -- observe, intervene, escalate
    intervention_level INTEGER CHECK (intervention_level >= 1 AND intervention_level <= 5), -- Praotes levels
    sophia_reasoning TEXT,

    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_domain CHECK (domain IN ('known', 'unknown')),
    CONSTRAINT chk_sophia_recommendation CHECK (sophia_recommendation IN ('observe', 'intervene', 'escalate'))
);

CREATE INDEX idx_penelope_diagnoses_anomaly ON penelope_diagnoses(anomaly_id);
CREATE INDEX idx_penelope_diagnoses_confidence ON penelope_diagnoses(confidence DESC);
CREATE INDEX idx_penelope_diagnoses_recommendation ON penelope_diagnoses(sophia_recommendation);

-- =============================================================================
-- PATCHES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_patches (
    patch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnosis_id UUID NOT NULL REFERENCES penelope_diagnoses(diagnosis_id) ON DELETE CASCADE,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    patch_content TEXT NOT NULL,
    diff TEXT NOT NULL,
    affected_files TEXT[] NOT NULL,
    patch_size_lines INTEGER NOT NULL,

    -- Quality Metrics
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    mansidao_score REAL NOT NULL CHECK (mansidao_score >= 0.0 AND mansidao_score <= 1.0),
    reversibility_score REAL NOT NULL CHECK (reversibility_score >= 0.0 AND reversibility_score <= 1.0),

    -- Tapeinophrosyne (Humility) Assessment
    competence_level VARCHAR(50) NOT NULL, -- autonomous, assisted, defer
    humility_notes TEXT,
    uncertainty_factors JSONB DEFAULT '[]'::JSONB,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'generated', -- generated, validated, deployed, rolled_back, failed
    validated_at TIMESTAMP WITH TIME ZONE,
    deployed_at TIMESTAMP WITH TIME ZONE,
    git_commit_sha VARCHAR(40),

    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_competence_level CHECK (competence_level IN ('autonomous', 'assisted', 'defer')),
    CONSTRAINT chk_patch_status CHECK (status IN ('generated', 'validated', 'deployed', 'rolled_back', 'failed'))
);

CREATE INDEX idx_penelope_patches_diagnosis ON penelope_patches(diagnosis_id);
CREATE INDEX idx_penelope_patches_status ON penelope_patches(status);
CREATE INDEX idx_penelope_patches_mansidao ON penelope_patches(mansidao_score DESC);
CREATE INDEX idx_penelope_patches_deployed_at ON penelope_patches(deployed_at DESC NULLS LAST);

-- =============================================================================
-- PATCH VALIDATIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_patch_validations (
    validation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patch_id UUID NOT NULL REFERENCES penelope_patches(patch_id) ON DELETE CASCADE,
    validated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    validation_status VARCHAR(50) NOT NULL, -- passed, failed, warnings
    tests_run INTEGER NOT NULL,
    tests_passed INTEGER NOT NULL,
    tests_failed INTEGER NOT NULL,
    test_results JSONB DEFAULT '[]'::JSONB,
    performance_impact JSONB DEFAULT '{}'::JSONB,
    side_effects_detected TEXT[],

    CONSTRAINT chk_validation_status CHECK (validation_status IN ('passed', 'failed', 'warnings'))
);

CREATE INDEX idx_penelope_validations_patch ON penelope_patch_validations(patch_id);
CREATE INDEX idx_penelope_validations_status ON penelope_patch_validations(validation_status);

-- =============================================================================
-- WISDOM BASE TABLE (Historical Precedents)
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_wisdom_base (
    precedent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(255) UNIQUE NOT NULL,
    stored_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    anomaly_type VARCHAR(100) NOT NULL,
    service VARCHAR(255) NOT NULL,
    root_cause TEXT NOT NULL,
    patch_applied TEXT,
    outcome VARCHAR(50) NOT NULL, -- success, failure
    lessons_learned TEXT,
    -- similarity_embedding VECTOR(768), -- For future vector search (Phase 2) - REQUIRES pgvector extension
    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_outcome CHECK (outcome IN ('success', 'failure'))
);

CREATE INDEX idx_penelope_wisdom_type_service ON penelope_wisdom_base(anomaly_type, service);
CREATE INDEX idx_penelope_wisdom_outcome ON penelope_wisdom_base(outcome);
CREATE INDEX idx_penelope_wisdom_stored_at ON penelope_wisdom_base(stored_at DESC);

-- =============================================================================
-- LESSONS LEARNED TABLE (Artigo VII - Aletheia / Truth)
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_lessons_learned (
    lesson_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    learned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    patch_id UUID REFERENCES penelope_patches(patch_id) ON DELETE CASCADE,
    what_expected TEXT NOT NULL,
    what_happened TEXT NOT NULL,
    root_cause_of_failure TEXT NOT NULL,
    lesson_learned TEXT NOT NULL,
    adjustment_needed TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_penelope_lessons_learned_at ON penelope_lessons_learned(learned_at DESC);
CREATE INDEX idx_penelope_lessons_patch ON penelope_lessons_learned(patch_id);

-- =============================================================================
-- SABBATH LOG TABLE (Artigo VI - Sabbath)
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_sabbath_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    logged_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_sabbath BOOLEAN NOT NULL,
    action_attempted VARCHAR(100), -- patch_generation, patch_deployment, etc.
    action_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    exception_type VARCHAR(50), -- P0_critical, security_breach, data_loss_risk
    exception_approved_by VARCHAR(255),
    notes TEXT
);

CREATE INDEX idx_penelope_sabbath_logged_at ON penelope_sabbath_log(logged_at DESC);
CREATE INDEX idx_penelope_sabbath_blocked ON penelope_sabbath_log(action_blocked);

-- =============================================================================
-- GOVERNANCE METRICS TABLE (7 Articles Compliance)
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_governance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    article VARCHAR(50) NOT NULL, -- sophia, praotes, tapeinophrosyne, stewardship, agape, sabbath, aletheia
    metric_name VARCHAR(100) NOT NULL,
    metric_value REAL NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_article CHECK (article IN ('sophia', 'praotes', 'tapeinophrosyne', 'stewardship', 'agape', 'sabbath', 'aletheia'))
);

CREATE INDEX idx_penelope_governance_article ON penelope_governance_metrics(article, recorded_at DESC);
CREATE INDEX idx_penelope_governance_metric ON penelope_governance_metrics(metric_name, recorded_at DESC);

-- =============================================================================
-- VIRTUES DASHBOARD TABLE (Real-time Compliance)
-- =============================================================================

CREATE TABLE IF NOT EXISTS penelope_virtues_dashboard (
    dashboard_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Sophia (Wisdom)
    fir REAL CHECK (fir >= 0.0 AND fir <= 1.0), -- False Intervention Rate
    wrs REAL CHECK (wrs >= 0.0 AND wrs <= 1.0), -- Wisdom Recall Score
    ta REAL CHECK (ta >= 0.0 AND ta <= 1.0), -- Timing Accuracy

    -- Praotes (Meekness)
    aps REAL, -- Average Patch Size (lines)
    rs REAL CHECK (rs >= 0.0 AND rs <= 1.0), -- Reversibility Score
    acp REAL CHECK (acp >= 0.0 AND acp <= 1.0), -- API Contract Preservation

    -- Tapeinophrosyne (Humility)
    aer REAL CHECK (aer >= 0.0 AND aer <= 1.0), -- Appropriate Escalation Rate
    fcr REAL CHECK (fcr >= 0.0 AND fcr <= 1.0), -- False Confidence Rate
    lr REAL CHECK (lr >= 0.0 AND lr <= 1.0), -- Learning Rate

    -- Overall
    hsr REAL CHECK (hsr >= 0.0 AND hsr <= 1.0), -- Healing Success Rate
    mttr REAL, -- Mean Time to Repair (minutes)

    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_penelope_virtues_calculated_at ON penelope_virtues_dashboard(calculated_at DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to check if it's Sabbath (Sunday UTC)
CREATE OR REPLACE FUNCTION is_sabbath()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXTRACT(DOW FROM NOW() AT TIME ZONE 'UTC') = 0; -- Sunday = 0
END;
$$ LANGUAGE plpgsql;

-- Function to validate patch size (Praotes compliance)
CREATE OR REPLACE FUNCTION validate_patch_size(patch_size INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN patch_size <= 25; -- Max 25 lines per Article II
END;
$$ LANGUAGE plpgsql;

-- Function to calculate Healing Success Rate
CREATE OR REPLACE FUNCTION calculate_healing_success_rate(days INTEGER DEFAULT 7)
RETURNS REAL AS $$
DECLARE
    total_anomalies INTEGER;
    resolved_anomalies INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_anomalies
    FROM penelope_anomalies
    WHERE detected_at >= NOW() - INTERVAL '1 day' * days;

    SELECT COUNT(*) INTO resolved_anomalies
    FROM penelope_anomalies
    WHERE detected_at >= NOW() - INTERVAL '1 day' * days
    AND status = 'resolved';

    IF total_anomalies = 0 THEN
        RETURN 0.0;
    ELSE
        RETURN resolved_anomalies::REAL / total_anomalies::REAL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get Sabbath compliance rate
CREATE OR REPLACE FUNCTION get_sabbath_compliance_rate(days INTEGER DEFAULT 30)
RETURNS REAL AS $$
DECLARE
    total_sundays INTEGER;
    compliant_sundays INTEGER;
BEGIN
    -- Count Sundays in period
    SELECT COUNT(DISTINCT DATE(logged_at))
    INTO total_sundays
    FROM penelope_sabbath_log
    WHERE logged_at >= NOW() - INTERVAL '1 day' * days
    AND is_sabbath = TRUE;

    -- Count compliant Sundays (no patches or only P0 exceptions)
    SELECT COUNT(DISTINCT DATE(logged_at))
    INTO compliant_sundays
    FROM penelope_sabbath_log
    WHERE logged_at >= NOW() - INTERVAL '1 day' * days
    AND is_sabbath = TRUE
    AND (action_blocked = FALSE OR exception_type = 'P0_critical');

    IF total_sundays = 0 THEN
        RETURN 1.0; -- Perfect compliance if no Sundays yet
    ELSE
        RETURN compliant_sundays::REAL / total_sundays::REAL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger to log Sabbath enforcement
CREATE OR REPLACE FUNCTION log_sabbath_check()
RETURNS TRIGGER AS $$
BEGIN
    IF is_sabbath() THEN
        INSERT INTO penelope_sabbath_log (is_sabbath, action_attempted, action_blocked, notes)
        VALUES (TRUE, TG_TABLE_NAME, TRUE, 'Sabbath mode: patch generation blocked');

        -- Raise exception to block action (unless P0)
        IF NEW.severity != 'P0' THEN
            RAISE EXCEPTION 'Sabbath mode active - no patches on Sundays (except P0 critical)';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply Sabbath trigger to patches table
CREATE TRIGGER trigger_sabbath_enforcement
BEFORE INSERT ON penelope_patches
FOR EACH ROW
EXECUTE FUNCTION log_sabbath_check();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE penelope_anomalies IS 'Detected system anomalies awaiting diagnosis';
COMMENT ON TABLE penelope_diagnoses IS 'Causal diagnoses by Sophia Engine';
COMMENT ON TABLE penelope_patches IS 'Generated code patches (governed by 7 Articles)';
COMMENT ON TABLE penelope_patch_validations IS 'Digital twin validation results';
COMMENT ON TABLE penelope_wisdom_base IS 'Historical precedents (Article VII - Aletheia)';
COMMENT ON TABLE penelope_lessons_learned IS 'Lessons from failures (Humility)';
COMMENT ON TABLE penelope_sabbath_log IS 'Sabbath observance log (Article VI)';
COMMENT ON TABLE penelope_governance_metrics IS 'Compliance metrics for 7 Biblical Articles';
COMMENT ON TABLE penelope_virtues_dashboard IS 'Real-time virtues compliance dashboard';

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions to application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO penelope_service;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO penelope_service;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO penelope_service;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
