"""Maximus HCL Planner Service - Fuzzy Logic Controller.

This module implements a Fuzzy Logic Controller for the Homeostatic Control
Loop (HCL) Planner Service. Fuzzy logic allows Maximus AI to reason with
uncertainty and imprecision, mimicking human-like decision-making processes
for resource management.

By defining linguistic variables (e.g., 'CPU usage is high', 'performance is low')
and fuzzy rules, this controller can generate adaptive resource alignment actions
without requiring a precise mathematical model of the system. This module is
crucial for providing robust and flexible planning capabilities in complex and
dynamic operational environments.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class FuzzyController:
    """Implements a Fuzzy Logic Controller for the HCL Planner Service.

    Fuzzy logic allows Maximus AI to reason with uncertainty and imprecision,
    mimicking human-like decision-making processes for resource management.
    """

    def __init__(self):
        """Initializes the FuzzyController, defining fuzzy sets and rules."""
        self.fuzzy_sets = self._define_fuzzy_sets()
        self.fuzzy_rules = self._define_fuzzy_rules()
        self.last_decision_time: Optional[datetime] = None
        print("[FuzzyController] Initialized Fuzzy Logic Controller.")

    def _define_fuzzy_sets(self) -> Dict[str, Dict[str, Any]]:
        """Defines linguistic terms and their membership functions for input/output variables.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary defining fuzzy sets.
        """
        # Example fuzzy sets for CPU Usage (Input)
        return {
            "cpu_usage": {
                "low": lambda x: max(0, min(1, (50 - x) / 50)),
                "medium": lambda x: max(0, min(1, (x - 25) / 50, (75 - x) / 50)),
                "high": lambda x: max(0, min(1, (x - 50) / 50)),
            },
            "health_score": {
                "poor": lambda x: max(0, min(1, (0.5 - x) / 0.5)),
                "fair": lambda x: max(0, min(1, (x - 0.25) / 0.5, (0.75 - x) / 0.5)),
                "good": lambda x: max(0, min(1, (x - 0.5) / 0.5)),
            },
            "performance_priority": {
                "low": lambda x: max(0, min(1, (0.5 - x) / 0.5)),
                "medium": lambda x: max(0, min(1, (x - 0.25) / 0.5, (0.75 - x) / 0.5)),
                "high": lambda x: max(0, min(1, (x - 0.5) / 0.5)),
            },
        }

    def _define_fuzzy_rules(self) -> List[Dict[str, Any]]:
        """Defines fuzzy rules that map input conditions to output actions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a fuzzy rule.
        """
        # Example fuzzy rules
        return [
            {
                "IF": {"cpu_usage": "high", "health_score": "poor"},
                "THEN": {"action": "scale_up", "intensity": "high"},
            },
            {
                "IF": {"cpu_usage": "medium", "health_score": "fair"},
                "THEN": {"action": "optimize_memory", "intensity": "medium"},
            },
            {
                "IF": {"cpu_usage": "low", "health_score": "good"},
                "THEN": {"action": "no_action", "intensity": "low"},
            },
            {
                "IF": {"performance_priority": "high", "cpu_usage": "medium"},
                "THEN": {"action": "scale_up", "intensity": "medium"},
            },
        ]

    def _fuzzify(self, variable_name: str, value: float) -> Dict[str, float]:
        """Converts a crisp input value into fuzzy membership values for a given variable.

        Args:
            variable_name (str): The name of the linguistic variable.
            value (float): The crisp input value.

        Returns:
            Dict[str, float]: A dictionary of membership values for each linguistic term.
        """
        memberships = {}
        if variable_name in self.fuzzy_sets:
            for term, func in self.fuzzy_sets[variable_name].items():
                memberships[term] = func(value)
        return memberships

    def _infer(self, fuzzified_inputs: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Applies fuzzy rules to fuzzified inputs to infer output actions.

        Args:
            fuzzified_inputs (Dict[str, Dict[str, float]]): Fuzzified input variables.

        Returns:
            Dict[str, float]: A dictionary of inferred output actions and their strengths.
        """
        inferred_actions = defaultdict(float)
        for rule in self.fuzzy_rules:
            antecedent_strength = 1.0
            for var, term in rule["IF"].items():
                antecedent_strength = min(antecedent_strength, fuzzified_inputs.get(var, {}).get(term, 0.0))

            for action, intensity_term in rule["THEN"].items():
                # For simplicity, we'll just take the max strength for each action
                inferred_actions[action] = max(inferred_actions[action], antecedent_strength)
        return inferred_actions

    def _defuzzify(self, inferred_actions: Dict[str, float]) -> List[Dict[str, Any]]:
        """Converts inferred fuzzy actions into crisp, actionable commands.

        Args:
            inferred_actions (Dict[str, float]): Inferred output actions and their strengths.

        Returns:
            List[Dict[str, Any]]: A list of crisp, actionable commands.
        """
        crisp_actions = []
        for action_type, strength in inferred_actions.items():
            if strength > 0.3:  # Only consider actions with sufficient strength
                # Simple defuzzification: higher strength means more aggressive action
                if action_type == "scale_up":
                    replicas = 1 if strength < 0.6 else 2
                    crisp_actions.append(
                        {
                            "type": "scale_deployment",
                            "parameters": {
                                "deployment_name": "maximus-core",
                                "replicas": replicas,
                            },
                        }
                    )
                elif action_type == "optimize_memory":
                    memory_limit = "1Gi" if strength < 0.6 else "512Mi"
                    crisp_actions.append(
                        {
                            "type": "update_resource_limits",
                            "parameters": {
                                "deployment_name": "maximus-core",
                                "memory_limit": memory_limit,
                            },
                        }
                    )
                elif action_type == "no_action":
                    if not crisp_actions:  # Only add if no other actions are suggested
                        crisp_actions.append(
                            {
                                "type": "log_status",
                                "parameters": {"message": "System stable, no action needed."},
                            }
                        )
        return crisp_actions

    def generate_actions(
        self, health_score: float, cpu_usage: float, performance_priority: float
    ) -> List[Dict[str, Any]]:
        """Generates a list of actionable commands based on fuzzy logic.

        Args:
            health_score (float): The overall system health score (0.0 to 1.0).
            cpu_usage (float): Current CPU utilization (0-100%).
            performance_priority (float): Priority for performance (0.0 to 1.0).

        Returns:
            List[Dict[str, Any]]: A list of crisp, actionable commands.
        """
        print("[FuzzyController] Generating actions using fuzzy logic.")
        self.last_decision_time = datetime.now()

        fuzzified_inputs = {
            "cpu_usage": self._fuzzify("cpu_usage", cpu_usage),
            "health_score": self._fuzzify("health_score", health_score),
            "performance_priority": self._fuzzify("performance_priority", performance_priority),
        }

        inferred_actions = self._infer(fuzzified_inputs)
        crisp_actions = self._defuzzify(inferred_actions)

        return crisp_actions

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the fuzzy controller.

        Returns:
            Dict[str, Any]: A dictionary with the current status and last decision time.
        """
        return {
            "status": "active",
            "last_decision": (self.last_decision_time.isoformat() if self.last_decision_time else "N/A"),
            "fuzzy_sets_count": len(self.fuzzy_sets),
            "fuzzy_rules_count": len(self.fuzzy_rules),
        }
