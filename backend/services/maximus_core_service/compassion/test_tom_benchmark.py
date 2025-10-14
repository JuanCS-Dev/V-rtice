"""
Test Suite for ToMBenchmarkRunner
==================================

FASE 3: Sally-Anne benchmark validation
Target: tom_accuracy ≥ 85%, coverage ≥ 95%

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import pytest
from typing import Dict, Any


# ===========================================================================
# BENCHMARK RUNNER TESTS
# ===========================================================================

@pytest.mark.asyncio
async def test_benchmark_runner_initialization():
    """Test ToMBenchmarkRunner initializes correctly."""
    from compassion.tom_benchmark import ToMBenchmarkRunner

    runner = ToMBenchmarkRunner()

    assert runner.results == []
    assert runner.total_scenarios == 0
    assert runner.correct_count == 0


@pytest.mark.asyncio
async def test_run_single_scenario_correct():
    """Test running single scenario with correct answer."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()
    scenario = get_scenario("classic_basket_box")

    # Simulate correct prediction
    predicted_answer = "basket"

    result = await runner.run_scenario(scenario, predicted_answer)

    assert result["scenario_id"] == "classic_basket_box"
    assert result["predicted"] == "basket"
    assert result["expected"] == "basket"
    assert result["correct"] is True


@pytest.mark.asyncio
async def test_run_single_scenario_incorrect():
    """Test running single scenario with incorrect answer."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()
    scenario = get_scenario("classic_basket_box")

    # Simulate incorrect prediction (Sally knows about move)
    predicted_answer = "box"  # Wrong! Sally doesn't know

    result = await runner.run_scenario(scenario, predicted_answer)

    assert result["scenario_id"] == "classic_basket_box"
    assert result["predicted"] == "box"
    assert result["expected"] == "basket"
    assert result["correct"] is False


@pytest.mark.asyncio
async def test_run_all_scenarios():
    """Test running all 10 scenarios."""
    from compassion.tom_benchmark import ToMBenchmarkRunner

    runner = ToMBenchmarkRunner()

    # Mock predictor that always returns "basket"
    def naive_predictor(scenario: Dict[str, Any]) -> str:
        return "basket"

    await runner.run_all_scenarios(naive_predictor)

    assert runner.total_scenarios == 10
    assert len(runner.results) == 10


@pytest.mark.asyncio
async def test_calculate_accuracy():
    """Test accuracy calculation."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()

    # Simulate 7 correct, 3 incorrect
    correct_scenarios = [
        "classic_basket_box",
        "sally_returns_and_sees",
        "deception_false_info",
        "third_party_tom",
        "multiple_moves",
        "partial_observation",
        "inference_from_evidence",
    ]

    for scenario_id in correct_scenarios:
        scenario = get_scenario(scenario_id)
        await runner.run_scenario(scenario, scenario["correct_answer"])

    # Add 3 incorrect
    scenario = get_scenario("memory_decay")
    await runner.run_scenario(scenario, "basket")  # Wrong answer

    scenario = get_scenario("conflicting_evidence")
    await runner.run_scenario(scenario, "box")  # Wrong answer

    scenario = get_scenario("nested_second_order")
    await runner.run_scenario(scenario, "box")  # Wrong answer

    accuracy = runner.get_accuracy()
    assert abs(accuracy - 0.7) < 0.01  # 7/10 = 70%


@pytest.mark.asyncio
async def test_get_report():
    """Test comprehensive benchmark report generation."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()

    # Run a few scenarios
    await runner.run_scenario(get_scenario("classic_basket_box"), "basket")
    await runner.run_scenario(get_scenario("sally_returns_and_sees"), "box")

    report = runner.get_report()

    assert "total_scenarios" in report
    assert "correct_count" in report
    assert "accuracy" in report
    assert "results" in report
    assert report["total_scenarios"] == 2
    assert report["correct_count"] == 2
    assert report["accuracy"] == 1.0


@pytest.mark.asyncio
async def test_get_errors_only():
    """Test filtering for incorrect predictions only."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()

    # 2 correct, 1 incorrect
    await runner.run_scenario(get_scenario("classic_basket_box"), "basket")
    await runner.run_scenario(get_scenario("sally_returns_and_sees"), "basket")  # Wrong!
    await runner.run_scenario(get_scenario("deception_false_info"), "basket")

    errors = runner.get_errors()

    assert len(errors) == 1
    assert errors[0]["scenario_id"] == "sally_returns_and_sees"
    assert errors[0]["correct"] is False


@pytest.mark.asyncio
async def test_accuracy_by_difficulty():
    """Test accuracy breakdown by difficulty level."""
    from compassion.tom_benchmark import ToMBenchmarkRunner

    runner = ToMBenchmarkRunner()

    # Mock predictor with varying accuracy
    def predictor(scenario: Dict[str, Any]) -> str:
        # Correct for basic, wrong for advanced
        if scenario["id"] in ["classic_basket_box", "sally_returns_and_sees"]:
            return scenario["correct_answer"]
        else:
            return "basket"  # Default guess

    await runner.run_all_scenarios(predictor)

    accuracy_by_diff = runner.get_accuracy_by_difficulty()

    assert "basic" in accuracy_by_diff
    assert "intermediate" in accuracy_by_diff
    assert "advanced" in accuracy_by_diff

    # Basic should be 100% (2/2)
    assert accuracy_by_diff["basic"] == 1.0


@pytest.mark.asyncio
async def test_reset_benchmark():
    """Test resetting benchmark state."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()

    # Run some scenarios
    await runner.run_scenario(get_scenario("classic_basket_box"), "basket")
    await runner.run_scenario(get_scenario("sally_returns_and_sees"), "box")

    assert runner.total_scenarios == 2

    # Reset
    runner.reset()

    assert runner.total_scenarios == 0
    assert runner.correct_count == 0
    assert len(runner.results) == 0


# ===========================================================================
# TARGET ACCURACY VALIDATION
# ===========================================================================

@pytest.mark.asyncio
async def test_target_accuracy_85_percent():
    """Test that benchmark can validate ≥85% accuracy target."""
    from compassion.tom_benchmark import ToMBenchmarkRunner

    runner = ToMBenchmarkRunner()

    # Mock high-accuracy predictor (9/10 correct)
    def good_predictor(scenario: Dict[str, Any]) -> str:
        # Get all correct except memory_decay
        if scenario["id"] == "memory_decay":
            return "basket"  # Intentional error
        return scenario["correct_answer"]

    await runner.run_all_scenarios(good_predictor)

    accuracy = runner.get_accuracy()
    assert accuracy >= 0.85  # 9/10 = 90% ≥ 85% target


@pytest.mark.asyncio
async def test_repr_method():
    """Test __repr__ returns useful debug info."""
    from compassion.tom_benchmark import ToMBenchmarkRunner
    from compassion.sally_anne_dataset import get_scenario

    runner = ToMBenchmarkRunner()

    await runner.run_scenario(get_scenario("classic_basket_box"), "basket")
    await runner.run_scenario(get_scenario("sally_returns_and_sees"), "basket")

    repr_str = repr(runner)
    assert "ToMBenchmarkRunner" in repr_str
    assert "2" in repr_str  # 2 scenarios


# ===========================================================================
# DATASET HELPER FUNCTION TESTS
# ===========================================================================

def test_get_scenario_by_id():
    """Test retrieving scenario by ID."""
    from compassion.sally_anne_dataset import get_scenario

    scenario = get_scenario("classic_basket_box")

    assert scenario["id"] == "classic_basket_box"
    assert "setup" in scenario
    assert "question" in scenario
    assert "correct_answer" in scenario


def test_get_scenario_invalid_id():
    """Test get_scenario raises KeyError for invalid ID."""
    from compassion.sally_anne_dataset import get_scenario

    with pytest.raises(KeyError, match="nonexistent"):
        get_scenario("nonexistent_scenario")


def test_get_scenarios_by_difficulty():
    """Test filtering scenarios by difficulty level."""
    from compassion.sally_anne_dataset import get_scenarios_by_difficulty

    basic_scenarios = get_scenarios_by_difficulty("basic")
    assert len(basic_scenarios) == 2

    intermediate_scenarios = get_scenarios_by_difficulty("intermediate")
    assert len(intermediate_scenarios) == 4

    advanced_scenarios = get_scenarios_by_difficulty("advanced")
    assert len(advanced_scenarios) == 4


def test_get_scenarios_invalid_difficulty():
    """Test get_scenarios_by_difficulty raises error for invalid difficulty."""
    from compassion.sally_anne_dataset import get_scenarios_by_difficulty

    with pytest.raises(ValueError, match="Invalid difficulty"):
        get_scenarios_by_difficulty("impossible")


def test_get_all_scenarios():
    """Test retrieving all 10 scenarios."""
    from compassion.sally_anne_dataset import get_all_scenarios

    scenarios = get_all_scenarios()

    assert len(scenarios) == 10
    assert all("id" in s for s in scenarios)
    assert all("correct_answer" in s for s in scenarios)
