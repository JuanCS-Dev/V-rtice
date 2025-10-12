-- Reactive Fabric PostgreSQL Schema
-- Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
-- Sprint 1: Database Schema

-- Create schema
CREATE SCHEMA IF NOT EXISTS reactive_fabric;

-- Set search path
SET search_path TO reactive_fabric, public;

-- ============================================================================
-- HONEYPOTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS honeypots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    honeypot_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'ssh_001', 'web_001'
    type VARCHAR(50) NOT NULL,                 -- 'ssh', 'web', 'api'
    container_name VARCHAR(100) NOT NULL,
    port INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'offline',      -- 'online', 'offline', 'degraded'
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_honeypots_honeypot_id ON honeypots(honeypot_id);
CREATE INDEX idx_honeypots_type ON honeypots(type);
CREATE INDEX idx_honeypots_status ON honeypots(status);

-- ============================================================================
-- ATTACKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS attacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    honeypot_id UUID REFERENCES honeypots(id) ON DELETE CASCADE,
    attacker_ip INET NOT NULL,
    attack_type VARCHAR(100) NOT NULL,         -- 'brute_force', 'sql_injection', etc.
    severity VARCHAR(20) NOT NULL,             -- 'low', 'medium', 'high', 'critical'
    confidence FLOAT DEFAULT 1.0,
    ttps JSONB DEFAULT '[]'::jsonb,            -- Array of MITRE ATT&CK technique IDs
    iocs JSONB DEFAULT '{}'::jsonb,            -- IoCs: {ips: [], domains: [], hashes: []}
    payload TEXT,                              -- Attack payload (sanitized)
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_attacks_honeypot_id ON attacks(honeypot_id);
CREATE INDEX idx_attacks_attacker_ip ON attacks(attacker_ip);
CREATE INDEX idx_attacks_attack_type ON attacks(attack_type);
CREATE INDEX idx_attacks_severity ON attacks(severity);
CREATE INDEX idx_attacks_captured_at ON attacks(captured_at DESC);
CREATE INDEX idx_attacks_ttps ON attacks USING GIN(ttps);

-- ============================================================================
-- TTPS TABLE (MITRE ATT&CK Techniques)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ttps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technique_id VARCHAR(20) UNIQUE NOT NULL,  -- e.g., 'T1110', 'T1190'
    technique_name VARCHAR(200) NOT NULL,
    tactic VARCHAR(100),                       -- 'Initial Access', 'Execution', etc.
    description TEXT,
    observed_count INTEGER DEFAULT 0,
    first_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_observed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_ttps_technique_id ON ttps(technique_id);
CREATE INDEX idx_ttps_observed_count ON ttps(observed_count DESC);
CREATE INDEX idx_ttps_last_observed ON ttps(last_observed DESC);

-- ============================================================================
-- IOCS TABLE (Indicators of Compromise)
-- ============================================================================
CREATE TABLE IF NOT EXISTS iocs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ioc_type VARCHAR(50) NOT NULL,            -- 'ip', 'domain', 'hash', 'email', 'username'
    ioc_value TEXT NOT NULL,
    threat_level VARCHAR(20) DEFAULT 'unknown', -- 'low', 'medium', 'high', 'critical'
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    occurrences INTEGER DEFAULT 1,
    associated_attacks UUID[] DEFAULT '{}',    -- Array of attack IDs
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_iocs_type ON iocs(ioc_type);
CREATE INDEX idx_iocs_value ON iocs(ioc_value);
CREATE INDEX idx_iocs_threat_level ON iocs(threat_level);
CREATE INDEX idx_iocs_last_seen ON iocs(last_seen DESC);

-- ============================================================================
-- FORENSIC_CAPTURES TABLE (Track processed captures)
-- ============================================================================
CREATE TABLE IF NOT EXISTS forensic_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    honeypot_id UUID REFERENCES honeypots(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,           -- 'cowrie_json', 'pcap', 'apache_log'
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),                    -- SHA256 hash
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    attacks_extracted INTEGER DEFAULT 0,
    ttps_extracted INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_forensic_captures_honeypot_id ON forensic_captures(honeypot_id);
CREATE INDEX idx_forensic_captures_processing_status ON forensic_captures(processing_status);
CREATE INDEX idx_forensic_captures_captured_at ON forensic_captures(captured_at DESC);
CREATE INDEX idx_forensic_captures_file_hash ON forensic_captures(file_hash);

-- ============================================================================
-- METRICS TABLE (Aggregated metrics for dashboards)
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    honeypot_id UUID REFERENCES honeypots(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,        -- 'connections', 'attacks', 'unique_ips', etc.
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL, -- For time-series data
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_metrics_honeypot_id ON metrics(honeypot_id);
CREATE INDEX idx_metrics_type ON metrics(metric_type);
CREATE INDEX idx_metrics_time_bucket ON metrics(time_bucket DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for honeypots table
CREATE TRIGGER update_honeypots_updated_at
    BEFORE UPDATE ON honeypots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to increment TTP observed count
CREATE OR REPLACE FUNCTION increment_ttp_count()
RETURNS TRIGGER AS $$
DECLARE
    ttp_id TEXT;
BEGIN
    -- Loop through TTPs in new attack
    FOR ttp_id IN SELECT jsonb_array_elements_text(NEW.ttps)
    LOOP
        INSERT INTO ttps (technique_id, technique_name, observed_count, last_observed)
        VALUES (ttp_id, 'Unknown', 1, NEW.captured_at)
        ON CONFLICT (technique_id) DO UPDATE SET
            observed_count = ttps.observed_count + 1,
            last_observed = NEW.captured_at;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update TTP counts when attack is inserted
CREATE TRIGGER update_ttp_counts_on_attack
    AFTER INSERT ON attacks
    FOR EACH ROW
    EXECUTE FUNCTION increment_ttp_count();

-- ============================================================================
-- SEED DATA (Initial honeypots)
-- ============================================================================
INSERT INTO honeypots (honeypot_id, type, container_name, port, status, config)
VALUES 
    ('ssh_001', 'ssh', 'reactive-fabric-honeypot-ssh', 2222, 'offline', '{"backend": "cowrie"}'::jsonb),
    ('web_001', 'web', 'reactive-fabric-honeypot-web', 8080, 'offline', '{"backend": "apache_php"}'::jsonb),
    ('api_001', 'api', 'reactive-fabric-honeypot-api', 8081, 'offline', '{"backend": "fastapi"}'::jsonb)
ON CONFLICT (honeypot_id) DO NOTHING;

-- ============================================================================
-- VIEWS (For common queries)
-- ============================================================================

-- View: Honeypot stats (attacks per honeypot)
CREATE OR REPLACE VIEW honeypot_stats AS
SELECT 
    h.id,
    h.honeypot_id,
    h.type,
    h.status,
    COUNT(a.id) AS total_attacks,
    COUNT(DISTINCT a.attacker_ip) AS unique_ips,
    MAX(a.captured_at) AS last_attack,
    COALESCE(SUM(CASE WHEN a.severity = 'critical' THEN 1 ELSE 0 END), 0) AS critical_attacks,
    COALESCE(SUM(CASE WHEN a.severity = 'high' THEN 1 ELSE 0 END), 0) AS high_attacks
FROM honeypots h
LEFT JOIN attacks a ON h.id = a.honeypot_id
GROUP BY h.id, h.honeypot_id, h.type, h.status;

-- View: Top attackers
CREATE OR REPLACE VIEW top_attackers AS
SELECT 
    attacker_ip,
    COUNT(*) AS attack_count,
    ARRAY_AGG(DISTINCT attack_type) AS attack_types,
    MAX(captured_at) AS last_attack,
    MAX(severity) AS max_severity
FROM attacks
GROUP BY attacker_ip
ORDER BY attack_count DESC;

-- View: TTP frequency
CREATE OR REPLACE VIEW ttp_frequency AS
SELECT 
    t.technique_id,
    t.technique_name,
    t.tactic,
    t.observed_count,
    t.last_observed,
    COUNT(DISTINCT a.honeypot_id) AS affected_honeypots
FROM ttps t
LEFT JOIN attacks a ON a.ttps @> jsonb_build_array(t.technique_id)
GROUP BY t.technique_id, t.technique_name, t.tactic, t.observed_count, t.last_observed
ORDER BY t.observed_count DESC;

-- ============================================================================
-- GRANTS (Adjust as needed for production)
-- ============================================================================
-- GRANT USAGE ON SCHEMA reactive_fabric TO vertice_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA reactive_fabric TO vertice_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA reactive_fabric TO vertice_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON SCHEMA reactive_fabric IS 'Reactive Fabric honeypot threat intelligence schema';
COMMENT ON TABLE honeypots IS 'Registered honeypots with status and configuration';
COMMENT ON TABLE attacks IS 'Detected attacks with TTPs and IoCs';
COMMENT ON TABLE ttps IS 'MITRE ATT&CK techniques observed across honeypots';
COMMENT ON TABLE iocs IS 'Indicators of Compromise aggregated across attacks';
COMMENT ON TABLE forensic_captures IS 'Tracking of processed forensic capture files';
COMMENT ON TABLE metrics IS 'Time-series metrics for dashboards';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
