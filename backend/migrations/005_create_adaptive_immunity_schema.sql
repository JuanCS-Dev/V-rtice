-- Migration 005: Create Adaptive Immunity Schema
-- Data: 2025-10-19
-- Objetivo: Consolidar infraestrutura do sistema imunológico adaptativo

-- ==================== SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS adaptive_immunity;

-- Grant permissions
GRANT ALL ON SCHEMA adaptive_immunity TO postgres;
GRANT USAGE ON SCHEMA adaptive_immunity TO vertice;

-- ==================== AGENTS TABLE ====================
CREATE TABLE IF NOT EXISTS adaptive_immunity.agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_type VARCHAR(30) NOT NULL CHECK (agent_type IN ('neutrophil', 'macrofago', 'dendritic', 'cytotoxic_t', 'treg', 'nk_cell', 'b_cell', 'helper_t')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'compromised', 'healing', 'apoptotic')),
    activation_level FLOAT DEFAULT 0.5 CHECK (activation_level BETWEEN 0 AND 1),
    last_seen TIMESTAMP DEFAULT NOW(),
    metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE adaptive_immunity.agents IS 'Registro de todos os agentes imunológicos do sistema';
COMMENT ON COLUMN adaptive_immunity.agents.activation_level IS 'Nível de ativação do agente (0=inativo, 1=máxima ativação)';

-- ==================== APVs (ANOMALY PATCH VECTORS) ====================
CREATE TABLE IF NOT EXISTS adaptive_immunity.apvs (
    id SERIAL PRIMARY KEY,
    apv_signature TEXT NOT NULL UNIQUE,
    patch_code TEXT NOT NULL,
    vulnerability_pattern TEXT NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    deployment_status VARCHAR(20) DEFAULT 'pending' CHECK (deployment_status IN ('pending', 'deployed', 'reverted', 'deprecated')),
    created_at TIMESTAMP DEFAULT NOW(),
    deployed_at TIMESTAMP,
    reverted_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id) ON DELETE SET NULL,
    threat_id VARCHAR(100),
    efficacy_score FLOAT CHECK (efficacy_score BETWEEN 0 AND 1)
);

COMMENT ON TABLE adaptive_immunity.apvs IS 'Anomaly Patch Vectors - patches gerados pelo sistema imunológico';
COMMENT ON COLUMN adaptive_immunity.apvs.confidence_score IS 'Confiança na eficácia do patch (0-1)';
COMMENT ON COLUMN adaptive_immunity.apvs.efficacy_score IS 'Eficácia medida após deployment (0-1)';

-- ==================== CYTOKINES (INTER-AGENT MESSAGES) ====================
CREATE TABLE IF NOT EXISTS adaptive_immunity.cytokines (
    id SERIAL PRIMARY KEY,
    cytokine_type VARCHAR(50) NOT NULL,
    source_agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id),
    target_agent_id VARCHAR(50),
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    consumed_at TIMESTAMP,
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical'))
);

COMMENT ON TABLE adaptive_immunity.cytokines IS 'Mensagens de comunicação entre agentes (cytokine signaling)';

-- ==================== THREATS LOG ====================
CREATE TABLE IF NOT EXISTS adaptive_immunity.threats (
    id SERIAL PRIMARY KEY,
    threat_id VARCHAR(100) UNIQUE NOT NULL,
    threat_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    source_ip INET,
    source_system VARCHAR(100),
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'analyzing', 'responding', 'resolved', 'ignored')),
    metadata JSONB DEFAULT '{}'::jsonb,
    response_strategy TEXT
);

COMMENT ON TABLE adaptive_immunity.threats IS 'Log de threats detectados pelo Reactive Fabric e processados pelo sistema imunológico';

-- ==================== AUDIT LOG ====================
CREATE TABLE IF NOT EXISTS adaptive_immunity.audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id),
    apv_id INTEGER REFERENCES adaptive_immunity.apvs(id),
    threat_id VARCHAR(100) REFERENCES adaptive_immunity.threats(threat_id),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical'))
);

COMMENT ON TABLE adaptive_immunity.audit_log IS 'Auditoria de todas as ações do sistema imunológico';

-- ==================== INDEXES ====================

-- Agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_type ON adaptive_immunity.agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON adaptive_immunity.agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_last_seen ON adaptive_immunity.agents(last_seen DESC);

-- APVs indexes
CREATE INDEX IF NOT EXISTS idx_apvs_signature ON adaptive_immunity.apvs(apv_signature);
CREATE INDEX IF NOT EXISTS idx_apvs_status ON adaptive_immunity.apvs(deployment_status);
CREATE INDEX IF NOT EXISTS idx_apvs_agent_id ON adaptive_immunity.apvs(agent_id);
CREATE INDEX IF NOT EXISTS idx_apvs_threat_id ON adaptive_immunity.apvs(threat_id);
CREATE INDEX IF NOT EXISTS idx_apvs_created_at ON adaptive_immunity.apvs(created_at DESC);

-- Cytokines indexes
CREATE INDEX IF NOT EXISTS idx_cytokines_target ON adaptive_immunity.cytokines(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_cytokines_type ON adaptive_immunity.cytokines(cytokine_type);
CREATE INDEX IF NOT EXISTS idx_cytokines_consumed_at ON adaptive_immunity.cytokines(consumed_at);
CREATE INDEX IF NOT EXISTS idx_cytokines_priority ON adaptive_immunity.cytokines(priority);

-- Threats indexes
CREATE INDEX IF NOT EXISTS idx_threats_type ON adaptive_immunity.threats(threat_type);
CREATE INDEX IF NOT EXISTS idx_threats_severity ON adaptive_immunity.threats(severity);
CREATE INDEX IF NOT EXISTS idx_threats_status ON adaptive_immunity.threats(status);
CREATE INDEX IF NOT EXISTS idx_threats_detected_at ON adaptive_immunity.threats(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_threats_source_ip ON adaptive_immunity.threats(source_ip);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_event ON adaptive_immunity.audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_agent ON adaptive_immunity.audit_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_apv ON adaptive_immunity.audit_log(apv_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_threat ON adaptive_immunity.audit_log(threat_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON adaptive_immunity.audit_log(created_at DESC);

-- ==================== FUNCTIONS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION adaptive_immunity.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for agents table
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON adaptive_immunity.agents
    FOR EACH ROW
    EXECUTE FUNCTION adaptive_immunity.update_updated_at_column();

-- ==================== VIEWS ====================

-- View: Active agents summary
CREATE OR REPLACE VIEW adaptive_immunity.active_agents_summary AS
SELECT 
    agent_type,
    COUNT(*) as total,
    AVG(activation_level) as avg_activation,
    MAX(last_seen) as last_active
FROM adaptive_immunity.agents
WHERE status = 'active'
GROUP BY agent_type;

COMMENT ON VIEW adaptive_immunity.active_agents_summary IS 'Sumário de agentes ativos por tipo';

-- View: Pending APVs
CREATE OR REPLACE VIEW adaptive_immunity.pending_apvs AS
SELECT 
    apv_signature,
    vulnerability_pattern,
    confidence_score,
    created_at,
    agent_id
FROM adaptive_immunity.apvs
WHERE deployment_status = 'pending'
ORDER BY confidence_score DESC, created_at ASC;

COMMENT ON VIEW adaptive_immunity.pending_apvs IS 'APVs pendentes de deployment ordenados por confiança';

-- View: Unresolved threats
CREATE OR REPLACE VIEW adaptive_immunity.unresolved_threats AS
SELECT 
    threat_id,
    threat_type,
    severity,
    source_ip,
    detected_at,
    status,
    EXTRACT(EPOCH FROM (NOW() - detected_at)) / 60 as minutes_since_detection
FROM adaptive_immunity.threats
WHERE status IN ('new', 'analyzing', 'responding')
ORDER BY severity DESC, detected_at ASC;

COMMENT ON VIEW adaptive_immunity.unresolved_threats IS 'Threats não resolvidos com tempo desde detecção';

-- ==================== INITIAL DATA ====================

-- Insert default agents (não ativos, apenas registro)
INSERT INTO adaptive_immunity.agents (agent_id, agent_type, status, activation_level, metrics)
VALUES 
    ('neutrophil_001', 'neutrophil', 'inactive', 0.0, '{"deployment": "pending"}'::jsonb),
    ('macrofago_001', 'macrofago', 'inactive', 0.0, '{"deployment": "pending"}'::jsonb),
    ('dendritic_001', 'dendritic', 'inactive', 0.0, '{"deployment": "pending"}'::jsonb),
    ('cytotoxic_t_001', 'cytotoxic_t', 'inactive', 0.0, '{"deployment": "pending"}'::jsonb),
    ('treg_001', 'treg', 'inactive', 0.0, '{"deployment": "pending"}'::jsonb)
ON CONFLICT (agent_id) DO NOTHING;

-- ==================== SUCCESS MESSAGE ====================
DO $$
BEGIN
    RAISE NOTICE '✅ Schema adaptive_immunity created successfully';
    RAISE NOTICE '✅ 5 tables created: agents, apvs, cytokines, threats, audit_log';
    RAISE NOTICE '✅ 3 views created: active_agents_summary, pending_apvs, unresolved_threats';
    RAISE NOTICE '✅ 15 indexes created';
    RAISE NOTICE '✅ 5 default agents registered';
END $$;
