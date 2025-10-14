"""
Theory of Mind Benchmark Runner
================================

Runs Sally-Anne false belief tests to validate ToM accuracy.
Implements GAP 3 from ToM Engine refinement directive (FASE 3).

Target: tom_accuracy ≥ 85% across 10 scenarios

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

from typing import Dict, Any, List, Callable
import logging
from datetime import datetime

from compassion.sally_anne_dataset import (
    SALLY_ANNE_SCENARIOS,
    EXPECTED_ANSWERS,
    DIFFICULTY_LEVELS,
    get_all_scenarios,
)

logger = logging.getLogger(__name__)


class ToMBenchmarkRunner:
    """Runs Theory of Mind benchmarks using Sally-Anne scenarios.

    Validates false belief tracking accuracy against 10 test scenarios.

    Attributes:
        results: List of benchmark results (one per scenario)
        total_scenarios: Total number of scenarios run
        correct_count: Number of correct predictions
    """

    def __init__(self):
        """Initialize ToMBenchmarkRunner."""
        self.results: List[Dict[str, Any]] = []
        self.total_scenarios = 0
        self.correct_count = 0

        logger.info("ToMBenchmarkRunner initialized")

    async def run_scenario(
        self, scenario: Dict[str, Any], predicted_answer: str
    ) -> Dict[str, Any]:
        """Run a single Sally-Anne scenario.

        Args:
            scenario: Scenario dictionary from dataset
            predicted_answer: ToM engine's predicted answer

        Returns:
            Result dictionary with correctness evaluation
        """
        scenario_id = scenario["id"]
        expected = scenario["correct_answer"]
        is_correct = predicted_answer == expected

        result = {
            "scenario_id": scenario_id,
            "description": scenario["description"],
            "predicted": predicted_answer,
            "expected": expected,
            "correct": is_correct,
            "rationale": scenario["rationale"],
            "timestamp": datetime.utcnow(),
        }

        self.results.append(result)
        self.total_scenarios += 1

        if is_correct:
            self.correct_count += 1
            logger.info(f"✅ PASS: {scenario_id} (predicted={predicted_answer})")
        else:
            logger.warning(
                f"❌ FAIL: {scenario_id} (predicted={predicted_answer}, "
                f"expected={expected})"
            )

        return result

    async def run_all_scenarios(
        self, predictor: Callable[[Dict[str, Any]], str]
    ) -> List[Dict[str, Any]]:
        """Run all 10 Sally-Anne scenarios.

        Args:
            predictor: Function that takes scenario and returns predicted answer

        Returns:
            List of all results
        """
        scenarios = get_all_scenarios()

        for scenario in scenarios:
            predicted = predictor(scenario)
            await self.run_scenario(scenario, predicted)

        logger.info(
            f"Benchmark complete: {self.correct_count}/{self.total_scenarios} correct "
            f"({self.get_accuracy():.1%})"
        )

        return self.results

    def get_accuracy(self) -> float:
        """Calculate overall accuracy.

        Returns:
            Accuracy [0.0, 1.0], or 0.0 if no scenarios run
        """
        if self.total_scenarios == 0:
            return 0.0

        return self.correct_count / self.total_scenarios

    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive benchmark report.

        Returns:
            Report dictionary with accuracy and detailed results
        """
        return {
            "total_scenarios": self.total_scenarios,
            "correct_count": self.correct_count,
            "accuracy": self.get_accuracy(),
            "results": self.results,
            "meets_target": self.get_accuracy() >= 0.85,
        }

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get only incorrect predictions.

        Returns:
            List of error results
        """
        return [r for r in self.results if not r["correct"]]

    def get_accuracy_by_difficulty(self) -> Dict[str, float]:
        """Calculate accuracy breakdown by difficulty level.

        Returns:
            Dictionary mapping difficulty → accuracy
        """
        accuracy_by_diff = {}

        for difficulty, scenario_ids in DIFFICULTY_LEVELS.items():
            # Filter results for this difficulty
            diff_results = [
                r for r in self.results if r["scenario_id"] in scenario_ids
            ]

            if not diff_results:
                accuracy_by_diff[difficulty] = 0.0
            else:
                correct = sum(1 for r in diff_results if r["correct"])
                accuracy_by_diff[difficulty] = correct / len(diff_results)

        return accuracy_by_diff

    def reset(self) -> None:
        """Reset benchmark state (clear all results)."""
        self.results = []
        self.total_scenarios = 0
        self.correct_count = 0

        logger.info("Benchmark reset")

    def __repr__(self) -> str:
        accuracy = self.get_accuracy()
        return (
            f"ToMBenchmarkRunner(scenarios={self.total_scenarios}, "
            f"correct={self.correct_count}, "
            f"accuracy={accuracy:.1%})"
        )
