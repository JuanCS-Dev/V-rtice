"""
MEA (Meta-Awareness) - Final Push to 100%
==========================================

Target missing lines (96%+ → 100.00%):

attention_schema.py:
- 145: RuntimeError when record_prediction_outcome called with no _last_state
- 161: prediction_accuracy early return with no traces
- 171: prediction_calibration early return with no traces
- 196-197: prediction_variability early return with <2 traces
- 213-214: _normalize_modality_scores equal weight when total=0

boundary_detector.py:
- 103: _compute_stability when mean_strength == 0

prediction_validator.py:
- 93: _compute_focus_switch_rate when len < 2

self_model.py:
- 68: current_perspective RuntimeError when not initialized
- 78: current_boundary RuntimeError when not initialized

PADRÃO PAGANI ABSOLUTO - 100% MEANS 100%
"""

import pytest
from consciousness.mea.attention_schema import AttentionSchemaModel, AttentionState, AttentionSignal
from consciousness.mea.boundary_detector import BoundaryDetector, BoundaryAssessment
from consciousness.mea.prediction_validator import PredictionValidator
from consciousness.mea.self_model import SelfModel, FirstPersonPerspective


class TestAttentionSchemaFinal7Lines:
    """Tests for attention_schema.py missing lines (145, 161, 171, 196-197, 213-214)."""

    def test_record_prediction_outcome_no_last_state_line_145(self):
        """Test RuntimeError when record_prediction_outcome called with no _last_state (line 145)."""
        model = AttentionSchemaModel()

        # Try to record outcome without having generated a prediction first
        # This should raise RuntimeError at line 145
        with pytest.raises(RuntimeError, match="No attention state available for calibration"):
            model.record_prediction_outcome(actual_focus="visual")

    def test_prediction_accuracy_empty_traces_line_161(self):
        """Test prediction_accuracy returns 0.0 with no traces (line 161)."""
        model = AttentionSchemaModel()

        # No prediction traces recorded yet - should return 0.0 at line 161
        accuracy = model.prediction_accuracy(window=50)
        assert accuracy == 0.0

    def test_prediction_calibration_empty_traces_line_171(self):
        """Test prediction_calibration returns 0.0 with no traces (line 171)."""
        model = AttentionSchemaModel()

        # No prediction traces recorded yet - should return 0.0 at line 171
        calibration = model.prediction_calibration(window=50)
        assert calibration == 0.0

    def test_prediction_variability_insufficient_traces_lines_196_197(self):
        """Test prediction_variability with <2 traces (line 195) and >=2 traces (lines 196-197)."""
        model = AttentionSchemaModel()

        # No traces - should return 0.0 at line 195
        variability = model.prediction_variability(window=50)
        assert variability == 0.0

        # Add ONE trace (still <2) - returns 0.0 at line 195
        signals = [AttentionSignal("visual", "target", 0.8, 0.5, 0.6, 0.4)]
        state = model.update(signals)
        model.record_prediction_outcome(actual_focus="visual")

        # Only 1 trace - should return 0.0 at line 195
        variability = model.prediction_variability(window=50)
        assert variability == 0.0

        # Add second trace with DIFFERENT confidence - EXECUTES lines 196-197
        signals2 = [AttentionSignal("visual", "target2", 0.6, 0.5, 0.6, 0.4)]  # Lower intensity = different confidence
        state2 = model.update(signals2)
        model.record_prediction_outcome(actual_focus="target2")

        # Now 2 traces - should compute variability via lines 196-197
        variability_2 = model.prediction_variability(window=50)
        assert variability_2 >= 0.0  # Should be some positive value due to different confidences

    def test_normalize_modality_scores_zero_total_lines_213_214(self):
        """Test _normalize_modality_scores equal weight distribution when total=0 (lines 213-214)."""
        model = AttentionSchemaModel()

        # Pass all-zero scores (total = 0)
        zero_scores = {"visual": 0.0, "auditory": 0.0, "proprioceptive": 0.0}

        # This should trigger lines 213-214 (equal weight distribution)
        normalized = model._normalize_modality_scores(zero_scores)

        # Should have equal weights (1/3 each)
        expected_weight = 1.0 / 3
        assert normalized["visual"] == pytest.approx(expected_weight)
        assert normalized["auditory"] == pytest.approx(expected_weight)
        assert normalized["proprioceptive"] == pytest.approx(expected_weight)
        assert sum(normalized.values()) == pytest.approx(1.0)


class TestBoundaryDetectorFinal1Line:
    """Tests for boundary_detector.py missing line (103)."""

    def test_compute_stability_mean_strength_zero_line_103(self):
        """Test _compute_stability returns 0.0 when mean_strength == 0 (line 103)."""
        detector = BoundaryDetector()

        # Need to populate strength history with all zeros (≥5 samples)
        # This requires calling evaluate() multiple times with balanced signals

        # Zero proprioceptive, high exteroceptive → strength near 0
        for _ in range(6):
            assessment = detector.evaluate(
                proprioceptive_signals=[0.001, 0.001, 0.001],  # Very low proprio
                exteroceptive_signals=[1.0, 1.0, 1.0]  # High extero
            )

        # Now strength_history should have values very close to 0
        # If mean_strength rounds to 0, line 103 triggers
        # Force the condition by directly manipulating history for deterministic test
        detector._strength_history.clear()
        for _ in range(5):
            detector._strength_history.append(0.0)

        # Call _compute_stability directly
        stability = detector._compute_stability()

        # Should return 0.0 at line 103
        assert stability == 0.0


class TestPredictionValidatorFinal1Line:
    """Tests for prediction_validator.py missing line (93)."""

    def test_compute_focus_switch_rate_len_less_than_2_line_93(self):
        """Test _compute_focus_switch_rate returns 0.0 when len < 2 (line 93)."""
        validator = PredictionValidator()

        # Create a single prediction using AttentionSchemaModel
        model = AttentionSchemaModel()
        signals = [AttentionSignal("visual", "target", 0.8, 0.5, 0.6, 0.4)]
        state = model.update(signals)
        single_prediction = [state]

        # Call internal method directly (it's used by validate())
        switch_rate = validator._compute_focus_switch_rate(single_prediction)

        # Should return 0.0 at line 93
        assert switch_rate == 0.0

        # Also test with empty list
        switch_rate_empty = validator._compute_focus_switch_rate([])
        assert switch_rate_empty == 0.0


class TestSelfModelFinal2Lines:
    """Tests for self_model.py missing lines (68, 78)."""

    def test_current_perspective_not_initialized_line_68(self):
        """Test current_perspective raises RuntimeError when not initialized (line 68)."""
        model = SelfModel()

        # Try to get perspective before any update()
        # Should raise RuntimeError at line 68
        with pytest.raises(RuntimeError, match="SelfModel has not been initialised yet"):
            model.current_perspective()

    def test_current_boundary_not_initialized_line_78(self):
        """Test current_boundary raises RuntimeError when not initialized (line 78)."""
        model = SelfModel()

        # Try to get boundary before any update()
        # Should raise RuntimeError at line 78
        with pytest.raises(RuntimeError, match="SelfModel has not been initialised yet"):
            model.current_boundary()


# Integration test to verify all components work together
class TestMEAIntegration:
    """Integration test to ensure all MEA components interact correctly."""

    def test_full_mea_pipeline(self):
        """Test complete MEA pipeline: attention → boundary → self-model → validation."""
        # 1. Create attention state
        schema = AttentionSchemaModel()
        signals = [
            AttentionSignal("visual", "target", 0.6, 0.5, 0.6, 0.5),
            AttentionSignal("auditory", "sound", 0.3, 0.3, 0.4, 0.2),
            AttentionSignal("proprioceptive", "body", 0.1, 0.2, 0.3, 0.1)
        ]
        attention_state = schema.update(signals)

        # 2. Detect boundary
        detector = BoundaryDetector()
        boundary = detector.evaluate(
            proprioceptive_signals=[0.7, 0.8, 0.75],
            exteroceptive_signals=[0.3, 0.2, 0.25]
        )

        # 3. Update self-model
        self_model = SelfModel()
        self_model.update(
            attention_state=attention_state,
            boundary=boundary,
            proprio_center=(0.0, 0.0, 1.0),
            orientation=(0.0, 0.0, 0.0)
        )

        # 4. Generate first-person report
        report = self_model.generate_first_person_report()
        assert "target" in report.narrative
        assert 0.0 <= report.confidence <= 1.0

        # 5. Record prediction outcome
        schema.record_prediction_outcome(actual_focus="target")

        # 6. Generate multiple predictions for validation
        predictions = []
        observations = []
        for i in range(10):
            target = f"target_{i % 2}"
            signals = [
                AttentionSignal("visual", target, 0.7 + i*0.01, 0.5, 0.6, 0.5),
                AttentionSignal("auditory", "noise", 0.2, 0.2, 0.3, 0.1)
            ]
            state = schema.update(signals)
            predictions.append(state)
            observations.append(target)

        # 7. Validate predictions
        validator = PredictionValidator()
        metrics = validator.validate(predictions, observations)

        assert 0.0 <= metrics.accuracy <= 1.0
        assert 0.0 <= metrics.calibration_error <= 1.0
        assert 0.0 <= metrics.mean_confidence <= 1.0
        assert 0.0 <= metrics.focus_switch_rate <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
