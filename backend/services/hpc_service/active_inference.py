"""hPC Service - Active Inference Engine.

This module implements an active inference agent for autonomous threat hunting.
It is based on the Free Energy Principle by Karl Friston, where an agent actively
seeks out information to minimize surprise and uncertainty about its environment.

This agent uses the Bayesian Core to maintain its beliefs and decides on actions
(e.g., scanning an endpoint, requesting logs) that are expected to provide the
most information gain, a behavior known as epistemic foraging.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from .bayesian_core import (
    BayesianCore, Observation, BeliefState, ThreatLevel
)

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Enumeration for the types of actions the agent can take."""
    PROBE_ENDPOINT = "probe_endpoint"
    REQUEST_LOGS = "request_logs"
    ANALYZE_PAYLOAD = "analyze_payload"


@dataclass
class Action:
    """Represents a potential action to be taken to reduce uncertainty.

    Attributes:
        action_type (ActionType): The type of action to perform.
        parameters (Dict): The parameters for the action.
        expected_information_gain (float): The estimated reduction in entropy
            (epistemic value) this action is expected to provide.
        priority (float): The action's priority, often calculated as
            information gain divided by cost.
    """
    action_type: ActionType
    parameters: Dict
    expected_information_gain: float
    priority: float


@dataclass
class ActionResult:
    """Represents the result of an executed action."""
    action: Action
    observation: Optional[Observation]
    success: bool
    information_gained: float


class ActiveInferenceEngine:
    """An active inference engine for autonomous, uncertainty-driven threat hunting.

    This engine uses the beliefs from the Bayesian Core to identify areas of high
    uncertainty and then plans and executes actions to gather more information,
    thereby minimizing surprise and refining its model of the environment.
    """

    def __init__(self, bayesian_core: BayesianCore, exploration_budget: float = 100.0):
        """Initializes the ActiveInferenceEngine.

        Args:
            bayesian_core (BayesianCore): The Bayesian inference core to use for beliefs.
            exploration_budget (float): The total resource budget for an inference loop.
        """
        self.core = bayesian_core
        self.exploration_budget = exploration_budget
        self.action_executors: Dict[ActionType, Callable] = {}

    def register_action_executor(self, action_type: ActionType, executor: Callable):
        """Registers a function to execute a specific type of action."""
        self.action_executors[action_type] = executor

    async def infer(self, initial_observation: Optional[Observation] = None) -> Dict:
        """Runs the active inference loop to autonomously investigate the environment.

        The loop continues until the exploration budget is exhausted or uncertainty
        is minimized below a threshold.

        Args:
            initial_observation (Optional[Observation]): An initial observation to
                start the inference process.

        Returns:
            A dictionary summarizing the results of the inference loop.
        """
        if not self.core.belief_state: raise RuntimeError("Bayesian core must be trained first.")
        
        current_belief = self.core.belief_state
        if initial_observation: current_belief = self.core.update_beliefs(initial_observation, self.core.compute_prediction_error(initial_observation, self.core.predict()))

        executed_actions = []
        budget = self.exploration_budget
        
        while budget > 0 and current_belief.entropy > 0.5:
            uncertainty_map = self._compute_uncertainty_map(current_belief)
            actions = self._plan_actions(uncertainty_map)
            if not actions: break

            best_action = actions[0]
            result = await self._execute_action(best_action)
            executed_actions.append(result)
            budget -= 5 # Simplified cost

            if result.observation:
                current_belief = self.core.update_beliefs(result.observation, self.core.compute_prediction_error(result.observation, self.core.predict()))

        return {"final_entropy": current_belief.entropy, "actions_executed": len(executed_actions)}

    def _compute_uncertainty_map(self, belief: BeliefState) -> Dict[str, float]:
        """Computes the uncertainty across different features and sources."""
        # Simplified: uncertainty is just the entropy of the threat distribution
        return {"threat_assessment": belief.entropy}

    def _plan_actions(self, uncertainty_map: Dict[str, float]) -> List[Action]:
        """Plans a list of actions to take based on the uncertainty map."""
        actions = []
        for area, uncertainty in uncertainty_map.items():
            if uncertainty > 0.5:
                # Plan a generic action for any high-uncertainty area
                actions.append(Action(ActionType.PROBE_ENDPOINT, {"target": area}, uncertainty, uncertainty / 5.0))
        return sorted(actions, key=lambda a: a.priority, reverse=True)

    async def _execute_action(self, action: Action) -> ActionResult:
        """Executes a single action, either via a registered executor or by simulation."""
        executor = self.action_executors.get(action.action_type)
        entropy_before = self.core.belief_state.entropy
        
        if executor:
            observation = await executor(action.parameters)
        else:
            # Simulate observation if no real executor is registered
            observation = Observation(timestamp=time.time(), features=np.random.rand(self.core.num_features), source_id="simulated")
        
        new_belief = self.core.update_beliefs(observation, self.core.compute_prediction_error(observation, self.core.predict()))
        info_gained = entropy_before - new_belief.entropy
        
        return ActionResult(action, observation, True, info_gained)