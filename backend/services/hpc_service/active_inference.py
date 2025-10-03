"""
hPC - Active Inference Engine
==============================
Autonomous threat hunting via active inference.

Biological inspiration: Free Energy Principle (Karl Friston)
- Minimize surprise (free energy)
- Active inference: take actions to gather information
- Epistemic foraging: explore to reduce uncertainty

The agent actively seeks out threats by:
1. Identifying high-uncertainty areas (epistemic value)
2. Taking actions to observe those areas
3. Updating beliefs based on observations
4. Repeating until uncertainty is minimized

Actions:
- probe_endpoint(ip, port) - Active scanning
- request_logs(source_id, time_range) - Log collection
- trace_connection(flow_id) - Traffic analysis
- query_reputation(ip) - Threat intelligence
- analyze_payload(sample_id) - Deep inspection
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from bayesian_core import (
    BayesianCore, Observation, Prediction,
    PredictionError, BeliefState, ThreatLevel
)

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Available active inference actions"""
    PROBE_ENDPOINT = "probe_endpoint"
    REQUEST_LOGS = "request_logs"
    TRACE_CONNECTION = "trace_connection"
    QUERY_REPUTATION = "query_reputation"
    ANALYZE_PAYLOAD = "analyze_payload"
    MONITOR_HOST = "monitor_host"
    CORRELATE_EVENTS = "correlate_events"


@dataclass
class Action:
    """Action to reduce uncertainty"""
    action_type: ActionType
    parameters: Dict
    expected_information_gain: float  # Epistemic value
    expected_cost: float  # Resource cost (time, bandwidth, etc.)
    priority: float  # Information gain / cost


@dataclass
class ActionResult:
    """Result from executing an action"""
    action: Action
    observation: Optional[Observation]
    success: bool
    execution_time_ms: float
    information_gained: float  # Actual reduction in entropy
    metadata: Dict = field(default_factory=dict)


@dataclass
class InferenceState:
    """Current state of active inference"""
    current_belief: BeliefState
    uncertainty_map: Dict[str, float]  # Uncertainty per source/feature
    pending_actions: List[Action]
    executed_actions: List[ActionResult]
    total_information_gain: float
    exploration_budget: float  # Remaining resources


class ActiveInferenceEngine:
    """
    Active inference engine for autonomous threat hunting.

    Uses free energy minimization to decide which actions to take.

    Free Energy = Surprise + Divergence(posterior || prior)

    Agent minimizes free energy by:
    1. Reducing surprise (improving predictions)
    2. Reducing uncertainty (exploring unknown areas)
    """

    def __init__(
        self,
        bayesian_core: BayesianCore,
        exploration_budget: float = 100.0,
        information_threshold: float = 0.5,
        enable_exploration: bool = True
    ):
        self.core = bayesian_core
        self.exploration_budget = exploration_budget
        self.information_threshold = information_threshold
        self.enable_exploration = enable_exploration

        # Action executors (dependency injection for real actions)
        self.action_executors: Dict[ActionType, Callable] = {}

        # Inference state
        self.state: Optional[InferenceState] = None

        # Statistics
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "total_information_gained": 0.0,
            "budget_spent": 0.0,
            "threats_discovered": 0
        }

        logger.info("Active inference engine initialized")

    def register_action_executor(
        self,
        action_type: ActionType,
        executor: Callable
    ):
        """
        Register action executor function.

        Executor signature: async (parameters: Dict) -> Observation
        """
        self.action_executors[action_type] = executor
        logger.info(f"Registered executor for {action_type}")

    async def infer(
        self,
        initial_observation: Optional[Observation] = None
    ) -> InferenceState:
        """
        Run active inference loop.

        1. Observe current state
        2. Compute prediction
        3. Identify high-uncertainty areas
        4. Plan actions to reduce uncertainty
        5. Execute most valuable action
        6. Update beliefs
        7. Repeat until budget exhausted or uncertainty below threshold

        Args:
            initial_observation: Starting observation (optional)

        Returns:
            Final inference state with updated beliefs
        """
        logger.info("Starting active inference loop...")

        # Initialize state
        current_belief = self.core.belief_state
        if current_belief is None:
            raise RuntimeError("Bayesian core not trained (no prior)")

        self.state = InferenceState(
            current_belief=current_belief,
            uncertainty_map={},
            pending_actions=[],
            executed_actions=[],
            total_information_gain=0.0,
            exploration_budget=self.exploration_budget
        )

        # Process initial observation if provided
        if initial_observation:
            await self._process_observation(initial_observation)

        # Active inference loop
        iteration = 0
        max_iterations = 50

        while (
            self.state.exploration_budget > 0 and
            self.state.current_belief.entropy > self.information_threshold and
            iteration < max_iterations
        ):
            iteration += 1
            logger.info(
                f"Iteration {iteration}: entropy={self.state.current_belief.entropy:.3f}, "
                f"budget={self.state.exploration_budget:.1f}"
            )

            # 1. Compute uncertainty map
            uncertainty_map = self._compute_uncertainty_map()
            self.state.uncertainty_map = uncertainty_map

            # 2. Plan actions to reduce uncertainty
            actions = self._plan_actions(uncertainty_map)
            self.state.pending_actions = actions

            if not actions:
                logger.info("No valuable actions found, stopping inference")
                break

            # 3. Execute most valuable action
            best_action = actions[0]  # Sorted by priority
            result = await self._execute_action(best_action)

            self.state.executed_actions.append(result)
            self.state.exploration_budget -= result.action.expected_cost

            # 4. Update beliefs if observation obtained
            if result.observation:
                await self._process_observation(result.observation)

                # Update information gain
                self.state.total_information_gain += result.information_gained
                self.stats["total_information_gained"] += result.information_gained

            # Check for discovered threats
            if (
                self.state.current_belief.threat_probability[ThreatLevel.CRITICAL] > 0.5 or
                self.state.current_belief.threat_probability[ThreatLevel.HIGH] > 0.3
            ):
                self.stats["threats_discovered"] += 1
                logger.warning(
                    f"THREAT DISCOVERED: "
                    f"P(critical)={self.state.current_belief.threat_probability[ThreatLevel.CRITICAL]:.3f}, "
                    f"P(high)={self.state.current_belief.threat_probability[ThreatLevel.HIGH]:.3f}"
                )

        logger.info(
            f"Active inference complete: {iteration} iterations, "
            f"{len(self.state.executed_actions)} actions, "
            f"final entropy={self.state.current_belief.entropy:.3f}"
        )

        return self.state

    async def _process_observation(self, observation: Observation):
        """Process observation through predictive coding cycle"""
        # Generate prediction
        prediction = self.core.predict()

        # Compute prediction error
        pred_error = self.core.compute_prediction_error(observation, prediction)

        # Update beliefs
        new_belief = self.core.update_beliefs(observation, pred_error)

        # Update state
        self.state.current_belief = new_belief

    def _compute_uncertainty_map(self) -> Dict[str, float]:
        """
        Compute uncertainty map across different sources/features.

        High uncertainty = high epistemic value (should explore)
        """
        uncertainty_map = {}

        # Uncertainty from feature variances
        if self.state.current_belief.feature_distribution:
            for feature_name, (mean, std) in self.state.current_belief.feature_distribution.items():
                # Coefficient of variation (normalized uncertainty)
                uncertainty = std / (abs(mean) + 1e-6)
                uncertainty_map[f"feature_{feature_name}"] = uncertainty

        # Uncertainty from threat probabilities (entropy of distribution)
        threat_entropy = self.state.current_belief.entropy
        uncertainty_map["threat_assessment"] = threat_entropy

        # Uncertainty from observation history
        # Areas with few observations have high uncertainty
        if len(self.core.observation_history) > 0:
            recent_sources = [obs.source_id for obs in list(self.core.observation_history)[-50:]]
            source_counts = {}
            for source in recent_sources:
                source_counts[source] = source_counts.get(source, 0) + 1

            # Sources with few observations = high uncertainty
            for source, count in source_counts.items():
                uncertainty = 1.0 / (count + 1)  # Inverse frequency
                uncertainty_map[f"source_{source}"] = uncertainty

        return uncertainty_map

    def _plan_actions(self, uncertainty_map: Dict[str, float]) -> List[Action]:
        """
        Plan actions to reduce uncertainty.

        Actions are ranked by priority = information_gain / cost
        """
        actions = []

        # Sort uncertainty map by uncertainty (descending)
        sorted_uncertainty = sorted(
            uncertainty_map.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Generate actions for high-uncertainty areas
        for area, uncertainty in sorted_uncertainty[:10]:  # Top 10 uncertain areas
            if uncertainty < 0.1:
                continue  # Skip low-uncertainty areas

            # Determine action type based on area
            if area.startswith("source_"):
                source_id = area.replace("source_", "")

                # Multiple actions per source
                action_templates = [
                    (ActionType.REQUEST_LOGS, {"source_id": source_id, "time_range": "1h"}, 2.0),
                    (ActionType.MONITOR_HOST, {"source_id": source_id, "duration": 300}, 5.0),
                    (ActionType.QUERY_REPUTATION, {"ip": source_id}, 0.5),
                ]

                for action_type, params, cost in action_templates:
                    # Expected information gain proportional to uncertainty
                    expected_gain = uncertainty * 10.0

                    if expected_gain > 1.0:  # Only plan if meaningful gain
                        action = Action(
                            action_type=action_type,
                            parameters=params,
                            expected_information_gain=expected_gain,
                            expected_cost=cost,
                            priority=expected_gain / cost
                        )
                        actions.append(action)

            elif area.startswith("feature_"):
                feature_name = area.replace("feature_", "")

                # Feature-specific actions
                if "entropy" in feature_name or "payload" in feature_name:
                    action = Action(
                        action_type=ActionType.ANALYZE_PAYLOAD,
                        parameters={"feature": feature_name},
                        expected_information_gain=uncertainty * 8.0,
                        expected_cost=3.0,
                        priority=(uncertainty * 8.0) / 3.0
                    )
                    actions.append(action)

                elif "connection" in feature_name or "flow" in feature_name:
                    action = Action(
                        action_type=ActionType.TRACE_CONNECTION,
                        parameters={"feature": feature_name},
                        expected_information_gain=uncertainty * 7.0,
                        expected_cost=2.0,
                        priority=(uncertainty * 7.0) / 2.0
                    )
                    actions.append(action)

            elif area == "threat_assessment":
                # High threat uncertainty → correlate events
                action = Action(
                    action_type=ActionType.CORRELATE_EVENTS,
                    parameters={"time_window": "5m"},
                    expected_information_gain=uncertainty * 15.0,
                    expected_cost=4.0,
                    priority=(uncertainty * 15.0) / 4.0
                )
                actions.append(action)

        # Sort by priority (descending)
        actions.sort(key=lambda a: a.priority, reverse=True)

        # Filter by budget
        affordable_actions = []
        remaining_budget = self.state.exploration_budget
        for action in actions:
            if action.expected_cost <= remaining_budget:
                affordable_actions.append(action)
                remaining_budget -= action.expected_cost

        logger.info(f"Planned {len(affordable_actions)} actions (from {len(actions)} candidates)")

        return affordable_actions

    async def _execute_action(self, action: Action) -> ActionResult:
        """
        Execute action and measure information gain.

        If executor not registered, simulates action.
        """
        start_time = time.time()

        logger.info(f"Executing action: {action.action_type} (priority={action.priority:.2f})")

        observation = None
        success = False
        metadata = {}

        try:
            # Check if executor registered
            if action.action_type in self.action_executors:
                # Execute real action
                executor = self.action_executors[action.action_type]
                observation = await executor(action.parameters)
                success = True
                metadata["execution"] = "real"
            else:
                # Simulate action (for testing without real infrastructure)
                observation = await self._simulate_action(action)
                success = True
                metadata["execution"] = "simulated"

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            success = False
            metadata["error"] = str(e)

        execution_time_ms = (time.time() - start_time) * 1000

        # Compute actual information gain
        information_gained = 0.0
        if observation and self.state.current_belief:
            entropy_before = self.state.current_belief.entropy

            # Temporarily update beliefs to measure entropy change
            prediction = self.core.predict()
            pred_error = self.core.compute_prediction_error(observation, prediction)
            temp_belief = self.core.update_beliefs(observation, pred_error)

            entropy_after = temp_belief.entropy
            information_gained = max(0, entropy_before - entropy_after)

        result = ActionResult(
            action=action,
            observation=observation,
            success=success,
            execution_time_ms=execution_time_ms,
            information_gained=information_gained,
            metadata=metadata
        )

        # Update stats
        self.stats["total_actions"] += 1
        if success:
            self.stats["successful_actions"] += 1
        self.stats["budget_spent"] += action.expected_cost

        logger.info(
            f"Action completed: success={success}, "
            f"info_gain={information_gained:.3f}, "
            f"time={execution_time_ms:.2f}ms"
        )

        return result

    async def _simulate_action(self, action: Action) -> Observation:
        """
        Simulate action execution (for testing).

        Generates synthetic observations based on action type.
        """
        await asyncio.sleep(0.01)  # Simulate latency

        # Generate features based on action type
        if action.action_type == ActionType.PROBE_ENDPOINT:
            # Probing might reveal open ports, services
            features = np.concatenate([
                np.random.normal(500, 100, 10),
                np.random.uniform(0.3, 0.7, 10),
                np.random.randint(1, 50, 10).astype(float)
            ])

        elif action.action_type == ActionType.REQUEST_LOGS:
            # Logs might reveal attack patterns
            features = np.concatenate([
                np.random.normal(1000, 200, 10),
                np.random.uniform(0.5, 0.9, 10),
                np.random.randint(10, 200, 10).astype(float)
            ])

        elif action.action_type == ActionType.ANALYZE_PAYLOAD:
            # Payload analysis reveals deep features
            features = np.concatenate([
                np.random.normal(2000, 500, 10),
                np.random.uniform(0.6, 0.95, 10),
                np.random.randint(50, 500, 10).astype(float)
            ])

        else:
            # Default generic observation
            features = np.concatenate([
                np.random.normal(800, 150, 10),
                np.random.uniform(0.4, 0.8, 10),
                np.random.randint(5, 100, 10).astype(float)
            ])

        observation = Observation(
            timestamp=time.time(),
            features=features,
            source_id=action.parameters.get("source_id", "unknown"),
            metadata={
                "action_type": action.action_type,
                "simulated": True
            }
        )

        return observation

    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            **self.stats,
            "current_entropy": self.state.current_belief.entropy if self.state else None,
            "actions_executed": len(self.state.executed_actions) if self.state else 0,
            "remaining_budget": self.state.exploration_budget if self.state else 0
        }


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("ACTIVE INFERENCE ENGINE - AUTONOMOUS THREAT HUNTING")
    print("="*80 + "\n")

    async def test_active_inference():
        # Initialize Bayesian core
        core = BayesianCore(num_features=30, hierarchy_levels=4)

        # Learn prior from normal traffic
        np.random.seed(42)
        normal_obs = []
        for i in range(500):
            features = np.concatenate([
                np.random.normal(500, 100, 10),
                np.random.uniform(0, 1, 10),
                np.random.randint(0, 100, 10).astype(float)
            ])
            obs = Observation(
                timestamp=time.time(),
                features=features,
                source_id=f"source_{i % 5}",
                metadata={"type": "normal"}
            )
            normal_obs.append(obs)

        core.learn_prior(normal_obs)
        print(f"✓ Bayesian core trained on {len(normal_obs)} observations\n")

        # Initialize active inference engine
        ai_engine = ActiveInferenceEngine(
            bayesian_core=core,
            exploration_budget=50.0,
            information_threshold=1.0
        )

        # Run inference with initial suspicious observation
        suspicious_features = np.concatenate([
            np.random.normal(5000, 1000, 10),  # Anomalous
            np.random.uniform(0.7, 1.0, 10),
            np.random.randint(200, 500, 10).astype(float)
        ])

        initial_obs = Observation(
            timestamp=time.time(),
            features=suspicious_features,
            source_id="source_X",
            metadata={"type": "suspicious"}
        )

        print("Running active inference with suspicious initial observation...\n")

        final_state = await ai_engine.infer(initial_observation=initial_obs)

        # Results
        print("\n" + "="*80)
        print("INFERENCE RESULTS")
        print("="*80)
        print(f"\nFinal belief state:")
        print(f"  Threat probabilities:")
        for level, prob in final_state.current_belief.threat_probability.items():
            if prob > 0.01:
                print(f"    {level}: {prob:.4f}")
        print(f"  Entropy: {final_state.current_belief.entropy:.3f}")
        print(f"  Total information gained: {final_state.total_information_gain:.3f}")

        print(f"\nActions executed: {len(final_state.executed_actions)}")
        for i, result in enumerate(final_state.executed_actions[:5], 1):
            print(
                f"  {i}. {result.action.action_type}: "
                f"info_gain={result.information_gained:.3f}, "
                f"time={result.execution_time_ms:.2f}ms"
            )

        print(f"\nBudget: {final_state.exploration_budget:.1f} remaining "
              f"(spent {ai_engine.stats['budget_spent']:.1f})")

        # Stats
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        stats = ai_engine.get_stats()
        print(f"Total actions: {stats['total_actions']}")
        print(f"Successful actions: {stats['successful_actions']}")
        print(f"Total information gained: {stats['total_information_gained']:.3f}")
        print(f"Threats discovered: {stats['threats_discovered']}")

        print("\n" + "="*80)
        print("ACTIVE INFERENCE TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_active_inference())
