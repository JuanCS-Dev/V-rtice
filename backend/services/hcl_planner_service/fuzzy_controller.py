"""
HCL Planner - Fuzzy Logic Controller
=====================================
Fuzzy logic for operational mode selection.
Maps crisp inputs (metrics) to fuzzy operational modes.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class FuzzyOperationalController:
    """
    Fuzzy Logic Controller for HCL operational modes.

    Inputs:
    - CPU usage (0-100%)
    - Memory usage (0-100%)
    - Error rate (0-100 errors/min)
    - Latency (0-1000ms)

    Output:
    - Operational mode score (0-100)
      0-33: ENERGY_EFFICIENT
      34-66: BALANCED
      67-100: HIGH_PERFORMANCE
    """

    def __init__(self):
        """Initialize fuzzy controller"""
        logger.info("Initializing Fuzzy Logic Controller")

        # Define input universes
        self.cpu_usage = ctrl.Antecedent(np.arange(0, 101, 1), 'cpu_usage')
        self.memory_usage = ctrl.Antecedent(np.arange(0, 101, 1), 'memory_usage')
        self.error_rate = ctrl.Antecedent(np.arange(0, 101, 1), 'error_rate')
        self.latency = ctrl.Antecedent(np.arange(0, 1001, 1), 'latency')

        # Define output universe
        self.mode_score = ctrl.Consequent(np.arange(0, 101, 1), 'mode_score')

        # Define membership functions for CPU
        self.cpu_usage['low'] = fuzz.trimf(self.cpu_usage.universe, [0, 0, 40])
        self.cpu_usage['medium'] = fuzz.trimf(self.cpu_usage.universe, [30, 50, 70])
        self.cpu_usage['high'] = fuzz.trimf(self.cpu_usage.universe, [60, 100, 100])

        # Define membership functions for Memory
        self.memory_usage['low'] = fuzz.trimf(self.memory_usage.universe, [0, 0, 50])
        self.memory_usage['medium'] = fuzz.trimf(self.memory_usage.universe, [40, 60, 80])
        self.memory_usage['high'] = fuzz.trimf(self.memory_usage.universe, [70, 100, 100])

        # Define membership functions for Error Rate
        self.error_rate['low'] = fuzz.trimf(self.error_rate.universe, [0, 0, 20])
        self.error_rate['medium'] = fuzz.trimf(self.error_rate.universe, [15, 30, 50])
        self.error_rate['high'] = fuzz.trimf(self.error_rate.universe, [40, 100, 100])

        # Define membership functions for Latency
        self.latency['low'] = fuzz.trimf(self.latency.universe, [0, 0, 200])
        self.latency['medium'] = fuzz.trimf(self.latency.universe, [150, 400, 600])
        self.latency['high'] = fuzz.trimf(self.latency.universe, [500, 1000, 1000])

        # Define membership functions for Mode Score
        self.mode_score['energy_efficient'] = fuzz.trimf(self.mode_score.universe, [0, 0, 33])
        self.mode_score['balanced'] = fuzz.trimf(self.mode_score.universe, [20, 50, 80])
        self.mode_score['high_performance'] = fuzz.trimf(self.mode_score.universe, [67, 100, 100])

        # Define fuzzy rules
        self.rules = self._create_rules()

        # Create control system
        self.control_system = ctrl.ControlSystem(self.rules)
        self.controller = ctrl.ControlSystemSimulation(self.control_system)

        logger.info("Fuzzy controller initialized with {} rules".format(len(self.rules)))

    def _create_rules(self):
        """Create fuzzy inference rules"""
        rules = []

        # Rule 1: Low resource usage → Energy Efficient
        rules.append(ctrl.Rule(
            self.cpu_usage['low'] & self.memory_usage['low'] &
            self.error_rate['low'] & self.latency['low'],
            self.mode_score['energy_efficient']
        ))

        # Rule 2: Medium everything → Balanced
        rules.append(ctrl.Rule(
            self.cpu_usage['medium'] & self.memory_usage['medium'],
            self.mode_score['balanced']
        ))

        # Rule 3: High CPU or Memory → High Performance
        rules.append(ctrl.Rule(
            self.cpu_usage['high'] | self.memory_usage['high'],
            self.mode_score['high_performance']
        ))

        # Rule 4: High errors → High Performance (need resources to recover)
        rules.append(ctrl.Rule(
            self.error_rate['high'],
            self.mode_score['high_performance']
        ))

        # Rule 5: High latency → High Performance
        rules.append(ctrl.Rule(
            self.latency['high'],
            self.mode_score['high_performance']
        ))

        # Rule 6: Low CPU but high latency → High Performance
        rules.append(ctrl.Rule(
            self.cpu_usage['low'] & self.latency['high'],
            self.mode_score['high_performance']
        ))

        # Rule 7: High CPU but low errors/latency → Balanced (sustainable)
        rules.append(ctrl.Rule(
            self.cpu_usage['high'] & self.error_rate['low'] & self.latency['low'],
            self.mode_score['balanced']
        ))

        # Rule 8: Everything low except memory → Balanced
        rules.append(ctrl.Rule(
            self.cpu_usage['low'] & self.memory_usage['medium'] &
            self.error_rate['low'] & self.latency['low'],
            self.mode_score['balanced']
        ))

        # Rule 9: Spike in errors regardless of resources → High Performance
        rules.append(ctrl.Rule(
            self.error_rate['medium'] & self.latency['medium'],
            self.mode_score['high_performance']
        ))

        # Rule 10: All low → Energy Efficient
        rules.append(ctrl.Rule(
            self.cpu_usage['low'] & self.memory_usage['low'] &
            self.error_rate['low'],
            self.mode_score['energy_efficient']
        ))

        return rules

    def decide(
        self,
        cpu: float,
        memory: float,
        error_rate: float,
        latency: float
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Make operational mode decision.

        Args:
            cpu: CPU usage (0-100%)
            memory: Memory usage (0-100%)
            error_rate: Errors per minute (0-100)
            latency: Network latency p99 (0-1000ms)

        Returns:
            (mode, confidence, details)
            mode: "ENERGY_EFFICIENT", "BALANCED", or "HIGH_PERFORMANCE"
            confidence: 0-1
            details: Input values and intermediate scores
        """
        # Clip inputs to valid ranges
        cpu = np.clip(cpu, 0, 100)
        memory = np.clip(memory, 0, 100)
        error_rate = np.clip(error_rate, 0, 100)
        latency = np.clip(latency, 0, 1000)

        # Set inputs
        self.controller.input['cpu_usage'] = cpu
        self.controller.input['memory_usage'] = memory
        self.controller.input['error_rate'] = error_rate
        self.controller.input['latency'] = latency

        # Compute
        try:
            self.controller.compute()
            score = self.controller.output['mode_score']
        except Exception as e:
            logger.error(f"Fuzzy computation error: {e}")
            # Fallback to simple thresholding
            if cpu > 80 or memory > 80 or error_rate > 50 or latency > 500:
                score = 85  # HIGH_PERFORMANCE
            elif cpu < 30 and memory < 50 and error_rate < 10 and latency < 150:
                score = 15  # ENERGY_EFFICIENT
            else:
                score = 50  # BALANCED

        # Map score to mode
        if score < 33:
            mode = "ENERGY_EFFICIENT"
            confidence = (33 - score) / 33  # Higher confidence as score approaches 0
        elif score < 67:
            mode = "BALANCED"
            # Confidence is high in the middle of the range
            distance_from_center = abs(score - 50)
            confidence = 1.0 - (distance_from_center / 17)  # 17 is half of 33
        else:
            mode = "HIGH_PERFORMANCE"
            confidence = (score - 67) / 33  # Higher confidence as score approaches 100

        confidence = np.clip(confidence, 0.0, 1.0)

        details = {
            "cpu_usage": cpu,
            "memory_usage": memory,
            "error_rate": error_rate,
            "latency": latency,
            "fuzzy_score": score,
            "confidence": confidence
        }

        logger.info(f"Fuzzy decision: {mode} (score={score:.1f}, confidence={confidence:.2f})")

        return mode, confidence, details

    def visualize_membership_functions(self, save_path: str = None):
        """
        Visualize membership functions (for debugging/analysis).
        Requires matplotlib.
        """
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(3, 2, figsize=(12, 12))

            # CPU
            self.cpu_usage.view(ax=axes[0, 0])
            axes[0, 0].set_title('CPU Usage')

            # Memory
            self.memory_usage.view(ax=axes[0, 1])
            axes[0, 1].set_title('Memory Usage')

            # Error Rate
            self.error_rate.view(ax=axes[1, 0])
            axes[1, 0].set_title('Error Rate')

            # Latency
            self.latency.view(ax=axes[1, 1])
            axes[1, 1].set_title('Latency')

            # Mode Score
            self.mode_score.view(ax=axes[2, 0])
            axes[2, 0].set_title('Operational Mode Score')

            # Hide last subplot
            axes[2, 1].axis('off')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                logger.info(f"Membership functions saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            logger.warning("matplotlib not installed, cannot visualize")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    controller = FuzzyOperationalController()

    # Test scenarios
    scenarios = [
        {"cpu": 20, "memory": 30, "error_rate": 5, "latency": 80, "expected": "ENERGY_EFFICIENT"},
        {"cpu": 50, "memory": 55, "error_rate": 15, "latency": 250, "expected": "BALANCED"},
        {"cpu": 85, "memory": 78, "error_rate": 45, "latency": 600, "expected": "HIGH_PERFORMANCE"},
        {"cpu": 90, "memory": 90, "error_rate": 80, "latency": 850, "expected": "HIGH_PERFORMANCE"},
        {"cpu": 15, "memory": 20, "error_rate": 2, "latency": 50, "expected": "ENERGY_EFFICIENT"},
    ]

    print("\n" + "="*80)
    print("FUZZY LOGIC CONTROLLER TEST")
    print("="*80 + "\n")

    for i, scenario in enumerate(scenarios, 1):
        print(f"Scenario {i}:")
        mode, confidence, details = controller.decide(
            scenario["cpu"],
            scenario["memory"],
            scenario["error_rate"],
            scenario["latency"]
        )

        match = "✓" if mode == scenario["expected"] else "✗"
        print(f"  Expected: {scenario['expected']}")
        print(f"  Got: {mode} (confidence={confidence:.2f}) {match}")
        print(f"  Score: {details['fuzzy_score']:.1f}")
        print()
