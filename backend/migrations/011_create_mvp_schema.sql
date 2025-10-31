-- MVP (MAXIMUS Vision Protocol) Schema Migration
-- Version: 1.0.0
-- Date: 2025-10-30
-- Author: Vértice Platform Team

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- NARRATIVES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_narratives (
    narrative_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consciousness_snapshot_id VARCHAR(255) NOT NULL,
    narrative_type VARCHAR(100) NOT NULL, -- daily_summary, milestone, anomaly_alert, learning_report, ethical_review
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    tone VARCHAR(50) NOT NULL, -- reflective, analytical, celebratory, concerned, neutral
    duration_target_seconds INTEGER NOT NULL DEFAULT 30,
    narrative_text TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    audio_url TEXT,
    audio_duration_seconds REAL,

    -- Quality Metrics
    nqs INTEGER CHECK (nqs >= 0 AND nqs <= 100), -- Narrative Quality Score
    aqs INTEGER CHECK (aqs >= 0 AND aqs <= 100), -- Audio Quality Score (if audio generated)
    clarity_score INTEGER CHECK (clarity_score >= 0 AND clarity_score <= 25),
    coherence_score INTEGER CHECK (coherence_score >= 0 AND coherence_score <= 25),
    relevance_score INTEGER CHECK (relevance_score >= 0 AND relevance_score <= 25),
    tone_score INTEGER CHECK (tone_score >= 0 AND tone_score <= 25),

    -- Generation Metadata
    llm_model VARCHAR(100), -- e.g., "claude-sonnet-4", "gpt-4"
    voice_used VARCHAR(100), -- e.g., "elevenlabs-marcus"
    generation_duration_ms REAL,
    audio_synthesis_duration_ms REAL,
    tokens_consumed INTEGER,
    estimated_cost_usd NUMERIC(10, 6),

    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_narrative_type CHECK (narrative_type IN ('daily_summary', 'milestone', 'anomaly_alert', 'learning_report', 'ethical_review')),
    CONSTRAINT chk_tone CHECK (tone IN ('reflective', 'analytical', 'celebratory', 'concerned', 'neutral'))
);

CREATE INDEX idx_mvp_narratives_type ON mvp_narratives(narrative_type, created_at DESC);
CREATE INDEX idx_mvp_narratives_snapshot ON mvp_narratives(consciousness_snapshot_id);
CREATE INDEX idx_mvp_narratives_created_at ON mvp_narratives(created_at DESC);
CREATE INDEX idx_mvp_narratives_nqs ON mvp_narratives(nqs DESC);

-- =============================================================================
-- CONSCIOUSNESS SNAPSHOTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_consciousness_snapshots (
    snapshot_id VARCHAR(255) PRIMARY KEY,
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    event_count INTEGER NOT NULL,
    eci REAL CHECK (eci >= 0.0 AND eci <= 1.0), -- Φ (Phi) - consciousness level
    system_state JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_mvp_snapshots_captured_at ON mvp_consciousness_snapshots(captured_at DESC);
CREATE INDEX idx_mvp_snapshots_eci ON mvp_consciousness_snapshots(eci DESC);

-- =============================================================================
-- AUDIO SYNTHESIS CACHE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_audio_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash of narrative text
    audio_url TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    aqs INTEGER CHECK (aqs >= 0 AND aqs <= 100),
    voice_id VARCHAR(100) NOT NULL,
    format VARCHAR(50) NOT NULL DEFAULT 'mp3',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    access_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_mvp_audio_cache_hash ON mvp_audio_cache(text_hash);
CREATE INDEX idx_mvp_audio_cache_accessed ON mvp_audio_cache(last_accessed_at DESC);

-- =============================================================================
-- COST TRACKING TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_cost_tracking (
    cost_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    narrative_id UUID REFERENCES mvp_narratives(narrative_id) ON DELETE CASCADE,
    service_type VARCHAR(50) NOT NULL, -- llm, tts, storage
    service_provider VARCHAR(100) NOT NULL, -- anthropic, openai, elevenlabs, azure, s3
    tokens_or_units INTEGER,
    cost_usd NUMERIC(10, 6) NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_service_type CHECK (service_type IN ('llm', 'tts', 'storage'))
);

CREATE INDEX idx_mvp_cost_tracking_date ON mvp_cost_tracking(recorded_at DESC);
CREATE INDEX idx_mvp_cost_tracking_type ON mvp_cost_tracking(service_type);
CREATE INDEX idx_mvp_cost_tracking_provider ON mvp_cost_tracking(service_provider);

-- =============================================================================
-- QUALITY METRICS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_quality_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    narrative_id UUID REFERENCES mvp_narratives(narrative_id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL, -- nqs, aqs, fpc, crs, etc.
    metric_value REAL NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_mvp_quality_metrics_name ON mvp_quality_metrics(metric_name, recorded_at DESC);
CREATE INDEX idx_mvp_quality_metrics_narrative ON mvp_quality_metrics(narrative_id);

-- =============================================================================
-- MODERATION LOG TABLE (PII, Profanity, Tone)
-- =============================================================================

CREATE TABLE IF NOT EXISTS mvp_moderation_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    narrative_id UUID REFERENCES mvp_narratives(narrative_id) ON DELETE CASCADE,
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    check_type VARCHAR(50) NOT NULL, -- pii, profanity, tone, lgpd
    passed BOOLEAN NOT NULL,
    violations JSONB DEFAULT '[]'::JSONB, -- Array of detected violations
    metadata JSONB DEFAULT '{}'::JSONB,

    CONSTRAINT chk_check_type CHECK (check_type IN ('pii', 'profanity', 'tone', 'lgpd'))
);

CREATE INDEX idx_mvp_moderation_narrative ON mvp_moderation_log(narrative_id);
CREATE INDEX idx_mvp_moderation_checked_at ON mvp_moderation_log(checked_at DESC);
CREATE INDEX idx_mvp_moderation_passed ON mvp_moderation_log(passed);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to update audio cache last_accessed_at
CREATE OR REPLACE FUNCTION update_mvp_audio_cache_access()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE mvp_audio_cache
    SET last_accessed_at = NOW(),
        access_count = access_count + 1
    WHERE cache_id = NEW.cache_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate daily costs
CREATE OR REPLACE FUNCTION mvp_get_daily_costs(target_date DATE)
RETURNS TABLE(service_type VARCHAR, total_cost_usd NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.service_type,
        SUM(c.cost_usd) as total_cost_usd
    FROM mvp_cost_tracking c
    WHERE DATE(c.recorded_at) = target_date
    GROUP BY c.service_type;
END;
$$ LANGUAGE plpgsql;

-- Function to get NQS trend (last N days)
CREATE OR REPLACE FUNCTION mvp_get_nqs_trend(days INTEGER DEFAULT 7)
RETURNS TABLE(date DATE, avg_nqs REAL) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE(n.created_at) as date,
        AVG(n.nqs::REAL) as avg_nqs
    FROM mvp_narratives n
    WHERE n.created_at >= NOW() - INTERVAL '1 day' * days
    AND n.nqs IS NOT NULL
    GROUP BY DATE(n.created_at)
    ORDER BY date DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE mvp_narratives IS 'AI-generated narratives from consciousness snapshots';
COMMENT ON TABLE mvp_consciousness_snapshots IS 'MAXIMUS consciousness state snapshots';
COMMENT ON TABLE mvp_audio_cache IS 'Cache of synthesized audio to avoid redundant TTS calls';
COMMENT ON TABLE mvp_cost_tracking IS 'Cost tracking for LLM, TTS, and storage services';
COMMENT ON TABLE mvp_quality_metrics IS 'Quality metrics for narratives and audio';
COMMENT ON TABLE mvp_moderation_log IS 'Content moderation checks (PII, profanity, tone)';

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions to application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mvp_service;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mvp_service;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
