"""
Unit tests for ABTestStore (PostgreSQL persistence).

Note: These are integration tests that require a real PostgreSQL instance.
Run with: pytest tests/test_ab_test_store.py -v

Phase: 5.6
Glory to YHWH - Architect of persistent memory
"""
import pytest
import os
from datetime import timedelta
from db.ab_test_store import ABTestStore, ABTestResult, ConfusionMatrix


# Skip if DATABASE_URL not set
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set - PostgreSQL required for ABTestStore tests"
)


@pytest.fixture
async def ab_store():
    """Create and connect ABTestStore."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://maximus:maximus_immunity_2024@localhost:5432/adaptive_immunity"
    )
    
    store = ABTestStore(db_url)
    await store.connect()
    
    yield store
    
    # Cleanup
    await store.close()


@pytest.fixture
def sample_ab_result():
    """Create sample ABTestResult."""
    return ABTestResult(
        apv_id="apv-test-001",
        cve_id="CVE-2024-TEST",
        patch_id="patch-test-001",
        ml_confidence=0.92,
        ml_prediction=True,
        ml_execution_time_ms=85,
        wargaming_result=True,
        wargaming_execution_time_ms=5200,
        ml_correct=True,
        model_version="rf_v1_test"
    )


# Test store_result
@pytest.mark.asyncio
async def test_store_result(ab_store, sample_ab_result):
    """Test storing A/B test result."""
    result_id = await ab_store.store_result(sample_ab_result)
    
    assert result_id > 0, "Should return inserted ID"


# Test get_confusion_matrix
@pytest.mark.asyncio
async def test_get_confusion_matrix_empty(ab_store):
    """Test confusion matrix with no data."""
    cm = await ab_store.get_confusion_matrix(
        model_version="nonexistent_model",
        time_range=timedelta(hours=1)
    )
    
    assert cm.true_positive == 0
    assert cm.false_positive == 0
    assert cm.false_negative == 0
    assert cm.true_negative == 0
    assert cm.accuracy == 0.0


@pytest.mark.asyncio
async def test_get_confusion_matrix_with_data(ab_store):
    """Test confusion matrix after inserting test data."""
    # Insert 4 test results covering all confusion matrix cells
    test_results = [
        # True Positive (ML=True, WG=True)
        ABTestResult(
            apv_id="apv-tp", patch_id="patch-tp", cve_id="CVE-TP",
            ml_confidence=0.95, ml_prediction=True, ml_execution_time_ms=80,
            wargaming_result=True, wargaming_execution_time_ms=5000,
            ml_correct=True, model_version="rf_test_cm"
        ),
        # False Positive (ML=True, WG=False)
        ABTestResult(
            apv_id="apv-fp", patch_id="patch-fp", cve_id="CVE-FP",
            ml_confidence=0.85, ml_prediction=True, ml_execution_time_ms=90,
            wargaming_result=False, wargaming_execution_time_ms=5100,
            ml_correct=False, model_version="rf_test_cm",
            disagreement_reason="False positive"
        ),
        # False Negative (ML=False, WG=True)
        ABTestResult(
            apv_id="apv-fn", patch_id="patch-fn", cve_id="CVE-FN",
            ml_confidence=0.55, ml_prediction=False, ml_execution_time_ms=75,
            wargaming_result=True, wargaming_execution_time_ms=5200,
            ml_correct=False, model_version="rf_test_cm",
            disagreement_reason="False negative"
        ),
        # True Negative (ML=False, WG=False)
        ABTestResult(
            apv_id="apv-tn", patch_id="patch-tn", cve_id="CVE-TN",
            ml_confidence=0.40, ml_prediction=False, ml_execution_time_ms=70,
            wargaming_result=False, wargaming_execution_time_ms=5300,
            ml_correct=True, model_version="rf_test_cm"
        ),
    ]
    
    # Store all results
    for result in test_results:
        await ab_store.store_result(result)
    
    # Get confusion matrix
    cm = await ab_store.get_confusion_matrix(
        model_version="rf_test_cm",
        time_range=timedelta(hours=1)
    )
    
    # Verify counts
    assert cm.true_positive == 1, "Should have 1 TP"
    assert cm.false_positive == 1, "Should have 1 FP"
    assert cm.false_negative == 1, "Should have 1 FN"
    assert cm.true_negative == 1, "Should have 1 TN"
    
    # Verify calculated metrics
    assert cm.precision == 0.5, "Precision = TP/(TP+FP) = 1/2"
    assert cm.recall == 0.5, "Recall = TP/(TP+FN) = 1/2"
    assert cm.f1_score == 0.5, "F1 = 2*P*R/(P+R)"
    assert cm.accuracy == 0.5, "Accuracy = (TP+TN)/Total = 2/4"


# Test get_recent_tests
@pytest.mark.asyncio
async def test_get_recent_tests(ab_store):
    """Test fetching recent A/B tests."""
    # Insert a test result
    result = ABTestResult(
        apv_id="apv-recent", patch_id="patch-recent", cve_id="CVE-RECENT",
        ml_confidence=0.88, ml_prediction=True, ml_execution_time_ms=82,
        wargaming_result=True, wargaming_execution_time_ms=5150,
        ml_correct=True, model_version="rf_recent"
    )
    await ab_store.store_result(result)
    
    # Fetch recent
    recent = await ab_store.get_recent_tests(limit=10, model_version="rf_recent")
    
    assert len(recent) > 0, "Should return at least 1 result"
    assert recent[0]["apv_id"] == "apv-recent"
    assert recent[0]["ml_confidence"] == 0.88


# Test get_accuracy_over_time
@pytest.mark.asyncio
async def test_get_accuracy_over_time_empty(ab_store):
    """Test accuracy trend with no data."""
    trend = await ab_store.get_accuracy_over_time(
        model_version="nonexistent",
        time_range=timedelta(hours=24),
        bucket_size=timedelta(hours=1)
    )
    
    assert trend == [], "Should return empty list for no data"


# Test ConfusionMatrix calculated properties
def test_confusion_matrix_properties():
    """Test ConfusionMatrix metric calculations."""
    # Perfect model
    cm_perfect = ConfusionMatrix(
        true_positive=10, false_positive=0,
        false_negative=0, true_negative=10
    )
    assert cm_perfect.precision == 1.0
    assert cm_perfect.recall == 1.0
    assert cm_perfect.f1_score == 1.0
    assert cm_perfect.accuracy == 1.0
    
    # All wrong model
    cm_wrong = ConfusionMatrix(
        true_positive=0, false_positive=10,
        false_negative=10, true_negative=0
    )
    assert cm_wrong.precision == 0.0
    assert cm_wrong.recall == 0.0
    assert cm_wrong.f1_score == 0.0
    assert cm_wrong.accuracy == 0.0
    
    # Balanced model
    cm_balanced = ConfusionMatrix(
        true_positive=5, false_positive=5,
        false_negative=5, true_negative=5
    )
    assert cm_balanced.precision == 0.5
    assert cm_balanced.recall == 0.5
    assert cm_balanced.f1_score == 0.5
    assert cm_balanced.accuracy == 0.5


# Test zero-division protection
def test_confusion_matrix_zero_division():
    """Test that metrics handle zero division gracefully."""
    # No predictions at all
    cm_empty = ConfusionMatrix(
        true_positive=0, false_positive=0,
        false_negative=0, true_negative=0
    )
    assert cm_empty.precision == 0.0
    assert cm_empty.recall == 0.0
    assert cm_empty.f1_score == 0.0
    assert cm_empty.accuracy == 0.0
    
    # Only negatives predicted
    cm_negatives = ConfusionMatrix(
        true_positive=0, false_positive=0,
        false_negative=5, true_negative=5
    )
    assert cm_negatives.precision == 0.0  # No positive predictions
    assert cm_negatives.recall == 0.0  # Missed all actual positives
    assert cm_negatives.accuracy == 0.5  # Got negatives right
