-- MABA (MAXIMUS Browser Agent) Schema Migration
-- Version: 1.0.0
-- Date: 2025-10-30
-- Author: Vértice Platform Team

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- BROWSER SESSIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_browser_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    headless BOOLEAN NOT NULL DEFAULT TRUE,
    user_agent TEXT,
    viewport_width INTEGER DEFAULT 1920,
    viewport_height INTEGER DEFAULT 1080,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, closed, error
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Indexes
    CONSTRAINT chk_status CHECK (status IN ('active', 'closed', 'error'))
);

CREATE INDEX idx_maba_sessions_status ON maba_browser_sessions(status);
CREATE INDEX idx_maba_sessions_created_at ON maba_browser_sessions(created_at DESC);

-- =============================================================================
-- NAVIGATION HISTORY TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_navigation_history (
    navigation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES maba_browser_sessions(session_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    navigated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    wait_until VARCHAR(50) DEFAULT 'networkidle',
    timeout_ms INTEGER DEFAULT 30000,
    status VARCHAR(50) NOT NULL, -- success, timeout, error
    duration_ms REAL,
    error_message TEXT,
    screenshot_path TEXT,

    -- Indexes
    CONSTRAINT chk_navigation_status CHECK (status IN ('success', 'timeout', 'error'))
);

CREATE INDEX idx_maba_navigation_session ON maba_navigation_history(session_id, navigated_at DESC);
CREATE INDEX idx_maba_navigation_url ON maba_navigation_history(url);
CREATE INDEX idx_maba_navigation_status ON maba_navigation_history(status);

-- =============================================================================
-- COGNITIVE MAPS TABLE (Website Structure Learning)
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_cognitive_maps (
    map_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain VARCHAR(255) NOT NULL,
    entry_point TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1,
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    nodes_discovered INTEGER NOT NULL DEFAULT 0,
    edges_mapped INTEGER NOT NULL DEFAULT 0,
    graph_data JSONB NOT NULL DEFAULT '{}'::JSONB, -- Actual graph structure
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Ensure only one active map per domain+entry_point
    UNIQUE (domain, entry_point, version)
);

CREATE INDEX idx_maba_cognitive_maps_domain ON maba_cognitive_maps(domain);
CREATE INDEX idx_maba_cognitive_maps_confidence ON maba_cognitive_maps(confidence_score DESC);
CREATE INDEX idx_maba_cognitive_maps_updated ON maba_cognitive_maps(updated_at DESC);

-- =============================================================================
-- ELEMENT CACHE TABLE (Learned Selectors)
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_element_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    map_id UUID NOT NULL REFERENCES maba_cognitive_maps(map_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    description TEXT NOT NULL, -- Human-readable description (e.g., "login button")
    selector TEXT NOT NULL, -- CSS selector
    importance REAL NOT NULL DEFAULT 0.5 CHECK (importance >= 0.0 AND importance <= 1.0),
    last_verified_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    still_valid BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_maba_element_cache_map ON maba_element_cache(map_id);
CREATE INDEX idx_maba_element_cache_url ON maba_element_cache(url);
CREATE INDEX idx_maba_element_cache_description ON maba_element_cache(description);

-- =============================================================================
-- TASKS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(100) NOT NULL, -- navigate, extract, fill_form, etc.
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- queued, in_progress, completed, failed
    session_id UUID REFERENCES maba_browser_sessions(session_id) ON DELETE SET NULL,
    cognitive_map_used UUID REFERENCES maba_cognitive_maps(map_id) ON DELETE SET NULL,
    request_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    execution_time_ms REAL,

    CONSTRAINT chk_task_status CHECK (status IN ('queued', 'in_progress', 'completed', 'failed'))
);

CREATE INDEX idx_maba_tasks_status ON maba_tasks(status);
CREATE INDEX idx_maba_tasks_type ON maba_tasks(task_type);
CREATE INDEX idx_maba_tasks_created_at ON maba_tasks(created_at DESC);

-- =============================================================================
-- METRICS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS maba_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value REAL NOT NULL,
    labels JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_maba_metrics_name ON maba_metrics(metric_name, recorded_at DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to update cognitive map updated_at timestamp
CREATE OR REPLACE FUNCTION update_maba_cognitive_map_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_update_maba_cognitive_map_timestamp
BEFORE UPDATE ON maba_cognitive_maps
FOR EACH ROW
EXECUTE FUNCTION update_maba_cognitive_map_updated_at();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE maba_browser_sessions IS 'Browser sessions managed by MABA';
COMMENT ON TABLE maba_navigation_history IS 'History of all page navigations';
COMMENT ON TABLE maba_cognitive_maps IS 'Learned website structures (graphs)';
COMMENT ON TABLE maba_element_cache IS 'Cached element selectors from cognitive maps';
COMMENT ON TABLE maba_tasks IS 'Tasks executed by MABA';
COMMENT ON TABLE maba_metrics IS 'Performance and operational metrics';

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions to application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO maba_service;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO maba_service;

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
