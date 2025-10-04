"""ADR Core Response Engine.

This module contains the `ResponseEngine`, which is responsible for orchestrating
automated responses to detected threats. It uses a playbook-based system to
execute a series of actions, such as isolating a host or quarantining a file.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from ..models import (
    ResponseAction,
    Playbook,
    PlaybookExecution,
    PlaybookStep,
    ThreatDetection,
    ActionType,
    ActionStatus,
    SeverityLevel
)

logger = logging.getLogger(__name__)


class ResponseEngine:
    """Orchestrates automated, playbook-based responses to threats.

    This engine takes a threat detection, finds a matching playbook, and executes
    the defined response actions. It supports both automated execution and
    workflows requiring manual approval.

    Attributes:
        config (Dict[str, Any]): Configuration for the engine.
        enabled (bool): Whether the engine is active.
        auto_response_enabled (bool): Whether fully autonomous responses are enabled.
        playbooks (Dict[str, Playbook]): A dictionary of loaded playbooks, indexed by ID.
        active_executions (Dict[str, PlaybookExecution]): A dictionary of currently
            running playbook executions.
        stats (Dict[str, Any]): A dictionary for tracking engine statistics.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initializes the ResponseEngine.

        Args:
            config (Dict[str, Any]): A configuration dictionary for the engine,
                including settings like `enable_auto_response`.
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.auto_response_enabled = config.get('enable_auto_response', False)

        self.playbooks: Dict[str, Playbook] = {}
        self.active_executions: Dict[str, PlaybookExecution] = {}

        self.stats = {
            'total_responses': 0,
            'responses_completed': 0,
            'responses_failed': 0,
            'actions_executed': 0,
            'actions_failed': 0,
            'avg_response_time_ms': 0
        }

        logger.info(f"Response Engine initialized (Auto-response: {self.auto_response_enabled}).")

    async def respond_to_threat(
        self,
        detection: ThreatDetection,
        auto_approve: bool = False
    ) -> Optional[PlaybookExecution]:
        """Initiates a response to a given threat detection.

        This method finds a suitable playbook for the detection and, if conditions
        are met, creates and starts a playbook execution.

        Args:
            detection (ThreatDetection): The threat detection to respond to.
            auto_approve (bool, optional): If True, bypasses manual approval steps.
                Defaults to False.

        Returns:
            Optional[PlaybookExecution]: The created playbook execution instance,
                or None if no suitable playbook is found or if approval is required.
        """
        start_time = datetime.utcnow()

        playbook = self._find_matching_playbook(detection)
        if not playbook:
            logger.warning(f"No matching playbook found for detection {detection.detection_id}")
            return None

        can_auto_execute = (
            playbook.auto_execute and
            self.auto_response_enabled and
            (auto_approve or not playbook.require_approval)
        )

        if not can_auto_execute:
            logger.info(
                f"Playbook '{playbook.name}' requires manual approval for detection "
                f"{detection.detection_id}. Execution pending."
            )
            # In a real system, this would trigger a notification for approval.
            return None

        try:
            execution = self._create_execution(detection, playbook)
            asyncio.create_task(self._execute_playbook(execution))
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._update_stats(execution, execution_time_ms)
            
            return execution
        except Exception as e:
            logger.error(f"Failed to initiate response for {detection.detection_id}: {e}")
            self.stats['responses_failed'] += 1
            return None

    def _find_matching_playbook(self, detection: ThreatDetection) -> Optional[Playbook]:
        """Finds the best-matching playbook for a given detection."""
        # Simplified logic: find the first playbook that matches the threat type.
        # A real implementation would have more complex matching logic.
        for playbook in self.playbooks.values():
            if not playbook.enabled:
                continue

            if 'threat_types' in playbook.trigger_conditions:
                if detection.threat_type.value in playbook.trigger_conditions['threat_types']:
                    logger.info(f"Matched playbook '{playbook.name}' for detection.")
                    return playbook
        return None

    def _create_execution(
        self, detection: ThreatDetection, playbook: Playbook
    ) -> PlaybookExecution:
        """Creates a PlaybookExecution instance from a detection and playbook."""
        execution_id = f"exec_{hashlib.sha1(f'{playbook.playbook_id}{detection.detection_id}{datetime.utcnow()}'.encode()).hexdigest()[:12]}"
        
        actions = [self._create_action_from_step(step, detection) for step in playbook.steps]

        execution = PlaybookExecution(
            execution_id=execution_id,
            playbook_id=playbook.playbook_id,
            triggered_by=detection.detection_id,
            actions=actions,
            metadata={
                'detection_title': detection.title,
                'playbook_name': playbook.name
            }
        )
        self.active_executions[execution_id] = execution
        return execution

    def _create_action_from_step(
        self, step: PlaybookStep, detection: ThreatDetection
    ) -> ResponseAction:
        """Creates a ResponseAction from a playbook step and detection context."""
        target = self._resolve_target(step, detection)
        action_id = f"act_{hashlib.sha1(f'{step.step_id}{target}{datetime.utcnow()}'.encode()).hexdigest()[:12]}"

        return ResponseAction(
            action_id=action_id,
            action_type=step.action_type,
            target=target,
            parameters=step.parameters,
            priority=step.order,
            timeout_seconds=step.timeout_seconds,
            max_retries=step.max_retries if step.retry_on_failure else 0
        )

    def _resolve_target(self, step: PlaybookStep, detection: ThreatDetection) -> str:
        """Resolves the target for an action based on the detection context."""
        # Simple logic: use the first affected asset or first indicator value.
        if detection.affected_assets:
            return detection.affected_assets[0]
        if detection.indicators:
            return detection.indicators[0].value
        return "unresolved_target"

    async def _execute_playbook(self, execution: PlaybookExecution):
        """Executes the steps of a playbook execution instance."""
        logger.info(f"Starting execution for playbook '{execution.playbook_id}' (ID: {execution.execution_id}).")
        execution.status = 'running'
        execution.started_at = datetime.utcnow()

        try:
            # Simplified execution: run actions sequentially by order.
            # A real implementation would handle parallel execution.
            for action in sorted(execution.actions, key=lambda a: a.priority):
                await self._execute_action(action)
                if action.status == ActionStatus.FAILED:
                    logger.error(f"Action {action.action_id} failed. Stopping playbook execution.")
                    execution.status = 'failed'
                    break
            else: # No break
                execution.status = 'completed'
        except Exception as e:
            logger.error(f"Error during playbook execution {execution.execution_id}: {e}")
            execution.status = 'failed'
            execution.errors.append(str(e))
        finally:
            execution.completed_at = datetime.utcnow()
            execution.actions_completed = sum(1 for a in execution.actions if a.status == ActionStatus.COMPLETED)
            execution.actions_failed = sum(1 for a in execution.actions if a.status == ActionStatus.FAILED)
            logger.info(f"Playbook execution {execution.execution_id} finished with status: {execution.status}")

    async def _execute_action(self, action: ResponseAction):
        """Executes a single response action and updates its status."""
        action.status = ActionStatus.IN_PROGRESS
        action.started_at = datetime.utcnow()
        logger.info(f"Executing action: {action.action_type.value} on target '{action.target}'")

        try:
            # In a real system, this would call a handler for each action type.
            # Simulating action execution here.
            await asyncio.sleep(0.1) # Simulate I/O
            action.status = ActionStatus.COMPLETED
            action.result = {'message': 'Action simulated successfully'}
            self.stats['actions_executed'] += 1
            logger.info(f"Action {action.action_id} completed successfully.")
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            action.status = ActionStatus.FAILED
            action.error = str(e)
            self.stats['actions_failed'] += 1
        finally:
            action.completed_at = datetime.utcnow()

    def _update_stats(self, execution: PlaybookExecution, execution_time_ms: int):
        """Updates the internal statistics of the engine."""
        self.stats['total_responses'] += 1
        if execution.status == 'completed':
            self.stats['responses_completed'] += 1
        elif execution.status == 'failed':
            self.stats['responses_failed'] += 1

        total_responses = self.stats['total_responses']
        current_avg_time = self.stats['avg_response_time_ms']
        self.stats['avg_response_time_ms'] = \
            (current_avg_time * (total_responses - 1) + execution_time_ms) / total_responses

    def load_playbook(self, playbook: Playbook):
        """Loads or updates a playbook in the engine's memory.

        Args:
            playbook (Playbook): The playbook object to load.
        """
        self.playbooks[playbook.playbook_id] = playbook
        logger.info(f"Loaded playbook: '{playbook.name}' (ID: {playbook.playbook_id})")

    def get_stats(self) -> Dict[str, Any]:
        """Returns a copy of the current engine statistics.

        Returns:
            Dict[str, Any]: A dictionary containing engine performance metrics.
        """
        return self.stats.copy()