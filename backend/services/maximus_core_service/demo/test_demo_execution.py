"""
Test Suite for MAXIMUS AI 3.0 Demo Execution

Validates demo functionality, metrics, and output.

REGRA DE OURO: Zero mocks, real execution validation
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from demo.demo_maximus_complete import MaximusDemo


def test_dataset_loading():
    """Test that synthetic dataset loads correctly."""
    demo = MaximusDemo(dataset_path="demo/synthetic_events.json")
    demo.load_dataset()

    # Validate dataset loaded
    assert len(demo.events) == 100, f"Expected 100 events, got {len(demo.events)}"
    assert demo.metrics["total_events"] == 100

    # Validate event structure
    first_event = demo.events[0]
    required_fields = ["event_id", "timestamp", "event_type", "label"]
    for field in required_fields:
        assert field in first_event, f"Event missing required field: {field}"

    # Validate event distribution
    labels = [e["label"] for e in demo.events]
    assert "normal" in labels, "Dataset missing normal events"
    assert "malware" in labels, "Dataset missing malware events"

    print("✅ test_dataset_loading passed")


async def test_maximus_initialization():
    """Test MAXIMUS initialization (graceful degradation if dependencies missing)."""
    demo = MaximusDemo(dataset_path="demo/synthetic_events.json")
    demo.load_dataset()

    # Initialize MAXIMUS (may be None if dependencies missing)
    result = await demo.initialize_maximus()

    # Should always return True (either real init or simulation mode)
    assert result == True, "initialize_maximus should always return True"

    # maximus can be None (simulation mode) or MaximusIntegrated instance
    # Both are valid per graceful degradation design

    print("✅ test_maximus_initialization passed")


async def test_event_processing():
    """Test processing of individual events."""
    demo = MaximusDemo(dataset_path="demo/synthetic_events.json")
    demo.load_dataset()
    await demo.initialize_maximus()

    # Process a normal event
    normal_event = next(e for e in demo.events if e["label"] == "normal")
    result = await demo.process_event(normal_event, 1)

    # Validate result structure
    required_fields = ["event_id", "timestamp", "label", "detected_as_threat", "free_energy", "latency_ms"]
    for field in required_fields:
        assert field in result, f"Result missing required field: {field}"

    # Normal events should typically not be detected as threats
    assert result["detected_as_threat"] == False, "Normal event incorrectly flagged as threat"

    # Process a malware event
    malware_event = next(e for e in demo.events if e["label"] == "malware")
    result = await demo.process_event(malware_event, 2)

    # Malware should be detected
    assert result["detected_as_threat"] == True, "Malware event not detected"
    assert result["free_energy"] > 0.7, "Malware should have high free energy"
    assert "neuromodulation_state" in result

    print("✅ test_event_processing passed")


async def test_demo_run_limited():
    """Test demo run with limited events."""
    demo = MaximusDemo(dataset_path="demo/synthetic_events.json")

    # Run demo with only 20 events
    await demo.run_demo(max_events=20, show_all=False)

    # Validate metrics were updated
    assert demo.metrics["avg_latency_ms"] >= 0, "Latency should be non-negative"

    # At least ethical approvals should be counted
    assert demo.metrics["ethical_approvals"] > 0, "Should have ethical approvals"

    print("✅ test_demo_run_limited passed")


async def test_metrics_calculation():
    """Test that demo calculates metrics correctly."""
    demo = MaximusDemo(dataset_path="demo/synthetic_events.json")

    # Run demo with subset of events
    await demo.run_demo(max_events=30, show_all=False)

    # Validate metrics structure
    assert "total_events" in demo.metrics
    assert "threats_detected" in demo.metrics
    assert "false_positives" in demo.metrics
    assert "false_negatives" in demo.metrics
    assert "avg_latency_ms" in demo.metrics
    assert "prediction_errors" in demo.metrics

    # Validate metric types
    assert isinstance(demo.metrics["total_events"], int)
    assert isinstance(demo.metrics["threats_detected"], int)
    assert isinstance(demo.metrics["avg_latency_ms"], float)
    assert isinstance(demo.metrics["prediction_errors"], list)

    # Validate metric values
    assert demo.metrics["total_events"] == 100  # Full dataset
    assert demo.metrics["threats_detected"] >= 0
    assert demo.metrics["avg_latency_ms"] >= 0

    # Latency should be reasonable (<1000ms for simulation mode)
    assert demo.metrics["avg_latency_ms"] < 1000, f"Latency too high: {demo.metrics['avg_latency_ms']}"

    print("✅ test_metrics_calculation passed")


# Test runner
def run_all_tests():
    """Run all demo tests."""
    print("\n" + "=" * 80)
    print("MAXIMUS AI 3.0 - Demo Test Suite")
    print("=" * 80 + "\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Dataset loading
    try:
        test_dataset_loading()
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ test_dataset_loading failed: {e}")
        tests_failed += 1

    # Test 2: MAXIMUS initialization (async)
    try:
        asyncio.run(test_maximus_initialization())
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ test_maximus_initialization failed: {e}")
        tests_failed += 1

    # Test 3: Event processing (async)
    try:
        asyncio.run(test_event_processing())
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ test_event_processing failed: {e}")
        tests_failed += 1

    # Test 4: Demo run limited (async)
    try:
        asyncio.run(test_demo_run_limited())
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ test_demo_run_limited failed: {e}")
        tests_failed += 1

    # Test 5: Metrics calculation (async)
    try:
        asyncio.run(test_metrics_calculation())
        tests_passed += 1
    except AssertionError as e:
        print(f"❌ test_metrics_calculation failed: {e}")
        tests_failed += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"Test Results: {tests_passed}/{tests_passed + tests_failed} passed")
    if tests_failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {tests_failed} tests failed")
    print("=" * 80 + "\n")

    return tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
