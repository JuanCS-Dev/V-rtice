"""
MCEA Stress - Final 17 Lines to 100% ABSOLUTE
==============================================

Missing lines (92.70% → 100.00%):
191, 195, 199, 203, 205, 209, 360, 407-408, 420, 431-435, 486, 647

Target: 100.00% coverage with REAL execution.

PADRÃO PAGANI ABSOLUTO - 100% MEANS 100%
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from consciousness.mcea.stress import (
    StressMonitor,
    StressType,
    StressLevel,
    StressResponse,
)


class TestResilienceScorePenalties:
    """Tests for StressResponse.get_resilience_score() penalty branches (lines 191, 195, 199, 203, 205, 209)."""

    def test_resilience_score_arousal_runaway_penalty_line_191(self):
        """Test arousal_runaway_detected triggers -40 penalty (line 191)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.1,
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=True,  # Triggers line 191
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=60.0,
        )

        # Base score 100 - 40 (arousal runaway) = 60
        assert response.get_resilience_score() == 60.0

    def test_resilience_score_goal_failure_penalty_line_195(self):
        """Test goal_generation_failure triggers -20 penalty (line 195)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.1,
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=True,  # Triggers line 195
            coherence_collapse=False,
            duration_seconds=60.0,
        )

        # Base score 100 - 20 (goal failure) = 80
        assert response.get_resilience_score() == 80.0

    def test_resilience_score_coherence_collapse_penalty_line_199(self):
        """Test coherence_collapse triggers -30 penalty (line 199)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.1,
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=True,  # Triggers line 199
            duration_seconds=60.0,
        )

        # Base score 100 - 30 (coherence collapse) = 70
        assert response.get_resilience_score() == 70.0

    def test_resilience_score_poor_recovery_penalty_line_203(self):
        """Test full_recovery_achieved=False triggers -15 penalty (line 203)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.1,
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=30.0,
            full_recovery_achieved=False,  # Triggers line 203
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=60.0,
        )

        # Base score 100 - 15 (poor recovery) = 85
        assert response.get_resilience_score() == 85.0

    def test_resilience_score_slow_recovery_penalty_line_205(self):
        """Test recovery_time > 60s triggers -10 penalty (line 205)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.1,
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=70.0,  # > 60 triggers line 205
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=60.0,
        )

        # Base score 100 - 10 (slow recovery) = 90
        assert response.get_resilience_score() == 90.0

    def test_resilience_score_arousal_instability_penalty_line_209(self):
        """Test arousal_stability_cv > 0.3 triggers -10 penalty (line 209)."""
        response = StressResponse(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.SEVERE,
            initial_arousal=0.5,
            peak_arousal=0.9,
            final_arousal=0.6,
            arousal_stability_cv=0.4,  # > 0.3 triggers line 209
            peak_rest_need=0.5,
            peak_repair_need=0.5,
            peak_efficiency_need=0.5,
            goals_generated=5,
            goals_satisfied=3,
            critical_goals_generated=1,
            esgt_events=10,
            mean_esgt_coherence=0.8,
            esgt_coherence_degradation=0.1,
            recovery_time_seconds=30.0,
            full_recovery_achieved=True,
            arousal_runaway_detected=False,
            goal_generation_failure=False,
            coherence_collapse=False,
            duration_seconds=60.0,
        )

        # Base score 100 - 10 (instability) = 90
        assert response.get_resilience_score() == 90.0


class TestStressMonitorStartEdgeCase:
    """Test StressMonitor.start() early return (line 360)."""

    @pytest.mark.asyncio
    async def test_start_already_running_returns_early_line_360(self):
        """Test start() returns immediately if already _running (line 360)."""
        # Create mock arousal controller
        mock_arousal = MagicMock()
        mock_arousal.get_current_arousal.return_value = MagicMock(arousal=0.5)

        # Create mock needs monitor
        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)

        # First start - should set _running = True
        await monitor.start()
        assert monitor._running is True

        # Capture baseline from first start
        first_baseline = monitor._baseline_arousal

        # Second start - should return early at line 360 WITHOUT changing baseline
        await monitor.start()

        # Verify baseline wasn't recaptured (early return happened)
        assert monitor._baseline_arousal == first_baseline

        # Stop monitor
        await monitor.stop()


class TestStressMonitorExceptionHandling:
    """Test StressMonitor exception handling in monitoring loop (lines 407-408)."""

    @pytest.mark.asyncio
    async def test_monitoring_loop_exception_handling_lines_407_408(self):
        """Test monitoring loop catches exceptions and continues (lines 407-408)."""
        # Create mock arousal controller
        mock_arousal = MagicMock()

        # First call during start() - succeeds
        baseline_state = MagicMock()
        baseline_state.arousal = 0.5

        # Subsequent calls during monitoring loop - raise exception
        mock_arousal.get_current_arousal.side_effect = [
            baseline_state,  # First call in start()
            RuntimeError("Arousal failure!"),  # Subsequent calls in monitoring loop
            RuntimeError("Arousal failure!")
        ]
        mock_arousal.get_stress_level.return_value = 0.3

        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)

        # Start monitor (first get_current_arousal() succeeds)
        await monitor.start()

        # Let monitoring loop run briefly (will hit exception at line 407)
        await asyncio.sleep(1.5)  # Enough for 1-2 monitoring cycles

        # Monitor should still be running (exception caught, not propagated)
        assert monitor._running is True

        # Stop monitor
        await monitor.stop()


class TestStressLevelMappings:
    """Test stress level severity mappings (lines 431-435)."""

    def test_stress_level_moderate_line_431(self):
        """Test combined_stress [0.4, 0.6) → MODERATE (line 431)."""
        mock_arousal = MagicMock()
        current_state = MagicMock()
        current_state.arousal = 0.5
        mock_arousal.get_current_arousal.return_value = current_state
        mock_arousal.get_stress_level.return_value = 0.5  # Controller stress

        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)
        monitor._baseline_arousal = 0.0  # Set baseline to make stress = 0.5

        # Stress = 0.5 → should map to MODERATE (line 431)
        level = monitor._assess_stress_level()
        assert level == StressLevel.MODERATE

    def test_stress_level_severe_line_433(self):
        """Test combined_stress [0.6, 0.8) → SEVERE (line 433)."""
        mock_arousal = MagicMock()
        current_state = MagicMock()
        current_state.arousal = 0.7
        mock_arousal.get_current_arousal.return_value = current_state
        mock_arousal.get_stress_level.return_value = 0.7  # Controller stress

        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)
        monitor._baseline_arousal = 0.0  # Stress = 0.7

        # Stress = 0.7 → should map to SEVERE (line 433)
        level = monitor._assess_stress_level()
        assert level == StressLevel.SEVERE

    def test_stress_level_critical_line_435(self):
        """Test combined_stress >= 0.8 → CRITICAL (line 435)."""
        mock_arousal = MagicMock()
        current_state = MagicMock()
        current_state.arousal = 0.9
        mock_arousal.get_current_arousal.return_value = current_state
        mock_arousal.get_stress_level.return_value = 0.9  # Controller stress

        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)
        monitor._baseline_arousal = 0.0  # Stress = 0.9

        # Stress = 0.9 → should map to CRITICAL (line 435)
        level = monitor._assess_stress_level()
        assert level == StressLevel.CRITICAL


class TestRunStressTestDefaultDuration:
    """Test run_stress_test() duration_seconds default (line 486)."""

    @pytest.mark.asyncio
    async def test_run_stress_test_default_duration_line_486(self):
        """Test run_stress_test uses config default when duration_seconds=None (line 486)."""
        import time
        from consciousness.mcea.stress import StressTestConfig

        mock_arousal = MagicMock()
        current_state = MagicMock()
        current_state.arousal = 0.5
        mock_arousal.get_current_arousal.return_value = current_state
        mock_arousal.get_stress_level.return_value = 0.3
        mock_arousal.request_modulation = MagicMock()

        mock_needs = MagicMock()

        # Create REAL config with SHORT durations for fast test
        real_config = StressTestConfig(
            stress_duration_seconds=0.1,  # Very short stress phase
            recovery_duration_seconds=0.1,  # Very short recovery phase
        )

        monitor = StressMonitor(mock_arousal, config=real_config)

        # Start monitor first
        await monitor.start()

        # Call run_stress_test with duration_seconds=None (triggers line 486)
        # Line 486 will set duration_seconds = self.config.stress_duration_seconds (0.1)
        result = await monitor.run_stress_test(
            stress_type=StressType.AROUSAL_FORCING,
            stress_level=StressLevel.MILD,
            duration_seconds=None,  # Line 486: Use config default
        )

        # Verify result exists (test executed - line 486 was hit)
        assert isinstance(result, StressResponse)
        # Verify the duration from config was used
        assert result.duration_seconds == 0.1

        await monitor.stop()


class TestGetStressHistoryWithoutWindow:
    """Test get_stress_history() with window_seconds=None (line 647)."""

    @pytest.mark.asyncio
    async def test_get_stress_history_no_window_line_647(self):
        """Test get_stress_history returns full history when window_seconds=None (line 647)."""
        mock_arousal = MagicMock()
        mock_arousal.get_current_arousal.return_value = MagicMock(arousal=0.5)

        mock_needs = MagicMock()

        monitor = StressMonitor(mock_arousal, mock_needs)

        # Populate stress history manually
        import time

        monitor._stress_history = [
            (time.time() - 100, StressLevel.MILD),
            (time.time() - 50, StressLevel.MODERATE),
            (time.time() - 10, StressLevel.SEVERE),
        ]

        # Call with window_seconds=None (triggers line 647)
        history = monitor.get_stress_history(window_seconds=None)

        # Should return ALL history (full copy)
        assert len(history) == 3
        assert history[0][1] == StressLevel.MILD
        assert history[1][1] == StressLevel.MODERATE
        assert history[2][1] == StressLevel.SEVERE


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
