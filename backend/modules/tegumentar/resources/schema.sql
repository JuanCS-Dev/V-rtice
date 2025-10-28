-- Tegumentar Database Schema
-- PostgreSQL + TimescaleDB for Derme layer (stateful inspection)
--
-- Armazena antígenos capturados por Langerhans cells para análise
-- adaptativa e aprendizado do sistema imune digital.

-- Criar database (se não existir)
-- Executar como superuser: psql -U postgres -c "CREATE DATABASE tegumentar;"

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- TimescaleDB (opcional, mas recomendado para time-series)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Tabela de antígenos capturados
CREATE TABLE IF NOT EXISTS tegumentar_antigens (
    -- Identificador único do antígeno
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Origem do antígeno
    source_ip INET NOT NULL,
    destination_ip INET NOT NULL,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(10) NOT NULL,  -- TCP, UDP, ICMP, etc.

    -- Payload e assinaturas
    payload_hash VARCHAR(128) NOT NULL,  -- SHA-256 do payload
    payload_sample BYTEA,  -- Primeiros 512 bytes do payload (opcional)

    -- Detecção e classificação
    signatures_matched TEXT[],  -- IDs das assinaturas que bateram
    ml_anomaly_score REAL,  -- Score do modelo ML (0.0 a 1.0)
    threat_severity VARCHAR(20),  -- low, medium, high, critical

    -- Metadados
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_by_lymphnode BOOLEAN DEFAULT FALSE,
    vaccination_broadcast BOOLEAN DEFAULT FALSE,

    -- Features extraídas para ML
    features JSONB,  -- Features do FeatureExtractor

    -- Resposta aplicada
    action_taken VARCHAR(50),  -- block_ip, rate_limit, alert, etc.
    action_metadata JSONB,

    -- Índices para consultas rápidas
    CONSTRAINT valid_anomaly_score CHECK (ml_anomaly_score >= 0.0 AND ml_anomaly_score <= 1.0),
    CONSTRAINT valid_severity CHECK (threat_severity IN ('low', 'medium', 'high', 'critical'))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_antigens_source_ip ON tegumentar_antigens(source_ip);
CREATE INDEX IF NOT EXISTS idx_antigens_captured_at ON tegumentar_antigens(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_antigens_severity ON tegumentar_antigens(threat_severity);
CREATE INDEX IF NOT EXISTS idx_antigens_anomaly_score ON tegumentar_antigens(ml_anomaly_score DESC);
CREATE INDEX IF NOT EXISTS idx_antigens_payload_hash ON tegumentar_antigens(payload_hash);

-- Índice GIN para arrays e JSONB
CREATE INDEX IF NOT EXISTS idx_antigens_signatures ON tegumentar_antigens USING GIN(signatures_matched);
CREATE INDEX IF NOT EXISTS idx_antigens_features ON tegumentar_antigens USING GIN(features);

-- Converter para hypertable TimescaleDB (se extensão estiver instalada)
-- SELECT create_hypertable('tegumentar_antigens', 'captured_at', if_not_exists => TRUE);

-- View para estatísticas agregadas
CREATE OR REPLACE VIEW tegumentar_antigen_stats AS
SELECT
    DATE_TRUNC('hour', captured_at) AS hour,
    threat_severity,
    COUNT(*) AS antigen_count,
    AVG(ml_anomaly_score) AS avg_anomaly_score,
    COUNT(DISTINCT source_ip) AS unique_sources
FROM tegumentar_antigens
WHERE captured_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', captured_at), threat_severity
ORDER BY hour DESC, threat_severity;

-- View para top atacantes
CREATE OR REPLACE VIEW tegumentar_top_attackers AS
SELECT
    source_ip,
    COUNT(*) AS attack_count,
    MAX(threat_severity) AS max_severity,
    MAX(ml_anomaly_score) AS max_anomaly_score,
    MAX(captured_at) AS last_seen
FROM tegumentar_antigens
WHERE captured_at > NOW() - INTERVAL '7 days'
GROUP BY source_ip
ORDER BY attack_count DESC
LIMIT 100;

-- Comentários para documentação
COMMENT ON TABLE tegumentar_antigens IS 'Antígenos capturados pela camada Derme do Tegumentar (Langerhans cells digitais)';
COMMENT ON COLUMN tegumentar_antigens.ml_anomaly_score IS 'Score de anomalia do modelo ML (0.0=normal, 1.0=altamente anômalo)';
COMMENT ON COLUMN tegumentar_antigens.signatures_matched IS 'Array de IDs de assinaturas que identificaram esta ameaça';
COMMENT ON COLUMN tegumentar_antigens.payload_sample IS 'Primeiros 512 bytes do payload para análise forense (base64 encoded)';
COMMENT ON COLUMN tegumentar_antigens.validated_by_lymphnode IS 'Se o antígeno foi validado pelo Linfonodo Digital como ameaça real';
COMMENT ON COLUMN tegumentar_antigens.vaccination_broadcast IS 'Se as regras de vacinação foram broadcast para toda a rede';

-- Grants (ajustar conforme usuário da aplicação)
-- GRANT SELECT, INSERT, UPDATE ON tegumentar_antigens TO tegumentar_app;
-- GRANT SELECT ON tegumentar_antigen_stats TO tegumentar_app;
-- GRANT SELECT ON tegumentar_top_attackers TO tegumentar_app;
