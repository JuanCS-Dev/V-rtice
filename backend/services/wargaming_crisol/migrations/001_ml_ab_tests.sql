-- Phase 5.6: A/B Testing Database Schema
-- Create ml_ab_tests table for A/B testing results
-- Date: 2025-10-11
-- Author: MAXIMUS Team

-- Create ml_ab_tests table
CREATE TABLE IF NOT EXISTS ml_ab_tests (
    id SERIAL PRIMARY KEY,
    apv_id VARCHAR(50) NOT NULL,
    cve_id VARCHAR(50),
    patch_id VARCHAR(50) NOT NULL,
    
    -- ML Prediction
    ml_confidence FLOAT NOT NULL CHECK (ml_confidence BETWEEN 0 AND 1),
    ml_prediction BOOLEAN NOT NULL,
    ml_execution_time_ms INTEGER NOT NULL CHECK (ml_execution_time_ms >= 0),
    
    -- Wargaming Ground Truth
    wargaming_result BOOLEAN NOT NULL,
    wargaming_execution_time_ms INTEGER NOT NULL CHECK (wargaming_execution_time_ms >= 0),
    
    -- Comparison
    ml_correct BOOLEAN NOT NULL,
    disagreement_reason TEXT,
    
    -- Feature importance (JSONB for SHAP values, optional)
    shap_values JSONB,
    
    -- Metadata
    model_version VARCHAR(20) DEFAULT 'rf_v1',
    ab_test_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_ab_tests_created ON ml_ab_tests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ml_ab_tests_correct ON ml_ab_tests(ml_correct);
CREATE INDEX IF NOT EXISTS idx_ml_ab_tests_model ON ml_ab_tests(model_version);
CREATE INDEX IF NOT EXISTS idx_ml_ab_tests_apv ON ml_ab_tests(apv_id);

-- View for quick accuracy stats
CREATE OR REPLACE VIEW ml_accuracy_stats AS
SELECT
    model_version,
    COUNT(*) as total_tests,
    SUM(CASE WHEN ml_correct THEN 1 ELSE 0 END) as correct_predictions,
    ROUND(CAST(AVG(CASE WHEN ml_correct THEN 1.0 ELSE 0.0 END) AS NUMERIC), 4) as accuracy,
    ROUND(CAST(AVG(ml_confidence) AS NUMERIC), 4) as avg_confidence,
    ROUND(CAST(AVG(ml_execution_time_ms) AS NUMERIC), 2) as avg_ml_time_ms,
    ROUND(CAST(AVG(wargaming_execution_time_ms) AS NUMERIC), 2) as avg_wargaming_time_ms,
    MIN(created_at) as first_test,
    MAX(created_at) as last_test
FROM ml_ab_tests
GROUP BY model_version;

-- Confusion matrix calculation function
CREATE OR REPLACE FUNCTION calculate_confusion_matrix(
    p_model_version VARCHAR DEFAULT 'rf_v1',
    p_time_range INTERVAL DEFAULT INTERVAL '24 hours'
)
RETURNS TABLE (
    true_positive BIGINT,
    false_positive BIGINT,
    false_negative BIGINT,
    true_negative BIGINT,
    prec FLOAT,
    rec FLOAT,
    f1 FLOAT,
    acc FLOAT
) AS $$
DECLARE
    tp BIGINT;
    fp BIGINT;
    fn BIGINT;
    tn BIGINT;
    prec FLOAT;
    rec FLOAT;
    f1 FLOAT;
    acc FLOAT;
BEGIN
    -- Calculate confusion matrix
    SELECT
        COUNT(*) FILTER (WHERE ml_prediction = TRUE AND wargaming_result = TRUE),
        COUNT(*) FILTER (WHERE ml_prediction = TRUE AND wargaming_result = FALSE),
        COUNT(*) FILTER (WHERE ml_prediction = FALSE AND wargaming_result = TRUE),
        COUNT(*) FILTER (WHERE ml_prediction = FALSE AND wargaming_result = FALSE)
    INTO tp, fp, fn, tn
    FROM ml_ab_tests
    WHERE model_version = p_model_version
      AND created_at > NOW() - p_time_range;
    
    -- Calculate metrics (with zero-division protection)
    IF (tp + fp) > 0 THEN
        prec := tp::FLOAT / (tp + fp);
    ELSE
        prec := 0.0;
    END IF;
    
    IF (tp + fn) > 0 THEN
        rec := tp::FLOAT / (tp + fn);
    ELSE
        rec := 0.0;
    END IF;
    
    IF (prec + rec) > 0 THEN
        f1 := 2.0 * (prec * rec) / (prec + rec);
    ELSE
        f1 := 0.0;
    END IF;
    
    IF (tp + fp + fn + tn) > 0 THEN
        acc := (tp + tn)::FLOAT / (tp + fp + fn + tn);
    ELSE
        acc := 0.0;
    END IF;
    
    RETURN QUERY SELECT tp, fp, fn, tn, prec, rec, f1, acc;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (will be configured based on actual DB user)
-- GRANT SELECT, INSERT ON ml_ab_tests TO wargaming_user;
-- GRANT SELECT ON ml_accuracy_stats TO wargaming_user;
-- GRANT EXECUTE ON FUNCTION calculate_confusion_matrix TO wargaming_user;

-- Insert sample test data for initial validation
INSERT INTO ml_ab_tests (
    apv_id, cve_id, patch_id,
    ml_confidence, ml_prediction, ml_execution_time_ms,
    wargaming_result, wargaming_execution_time_ms,
    ml_correct, disagreement_reason
) VALUES
    -- True Positives
    ('apv-sample-001', 'CVE-2024-0001', 'patch-001', 0.95, TRUE, 85, TRUE, 8500, TRUE, NULL),
    ('apv-sample-002', 'CVE-2024-0002', 'patch-002', 0.92, TRUE, 90, TRUE, 8200, TRUE, NULL),
    ('apv-sample-003', 'CVE-2024-0003', 'patch-003', 0.88, TRUE, 95, TRUE, 9000, TRUE, NULL),
    
    -- True Negatives
    ('apv-sample-004', 'CVE-2024-0004', 'patch-004', 0.25, FALSE, 75, FALSE, 8800, TRUE, NULL),
    ('apv-sample-005', 'CVE-2024-0005', 'patch-005', 0.15, FALSE, 80, FALSE, 7900, TRUE, NULL),
    
    -- False Positive
    ('apv-sample-006', 'CVE-2024-0006', 'patch-006', 0.82, TRUE, 88, FALSE, 8400, FALSE, 'ML false positive: Predicted valid but wargaming failed'),
    
    -- False Negative
    ('apv-sample-007', 'CVE-2024-0007', 'patch-007', 0.65, FALSE, 92, TRUE, 9200, FALSE, 'ML false negative: Predicted invalid but wargaming succeeded');

-- Verify installation
SELECT 'ml_ab_tests table created' as status;
SELECT * FROM ml_accuracy_stats;
SELECT * FROM calculate_confusion_matrix('rf_v1', INTERVAL '1 year');
