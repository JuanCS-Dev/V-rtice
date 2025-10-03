"""
Resource Planner - REAL Fuzzy Logic Controller
===============================================

Planeja alocação de recursos usando Fuzzy Logic REAL.
Implementação inspirada em controladores fuzzy industriais.

Sem bibliotecas externas - implementação do zero usando numpy.
Baseado em Mamdani Fuzzy Inference System.

Variáveis de Entrada:
- CPU Load (Low, Medium, High, Critical)
- Memory Load (Low, Medium, High, Critical)
- Latency (Acceptable, Elevated, High, Critical)
- Trend (Decreasing, Stable, Increasing, Rapid)

Variável de Saída:
- Action Intensity (None, Minimal, Moderate, Aggressive)
- Target Mode (Energy, Balanced, Performance)
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

from .homeostatic_control import OperationalMode, SystemState
from .resource_analyzer import ResourceAnalysis


class ActionType(str, Enum):
    """Tipos de ação de alocação"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    OPTIMIZE_MEMORY = "optimize_memory"
    THROTTLE_REQUESTS = "throttle_requests"
    GARBAGE_COLLECT = "garbage_collect"
    RESTART_WORKERS = "restart_workers"
    NO_ACTION = "no_action"


class ResourcePlan(BaseModel):
    """Plano de alocação de recursos"""
    timestamp: str
    target_mode: OperationalMode
    actions: List[ActionType]
    action_intensity: float  # 0-1
    reasoning: str

    # Configurações específicas
    target_cpu_limit: Optional[float] = None  # % limit
    target_memory_limit: Optional[float] = None  # % limit
    target_max_workers: Optional[int] = None
    target_request_rate_limit: Optional[int] = None


class FuzzySet:
    """
    Conjunto Fuzzy - Implementação REAL.

    Usa funções de pertinência (membership functions):
    - Triangular
    - Trapezoidal
    - Gaussian (opcional)
    """

    def __init__(self, name: str, points: List[float], shape: str = "triangular"):
        self.name = name
        self.points = points
        self.shape = shape

    def membership(self, x: float) -> float:
        """
        Calcula grau de pertinência (membership degree) REAL.

        Returns:
            Valor entre 0 e 1
        """
        if self.shape == "triangular":
            # Triangular: [a, b, c]
            # membership = 0 se x <= a ou x >= c
            # membership cresce linearmente de a até b
            # membership decresce linearmente de b até c
            a, b, c = self.points

            if x <= a or x >= c:
                return 0.0
            elif x == b:
                return 1.0
            elif x < b:
                return (x - a) / (b - a)
            else:
                return (c - x) / (c - b)

        elif self.shape == "trapezoidal":
            # Trapezoidal: [a, b, c, d]
            a, b, c, d = self.points

            if x <= a or x >= d:
                return 0.0
            elif b <= x <= c:
                return 1.0
            elif x < b:
                return (x - a) / (b - a)
            else:
                return (d - x) / (d - c)

        elif self.shape == "gaussian":
            # Gaussian: [mean, std]
            mean, std = self.points
            return np.exp(-0.5 * ((x - mean) / std) ** 2)

        return 0.0


class FuzzyVariable:
    """Variável Fuzzy com múltiplos conjuntos"""

    def __init__(self, name: str, universe_min: float, universe_max: float):
        self.name = name
        self.universe_min = universe_min
        self.universe_max = universe_max
        self.sets: Dict[str, FuzzySet] = {}

    def add_set(self, fuzzy_set: FuzzySet):
        """Adiciona conjunto fuzzy"""
        self.sets[fuzzy_set.name] = fuzzy_set

    def fuzzify(self, value: float) -> Dict[str, float]:
        """
        Fuzzificação REAL - converte valor crisp em graus de pertinência.

        Returns:
            Dict com grau de pertinência para cada conjunto
        """
        memberships = {}
        for set_name, fuzzy_set in self.sets.items():
            memberships[set_name] = fuzzy_set.membership(value)
        return memberships


class ResourcePlanner:
    """
    Planejador de recursos usando Fuzzy Logic Controller REAL.

    Implementa Mamdani Fuzzy Inference System:
    1. Fuzzification - Converter inputs em graus de pertinência
    2. Rule Evaluation - Aplicar regras fuzzy
    3. Aggregation - Combinar resultados
    4. Defuzzification - Converter de volta para valores crisp
    """

    def __init__(self):
        self._init_fuzzy_system()

    def _init_fuzzy_system(self):
        """Inicializa sistema fuzzy com variáveis e regras"""

        # ===== INPUT VARIABLES =====

        # CPU Load (0-100%)
        self.cpu_load = FuzzyVariable("cpu_load", 0, 100)
        self.cpu_load.add_set(FuzzySet("low", [0, 0, 40], "triangular"))
        self.cpu_load.add_set(FuzzySet("medium", [30, 50, 70], "triangular"))
        self.cpu_load.add_set(FuzzySet("high", [60, 80, 90], "triangular"))
        self.cpu_load.add_set(FuzzySet("critical", [85, 95, 100], "triangular"))

        # Memory Load (0-100%)
        self.memory_load = FuzzyVariable("memory_load", 0, 100)
        self.memory_load.add_set(FuzzySet("low", [0, 0, 50], "triangular"))
        self.memory_load.add_set(FuzzySet("medium", [40, 60, 75], "triangular"))
        self.memory_load.add_set(FuzzySet("high", [70, 85, 95], "triangular"))
        self.memory_load.add_set(FuzzySet("critical", [90, 95, 100], "triangular"))

        # Latency (0-500ms)
        self.latency = FuzzyVariable("latency", 0, 500)
        self.latency.add_set(FuzzySet("acceptable", [0, 0, 50], "triangular"))
        self.latency.add_set(FuzzySet("elevated", [40, 80, 150], "triangular"))
        self.latency.add_set(FuzzySet("high", [120, 200, 300], "triangular"))
        self.latency.add_set(FuzzySet("critical", [250, 400, 500], "triangular"))

        # ===== OUTPUT VARIABLE =====

        # Action Intensity (0-100)
        self.action_intensity = FuzzyVariable("action_intensity", 0, 100)
        self.action_intensity.add_set(FuzzySet("none", [0, 0, 10], "triangular"))
        self.action_intensity.add_set(FuzzySet("minimal", [5, 20, 40], "triangular"))
        self.action_intensity.add_set(FuzzySet("moderate", [30, 50, 70], "triangular"))
        self.action_intensity.add_set(FuzzySet("aggressive", [60, 80, 100], "triangular"))

        # ===== FUZZY RULES (Knowledge Base) =====
        # Formato: IF (antecedent) THEN (consequent)

        self.rules = [
            # Critical situations - AGGRESSIVE action
            {
                "if": {"cpu_load": "critical", "memory_load": "high"},
                "then": {"action_intensity": "aggressive", "mode": OperationalMode.HIGH_PERFORMANCE}
            },
            {
                "if": {"memory_load": "critical"},
                "then": {"action_intensity": "aggressive", "mode": OperationalMode.HIGH_PERFORMANCE}
            },
            {
                "if": {"latency": "critical", "cpu_load": "high"},
                "then": {"action_intensity": "aggressive", "mode": OperationalMode.HIGH_PERFORMANCE}
            },

            # High load - MODERATE action
            {
                "if": {"cpu_load": "high", "memory_load": "medium"},
                "then": {"action_intensity": "moderate", "mode": OperationalMode.HIGH_PERFORMANCE}
            },
            {
                "if": {"cpu_load": "medium", "memory_load": "high"},
                "then": {"action_intensity": "moderate", "mode": OperationalMode.BALANCED}
            },
            {
                "if": {"latency": "high"},
                "then": {"action_intensity": "moderate", "mode": OperationalMode.BALANCED}
            },

            # Medium load - MINIMAL action
            {
                "if": {"cpu_load": "medium", "memory_load": "medium"},
                "then": {"action_intensity": "minimal", "mode": OperationalMode.BALANCED}
            },
            {
                "if": {"latency": "elevated", "cpu_load": "low"},
                "then": {"action_intensity": "minimal", "mode": OperationalMode.BALANCED}
            },

            # Low load - NO action (energy efficient)
            {
                "if": {"cpu_load": "low", "memory_load": "low"},
                "then": {"action_intensity": "none", "mode": OperationalMode.ENERGY_EFFICIENT}
            },
            {
                "if": {"cpu_load": "low", "latency": "acceptable"},
                "then": {"action_intensity": "none", "mode": OperationalMode.ENERGY_EFFICIENT}
            },
        ]

    async def create_plan(
        self,
        current_state: SystemState,
        analysis: ResourceAnalysis,
        current_mode: OperationalMode
    ) -> Optional[ResourcePlan]:
        """
        Cria plano de recursos usando Fuzzy Inference REAL.

        Steps:
        1. Fuzzify inputs
        2. Evaluate rules
        3. Aggregate outputs
        4. Defuzzify to get crisp action intensity
        5. Select actions based on intensity
        """

        # ===== 1. FUZZIFICATION =====
        cpu_fuzzy = self.cpu_load.fuzzify(current_state.cpu_usage)
        memory_fuzzy = self.memory_load.fuzzify(current_state.memory_usage)
        latency_fuzzy = self.latency.fuzzify(current_state.avg_latency_ms)

        # ===== 2. RULE EVALUATION =====
        rule_outputs = []

        for rule in self.rules:
            # Calcular firing strength (grau de ativação da regra)
            firing_strength = self._evaluate_rule_antecedent(
                rule["if"],
                {"cpu_load": cpu_fuzzy, "memory_load": memory_fuzzy, "latency": latency_fuzzy}
            )

            if firing_strength > 0:
                rule_outputs.append({
                    "firing_strength": firing_strength,
                    "consequent": rule["then"]
                })

        if not rule_outputs:
            # Nenhuma regra ativada - no action
            return None

        # ===== 3. AGGREGATION =====
        # Agregar outputs usando max (Mamdani)
        aggregated_intensities = {}
        aggregated_modes = {}

        for output in rule_outputs:
            intensity_set = output["consequent"]["action_intensity"]
            mode = output["consequent"]["mode"]
            strength = output["firing_strength"]

            # Max aggregation
            if intensity_set not in aggregated_intensities:
                aggregated_intensities[intensity_set] = strength
            else:
                aggregated_intensities[intensity_set] = max(
                    aggregated_intensities[intensity_set],
                    strength
                )

            if mode not in aggregated_modes:
                aggregated_modes[mode] = strength
            else:
                aggregated_modes[mode] = max(aggregated_modes[mode], strength)

        # ===== 4. DEFUZZIFICATION (Centroid Method) =====
        action_intensity_crisp = self._defuzzify_centroid(
            aggregated_intensities,
            self.action_intensity
        )

        # Select mode with highest strength
        target_mode = max(aggregated_modes, key=aggregated_modes.get)

        # ===== 5. SELECT ACTIONS =====
        actions = self._select_actions(
            action_intensity_crisp,
            current_state,
            analysis
        )

        # ===== 6. BUILD PLAN =====
        reasoning = self._generate_reasoning(
            current_state,
            analysis,
            action_intensity_crisp,
            target_mode,
            rule_outputs
        )

        plan = ResourcePlan(
            timestamp=datetime.now().isoformat(),
            target_mode=target_mode,
            actions=actions,
            action_intensity=action_intensity_crisp / 100.0,  # Normalize to 0-1
            reasoning=reasoning
        )

        # Set specific configurations based on intensity and mode
        plan = self._configure_plan_details(plan, current_state, action_intensity_crisp)

        return plan

    def _evaluate_rule_antecedent(
        self,
        antecedent: Dict[str, str],
        fuzzified_inputs: Dict[str, Dict[str, float]]
    ) -> float:
        """
        Avalia antecedente da regra usando AND (min).

        IF cpu_load is high AND memory_load is medium
        -> firing_strength = min(membership(cpu_load, high), membership(memory_load, medium))
        """
        memberships = []

        for var_name, set_name in antecedent.items():
            if var_name in fuzzified_inputs:
                membership = fuzzified_inputs[var_name].get(set_name, 0.0)
                memberships.append(membership)

        if not memberships:
            return 0.0

        # AND operator = min
        return min(memberships)

    def _defuzzify_centroid(
        self,
        aggregated_sets: Dict[str, float],
        output_variable: FuzzyVariable
    ) -> float:
        """
        Defuzzification usando método do centróide REAL.

        Calcula centro de massa da área sob a curva de membership.
        """
        # Discretizar universo de discurso
        x = np.linspace(output_variable.universe_min, output_variable.universe_max, 100)

        # Calcular membership agregado para cada ponto
        aggregated_membership = np.zeros_like(x)

        for set_name, strength in aggregated_sets.items():
            if set_name in output_variable.sets:
                fuzzy_set = output_variable.sets[set_name]
                for i, xi in enumerate(x):
                    # Membership clipped by firing strength
                    membership = min(fuzzy_set.membership(xi), strength)
                    aggregated_membership[i] = max(aggregated_membership[i], membership)

        # Centroid = ∫(x * μ(x)) / ∫μ(x)
        numerator = np.sum(x * aggregated_membership)
        denominator = np.sum(aggregated_membership)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _select_actions(
        self,
        intensity: float,
        state: SystemState,
        analysis: ResourceAnalysis
    ) -> List[ActionType]:
        """Seleciona ações baseado em intensidade e estado"""
        actions = []

        if intensity < 10:
            # No action needed
            actions.append(ActionType.NO_ACTION)

        elif intensity < 40:
            # Minimal actions
            if state.memory_usage > 70:
                actions.append(ActionType.GARBAGE_COLLECT)

        elif intensity < 70:
            # Moderate actions
            if state.cpu_usage > 70:
                actions.append(ActionType.SCALE_UP)
            if state.memory_usage > 75:
                actions.append(ActionType.OPTIMIZE_MEMORY)
            if state.avg_latency_ms > 100:
                actions.append(ActionType.THROTTLE_REQUESTS)

        else:
            # Aggressive actions
            if state.cpu_usage > 80:
                actions.extend([ActionType.SCALE_UP, ActionType.RESTART_WORKERS])
            if state.memory_usage > 85:
                actions.extend([ActionType.OPTIMIZE_MEMORY, ActionType.GARBAGE_COLLECT])
            if state.avg_latency_ms > 150:
                actions.append(ActionType.THROTTLE_REQUESTS)

        return actions if actions else [ActionType.NO_ACTION]

    def _configure_plan_details(
        self,
        plan: ResourcePlan,
        state: SystemState,
        intensity: float
    ) -> ResourcePlan:
        """Configura detalhes específicos do plano"""

        if plan.target_mode == OperationalMode.HIGH_PERFORMANCE:
            plan.target_cpu_limit = None  # Unlimited
            plan.target_memory_limit = None
            plan.target_max_workers = 16  # Max workers
            plan.target_request_rate_limit = None  # No throttling

        elif plan.target_mode == OperationalMode.BALANCED:
            plan.target_cpu_limit = 80.0
            plan.target_memory_limit = 75.0
            plan.target_max_workers = 8
            plan.target_request_rate_limit = 1000  # req/s

        elif plan.target_mode == OperationalMode.ENERGY_EFFICIENT:
            plan.target_cpu_limit = 50.0
            plan.target_memory_limit = 60.0
            plan.target_max_workers = 4
            plan.target_request_rate_limit = 500

        return plan

    def _generate_reasoning(
        self,
        state: SystemState,
        analysis: ResourceAnalysis,
        intensity: float,
        mode: OperationalMode,
        fired_rules: List[Dict]
    ) -> str:
        """Gera explicação do raciocínio fuzzy"""

        parts = [
            f"Fuzzy analysis: CPU={state.cpu_usage:.1f}%, MEM={state.memory_usage:.1f}%, LAT={state.avg_latency_ms:.1f}ms",
            f"Action intensity: {intensity:.1f}/100",
            f"Target mode: {mode}",
            f"Fired rules: {len(fired_rules)}"
        ]

        if analysis.anomalies:
            parts.append(f"Anomalies detected: {len(analysis.anomalies)}")

        if analysis.predicted_load_trend:
            parts.append(f"Trend: {analysis.predicted_load_trend}")

        return " | ".join(parts)
