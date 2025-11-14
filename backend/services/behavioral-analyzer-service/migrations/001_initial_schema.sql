-- TimescaleDB Schema for Behavioral Analyzer Service
-- Constitutional: Lei Zero - data retention policies respect user privacy (GDPR)
--
-- This migration creates the initial schema for persistent behavioral analysis data.
-- Replaces in-memory dictionaries with production-grade time-series database.

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- USER PROFILES TABLE
-- ============================================================================
-- Stores user behavioral profiles with baselines and risk scores

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Baseline metrics (JSON for flexibility)
    baseline_metrics JSONB NOT NULL DEFAULT '{}',

    -- Behavioral fingerprint
    fingerprint JSONB NOT NULL DEFAULT '{}',

    -- Risk assessment
    risk_score FLOAT DEFAULT 0.0,
    risk_level VARCHAR(50) DEFAULT 'low',  -- low, medium, high, critical

    -- Activity statistics
    total_events INTEGER DEFAULT 0,
    anomaly_count INTEGER DEFAULT 0,
    last_seen TIMESTAMPTZ,

    -- Constitutional: GDPR compliance
    data_retention_days INTEGER DEFAULT 90,
    consent_given BOOLEAN DEFAULT false,
    consent_date TIMESTAMPTZ,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated
    ON user_profiles(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_profiles_risk
    ON user_profiles(risk_score DESC)
    WHERE risk_score > 0.5;

CREATE INDEX IF NOT EXISTS idx_user_profiles_last_seen
    ON user_profiles(last_seen DESC)
    WHERE last_seen IS NOT NULL;

COMMENT ON TABLE user_profiles IS
    'User behavioral profiles with baselines and risk scores. Constitutional: Lei Zero GDPR compliance.';

-- ============================================================================
-- BEHAVIORAL EVENTS TABLE (Time-series)
-- ============================================================================
-- Logs all behavioral events for analysis and anomaly detection

CREATE TABLE IF NOT EXISTS behavioral_events (
    event_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Event classification
    event_type VARCHAR(100) NOT NULL,  -- login, api_call, data_access, privilege_escalation, etc.
    resource VARCHAR(255),
    action VARCHAR(100),

    -- Network context
    ip_address INET,
    user_agent TEXT,

    -- Risk assessment
    risk_score FLOAT,
    anomaly_detected BOOLEAN DEFAULT false,
    anomaly_reason TEXT,

    -- Response
    blocked BOOLEAN DEFAULT false,
    response_action VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Convert to hypertable for time-series optimization
-- Chunk by time (7 days per chunk)
SELECT create_hypertable(
    'behavioral_events',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Indexes for behavioral_events
CREATE INDEX IF NOT EXISTS idx_events_user_time
    ON behavioral_events(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_events_anomaly
    ON behavioral_events(anomaly_detected, timestamp DESC)
    WHERE anomaly_detected = true;

CREATE INDEX IF NOT EXISTS idx_events_risk
    ON behavioral_events(risk_score DESC, timestamp DESC)
    WHERE risk_score > 0.5;

CREATE INDEX IF NOT EXISTS idx_events_type
    ON behavioral_events(event_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_events_ip
    ON behavioral_events(ip_address, timestamp DESC)
    WHERE ip_address IS NOT NULL;

COMMENT ON TABLE behavioral_events IS
    'Time-series log of all behavioral events with anomaly detection results.';

-- ============================================================================
-- ANOMALIES TABLE
-- ============================================================================
-- Stores detected anomalies requiring investigation or response

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Anomaly classification
    anomaly_type VARCHAR(100) NOT NULL,  -- unusual_time, impossible_travel, privilege_abuse, etc.
    severity VARCHAR(50) NOT NULL,  -- low, medium, high, critical
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),

    -- Description
    title VARCHAR(500) NOT NULL,
    description TEXT,
    evidence JSONB DEFAULT '{}',

    -- Context
    related_events TEXT[],  -- Array of event_ids
    baseline_deviation FLOAT,  -- How far from baseline (std devs)

    -- Response tracking
    status VARCHAR(50) DEFAULT 'open',  -- open, investigating, resolved, false_positive
    priority INTEGER DEFAULT 0,  -- 0=low, 1=medium, 2=high, 3=critical
    assigned_to VARCHAR(255),
    investigated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    resolution TEXT,
    response_action TEXT,

    -- Feedback for ML
    false_positive BOOLEAN,
    feedback_notes TEXT,

    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
);

-- Indexes for anomalies
CREATE INDEX IF NOT EXISTS idx_anomalies_user_detected
    ON anomalies(user_id, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomalies_status_severity
    ON anomalies(status, severity, detected_at DESC)
    WHERE status IN ('open', 'investigating');

CREATE INDEX IF NOT EXISTS idx_anomalies_priority
    ON anomalies(priority DESC, detected_at DESC)
    WHERE status = 'open';

CREATE INDEX IF NOT EXISTS idx_anomalies_type
    ON anomalies(anomaly_type, detected_at DESC);

COMMENT ON TABLE anomalies IS
    'Detected behavioral anomalies requiring investigation. Constitutional: Lei Zero human oversight.';

-- ============================================================================
-- DATA RETENTION POLICIES
-- ============================================================================
-- Constitutional: Lei Zero - minimize data retention, respect user privacy

-- Automatically drop old behavioral events (90 days retention)
SELECT add_retention_policy(
    'behavioral_events',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Note: user_profiles and anomalies use application-level retention
-- based on user_profiles.data_retention_days and consent

-- ============================================================================
-- CONTINUOUS AGGREGATES (Pre-computed views)
-- ============================================================================
-- Optimize common queries with materialized aggregates

-- Hourly event statistics per user
CREATE MATERIALIZED VIEW IF NOT EXISTS user_events_hourly
WITH (timescaledb.continuous) AS
SELECT
    user_id,
    time_bucket('1 hour', timestamp) AS hour,
    COUNT(*) AS event_count,
    COUNT(*) FILTER (WHERE anomaly_detected) AS anomaly_count,
    AVG(risk_score) AS avg_risk_score,
    MAX(risk_score) AS max_risk_score,
    COUNT(DISTINCT event_type) AS unique_event_types,
    COUNT(DISTINCT ip_address) AS unique_ips
FROM behavioral_events
GROUP BY user_id, hour;

-- Refresh policy: update every 15 minutes
SELECT add_continuous_aggregate_policy(
    'user_events_hourly',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE
);

-- Daily anomaly summary
CREATE MATERIALIZED VIEW IF NOT EXISTS anomalies_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', detected_at) AS day,
    anomaly_type,
    severity,
    COUNT(*) AS count,
    AVG(confidence) AS avg_confidence,
    COUNT(DISTINCT user_id) AS affected_users
FROM anomalies
GROUP BY day, anomaly_type, severity;

-- Refresh policy: update every hour
SELECT add_continuous_aggregate_policy(
    'anomalies_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update user profile statistics (trigger function)
CREATE OR REPLACE FUNCTION update_user_profile_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_profiles
    SET
        total_events = total_events + 1,
        last_seen = NEW.timestamp,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;

    -- Update anomaly count if detected
    IF NEW.anomaly_detected THEN
        UPDATE user_profiles
        SET anomaly_count = anomaly_count + 1
        WHERE user_id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on behavioral_events insert
DROP TRIGGER IF EXISTS trg_update_user_stats ON behavioral_events;
CREATE TRIGGER trg_update_user_stats
    AFTER INSERT ON behavioral_events
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profile_stats();

-- ============================================================================
-- SEED DATA (for testing)
-- ============================================================================

-- Insert example user profile (only if empty)
INSERT INTO user_profiles (user_id, baseline_metrics, fingerprint, consent_given)
VALUES (
    'test_user_001',
    '{"avg_login_time": "09:00", "typical_ips": ["192.168.1.100"], "avg_session_duration": 3600}',
    '{"browser": "Chrome", "os": "Linux", "timezone": "America/Sao_Paulo"}',
    true
)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- GRANTS (for application user)
-- ============================================================================

-- Grant permissions to application database user
-- Note: Adjust username based on deployment configuration
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO behavioral_analyzer_app;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO behavioral_analyzer_app;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Output migration success
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001_initial_schema.sql completed successfully';
    RAISE NOTICE 'Created tables: user_profiles, behavioral_events, anomalies';
    RAISE NOTICE 'Created hypertable: behavioral_events (7-day chunks)';
    RAISE NOTICE 'Created continuous aggregates: user_events_hourly, anomalies_daily';
    RAISE NOTICE 'Data retention: 90 days (Constitutional Lei Zero compliance)';
END $$;
