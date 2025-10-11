-- Migration: Add wargaming_results table for ML training
-- Purpose: Store wargaming execution results with extracted features
-- Date: 2025-10-11
-- Phase: 5.1 - ML Data Collection

-- ============================================================================
-- TABLE: wargaming_results
-- ============================================================================
-- Stores results from two-phase wargaming for ML model training.
-- Each row = one exploit execution against one APV+patch combination.

CREATE TABLE IF NOT EXISTS wargaming_results (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- References
    apv_id INTEGER NOT NULL,  -- References apvs(id) when table exists
    patch_id INTEGER NOT NULL,  -- References patches(id) when table exists
    
    -- Exploit information
    exploit_cwe VARCHAR(50) NOT NULL,  -- e.g., "CWE-89"
    exploit_name VARCHAR(200) NOT NULL,  -- e.g., "SQL Injection Union-based"
    
    -- Wargaming results
    phase1_result VARCHAR(20) NOT NULL CHECK (phase1_result IN ('success', 'blocked', 'error')),
    phase2_result VARCHAR(20) NOT NULL CHECK (phase2_result IN ('success', 'blocked', 'error')),
    patch_validated BOOLEAN NOT NULL,  -- True if patch passed validation
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    
    -- ML Features (extracted from patch)
    -- Basic metrics
    lines_added INTEGER NOT NULL DEFAULT 0,
    lines_removed INTEGER NOT NULL DEFAULT 0,
    files_modified INTEGER NOT NULL DEFAULT 0,
    
    -- Complexity
    complexity_delta FLOAT NOT NULL DEFAULT 0.0,
    
    -- Security patterns (boolean as int: 0/1)
    has_input_validation BOOLEAN NOT NULL DEFAULT FALSE,
    has_sanitization BOOLEAN NOT NULL DEFAULT FALSE,
    has_encoding BOOLEAN NOT NULL DEFAULT FALSE,
    has_parameterization BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: one result per APV+patch+exploit combo
    UNIQUE(apv_id, patch_id, exploit_cwe)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Query by APV
CREATE INDEX IF NOT EXISTS idx_wargaming_results_apv 
ON wargaming_results(apv_id);

-- Query by patch
CREATE INDEX IF NOT EXISTS idx_wargaming_results_patch 
ON wargaming_results(patch_id);

-- Query validated patches (for training)
CREATE INDEX IF NOT EXISTS idx_wargaming_results_validated 
ON wargaming_results(patch_validated);

-- Query by CWE type
CREATE INDEX IF NOT EXISTS idx_wargaming_results_cwe 
ON wargaming_results(exploit_cwe);

-- Query by creation date (for incremental training)
CREATE INDEX IF NOT EXISTS idx_wargaming_results_created 
ON wargaming_results(created_at DESC);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE wargaming_results IS 
'Wargaming execution results for ML model training. Each row = one exploit test.';

COMMENT ON COLUMN wargaming_results.apv_id IS 
'ID of the APV (Active Potential Vulnerability) being tested';

COMMENT ON COLUMN wargaming_results.patch_id IS 
'ID of the patch being validated';

COMMENT ON COLUMN wargaming_results.exploit_cwe IS 
'CWE identifier of the exploit (e.g., CWE-89 for SQL Injection)';

COMMENT ON COLUMN wargaming_results.phase1_result IS 
'Phase 1 result: exploit vs vulnerable version. Expected: success';

COMMENT ON COLUMN wargaming_results.phase2_result IS 
'Phase 2 result: exploit vs patched version. Expected: blocked';

COMMENT ON COLUMN wargaming_results.patch_validated IS 
'True if patch passed both phases (Phase1=success, Phase2=blocked)';

COMMENT ON COLUMN wargaming_results.lines_added IS 
'Number of lines added in patch (from git diff)';

COMMENT ON COLUMN wargaming_results.complexity_delta IS 
'Change in cyclomatic complexity (added - removed control flow)';

COMMENT ON COLUMN wargaming_results.has_input_validation IS 
'Patch contains input validation patterns (if/assert/raise)';

COMMENT ON COLUMN wargaming_results.has_sanitization IS 
'Patch contains sanitization patterns (escape/strip/clean)';

COMMENT ON COLUMN wargaming_results.has_encoding IS 
'Patch contains encoding patterns (encode/quote/escape)';

COMMENT ON COLUMN wargaming_results.has_parameterization IS 
'Patch contains parameterized query patterns (?, prepared statements)';

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Export dataset for ML training
-- SELECT 
--     lines_added, lines_removed, files_modified,
--     complexity_delta,
--     has_input_validation::int, has_sanitization::int,
--     has_encoding::int, has_parameterization::int,
--     exploit_cwe,
--     patch_validated::int as label
-- FROM wargaming_results
-- WHERE execution_time_ms > 0  -- Valid executions only
-- ORDER BY created_at DESC;

-- Get validation success rate by CWE
-- SELECT 
--     exploit_cwe,
--     COUNT(*) as total,
--     SUM(CASE WHEN patch_validated THEN 1 ELSE 0 END) as validated,
--     ROUND(100.0 * SUM(CASE WHEN patch_validated THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate_pct
-- FROM wargaming_results
-- GROUP BY exploit_cwe
-- ORDER BY success_rate_pct DESC;

-- Get feature importance (avg by validated vs invalid)
-- SELECT 
--     patch_validated,
--     AVG(has_input_validation::int) as avg_validation,
--     AVG(has_sanitization::int) as avg_sanitization,
--     AVG(has_encoding::int) as avg_encoding,
--     AVG(has_parameterization::int) as avg_parameterization
-- FROM wargaming_results
-- GROUP BY patch_validated;
