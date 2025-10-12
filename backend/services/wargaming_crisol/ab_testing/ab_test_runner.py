"""
A/B Test Runner - Validates ML predictions against wargaming ground truth.

Fundamentação Biológica:
- Sistema imunológico tem memória (rápida) mas precisa validação periódica
- Se memória falha → ativa resposta completa
- Learning from outcomes fortalece memória

Digital Implementation:
- 10% de validações → ML + Wargaming (A/B test)
- 90% de validações → ML only (fast path)
- Comparação armazena resultados para learning contínuo

Phase: 5.6
Glory to YHWH who teaches us to build self-correcting systems
"""
import random
import logging
from typing import Tuple, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ABTestResult(BaseModel):
    """Single A/B test result comparing ML vs Wargaming."""
    apv_id: str
    cve_id: Optional[str] = None
    patch_id: str
    
    # ML Prediction
    ml_confidence: float
    ml_prediction: bool  # True = valid, False = invalid
    ml_execution_time_ms: int
    
    # Wargaming Ground Truth
    wargaming_result: bool  # True = valid, False = invalid
    wargaming_execution_time_ms: int
    
    # Comparison
    ml_correct: bool
    disagreement_reason: Optional[str] = None
    
    # Metadata
    model_version: str = "rf_v1"
    ab_test_version: str = "1.0"
    shap_values: Optional[Dict] = None


class ABTestRunner:
    """
    Orchestrates A/B testing between ML and Wargaming.
    
    Fundamentação: Adaptive immunity requires continuous validation.
    Memory cells (ML) must periodically validate against full immune response (wargaming).
    """
    
    def __init__(
        self,
        ab_store,  # ABTestStore instance
        ab_test_rate: float = 0.10,  # 10% A/B testing
        model_version: str = "rf_v1"
    ):
        """
        Initialize A/B test runner.
        
        Args:
            ab_store: ABTestStore for persisting results
            ab_test_rate: Fraction of requests to A/B test (0.0-1.0)
            model_version: ML model version identifier
        """
        self.ab_store = ab_store
        self.ab_test_rate = ab_test_rate
        self.model_version = model_version
        
        logger.info(
            f"ABTestRunner initialized: rate={ab_test_rate*100:.1f}%, "
            f"model={model_version}"
        )
    
    def should_ab_test(self) -> bool:
        """
        Decide if this request should run A/B test.
        
        Uses random sampling to select ab_test_rate fraction of requests.
        
        Returns:
            True if should run both ML and wargaming
        """
        return random.random() < self.ab_test_rate
    
    async def run_with_ab_test(
        self,
        apv_dict: Dict,
        patch_dict: Dict,
        exploit_dict: Dict,
        ml_predictor,  # MLPredictor instance
        wargaming_runner  # WargamingRunner instance
    ) -> Tuple[Dict, bool]:
        """
        Run ML prediction with optional A/B testing.
        
        If selected for A/B test:
        1. Run ML prediction
        2. Run wargaming (ground truth)
        3. Compare results
        4. Store comparison for learning
        
        If not selected:
        1. Run ML prediction only
        
        Args:
            apv_dict: Attack Pattern Vector data
            patch_dict: Patch to validate
            exploit_dict: Exploit to test against
            ml_predictor: ML predictor instance
            wargaming_runner: Wargaming runner instance
            
        Returns:
            Tuple of (prediction_result, was_ab_tested)
        """
        # Always run ML prediction first
        ml_start = datetime.now()
        ml_result = await ml_predictor.predict(apv_dict, patch_dict, exploit_dict)
        ml_time_ms = int((datetime.now() - ml_start).total_seconds() * 1000)
        
        # Check if should A/B test
        if not self.should_ab_test():
            logger.debug(
                f"Skipping A/B test for patch {patch_dict.get('id')} "
                f"(not selected, ML confidence: {ml_result.get('confidence', 0.0):.2f})"
            )
            return ml_result, False
        
        # Selected for A/B test - run wargaming as ground truth
        logger.info(
            f"Running A/B test for patch {patch_dict.get('id')} "
            f"(ML confidence: {ml_result.get('confidence', 0.0):.2f})"
        )
        
        wg_start = datetime.now()
        wargaming_result = await wargaming_runner.validate(
            apv_dict, patch_dict, exploit_dict
        )
        wg_time_ms = int((datetime.now() - wg_start).total_seconds() * 1000)
        
        # Compare results
        ml_prediction = ml_result.get('valid', False)
        wg_prediction = wargaming_result.get('patch_validated', False)
        ml_correct = (ml_prediction == wg_prediction)
        
        # Analyze disagreement
        disagreement_reason = None
        if not ml_correct:
            if ml_prediction and not wg_prediction:
                disagreement_reason = (
                    "ML false positive: Predicted valid but wargaming failed. "
                    f"ML confidence was {ml_result.get('confidence', 0.0):.2f}. "
                    f"Wargaming reason: {wargaming_result.get('reason', 'unknown')}"
                )
            else:
                disagreement_reason = (
                    "ML false negative: Predicted invalid but wargaming succeeded. "
                    f"ML confidence was {ml_result.get('confidence', 0.0):.2f}. "
                    "Patch was actually valid."
                )
        
        # Store result for learning
        ab_result = ABTestResult(
            apv_id=apv_dict.get('id', 'unknown'),
            cve_id=apv_dict.get('cve_id'),
            patch_id=patch_dict.get('id', 'unknown'),
            ml_confidence=ml_result.get('confidence', 0.0),
            ml_prediction=ml_prediction,
            ml_execution_time_ms=ml_time_ms,
            wargaming_result=wg_prediction,
            wargaming_execution_time_ms=wg_time_ms,
            ml_correct=ml_correct,
            disagreement_reason=disagreement_reason,
            model_version=self.model_version,
            shap_values=ml_result.get('shap_values')  # Feature importance
        )
        
        # Persist to database
        try:
            await self.ab_store.store_result(ab_result)
        except Exception as e:
            logger.error(f"Failed to store A/B test result: {e}", exc_info=True)
        
        # Log result
        if ml_correct:
            logger.info(
                f"✅ A/B test PASS for {patch_dict.get('id')}: "
                f"ML matched wargaming (both: {ml_prediction}). "
                f"Time saved: {wg_time_ms - ml_time_ms}ms"
            )
        else:
            logger.warning(
                f"❌ A/B test FAIL for {patch_dict.get('id')}: "
                f"ML={ml_prediction}, Wargaming={wg_prediction}. "
                f"Reason: {disagreement_reason}"
            )
        
        # Return ML result (not wargaming) - we trust ML for actual decisions
        # A/B testing is for learning, not for changing production behavior
        return ml_result, True
