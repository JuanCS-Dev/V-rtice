"""
Metacognitive Monitor - Targeted Coverage Tests

Objetivo: Cobrir consciousness/metacognition/monitor.py (174 lines, 0% → 70%+)

Testa confidence tracking, error trends, reasoning quality monitoring

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest

from consciousness.metacognition.monitor import MetacognitiveMonitor


# ===== INITIALIZATION TESTS =====

def test_metacognitive_monitor_initialization():
    """
    SCENARIO: MetacognitiveMonitor created with default window_size
    EXPECTED: window_size=100, empty errors, total_recordings=0
    """
    monitor = MetacognitiveMonitor()

    assert monitor.window_size == 100
    assert len(monitor.errors) == 0
    assert monitor.total_recordings == 0


def test_metacognitive_monitor_custom_window_size():
    """
    SCENARIO: MetacognitiveMonitor created with window_size=50
    EXPECTED: window_size=50
    """
    monitor = MetacognitiveMonitor(window_size=50)

    assert monitor.window_size == 50


# ===== RECORD_ERROR TESTS =====

def test_record_error_increments_total():
    """
    SCENARIO: record_error() called 3 times
    EXPECTED: total_recordings=3, 3 errors stored
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(0.1)
    monitor.record_error(0.2)
    monitor.record_error(0.3)

    assert monitor.total_recordings == 3
    assert len(monitor.errors) == 3


def test_record_error_clamps_negative():
    """
    SCENARIO: record_error(-0.5) with out-of-range value
    EXPECTED: Error clamped to 0.0
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(-0.5)

    assert list(monitor.errors) == [0.0]


def test_record_error_clamps_above_1():
    """
    SCENARIO: record_error(1.5) with out-of-range value
    EXPECTED: Error clamped to 1.0
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(1.5)

    assert list(monitor.errors) == [1.0]


def test_record_error_respects_maxlen():
    """
    SCENARIO: MetacognitiveMonitor(window_size=3), record 5 errors
    EXPECTED: Only last 3 errors retained (FIFO)
    """
    monitor = MetacognitiveMonitor(window_size=3)

    monitor.record_error(0.1)
    monitor.record_error(0.2)
    monitor.record_error(0.3)
    monitor.record_error(0.4)
    monitor.record_error(0.5)

    assert len(monitor.errors) == 3
    assert list(monitor.errors) == [0.3, 0.4, 0.5]


# ===== CALCULATE_CONFIDENCE TESTS =====

def test_calculate_confidence_no_data():
    """
    SCENARIO: calculate_confidence() with no errors recorded
    EXPECTED: Neutral confidence = 0.5
    """
    monitor = MetacognitiveMonitor()

    confidence = monitor.calculate_confidence()

    assert confidence == 0.5


def test_calculate_confidence_perfect():
    """
    SCENARIO: calculate_confidence() with all 0.0 errors (perfect)
    EXPECTED: Confidence = 1.0
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(0.0)
    monitor.record_error(0.0)
    monitor.record_error(0.0)

    confidence = monitor.calculate_confidence()

    assert confidence == 1.0


def test_calculate_confidence_total_error():
    """
    SCENARIO: calculate_confidence() with all 1.0 errors (total failure)
    EXPECTED: Confidence = 0.0
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(1.0)
    monitor.record_error(1.0)
    monitor.record_error(1.0)

    confidence = monitor.calculate_confidence()

    assert confidence == 0.0


def test_calculate_confidence_average():
    """
    SCENARIO: calculate_confidence() with errors [0.1, 0.3, 0.2] (avg=0.2)
    EXPECTED: Confidence = 1.0 - 0.2 = 0.8
    """
    monitor = MetacognitiveMonitor()

    monitor.record_error(0.1)
    monitor.record_error(0.3)
    monitor.record_error(0.2)

    confidence = monitor.calculate_confidence()

    assert abs(confidence - 0.8) < 1e-6


# ===== GET_RECENT_ERRORS TESTS =====

def test_get_recent_errors_default():
    """
    SCENARIO: get_recent_errors() with 15 errors, default n=10
    EXPECTED: Returns last 10 errors
    """
    monitor = MetacognitiveMonitor()

    for i in range(15):
        monitor.record_error(i * 0.01)

    recent = monitor.get_recent_errors()

    assert len(recent) == 10
    assert recent == [i * 0.01 for i in range(5, 15)]


def test_get_recent_errors_custom_n():
    """
    SCENARIO: get_recent_errors(n=5) with 10 errors
    EXPECTED: Returns last 5 errors
    """
    monitor = MetacognitiveMonitor()

    for i in range(10):
        monitor.record_error(i * 0.1)

    recent = monitor.get_recent_errors(n=5)

    assert len(recent) == 5


# ===== GET_ERROR_TREND TESTS =====

def test_get_error_trend_insufficient_data():
    """
    SCENARIO: get_error_trend() with only 5 errors (window=10)
    EXPECTED: Returns "insufficient_data"
    """
    monitor = MetacognitiveMonitor()

    for i in range(5):
        monitor.record_error(0.1)

    trend = monitor.get_error_trend(window=10)

    assert trend == "insufficient_data"


def test_get_error_trend_improving():
    """
    SCENARIO: get_error_trend() with decreasing errors (0.8 → 0.2)
    EXPECTED: Returns "improving"
    """
    monitor = MetacognitiveMonitor()

    # First half: high errors (0.8, 0.7, 0.7, 0.6, 0.6)
    for _ in range(5):
        monitor.record_error(0.7)

    # Second half: low errors (0.2, 0.2, 0.3, 0.2, 0.2)
    for _ in range(5):
        monitor.record_error(0.2)

    trend = monitor.get_error_trend(window=10)

    assert trend == "improving"


def test_get_error_trend_degrading():
    """
    SCENARIO: get_error_trend() with increasing errors (0.2 → 0.8)
    EXPECTED: Returns "degrading"
    """
    monitor = MetacognitiveMonitor()

    # First half: low errors
    for _ in range(5):
        monitor.record_error(0.2)

    # Second half: high errors
    for _ in range(5):
        monitor.record_error(0.7)

    trend = monitor.get_error_trend(window=10)

    assert trend == "degrading"


def test_get_error_trend_stable():
    """
    SCENARIO: get_error_trend() with consistent errors (0.5 ± 0.05)
    EXPECTED: Returns "stable"
    """
    monitor = MetacognitiveMonitor()

    for _ in range(10):
        monitor.record_error(0.5)

    trend = monitor.get_error_trend(window=10)

    assert trend == "stable"


# ===== RESET TESTS =====

def test_reset_clears_errors():
    """
    SCENARIO: reset() called after recording 10 errors
    EXPECTED: errors cleared, total_recordings unchanged
    """
    monitor = MetacognitiveMonitor()

    for i in range(10):
        monitor.record_error(0.1)

    assert len(monitor.errors) == 10
    assert monitor.total_recordings == 10

    monitor.reset()

    assert len(monitor.errors) == 0
    assert monitor.total_recordings == 10  # Counter not reset


# ===== GET_STATS TESTS =====

def test_get_stats_empty():
    """
    SCENARIO: get_stats() with no errors recorded
    EXPECTED: neutral confidence, insufficient_data trend
    """
    monitor = MetacognitiveMonitor()

    stats = monitor.get_stats()

    assert stats["total_recordings"] == 0
    assert stats["window_size"] == 100
    assert stats["current_error_count"] == 0
    assert stats["current_confidence"] == 0.5
    assert stats["error_trend"] == "insufficient_data"
    assert stats["avg_error"] == 0.0


def test_get_stats_with_data():
    """
    SCENARIO: get_stats() after recording 15 errors (avg=0.3)
    EXPECTED: confidence=0.7, avg_error=0.3
    """
    monitor = MetacognitiveMonitor()

    for _ in range(15):
        monitor.record_error(0.3)

    stats = monitor.get_stats()

    assert stats["total_recordings"] == 15
    assert stats["current_error_count"] == 15
    assert abs(stats["current_confidence"] - 0.7) < 1e-6
    assert abs(stats["avg_error"] - 0.3) < 1e-6
    assert stats["error_trend"] == "stable"


# ===== REPR TESTS =====

def test_repr():
    """
    SCENARIO: MetacognitiveMonitor.__repr__() with 5 errors
    EXPECTED: Includes error count and confidence
    """
    monitor = MetacognitiveMonitor()

    for _ in range(5):
        monitor.record_error(0.2)

    repr_str = repr(monitor)

    assert "MetacognitiveMonitor" in repr_str
    assert "5/100" in repr_str
    assert "confidence=0.800" in repr_str


def test_docstring_confidence_formula():
    """
    SCENARIO: Module documents confidence calculation formula
    EXPECTED: Mentions confidence = 1 - average_error
    """
    import consciousness.metacognition.monitor as module

    assert "Confidence = 1 - average_error" in module.__doc__
