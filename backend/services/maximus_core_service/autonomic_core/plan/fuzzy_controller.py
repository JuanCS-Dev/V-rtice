"""Fuzzy Logic Controller - Mode Selection"""

import logging

import numpy as np

try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl

    SKFUZZY_AVAILABLE = True
except ImportError:
    SKFUZZY_AVAILABLE = False
    logging.warning("scikit-fuzzy not available, using fallback mode selection")

logger = logging.getLogger(__name__)


class FuzzyLogicController:
    """Fuzzy controller for operational mode selection."""

    def __init__(self):
        if SKFUZZY_AVAILABLE:
            self._setup_fuzzy_system()
        else:
            logger.warning("Using rule-based fallback (install scikit-fuzzy for full functionality)")

    def _setup_fuzzy_system(self):
        """Setup fuzzy inference system."""
        # Input variables
        self.traffic = ctrl.Antecedent(np.arange(0, 101, 1), "traffic")
        self.alerts = ctrl.Antecedent(np.arange(0, 101, 1), "alerts")
        self.sla_risk = ctrl.Antecedent(np.arange(0, 101, 1), "sla_risk")

        # Output variable (0=EFFICIENT, 1=BALANCED, 2=HIGH_PERF)
        self.mode = ctrl.Consequent(np.arange(0, 3, 1), "mode")

        # Membership functions
        self.traffic["low"] = fuzz.trimf(self.traffic.universe, [0, 0, 50])
        self.traffic["medium"] = fuzz.trimf(self.traffic.universe, [25, 50, 75])
        self.traffic["high"] = fuzz.trimf(self.traffic.universe, [50, 100, 100])

        self.alerts["low"] = fuzz.trimf(self.alerts.universe, [0, 0, 30])
        self.alerts["medium"] = fuzz.trimf(self.alerts.universe, [20, 50, 80])
        self.alerts["high"] = fuzz.trimf(self.alerts.universe, [70, 100, 100])

        # Rules
        rules = [
            ctrl.Rule(
                self.traffic["high"] | self.alerts["high"],
                self.mode["high_performance"],
            ),
            ctrl.Rule(self.traffic["low"] & self.alerts["low"], self.mode["energy_efficient"]),
        ]

        self.controller = ctrl.ControlSystem(rules)
        self.simulation = ctrl.ControlSystemSimulation(self.controller)

    def decide_mode(self, traffic: float, alerts: float, sla_risk: float) -> str:
        """
        Decide operational mode based on system state.

        Args:
            traffic: Traffic level 0-100%
            alerts: Alert severity 0-100
            sla_risk: SLA breach risk 0-100

        Returns:
            Mode name: 'HIGH_PERFORMANCE', 'BALANCED', or 'ENERGY_EFFICIENT'
        """
        if not SKFUZZY_AVAILABLE:
            return self._fallback_mode_selection(traffic, alerts, sla_risk)

        try:
            self.simulation.input["traffic"] = traffic
            self.simulation.input["alerts"] = alerts
            self.simulation.input["sla_risk"] = sla_risk
            self.simulation.compute()

            mode_value = self.simulation.output["mode"]

            if mode_value >= 1.5:
                return "HIGH_PERFORMANCE"
            if mode_value >= 0.5:
                return "BALANCED"
            return "ENERGY_EFFICIENT"

        except Exception as e:
            logger.error(f"Fuzzy controller error: {e}")
            return self._fallback_mode_selection(traffic, alerts, sla_risk)

    def _fallback_mode_selection(self, traffic: float, alerts: float, sla_risk: float) -> str:
        """Simple rule-based fallback."""
        if traffic > 70 or alerts > 50 or sla_risk > 60:
            return "HIGH_PERFORMANCE"
        if traffic < 30 and alerts < 20 and sla_risk < 20:
            return "ENERGY_EFFICIENT"
        return "BALANCED"
