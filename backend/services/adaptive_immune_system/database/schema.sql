-- =========================================================================
-- ADAPTIVE IMMUNE SYSTEM - DATABASE SCHEMA
-- =========================================================================
-- Description: Complete database schema for Oráculo-Eureka-Wargaming-HITL
-- Version: 1.0.0
-- Date: 2025-10-13
-- =========================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- =========================================================================
-- TABLE: threats
-- Description: CVE data from multiple feeds (NVD, GHSA, OSV)
-- =========================================================================
CREATE TABLE IF NOT EXISTS threats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identification
    cve_id VARCHAR(20) UNIQUE NOT NULL,  -- CVE-YYYY-NNNNN
    source VARCHAR(50) NOT NULL,  -- 'nvd', 'ghsa', 'osv'

    -- Metadata
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    published_date TIMESTAMP NOT NULL,
    last_modified_date TIMESTAMP NOT NULL,

    -- Severity
    cvss_score NUMERIC(3,1),  -- 0.0 to 10.0
    cvss_vector TEXT,
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'

    -- Affected ecosystems and packages
    ecosystems TEXT[],  -- ['npm', 'pypi', 'cargo']
    affected_packages JSONB,  -- [{"name": "lodash", "version": "4.17.20", "ecosystem": "npm"}]

    -- Technical details
    cwe_ids TEXT[],  -- ['CWE-79', 'CWE-89']
    references JSONB,  -- [{"url": "...", "type": "advisory"}]

    -- Status
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'triaged', 'ignored', 'processed'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for performance
    CHECK (cvss_score IS NULL OR (cvss_score >= 0 AND cvss_score <= 10)),
    CHECK (source IN ('nvd', 'ghsa', 'osv', 'other'))
);

CREATE INDEX idx_threats_cve_id ON threats(cve_id);
CREATE INDEX idx_threats_source ON threats(source);
CREATE INDEX idx_threats_status ON threats(status);
CREATE INDEX idx_threats_severity ON threats(severity);
CREATE INDEX idx_threats_published_date ON threats(published_date DESC);
CREATE INDEX idx_threats_cvss_score ON threats(cvss_score DESC);
CREATE INDEX idx_threats_ecosystems ON threats USING gin(ecosystems);
CREATE INDEX idx_threats_affected_packages ON threats USING gin(affected_packages);

-- =========================================================================
-- TABLE: dependencies
-- Description: Inventory of all dependencies across projects
-- =========================================================================
CREATE TABLE IF NOT EXISTS dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Project context
    project_name VARCHAR(255) NOT NULL,
    project_path TEXT NOT NULL,

    -- Package identification
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(100) NOT NULL,
    ecosystem VARCHAR(50) NOT NULL,  -- 'npm', 'pypi', 'cargo', 'go', 'docker'

    -- Metadata
    direct_dependency BOOLEAN DEFAULT TRUE,  -- False if transitive
    parent_package VARCHAR(255),  -- If transitive, who requires it

    -- Location
    manifest_file TEXT,  -- 'package.json', 'requirements.txt', 'Cargo.toml'

    -- Timestamps
    scanned_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(project_name, package_name, package_version, ecosystem)
);

CREATE INDEX idx_dependencies_project_name ON dependencies(project_name);
CREATE INDEX idx_dependencies_package_name ON dependencies(package_name);
CREATE INDEX idx_dependencies_ecosystem ON dependencies(ecosystem);
CREATE INDEX idx_dependencies_scanned_at ON dependencies(scanned_at DESC);

-- =========================================================================
-- TABLE: apvs (Ameaça Potencial Verificada)
-- Description: Matched vulnerabilities to our dependencies
-- =========================================================================
CREATE TABLE IF NOT EXISTS apvs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- References
    threat_id UUID NOT NULL REFERENCES threats(id) ON DELETE CASCADE,
    dependency_id UUID NOT NULL REFERENCES dependencies(id) ON DELETE CASCADE,

    -- APV metadata
    apv_code VARCHAR(50) UNIQUE NOT NULL,  -- 'APV-20251013-001'
    priority INTEGER NOT NULL,  -- 1 (critical) to 10 (low)

    -- Vulnerability signature for AST-grep matching
    vulnerable_code_signature TEXT,  -- Regex or AST pattern
    vulnerable_code_type VARCHAR(50),  -- 'regex', 'ast-grep', 'semgrep'

    -- Context
    affected_files TEXT[],  -- Potential files in codebase
    exploitation_difficulty VARCHAR(20),  -- 'easy', 'medium', 'hard'
    exploitability_score NUMERIC(3,1),  -- 0.0 to 10.0

    -- Status tracking
    status VARCHAR(30) DEFAULT 'pending',  -- 'pending', 'dispatched', 'confirmed', 'false_positive', 'remediated'
    dispatched_to_eureka_at TIMESTAMP,
    confirmed_at TIMESTAMP,

    -- HITL decision
    requires_human_review BOOLEAN DEFAULT FALSE,
    human_decision VARCHAR(20),  -- 'approved', 'rejected', 'deferred', NULL
    human_decision_by VARCHAR(100),
    human_decision_at TIMESTAMP,
    human_decision_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (priority >= 1 AND priority <= 10),
    CHECK (exploitability_score IS NULL OR (exploitability_score >= 0 AND exploitability_score <= 10)),
    CHECK (exploitation_difficulty IN ('easy', 'medium', 'hard', 'unknown'))
);

CREATE INDEX idx_apvs_threat_id ON apvs(threat_id);
CREATE INDEX idx_apvs_dependency_id ON apvs(dependency_id);
CREATE INDEX idx_apvs_apv_code ON apvs(apv_code);
CREATE INDEX idx_apvs_status ON apvs(status);
CREATE INDEX idx_apvs_priority ON apvs(priority);
CREATE INDEX idx_apvs_requires_human_review ON apvs(requires_human_review);
CREATE INDEX idx_apvs_human_decision ON apvs(human_decision);
CREATE INDEX idx_apvs_created_at ON apvs(created_at DESC);

-- =========================================================================
-- TABLE: remedies
-- Description: Generated remedies for confirmed vulnerabilities
-- =========================================================================
CREATE TABLE IF NOT EXISTS remedies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference
    apv_id UUID NOT NULL REFERENCES apvs(id) ON DELETE CASCADE,

    -- Remedy identification
    remedy_code VARCHAR(50) UNIQUE NOT NULL,  -- 'REM-20251013-001'
    remedy_type VARCHAR(30) NOT NULL,  -- 'dependency_upgrade', 'code_patch', 'configuration_change', 'no_fix_available'

    -- Remedy details
    description TEXT NOT NULL,
    implementation_steps JSONB,  -- [{"step": 1, "action": "...", "command": "..."}]

    -- For dependency upgrades
    current_version VARCHAR(100),
    target_version VARCHAR(100),

    -- For code patches
    code_diff TEXT,  -- Git diff format
    affected_files TEXT[],

    -- Breaking changes analysis
    breaking_changes_detected BOOLEAN DEFAULT FALSE,
    breaking_changes_description TEXT,
    breaking_changes_mitigation TEXT,

    -- LLM metadata
    llm_model VARCHAR(100),  -- 'claude-3-sonnet-20240229'
    llm_confidence NUMERIC(3,2),  -- 0.00 to 1.00
    llm_reasoning TEXT,

    -- Status
    status VARCHAR(30) DEFAULT 'generated',  -- 'generated', 'validated', 'pr_created', 'merged', 'failed'
    validation_status VARCHAR(30),  -- 'pending', 'passed', 'failed'
    validation_error TEXT,

    -- GitHub PR
    github_pr_number INTEGER,
    github_pr_url TEXT,
    github_branch_name VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (llm_confidence IS NULL OR (llm_confidence >= 0 AND llm_confidence <= 1)),
    CHECK (remedy_type IN ('dependency_upgrade', 'code_patch', 'configuration_change', 'no_fix_available', 'manual_intervention'))
);

CREATE INDEX idx_remedies_apv_id ON remedies(apv_id);
CREATE INDEX idx_remedies_remedy_code ON remedies(remedy_code);
CREATE INDEX idx_remedies_status ON remedies(status);
CREATE INDEX idx_remedies_remedy_type ON remedies(remedy_type);
CREATE INDEX idx_remedies_github_pr_number ON remedies(github_pr_number);
CREATE INDEX idx_remedies_created_at ON remedies(created_at DESC);

-- =========================================================================
-- TABLE: wargame_runs
-- Description: Empirical validation results from GitHub Actions
-- =========================================================================
CREATE TABLE IF NOT EXISTS wargame_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference
    remedy_id UUID NOT NULL REFERENCES remedies(id) ON DELETE CASCADE,

    -- Wargame identification
    run_code VARCHAR(50) UNIQUE NOT NULL,  -- 'WAR-20251013-001'
    github_actions_run_id BIGINT,
    github_actions_run_url TEXT,

    -- Test phases
    exploit_before_patch_status VARCHAR(20),  -- 'vulnerable', 'not_vulnerable', 'error', 'timeout'
    exploit_before_patch_output TEXT,
    exploit_before_patch_duration_ms INTEGER,

    exploit_after_patch_status VARCHAR(20),  -- 'fixed', 'still_vulnerable', 'error', 'timeout'
    exploit_after_patch_output TEXT,
    exploit_after_patch_duration_ms INTEGER,

    -- Verdict
    verdict VARCHAR(30) NOT NULL,  -- 'success', 'failed', 'inconclusive', 'error'
    verdict_reason TEXT,
    confidence_score NUMERIC(3,2),  -- 0.00 to 1.00

    -- Exploit metadata
    exploit_type VARCHAR(50),  -- 'sql_injection', 'xss', 'rce', 'dos', etc.
    exploit_script_path TEXT,

    -- Full report
    full_report JSONB,  -- Complete GitHub Actions logs + analysis

    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (verdict IN ('success', 'failed', 'inconclusive', 'error')),
    CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
);

CREATE INDEX idx_wargame_runs_remedy_id ON wargame_runs(remedy_id);
CREATE INDEX idx_wargame_runs_run_code ON wargame_runs(run_code);
CREATE INDEX idx_wargame_runs_verdict ON wargame_runs(verdict);
CREATE INDEX idx_wargame_runs_github_actions_run_id ON wargame_runs(github_actions_run_id);
CREATE INDEX idx_wargame_runs_completed_at ON wargame_runs(completed_at DESC);

-- =========================================================================
-- TABLE: hitl_decisions
-- Description: Human-in-the-loop decisions and audit trail
-- =========================================================================
CREATE TABLE IF NOT EXISTS hitl_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference (polymorphic - can be apv, remedy, or wargame)
    entity_type VARCHAR(20) NOT NULL,  -- 'apv', 'remedy', 'wargame'
    entity_id UUID NOT NULL,

    -- Decision metadata
    decision_type VARCHAR(30) NOT NULL,  -- 'approve_apv', 'reject_apv', 'approve_remedy', 'approve_pr_merge', etc.
    decision VARCHAR(20) NOT NULL,  -- 'approved', 'rejected', 'deferred'

    -- Human operator
    decided_by VARCHAR(100) NOT NULL,  -- Username or email
    decided_at TIMESTAMP DEFAULT NOW(),

    -- Justification
    notes TEXT,
    risk_assessment TEXT,
    additional_context JSONB,

    -- Audit trail
    ip_address INET,
    user_agent TEXT,
    session_id UUID,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CHECK (entity_type IN ('apv', 'remedy', 'wargame', 'pr')),
    CHECK (decision IN ('approved', 'rejected', 'deferred', 'escalated'))
);

CREATE INDEX idx_hitl_decisions_entity_type_id ON hitl_decisions(entity_type, entity_id);
CREATE INDEX idx_hitl_decisions_decided_by ON hitl_decisions(decided_by);
CREATE INDEX idx_hitl_decisions_decided_at ON hitl_decisions(decided_at DESC);
CREATE INDEX idx_hitl_decisions_decision ON hitl_decisions(decision);

-- =========================================================================
-- TABLE: feed_sync_status
-- Description: Track last successful sync for each CVE feed
-- =========================================================================
CREATE TABLE IF NOT EXISTS feed_sync_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    feed_name VARCHAR(50) UNIQUE NOT NULL,  -- 'nvd', 'ghsa', 'osv'
    last_sync_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error TEXT,

    sync_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Stats
    total_threats_ingested INTEGER DEFAULT 0,
    last_sync_duration_ms INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CHECK (feed_name IN ('nvd', 'ghsa', 'osv'))
);

CREATE INDEX idx_feed_sync_status_feed_name ON feed_sync_status(feed_name);

-- =========================================================================
-- VIEWS: Convenience views for common queries
-- =========================================================================

-- High priority APVs requiring immediate attention
CREATE OR REPLACE VIEW vw_critical_apvs AS
SELECT
    a.id,
    a.apv_code,
    a.priority,
    a.status,
    t.cve_id,
    t.title,
    t.cvss_score,
    t.severity,
    d.project_name,
    d.package_name,
    d.package_version,
    a.created_at
FROM apvs a
JOIN threats t ON a.threat_id = t.id
JOIN dependencies d ON a.dependency_id = d.id
WHERE a.priority <= 3
  AND a.status IN ('pending', 'dispatched')
ORDER BY a.priority, a.created_at;

-- APVs awaiting human review
CREATE OR REPLACE VIEW vw_pending_hitl_apvs AS
SELECT
    a.id,
    a.apv_code,
    a.priority,
    t.cve_id,
    t.title,
    t.severity,
    d.project_name,
    d.package_name,
    a.created_at
FROM apvs a
JOIN threats t ON a.threat_id = t.id
JOIN dependencies d ON a.dependency_id = d.id
WHERE a.requires_human_review = TRUE
  AND a.human_decision IS NULL
ORDER BY a.priority, a.created_at;

-- Remedies pending wargaming validation
CREATE OR REPLACE VIEW vw_pending_wargame_remedies AS
SELECT
    r.id,
    r.remedy_code,
    r.remedy_type,
    r.status,
    r.github_pr_url,
    a.apv_code,
    t.cve_id,
    r.created_at
FROM remedies r
JOIN apvs a ON r.apv_id = a.id
JOIN threats t ON a.threat_id = t.id
WHERE r.status IN ('generated', 'pr_created')
  AND NOT EXISTS (
    SELECT 1 FROM wargame_runs w
    WHERE w.remedy_id = r.id
      AND w.verdict IN ('success', 'failed')
  )
ORDER BY r.created_at;

-- System health dashboard metrics
CREATE OR REPLACE VIEW vw_system_metrics AS
SELECT
    (SELECT COUNT(*) FROM threats WHERE status = 'new') as new_threats,
    (SELECT COUNT(*) FROM apvs WHERE status = 'pending') as pending_apvs,
    (SELECT COUNT(*) FROM apvs WHERE requires_human_review = TRUE AND human_decision IS NULL) as pending_hitl_decisions,
    (SELECT COUNT(*) FROM remedies WHERE status = 'generated') as pending_remedies,
    (SELECT COUNT(*) FROM remedies WHERE github_pr_number IS NOT NULL AND status != 'merged') as open_prs,
    (SELECT COUNT(*) FROM wargame_runs WHERE verdict = 'success') as successful_wargames,
    (SELECT COUNT(*) FROM wargame_runs WHERE verdict = 'failed') as failed_wargames;

-- =========================================================================
-- TRIGGERS: Auto-update timestamps
-- =========================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_threats_updated_at BEFORE UPDATE ON threats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dependencies_updated_at BEFORE UPDATE ON dependencies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_apvs_updated_at BEFORE UPDATE ON apvs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_remedies_updated_at BEFORE UPDATE ON remedies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_wargame_runs_updated_at BEFORE UPDATE ON wargame_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feed_sync_status_updated_at BEFORE UPDATE ON feed_sync_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================================================
-- SEED DATA: Initialize feed sync status
-- =========================================================================

INSERT INTO feed_sync_status (feed_name)
VALUES ('nvd'), ('ghsa'), ('osv')
ON CONFLICT (feed_name) DO NOTHING;

-- =========================================================================
-- END OF SCHEMA
-- =========================================================================
