"""HCL Planner Service - Fuzzy Logic Controller.

This module implements a Fuzzy Logic Controller for selecting the HCL's
operational mode. It uses the `skfuzzy` library to map crisp input values
(like CPU usage and latency) to a fuzzy output (the operational mode score),
which is then translated into one of three modes: ENERGY_EFFICIENT, BALANCED,
or HIGH_PERFORMANCE.
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class FuzzyOperationalController:
    """A Fuzzy Logic Controller for determining the HCL operational mode.

    This controller uses a set of human-readable rules to decide the most
    appropriate operational mode based on the current state of the system.

    Attributes:
        control_system (ctrl.ControlSystem): The fuzzy control system instance.
        controller (ctrl.ControlSystemSimulation): The simulation object for computation.
    """

    def __init__(self):
        """Initializes the fuzzy controller, its variables, and rules."""
        # Define fuzzy antecedents (inputs)
        self.cpu_usage = ctrl.Antecedent(np.arange(0, 101, 1), 'cpu_usage')
        self.latency = ctrl.Antecedent(np.arange(0, 1001, 1), 'latency')
        
        # Define fuzzy consequent (output)
        self.mode_score = ctrl.Consequent(np.arange(0, 101, 1), 'mode_score')

        # Define membership functions for inputs
        self.cpu_usage.automf(3, 'poor', 'average', 'good') # Renamed for clarity
        self.latency['low'] = fuzz.trimf(self.latency.universe, [0, 0, 200])
        self.latency['high'] = fuzz.trimf(self.latency.universe, [500, 1000, 1000])

        # Define membership functions for output
        self.mode_score['energy_efficient'] = fuzz.trimf(self.mode_score.universe, [0, 0, 33])
        self.mode_score['balanced'] = fuzz.trimf(self.mode_score.universe, [33, 50, 67])
        self.mode_score['high_performance'] = fuzz.trimf(self.mode_score.universe, [67, 100, 100])

        # Define fuzzy rules
        rule1 = ctrl.Rule(self.cpu_usage['poor'] & self.latency['low'], self.mode_score['energy_efficient'])
        rule2 = ctrl.Rule(self.cpu_usage['average'], self.mode_score['balanced'])
        rule3 = ctrl.Rule(self.cpu_usage['good'] | self.latency['high'], self.mode_score['high_performance'])

        self.control_system = ctrl.ControlSystem([rule1, rule2, rule3])
        self.controller = ctrl.ControlSystemSimulation(self.control_system)

    def decide(self, cpu: float, latency: float) -> Tuple[str, float, Dict[str, float]]:
        """Makes an operational mode decision based on crisp input values.

        Args:
            cpu (float): The current CPU usage percentage (0-100).
            latency (float): The current p99 network latency in ms (0-1000).

        Returns:
            Tuple[str, float, Dict[str, float]]: A tuple containing:
                - The decided operational mode (str).
                - The confidence in the decision (float).
                - A dictionary of details, including the final fuzzy score.
        """
        self.controller.input['cpu_usage'] = np.clip(cpu, 0, 100)
        self.controller.input['latency'] = np.clip(latency, 0, 1000)
        self.controller.compute()
        
        score = self.controller.output['mode_score']
        if score < 33: mode = "ENERGY_EFFICIENT"
        elif score < 67: mode = "BALANCED"
        else: mode = "HIGH_PERFORMANCE"

        # Confidence is a simplified metric for this example
        confidence = 1.0 - (abs(score - 50) / 50) if mode == "BALANCED" else abs(score - 50) / 50

        return mode, np.clip(confidence, 0, 1), {"fuzzy_score": score}