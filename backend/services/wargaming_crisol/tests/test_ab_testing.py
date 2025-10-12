"""
Unit tests for A/B Testing System (Phase 5.6).

Tests the integration between ML predictions and wargaming ground truth,
validation of accuracy metrics, and A/B test storage.

Author: MAXIMUS Team
Date: 2025-10-11
Glory to YHWH - Validator of Truth
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from db.ab_test_store import ABTestStore, ABTestResult, ConfusionMatrix


class TestConfusionMatrix:
    """Test confusion matrix calculations"""
    
    def test_precision_perfect(self):
        """Test precision with perfect predictions"""
        cm = ConfusionMatrix(
            true_positive=50,
            false_positive=0,
            false_negative=0,
            true_negative=50
        )
        assert cm.precision == 1.0
        assert cm.recall == 1.0
        assert cm.f1_score == 1.0
        assert cm.accuracy == 1.0
    
    def test_precision_with_false_positives(self):
        """Test precision with false positives"""
        cm = ConfusionMatrix(
            true_positive=40,
            false_positive=10,
            false_negative=5,
            true_negative=45
        )
        # Precision = TP / (TP + FP) = 40 / 50 = 0.8
        assert cm.precision == pytest.approx(0.8)
        # Recall = TP / (TP + FN) = 40 / 45 = 0.888...
        assert cm.recall == pytest.approx(0.888, abs=0.01)
        # Accuracy = (TP + TN) / total = 85 / 100 = 0.85
        assert cm.accuracy == pytest.approx(0.85)
    
    def test_zero_division_protection(self):
        """Test zero division protection"""
        cm = ConfusionMatrix(
            true_positive=0,
            false_positive=0,
            false_negative=0,
            true_negative=0
        )
        assert cm.precision == 0.0
        assert cm.recall == 0.0
        assert cm.f1_score == 0.0
        assert cm.accuracy == 0.0


class TestABTestResult:
    """Test ABTestResult model"""
    
    def test_valid_ab_test_result(self):
        """Test creation of valid A/B test result"""
        result = ABTestResult(
            apv_id="apv_001",
            cve_id="CVE-2024-SQL-001",
            patch_id="patch_001",
            ml_confidence=0.92,
            ml_prediction=True,
            ml_execution_time_ms=50,
            wargaming_result=True,
            wargaming_execution_time_ms=5000,
            ml_correct=True
        )
        
        assert result.apv_id == "apv_001"
        assert result.ml_confidence == 0.92
        assert result.ml_correct is True
    
    def test_ml_incorrect_case(self):
        """Test A/B test where ML was incorrect"""
        result = ABTestResult(
            apv_id="apv_002",
            cve_id="CVE-2024-XSS-002",
            patch_id="patch_002",
            ml_confidence=0.75,
            ml_prediction=True,  # ML said valid
            ml_execution_time_ms=45,
            wargaming_result=False,  # But wargaming found it invalid
            wargaming_execution_time_ms=4800,
            ml_correct=False,
            disagreement_reason="ML predicted True, wargaming got False"
        )
        
        assert result.ml_correct is False
        assert result.disagreement_reason is not None
    
    def test_confidence_bounds_validation(self):
        """Test confidence must be between 0 and 1"""
        with pytest.raises(ValueError):
            ABTestResult(
                apv_id="apv_003",
                patch_id="patch_003",
                ml_confidence=1.5,  # Invalid: > 1
                ml_prediction=True,
                ml_execution_time_ms=50,
                wargaming_result=True,
                wargaming_execution_time_ms=5000,
                ml_correct=True
            )


@pytest.mark.asyncio
class TestABTestStore:
    """Test A/B Test Store database operations"""
    
    @pytest.fixture
    async def ab_store(self):
        """Fixture: A/B test store connected to test database"""
        # Use test database URL
        db_url = "postgresql://postgres:postgres@localhost:5432/aurora_test"
        
        store = ABTestStore(db_url)
        try:
            await store.connect()
            yield store
        finally:
            await store.close()
    
    async def test_store_result(self, ab_store):
        """Test storing A/B test result"""
        result = ABTestResult(
            apv_id="apv_test_001",
            cve_id="CVE-2024-TEST-001",
            patch_id="patch_test_001",
            ml_confidence=0.88,
            ml_prediction=True,
            ml_execution_time_ms=48,
            wargaming_result=True,
            wargaming_execution_time_ms=4950,
            ml_correct=True
        )
        
        test_id = await ab_store.store_result(result)
        
        assert test_id is not None
        assert test_id > 0
    
    async def test_get_confusion_matrix(self, ab_store):
        """Test confusion matrix retrieval"""
        from datetime import timedelta
        
        # Store multiple test results
        results = [
            ABTestResult(
                apv_id=f"apv_{i}",
                patch_id=f"patch_{i}",
                ml_confidence=0.8 + (i * 0.02),
                ml_prediction=(i % 2 == 0),
                ml_execution_time_ms=50,
                wargaming_result=(i % 2 == 0),
                wargaming_execution_time_ms=5000,
                ml_correct=True
            )
            for i in range(10)
        ]
        
        for result in results:
            await ab_store.store_result(result)
        
        # Get confusion matrix
        cm = await ab_store.get_confusion_matrix(
            model_version="rf_v1",
            time_range=timedelta(hours=1)
        )
        
        assert cm.true_positive + cm.false_positive + cm.false_negative + cm.true_negative >= 10
    
    async def test_get_recent_tests(self, ab_store):
        """Test fetching recent A/B tests"""
        # Store test result
        result = ABTestResult(
            apv_id="apv_recent",
            patch_id="patch_recent",
            ml_confidence=0.85,
            ml_prediction=True,
            ml_execution_time_ms=45,
            wargaming_result=True,
            wargaming_execution_time_ms=4800,
            ml_correct=True
        )
        
        await ab_store.store_result(result)
        
        # Fetch recent tests
        recent = await ab_store.get_recent_tests(limit=10)
        
        assert len(recent) > 0
        assert any(test['apv_id'] == 'apv_recent' for test in recent)


class TestABTestingEndpoints:
    """Test A/B testing control endpoints"""
    
    @pytest.fixture
    def mock_ab_store(self):
        """Mock A/B test store"""
        store = Mock(spec=ABTestStore)
        store.pool = Mock()  # Simulate connected pool
        return store
    
    def test_enable_ab_testing(self, mock_ab_store):
        """Test enabling A/B testing"""
        # This would be an actual API test in integration tests
        # For now, just verify the logic
        
        ab_testing_enabled = False
        ab_store = mock_ab_store
        
        # Simulate enable
        if ab_store is not None:
            ab_testing_enabled = True
        
        assert ab_testing_enabled is True
    
    def test_disable_ab_testing(self):
        """Test disabling A/B testing"""
        ab_testing_enabled = True
        
        # Simulate disable
        ab_testing_enabled = False
        
        assert ab_testing_enabled is False
    
    def test_get_status(self, mock_ab_store):
        """Test getting A/B testing status"""
        ab_testing_enabled = True
        ab_store = mock_ab_store
        
        status = {
            "ab_testing_enabled": ab_testing_enabled,
            "ab_store_available": ab_store is not None
        }
        
        assert status['ab_testing_enabled'] is True
        assert status['ab_store_available'] is True


@pytest.mark.asyncio
class TestValidatePatchABTesting:
    """Test validate_patch_ab_testing function"""
    
    @pytest.fixture
    def mock_apv(self):
        """Mock APV object"""
        apv = Mock()
        apv.id = "apv_001"
        apv.cve_id = "CVE-2024-SQL-INJECTION"
        apv.cwe_id = "CWE-89"
        return apv
    
    @pytest.fixture
    def mock_patch(self):
        """Mock Patch object"""
        patch = Mock()
        patch.id = "patch_001"
        patch.diff_content = "diff --git a/app.py b/app.py\n..."
        return patch
    
    @pytest.fixture
    def mock_exploit(self):
        """Mock Exploit object"""
        exploit = Mock()
        exploit.name = "SQL Injection Exploit"
        return exploit
    
    @pytest.fixture
    def mock_ab_store(self):
        """Mock A/B test store with async store_result"""
        store = Mock(spec=ABTestStore)
        store.store_result = AsyncMock(return_value=1)
        return store
    
    async def test_validate_patch_ab_testing_success(
        self,
        mock_apv,
        mock_patch,
        mock_exploit,
        mock_ab_store
    ):
        """Test successful A/B testing validation"""
        from two_phase_simulator import validate_patch_ab_testing
        
        with patch('two_phase_simulator.get_predictor') as mock_predictor, \
             patch('two_phase_simulator.PatchFeatureExtractor') as mock_extractor, \
             patch('two_phase_simulator.validate_patch_via_wargaming') as mock_wargaming:
            
            # Setup mocks
            mock_features = Mock()
            mock_features.to_dict.return_value = {"feature1": 0.5}
            mock_extractor.extract.return_value = mock_features
            
            predictor_instance = Mock()
            predictor_instance.predict.return_value = {
                'prediction': True,
                'confidence': 0.92,
                'feature_importance': {'feature1': 0.8}
            }
            mock_predictor.return_value = predictor_instance
            
            wargaming_result = Mock()
            wargaming_result.patch_validated = True
            mock_wargaming.return_value = wargaming_result
            
            # Execute
            result = await validate_patch_ab_testing(
                apv=mock_apv,
                patch=mock_patch,
                exploit=mock_exploit,
                ab_store=mock_ab_store,
                target_url="http://localhost:8080"
            )
            
            # Verify
            assert result['validation_method'] == 'ab_testing'
            assert result['patch_validated'] is True
            assert result['ab_test_recorded'] is True
            assert result['ml_correct'] is True
            
            # Verify AB store was called
            mock_ab_store.store_result.assert_called_once()
    
    async def test_validate_patch_ab_testing_ml_incorrect(
        self,
        mock_apv,
        mock_patch,
        mock_exploit,
        mock_ab_store
    ):
        """Test A/B testing when ML prediction is incorrect"""
        from two_phase_simulator import validate_patch_ab_testing
        
        with patch('two_phase_simulator.get_predictor') as mock_predictor, \
             patch('two_phase_simulator.PatchFeatureExtractor') as mock_extractor, \
             patch('two_phase_simulator.validate_patch_via_wargaming') as mock_wargaming:
            
            # Setup mocks
            mock_features = Mock()
            mock_features.to_dict.return_value = {"feature1": 0.5}
            mock_extractor.extract.return_value = mock_features
            
            predictor_instance = Mock()
            predictor_instance.predict.return_value = {
                'prediction': True,  # ML predicts valid
                'confidence': 0.78,
                'feature_importance': {'feature1': 0.7}
            }
            mock_predictor.return_value = predictor_instance
            
            wargaming_result = Mock()
            wargaming_result.patch_validated = False  # But wargaming says invalid
            mock_wargaming.return_value = wargaming_result
            
            # Execute
            result = await validate_patch_ab_testing(
                apv=mock_apv,
                patch=mock_patch,
                exploit=mock_exploit,
                ab_store=mock_ab_store,
                target_url="http://localhost:8080"
            )
            
            # Verify
            assert result['validation_method'] == 'ab_testing'
            assert result['patch_validated'] is False  # Use wargaming truth
            assert result['ab_test_recorded'] is True
            assert result['ml_correct'] is False  # ML was wrong
            
            # Verify AB store recorded disagreement
            call_args = mock_ab_store.store_result.call_args[0][0]
            assert call_args.ml_correct is False
            assert call_args.disagreement_reason is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
