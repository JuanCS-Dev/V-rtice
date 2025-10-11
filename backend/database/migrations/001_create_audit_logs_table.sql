-- =====================================================================
-- Audit Logs Table Migration
-- =====================================================================
-- 
-- Purpose: Create comprehensive audit logging table for compliance
-- Issue: #36 - Comprehensive audit logging
-- Standards: SOC 2, ISO 27001, PCI-DSS
-- Retention: 365 days (1 year)
--
-- Security Features:
-- - Immutable audit trail (INSERT only, no UPDATE/DELETE)
-- - Indexed for fast queries
-- - JSONB for flexible detail storage
-- - Timestamp tracking (creation + event time)
-- - IP address tracking (INET type)
--
-- Usage:
--   psql -U vertice -d vertice_audit -f 001_create_audit_logs_table.sql
--

-- Create audit database if not exists
CREATE DATABASE IF NOT EXISTS vertice_audit;

-- Connect to audit database
\c vertice_audit;

-- =====================================================================
-- Main Audit Logs Table
-- =====================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Timestamp (event occurrence time)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(100),
    resource VARCHAR(255),
    
    -- User identification
    user_id INTEGER,
    username VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Network details
    ip_address INET,
    user_agent TEXT,
    
    -- Request tracking
    request_id VARCHAR(255),
    
    -- Event outcome
    success BOOLEAN,
    severity VARCHAR(20),
    
    -- Additional context (flexible JSON)
    details JSONB,
    
    -- Record creation (immutable)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- Indexes for Performance
-- =====================================================================

-- Most common query: recent events
CREATE INDEX idx_audit_logs_timestamp 
    ON audit_logs(timestamp DESC);

-- User activity queries
CREATE INDEX idx_audit_logs_user_id 
    ON audit_logs(user_id) 
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_audit_logs_username 
    ON audit_logs(username) 
    WHERE username IS NOT NULL;

-- Event type filtering
CREATE INDEX idx_audit_logs_event_type 
    ON audit_logs(event_type);

-- Severity filtering (security incidents)
CREATE INDEX idx_audit_logs_severity 
    ON audit_logs(severity) 
    WHERE severity IN ('warning', 'error', 'critical');

-- IP address tracking (suspicious activity)
CREATE INDEX idx_audit_logs_ip_address 
    ON audit_logs(ip_address) 
    WHERE ip_address IS NOT NULL;

-- Request tracing
CREATE INDEX idx_audit_logs_request_id 
    ON audit_logs(request_id) 
    WHERE request_id IS NOT NULL;

-- Session tracking
CREATE INDEX idx_audit_logs_session_id 
    ON audit_logs(session_id) 
    WHERE session_id IS NOT NULL;

-- JSONB details (GIN index for flexible queries)
CREATE INDEX idx_audit_logs_details 
    ON audit_logs USING GIN (details);

-- =====================================================================
-- Partitioning (for large-scale deployments)
-- =====================================================================

-- Create partitions by month (optional, for >10M records)
-- Uncomment if needed:
--
-- CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
-- 
-- CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs
--     FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- =====================================================================
-- Retention Policy (Auto-delete old records)
-- =====================================================================

-- Function to delete old audit logs
CREATE OR REPLACE FUNCTION delete_old_audit_logs(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule daily cleanup (requires pg_cron extension)
-- Uncomment if pg_cron is installed:
--
-- SELECT cron.schedule(
--     'cleanup-old-audit-logs',
--     '0 3 * * *',  -- 3 AM daily
--     'SELECT delete_old_audit_logs(365);'
-- );

-- =====================================================================
-- Security: Prevent Modifications (INSERT-only)
-- =====================================================================

-- Revoke UPDATE and DELETE permissions
-- (Adjust user/role as needed)
-- REVOKE UPDATE, DELETE ON audit_logs FROM public;
-- GRANT SELECT, INSERT ON audit_logs TO vertice_app;

-- =====================================================================
-- Views for Common Queries
-- =====================================================================

-- Recent security events
CREATE OR REPLACE VIEW recent_security_events AS
SELECT 
    id,
    timestamp,
    event_type,
    username,
    ip_address,
    action,
    resource,
    severity,
    details
FROM audit_logs
WHERE severity IN ('warning', 'error', 'critical')
ORDER BY timestamp DESC
LIMIT 1000;

-- Failed authentication attempts
CREATE OR REPLACE VIEW failed_auth_attempts AS
SELECT 
    timestamp,
    username,
    ip_address,
    details->>'method' AS auth_method,
    details
FROM audit_logs
WHERE event_type = 'AUTH_FAILURE'
ORDER BY timestamp DESC
LIMIT 1000;

-- User activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT 
    user_id,
    username,
    COUNT(*) AS total_events,
    COUNT(CASE WHEN success = true THEN 1 END) AS successful_events,
    COUNT(CASE WHEN success = false THEN 1 END) AS failed_events,
    MIN(timestamp) AS first_seen,
    MAX(timestamp) AS last_seen
FROM audit_logs
WHERE user_id IS NOT NULL
GROUP BY user_id, username
ORDER BY total_events DESC;

-- =====================================================================
-- Sample Data (for testing)
-- =====================================================================

-- Insert sample audit logs
INSERT INTO audit_logs (
    timestamp, event_type, user_id, username, ip_address,
    action, resource, details, success, severity
) VALUES
    (NOW(), 'AUTH_SUCCESS', 1, 'admin', '192.168.1.1', 'login', 'auth_system', '{"method": "password"}', true, 'info'),
    (NOW(), 'DATA_ACCESS', 1, 'admin', '192.168.1.1', 'read', 'api_keys', '{"sensitive": true}', true, 'warning'),
    (NOW(), 'CONFIG_CHANGE', 1, 'admin', '192.168.1.1', 'update', 'rate_limit', '{"old_value": "100", "new_value": "200"}', true, 'warning'),
    (NOW(), 'TOOL_EXECUTION', 2, 'analyst', '192.168.1.2', 'execute', 'nmap', '{"target": "192.168.1.0/24"}', true, 'warning'),
    (NOW(), 'AUTH_FAILURE', NULL, 'hacker', '1.2.3.4', 'login', 'auth_system', '{"method": "password", "attempts": 10}', false, 'error');

-- =====================================================================
-- Verification
-- =====================================================================

-- Check table creation
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename = 'audit_logs';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'audit_logs';

-- Check views
SELECT viewname
FROM pg_views
WHERE viewname LIKE '%audit%' OR viewname LIKE '%auth%';

-- Count records
SELECT 
    COUNT(*) AS total_records,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT event_type) AS unique_event_types,
    MIN(timestamp) AS oldest_event,
    MAX(timestamp) AS newest_event
FROM audit_logs;

-- =====================================================================
-- Rollback (if needed)
-- =====================================================================

-- DROP TABLE IF EXISTS audit_logs CASCADE;
-- DROP VIEW IF EXISTS recent_security_events;
-- DROP VIEW IF EXISTS failed_auth_attempts;
-- DROP VIEW IF EXISTS user_activity_summary;
-- DROP FUNCTION IF EXISTS delete_old_audit_logs(INTEGER);

-- =====================================================================
-- Migration Complete
-- =====================================================================

\echo '✅ Audit logs table created successfully!'
\echo 'Total indexes:', (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'audit_logs');
\echo 'Total views:', (SELECT COUNT(*) FROM pg_views WHERE viewname LIKE '%audit%' OR viewname LIKE '%auth%');
