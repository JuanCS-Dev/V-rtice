"""PostgreSQL + TimescaleDB Schema for HCL Decisions"""

CREATE_SCHEMA_SQL = """
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- HCL Decisions table
CREATE TABLE IF NOT EXISTS hcl_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trigger TEXT NOT NULL,
    operational_mode TEXT NOT NULL CHECK (operational_mode IN ('HIGH_PERFORMANCE', 'BALANCED', 'ENERGY_EFFICIENT')),
    actions_taken JSONB NOT NULL,
    state_before JSONB NOT NULL,
    state_after JSONB,
    outcome TEXT CHECK (outcome IN ('SUCCESS', 'PARTIAL', 'FAILED')),
    reward_signal FLOAT,
    human_feedback TEXT
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('hcl_decisions', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON hcl_decisions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_outcome ON hcl_decisions (outcome);
CREATE INDEX IF NOT EXISTS idx_decisions_mode ON hcl_decisions (operational_mode);
CREATE INDEX IF NOT EXISTS idx_decisions_actions_gin ON hcl_decisions USING GIN (actions_taken);

-- Retention policy: 90 days detailed
SELECT add_retention_policy('hcl_decisions', INTERVAL '90 days', if_not_exists => TRUE);

-- Continuous aggregate for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS hcl_decisions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    operational_mode,
    COUNT(*) as decision_count,
    AVG(reward_signal) as avg_reward,
    COUNT(CASE WHEN outcome = 'SUCCESS' THEN 1 END) as success_count
FROM hcl_decisions
GROUP BY hour, operational_mode;
"""


async def create_schema(connection):
    """Create database schema."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        await connection.execute(CREATE_SCHEMA_SQL)
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Error creating schema: {e}")
        raise
