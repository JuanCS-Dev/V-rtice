-- ============================================================================
-- Cognitive Defense System - Database Schema Initialization
-- ============================================================================
-- Version: 2.0.0
-- Description: PostgreSQL schema for narrative manipulation detection system
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For similarity search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For composite indexes

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE analysis_status AS ENUM ('pending', 'processing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_taken AS ENUM ('allowed', 'flagged', 'warned', 'blocked', 'quarantined');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- TABLE: analysis_history
-- Historical record of all analyses
-- ============================================================================

CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Input
    text_hash VARCHAR(64) NOT NULL,
    text TEXT NOT NULL,
    source_url VARCHAR(2048),
    source_domain VARCHAR(255),

    -- Status
    status analysis_status NOT NULL DEFAULT 'pending',

    -- Results
    threat_score FLOAT CHECK (threat_score >= 0 AND threat_score <= 1),
    severity VARCHAR(20),
    recommended_action action_taken,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),

    -- Module Scores
    credibility_score FLOAT,
    emotional_score FLOAT,
    logical_score FLOAT,
    reality_score FLOAT,

    -- Full Report (JSONB for efficient querying)
    report_json JSONB,

    -- Performance Metrics
    processing_time_ms FLOAT,
    tier2_used BOOLEAN DEFAULT FALSE,
    models_used TEXT[],

    -- Foreign Keys
    source_reputation_id UUID REFERENCES source_reputation(id)
);

-- Indexes for analysis_history
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_text_hash ON analysis_history(text_hash);
CREATE INDEX IF NOT EXISTS idx_analysis_source_domain ON analysis_history(source_domain);
CREATE INDEX IF NOT EXISTS idx_analysis_source_domain_created ON analysis_history(source_domain, created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_threat_score ON analysis_history(threat_score DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_history(status);
CREATE INDEX IF NOT EXISTS idx_analysis_report_json ON analysis_history USING GIN(report_json);

-- ============================================================================
-- TABLE: source_reputation
-- Dynamic source credibility tracking with Bayesian updates
-- ============================================================================

CREATE TABLE IF NOT EXISTS source_reputation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Source Identification
    domain VARCHAR(255) UNIQUE NOT NULL,
    domain_fingerprint VARCHAR(128),

    -- NewsGuard Data
    newsguard_score FLOAT,
    newsguard_rating VARCHAR(50),
    newsguard_last_updated TIMESTAMP,
    newsguard_nutrition_label JSONB,

    -- Bayesian Credibility
    prior_credibility FLOAT NOT NULL DEFAULT 0.5 CHECK (prior_credibility >= 0 AND prior_credibility <= 1),
    posterior_credibility FLOAT NOT NULL DEFAULT 0.5 CHECK (posterior_credibility >= 0 AND posterior_credibility <= 1),
    alpha FLOAT NOT NULL DEFAULT 1.0 CHECK (alpha > 0),
    beta FLOAT NOT NULL DEFAULT 1.0 CHECK (beta > 0),

    -- Historical Statistics
    total_analyses INTEGER NOT NULL DEFAULT 0,
    false_content_count INTEGER NOT NULL DEFAULT 0,
    true_content_count INTEGER NOT NULL DEFAULT 0,
    last_false_content_date TIMESTAMP,

    -- Domain Hopping Detection
    similar_domains TEXT[],
    cluster_id VARCHAR(64),

    -- Metadata
    first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    last_analyzed TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for source_reputation
CREATE INDEX IF NOT EXISTS idx_source_domain ON source_reputation(domain);
CREATE INDEX IF NOT EXISTS idx_source_posterior ON source_reputation(posterior_credibility DESC);
CREATE INDEX IF NOT EXISTS idx_source_cluster ON source_reputation(cluster_id);
CREATE INDEX IF NOT EXISTS idx_source_fingerprint ON source_reputation(domain_fingerprint);

-- ============================================================================
-- TABLE: fact_check_cache
-- Cache for external fact-checking API results
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_check_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Claim Identification
    claim_text_hash VARCHAR(64) NOT NULL,
    claim_text TEXT NOT NULL,

    -- Verification Result
    verification_status VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),

    -- Source Attribution
    source_api VARCHAR(50) NOT NULL,
    source_url VARCHAR(2048),
    rating_text VARCHAR(255),

    -- Full API Response
    api_response_json JSONB,

    -- Cache Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign Keys
    source_reputation_id UUID REFERENCES source_reputation(id)
);

-- Indexes for fact_check_cache
CREATE INDEX IF NOT EXISTS idx_factcheck_claim_hash ON fact_check_cache(claim_text_hash);
CREATE INDEX IF NOT EXISTS idx_factcheck_expires ON fact_check_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_factcheck_source_api ON fact_check_cache(source_api);
CREATE INDEX IF NOT EXISTS idx_factcheck_claim_text_trgm ON fact_check_cache USING GIN(claim_text gin_trgm_ops);

-- ============================================================================
-- TABLE: entity_cache
-- Cache for entity linking results (DBpedia Spotlight)
-- ============================================================================

CREATE TABLE IF NOT EXISTS entity_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Entity Identification
    surface_form VARCHAR(255) NOT NULL,
    context_hash VARCHAR(64) NOT NULL,

    -- Linked Entity
    entity_uri VARCHAR(512) NOT NULL,
    entity_types TEXT[],
    confidence FLOAT NOT NULL,
    support INTEGER DEFAULT 0,

    -- Wikidata/DBpedia Metadata
    wikidata_id VARCHAR(20),
    dbpedia_abstract TEXT,
    entity_metadata JSONB,

    -- Cache Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,

    UNIQUE(surface_form, context_hash)
);

-- Indexes for entity_cache
CREATE INDEX IF NOT EXISTS idx_entity_surface ON entity_cache(surface_form);
CREATE INDEX IF NOT EXISTS idx_entity_uri ON entity_cache(entity_uri);
CREATE INDEX IF NOT EXISTS idx_entity_expires ON entity_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_entity_wikidata ON entity_cache(wikidata_id);

-- ============================================================================
-- TABLE: propaganda_patterns
-- Learned propaganda patterns for model improvement
-- ============================================================================

CREATE TABLE IF NOT EXISTS propaganda_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pattern
    technique VARCHAR(50) NOT NULL,
    pattern_text TEXT NOT NULL,
    pattern_embedding FLOAT[],  -- 768-dim sentence embedding

    -- Statistics
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    false_positive_count INTEGER NOT NULL DEFAULT 0,
    precision FLOAT,

    -- Context
    typical_contexts TEXT[],
    language VARCHAR(5) NOT NULL DEFAULT 'pt',

    -- Metadata
    first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for propaganda_patterns
CREATE INDEX IF NOT EXISTS idx_propaganda_technique ON propaganda_patterns(technique);
CREATE INDEX IF NOT EXISTS idx_propaganda_precision ON propaganda_patterns(technique, precision DESC);
CREATE INDEX IF NOT EXISTS idx_propaganda_language ON propaganda_patterns(language);

-- ============================================================================
-- TABLE: argument_frameworks
-- Abstract Argumentation Framework instances
-- ============================================================================

CREATE TABLE IF NOT EXISTS argument_frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Framework Metadata
    analysis_id UUID NOT NULL REFERENCES analysis_history(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Seriema Graph Reference
    neo4j_graph_id VARCHAR(64),

    -- Argumentation Structure (simplified JSON)
    arguments_json JSONB NOT NULL,
    attacks_json JSONB NOT NULL,

    -- Computed Properties
    coherence_score FLOAT,
    grounded_extensions JSONB,
    preferred_extensions JSONB
);

-- Indexes for argument_frameworks
CREATE INDEX IF NOT EXISTS idx_af_analysis_id ON argument_frameworks(analysis_id);
CREATE INDEX IF NOT EXISTS idx_af_neo4j_id ON argument_frameworks(neo4j_graph_id);
CREATE INDEX IF NOT EXISTS idx_af_created ON argument_frameworks(created_at DESC);

-- ============================================================================
-- TABLE: ml_model_metrics
-- MLOps metrics for model performance tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_model_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model Identification
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,

    -- Performance Metrics
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,

    -- Inference Performance
    avg_inference_time_ms FLOAT,
    throughput_samples_per_sec FLOAT,

    -- Robustness
    adversarial_accuracy FLOAT,
    certified_radius FLOAT,

    -- Data Drift
    feature_drift_detected BOOLEAN DEFAULT FALSE,
    drift_score FLOAT,

    -- Metadata
    evaluation_dataset VARCHAR(255),
    notes TEXT
);

-- Indexes for ml_model_metrics
CREATE INDEX IF NOT EXISTS idx_ml_metrics_model ON ml_model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_metrics_timestamp ON ml_model_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ml_metrics_model_time ON ml_model_metrics(model_name, timestamp DESC);

-- ============================================================================
-- TABLE: adversarial_examples
-- Repository of adversarial examples for training
-- ============================================================================

CREATE TABLE IF NOT EXISTS adversarial_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Original & Perturbed
    original_text TEXT NOT NULL,
    perturbed_text TEXT NOT NULL,
    perturbation_type VARCHAR(50) NOT NULL,

    -- Model Fooling
    model_fooled VARCHAR(100) NOT NULL,
    original_prediction VARCHAR(50) NOT NULL,
    perturbed_prediction VARCHAR(50) NOT NULL,

    -- Defense Training
    used_in_training BOOLEAN DEFAULT FALSE,
    defense_effective BOOLEAN,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for adversarial_examples
CREATE INDEX IF NOT EXISTS idx_adv_model ON adversarial_examples(model_fooled);
CREATE INDEX IF NOT EXISTS idx_adv_type ON adversarial_examples(perturbation_type);
CREATE INDEX IF NOT EXISTS idx_adv_training ON adversarial_examples(used_in_training) WHERE used_in_training = FALSE;

-- ============================================================================
-- TABLE: background_tasks
-- Kafka/async task tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS background_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Task Info
    task_type VARCHAR(50) NOT NULL,
    kafka_topic VARCHAR(100),
    kafka_partition INTEGER,
    kafka_offset BIGINT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Payload & Result
    payload JSONB,
    result JSONB,
    error_message TEXT,

    -- Retry Logic
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3
);

-- Indexes for background_tasks
CREATE INDEX IF NOT EXISTS idx_task_type ON background_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_task_status ON background_tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_created ON background_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_status_created ON background_tasks(status, created_at);

-- ============================================================================
-- MATERIALIZED VIEWS (for analytics)
-- ============================================================================

-- Domain credibility summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_credibility_summary AS
SELECT
    sr.domain,
    sr.posterior_credibility,
    sr.total_analyses,
    sr.false_content_count,
    sr.true_content_count,
    COUNT(ah.id) as recent_analyses_30d,
    AVG(ah.threat_score) as avg_threat_score_30d
FROM source_reputation sr
LEFT JOIN analysis_history ah ON ah.source_domain = sr.domain
    AND ah.created_at >= NOW() - INTERVAL '30 days'
GROUP BY sr.id, sr.domain, sr.posterior_credibility, sr.total_analyses, sr.false_content_count, sr.true_content_count;

CREATE INDEX IF NOT EXISTS idx_mv_domain_credibility ON mv_domain_credibility_summary(domain);
CREATE INDEX IF NOT EXISTS idx_mv_posterior_credibility ON mv_domain_credibility_summary(posterior_credibility DESC);

-- Daily analysis statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_stats AS
SELECT
    DATE(created_at) as analysis_date,
    COUNT(*) as total_analyses,
    AVG(threat_score) as avg_threat_score,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE severity = 'high') as high_count,
    COUNT(*) FILTER (WHERE tier2_used = TRUE) as tier2_count,
    AVG(processing_time_ms) as avg_processing_time
FROM analysis_history
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE(created_at);

CREATE INDEX IF NOT EXISTS idx_mv_daily_stats_date ON mv_daily_stats(analysis_date DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update last_analyzed timestamp
CREATE OR REPLACE FUNCTION update_last_analyzed()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE source_reputation
    SET last_analyzed = NOW()
    WHERE domain = NEW.source_domain;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on analysis_history insert
DROP TRIGGER IF EXISTS trigger_update_last_analyzed ON analysis_history;
CREATE TRIGGER trigger_update_last_analyzed
    AFTER INSERT ON analysis_history
    FOR EACH ROW
    WHEN (NEW.source_domain IS NOT NULL)
    EXECUTE FUNCTION update_last_analyzed();

-- Function to auto-expire cache entries
CREATE OR REPLACE FUNCTION delete_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM fact_check_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    DELETE FROM entity_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS (adjust for your PostgreSQL user)
-- ============================================================================

-- Example: GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cogdef_user;
-- Example: GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cogdef_user;

-- ============================================================================
-- INITIAL DATA (optional)
-- ============================================================================

-- Insert trusted domains as seed data
INSERT INTO source_reputation (domain, newsguard_score, newsguard_rating, prior_credibility, posterior_credibility)
VALUES
    ('wikipedia.org', 95.0, 'trusted', 0.95, 0.95),
    ('reuters.com', 92.0, 'trusted', 0.92, 0.92),
    ('apnews.com', 93.0, 'trusted', 0.93, 0.93),
    ('bbc.com', 90.0, 'trusted', 0.90, 0.90)
ON CONFLICT (domain) DO NOTHING;

-- ============================================================================
-- MAINTENANCE TASKS (run periodically)
-- ============================================================================

-- Refresh materialized views (run daily)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_domain_credibility_summary;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_stats;

-- Clean expired cache (run hourly)
-- SELECT delete_expired_cache();

-- Vacuum and analyze (run weekly)
-- VACUUM ANALYZE;

-- ============================================================================
-- SCHEMA VERSION
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description)
VALUES ('2.0.0', 'Initial Cognitive Defense System schema')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
