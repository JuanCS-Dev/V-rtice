-- HCL Knowledge Base Schema
-- PostgreSQL 15+ with TimescaleDB extension
-- Stores all HCL decisions, states, and outcomes for learning and analytics

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main decisions table
CREATE TABLE IF NOT EXISTS hcl_decisions (
    id UUID DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp),

    -- Trigger information
    trigger_type TEXT NOT NULL, -- 'cpu_threshold', 'memory_threshold', 'prediction', 'manual'
    trigger_details JSONB NOT NULL, -- {metric: 'cpu_usage', value: 85.5, threshold: 80, ...}

    -- Operational mode
    operational_mode TEXT NOT NULL, -- 'HIGH_PERFORMANCE', 'BALANCED', 'ENERGY_EFFICIENT'
    previous_mode TEXT,

    -- Actions taken
    actions_taken JSONB NOT NULL, -- [{service: 'maximus_core', action: 'scale', from: 3, to: 5}, ...]

    -- System state snapshots
    state_before JSONB NOT NULL, -- {cpu: 85.5, memory: 78.2, gpu: 45.0, ...}
    state_after JSONB, -- Same structure, null if not yet measured

    -- Outcome evaluation (filled after 5min)
    outcome TEXT, -- 'SUCCESS', 'PARTIAL', 'FAILED', 'PENDING'
    outcome_measured_at TIMESTAMPTZ,

    -- Reward signal for RL training
    reward_signal FLOAT, -- Computed based on metrics improvement

    -- Human feedback (optional)
    human_feedback TEXT,
    human_feedback_at TIMESTAMPTZ,
    analyst_id TEXT,

    -- Metadata
    decision_latency_ms INT, -- Time to make decision
    execution_latency_ms INT, -- Time to execute actions
    planner_used TEXT -- 'fuzzy', 'rl_agent', 'manual'
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('hcl_decisions', 'timestamp', if_not_exists => TRUE);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON hcl_decisions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON hcl_decisions(outcome);
CREATE INDEX IF NOT EXISTS idx_decisions_mode ON hcl_decisions(operational_mode);
CREATE INDEX IF NOT EXISTS idx_decisions_trigger ON hcl_decisions(trigger_type);
CREATE INDEX IF NOT EXISTS idx_decisions_planner ON hcl_decisions(planner_used);

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_decisions_actions ON hcl_decisions USING GIN(actions_taken);
CREATE INDEX IF NOT EXISTS idx_decisions_state_before ON hcl_decisions USING GIN(state_before);

-- Retention policy: keep detailed data for 1 year, aggregates forever
SELECT add_retention_policy('hcl_decisions', INTERVAL '365 days', if_not_exists => TRUE);

-- Continuous aggregates for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS hcl_decisions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    operational_mode,
    outcome,
    COUNT(*) as decision_count,
    AVG((state_after->>'cpu')::float - (state_before->>'cpu')::float) as avg_cpu_delta,
    AVG((state_after->>'memory')::float - (state_before->>'memory')::float) as avg_memory_delta,
    AVG(reward_signal) as avg_reward,
    AVG(decision_latency_ms) as avg_decision_latency,
    AVG(execution_latency_ms) as avg_execution_latency
FROM hcl_decisions
WHERE outcome != 'PENDING'
GROUP BY hour, operational_mode, outcome
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('hcl_decisions_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- System metrics time-series (raw telemetry)
CREATE TABLE IF NOT EXISTS system_metrics (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,
    tags JSONB, -- {host: 'node-1', pod: 'maximus-core-abc123', ...}
    PRIMARY KEY (timestamp, service_name, metric_name)
);

-- Convert to hypertable
SELECT create_hypertable('system_metrics', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_metrics_service ON system_metrics(service_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_tags ON system_metrics USING GIN(tags);

-- Retention: 90 days detailed
SELECT add_retention_policy('system_metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Compression policy (native compression, not columnstore)
ALTER TABLE system_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'service_name,metric_name'
);

SELECT add_compression_policy('system_metrics', INTERVAL '7 days', if_not_exists => TRUE);

-- Continuous aggregate for metrics (1-minute averages)
CREATE MATERIALIZED VIEW IF NOT EXISTS system_metrics_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS minute,
    service_name,
    metric_name,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value,
    MIN(metric_value) as min_value,
    STDDEV(metric_value) as stddev_value
FROM system_metrics
GROUP BY minute, service_name, metric_name
WITH NO DATA;

SELECT add_continuous_aggregate_policy('system_metrics_1min',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- Model training history
CREATE TABLE IF NOT EXISTS hcl_model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL, -- 'sarima_cpu', 'isolation_forest', 'xgboost_failure', 'rl_sac'
    version INTEGER NOT NULL,
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    training_dataset_start TIMESTAMPTZ NOT NULL,
    training_dataset_end TIMESTAMPTZ NOT NULL,
    training_samples INT NOT NULL,

    -- Performance metrics
    metrics JSONB NOT NULL, -- {auc_roc: 0.95, precision: 0.92, recall: 0.88, ...}

    -- Model artifacts
    model_path TEXT NOT NULL, -- S3/file path to serialized model
    model_size_bytes BIGINT,

    -- Deployment status
    deployed BOOLEAN DEFAULT FALSE,
    deployed_at TIMESTAMPTZ,
    replaced_version INTEGER, -- Previous version that was replaced

    -- Training metadata
    hyperparameters JSONB,
    training_duration_seconds INT,
    training_logs TEXT,

    UNIQUE(model_name, version)
);

CREATE INDEX IF NOT EXISTS idx_model_versions_name ON hcl_model_versions(model_name, version DESC);
CREATE INDEX IF NOT EXISTS idx_model_versions_deployed ON hcl_model_versions(model_name, deployed) WHERE deployed = TRUE;

-- Comments
COMMENT ON TABLE hcl_decisions IS 'Stores all HCL decisions with before/after states for learning';
COMMENT ON TABLE system_metrics IS 'Raw system telemetry time-series data';
COMMENT ON TABLE hcl_model_versions IS 'Tracks ML model versions and deployments';
COMMENT ON COLUMN hcl_decisions.reward_signal IS 'Computed reward for RL training: +10*SLA - 5*cost - 10*downtime';
COMMENT ON COLUMN hcl_decisions.actions_taken IS 'Array of actions: [{service, action, from, to, api_call}, ...]';
