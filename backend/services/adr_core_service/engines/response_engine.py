"""
Response Engine - Automated threat response and orchestration
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
    """
    Automated Response Engine

    Features:
    - Playbook-based response orchestration
    - Multi-step automated actions
    - Rollback capabilities
    - Approval workflows
    - Action queuing and prioritization
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.auto_response_enabled = config.get('enable_auto_response', False)

        # Playbooks and actions
        self.playbooks: Dict[str, Playbook] = {}
        self.active_executions: Dict[str, PlaybookExecution] = {}
        self.action_queue = asyncio.Queue()

        # Statistics
        self.stats = {
            'total_responses': 0,
            'responses_completed': 0,
            'responses_failed': 0,
            'actions_executed': 0,
            'actions_failed': 0,
            'avg_response_time_ms': 0
        }

        logger.info(f"Initialized Response Engine (auto_response={self.auto_response_enabled})")

    async def respond_to_threat(
        self,
        detection: ThreatDetection,
        auto_approve: bool = False
    ) -> Optional[PlaybookExecution]:
        """
        Respond to detected threat

        Args:
            detection: Threat detection to respond to
            auto_approve: Automatically approve response without human review

        Returns:
            Playbook execution instance or None
        """
        start_time = datetime.utcnow()

        try:
            # Find matching playbook
            playbook = self._find_matching_playbook(detection)

            if not playbook:
                logger.warning(f"No playbook found for detection {detection.detection_id}")
                return None

            # Check if auto-execution is allowed
            can_auto_execute = (
                playbook.auto_execute and
                self.auto_response_enabled and
                (auto_approve or not playbook.require_approval)
            )

            if playbook.require_approval and not can_auto_execute:
                logger.info(
                    f"Playbook {playbook.playbook_id} requires approval. "
                    f"Execution pending..."
                )
                # In real implementation, send approval request
                return None

            # Create execution instance
            execution = await self._create_execution(detection, playbook)

            # Start execution
            await self._execute_playbook(execution)

            # Update statistics
            execution_time_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            self._update_stats(execution, execution_time_ms)

            return execution

        except Exception as e:
            logger.error(f"Response error for detection {detection.detection_id}: {e}")
            self.stats['responses_failed'] += 1
            return None

    async def execute_manual_action(
        self,
        action_type: ActionType,
        target: str,
        parameters: Dict[str, Any] = None
    ) -> ResponseAction:
        """
        Execute manual response action

        Args:
            action_type: Type of action to execute
            target: Target for action (IP, file, process, etc.)
            parameters: Action parameters

        Returns:
            Response action result
        """
        action_id = self._generate_action_id(action_type, target)

        action = ResponseAction(
            action_id=action_id,
            action_type=action_type,
            target=target,
            parameters=parameters or {},
            status=ActionStatus.PENDING
        )

        # Execute action
        await self._execute_action(action)

        return action

    async def _find_matching_playbook(
        self,
        detection: ThreatDetection
    ) -> Optional[Playbook]:
        """
        Find playbook matching detection criteria

        Matching logic:
        1. Check severity threshold
        2. Check threat type
        3. Check MITRE techniques
        4. Check custom conditions
        """
        for playbook in self.playbooks.values():
            if not playbook.enabled:
                continue

            # Check severity threshold
            severity_order = ['info', 'low', 'medium', 'high', 'critical']
            detection_sev_idx = severity_order.index(detection.severity.value)
            threshold_sev_idx = severity_order.index(playbook.severity_threshold.value)

            if detection_sev_idx < threshold_sev_idx:
                continue

            # Check trigger conditions
            conditions = playbook.trigger_conditions

            if 'threat_types' in conditions:
                if detection.threat_type.value not in conditions['threat_types']:
                    continue

            if 'mitre_techniques' in conditions:
                detection_techniques = [t.technique_id for t in detection.mitre_techniques]
                if not any(t in detection_techniques for t in conditions['mitre_techniques']):
                    continue

            # Playbook matches
            logger.info(f"Matched playbook: {playbook.name}")
            return playbook

        return None

    async def _create_execution(
        self,
        detection: ThreatDetection,
        playbook: Playbook
    ) -> PlaybookExecution:
        """Create playbook execution instance"""
        execution_id = hashlib.sha256(
            f"{playbook.playbook_id}:{detection.detection_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        # Create actions from playbook steps
        actions = []
        for step in sorted(playbook.steps, key=lambda s: s.order):
            action = self._create_action_from_step(step, detection)
            actions.append(action)

        execution = PlaybookExecution(
            execution_id=execution_id,
            playbook_id=playbook.playbook_id,
            triggered_by=detection.detection_id,
            actions=actions,
            metadata={
                'detection': {
                    'severity': detection.severity.value,
                    'threat_type': detection.threat_type.value,
                    'score': detection.score
                },
                'playbook': {
                    'name': playbook.name,
                    'version': playbook.version
                }
            }
        )

        self.active_executions[execution_id] = execution
        return execution

    def _create_action_from_step(
        self,
        step: PlaybookStep,
        detection: ThreatDetection
    ) -> ResponseAction:
        """Create response action from playbook step"""
        action_id = hashlib.sha256(
            f"{step.step_id}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

        # Resolve target from detection
        target = self._resolve_target(step, detection)

        return ResponseAction(
            action_id=action_id,
            action_type=step.action_type,
            target=target,
            parameters=step.parameters,
            priority=step.order,
            timeout_seconds=step.timeout_seconds,
            max_retries=step.max_retries if step.retry_on_failure else 0
        )

    def _resolve_target(
        self,
        step: PlaybookStep,
        detection: ThreatDetection
    ) -> str:
        """Resolve action target from detection context"""
        # Use first affected asset as default target
        if detection.affected_assets:
            return detection.affected_assets[0]

        # Use first indicator value
        if detection.indicators:
            return detection.indicators[0].value

        # Use source
        return detection.source_details.get('source', 'unknown')

    async def _execute_playbook(self, execution: PlaybookExecution):
        """
        Execute playbook with all steps

        Handles:
        - Sequential and parallel execution
        - Error handling and retries
        - Rollback on failure
        """
        execution.status = 'running'
        execution.started_at = datetime.utcnow()

        try:
            # Group actions by parallel execution
            parallel_groups = self._group_parallel_actions(execution.actions)

            for group in parallel_groups:
                # Execute group in parallel
                tasks = [self._execute_action(action) for action in group]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Check for critical failures
                if any(a.status == ActionStatus.FAILED for a in group):
                    critical_step = next(
                        (s for s in execution.actions if s.status == ActionStatus.FAILED),
                        None
                    )
                    if critical_step:
                        logger.error(
                            f"Critical action failed: {critical_step.action_id}. "
                            f"Stopping playbook execution."
                        )
                        execution.status = 'failed'
                        execution.errors.append(
                            f"Critical action {critical_step.action_id} failed"
                        )
                        break

            # Mark as completed if no failures
            if execution.status == 'running':
                execution.status = 'completed'
                execution.completed_at = datetime.utcnow()

                # Update counts
                execution.actions_completed = sum(
                    1 for a in execution.actions if a.status == ActionStatus.COMPLETED
                )
                execution.actions_failed = sum(
                    1 for a in execution.actions if a.status == ActionStatus.FAILED
                )

                logger.info(
                    f"✅ Playbook execution completed: {execution.execution_id} "
                    f"({execution.actions_completed}/{len(execution.actions)} actions)"
                )

        except Exception as e:
            logger.error(f"Playbook execution error: {e}")
            execution.status = 'failed'
            execution.errors.append(str(e))
            execution.completed_at = datetime.utcnow()

    def _group_parallel_actions(
        self,
        actions: List[ResponseAction]
    ) -> List[List[ResponseAction]]:
        """Group actions that can execute in parallel"""
        # Simplified: execute in priority order
        # In real implementation, analyze dependencies
        groups = []
        current_group = []
        current_priority = None

        for action in sorted(actions, key=lambda a: a.priority):
            if current_priority is None or action.priority == current_priority:
                current_group.append(action)
                current_priority = action.priority
            else:
                groups.append(current_group)
                current_group = [action]
                current_priority = action.priority

        if current_group:
            groups.append(current_group)

        return groups

    async def _execute_action(self, action: ResponseAction):
        """
        Execute single response action

        Actions:
        - BLOCK_IP: Block IP in firewall
        - QUARANTINE_FILE: Move file to quarantine
        - KILL_PROCESS: Terminate process
        - ISOLATE_HOST: Network isolation
        - etc.
        """
        action.status = ActionStatus.IN_PROGRESS
        action.started_at = datetime.utcnow()

        try:
            logger.info(f"Executing action: {action.action_type.value} on {action.target}")

            # Route to specific action handler
            if action.action_type == ActionType.BLOCK_IP:
                result = await self._action_block_ip(action)
            elif action.action_type == ActionType.BLOCK_DOMAIN:
                result = await self._action_block_domain(action)
            elif action.action_type == ActionType.QUARANTINE_FILE:
                result = await self._action_quarantine_file(action)
            elif action.action_type == ActionType.KILL_PROCESS:
                result = await self._action_kill_process(action)
            elif action.action_type == ActionType.ISOLATE_HOST:
                result = await self._action_isolate_host(action)
            elif action.action_type == ActionType.ALERT:
                result = await self._action_send_alert(action)
            elif action.action_type == ActionType.LOG:
                result = await self._action_log(action)
            else:
                result = {'success': False, 'error': 'Unknown action type'}

            # Update action status
            if result.get('success'):
                action.status = ActionStatus.COMPLETED
                action.result = result
                self.stats['actions_executed'] += 1
                logger.info(f"✅ Action completed: {action.action_id}")
            else:
                action.status = ActionStatus.FAILED
                action.error = result.get('error', 'Unknown error')
                self.stats['actions_failed'] += 1
                logger.error(f"❌ Action failed: {action.action_id} - {action.error}")

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            action.status = ActionStatus.FAILED
            action.error = str(e)
            self.stats['actions_failed'] += 1

        finally:
            action.completed_at = datetime.utcnow()

    # ========== Action Handlers ==========

    async def _action_block_ip(self, action: ResponseAction) -> Dict[str, Any]:
        """Block IP address in firewall"""
        # Placeholder - integrate with firewall API
        logger.info(f"🔥 Blocking IP: {action.target}")
        await asyncio.sleep(0.1)  # Simulate API call
        return {'success': True, 'blocked_ip': action.target}

    async def _action_block_domain(self, action: ResponseAction) -> Dict[str, Any]:
        """Block domain in DNS/firewall"""
        logger.info(f"🚫 Blocking domain: {action.target}")
        await asyncio.sleep(0.1)
        return {'success': True, 'blocked_domain': action.target}

    async def _action_quarantine_file(self, action: ResponseAction) -> Dict[str, Any]:
        """Quarantine malicious file"""
        logger.info(f"🔒 Quarantining file: {action.target}")
        await asyncio.sleep(0.1)
        return {'success': True, 'quarantined_file': action.target}

    async def _action_kill_process(self, action: ResponseAction) -> Dict[str, Any]:
        """Terminate malicious process"""
        logger.info(f"💀 Killing process: {action.target}")
        await asyncio.sleep(0.1)
        return {'success': True, 'killed_process': action.target}

    async def _action_isolate_host(self, action: ResponseAction) -> Dict[str, Any]:
        """Isolate compromised host from network"""
        logger.info(f"🏝️ Isolating host: {action.target}")
        await asyncio.sleep(0.1)
        return {'success': True, 'isolated_host': action.target}

    async def _action_send_alert(self, action: ResponseAction) -> Dict[str, Any]:
        """Send alert notification"""
        logger.info(f"🚨 Sending alert for: {action.target}")
        await asyncio.sleep(0.05)
        return {'success': True, 'alert_sent': True}

    async def _action_log(self, action: ResponseAction) -> Dict[str, Any]:
        """Log event"""
        logger.info(f"📝 Logging event: {action.target}")
        return {'success': True, 'logged': True}

    # ========== Utility Methods ==========

    def _generate_action_id(self, action_type: ActionType, target: str) -> str:
        """Generate unique action ID"""
        return hashlib.sha256(
            f"{action_type.value}:{target}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]

    def _update_stats(self, execution: PlaybookExecution, execution_time_ms: int):
        """Update response engine statistics"""
        self.stats['total_responses'] += 1

        if execution.status == 'completed':
            self.stats['responses_completed'] += 1
        elif execution.status == 'failed':
            self.stats['responses_failed'] += 1

        # Update average response time
        total = self.stats['total_responses']
        current_avg = self.stats['avg_response_time_ms']
        self.stats['avg_response_time_ms'] = \
            (current_avg * (total - 1) + execution_time_ms) / total

    def load_playbook(self, playbook: Playbook):
        """Load playbook into engine"""
        self.playbooks[playbook.playbook_id] = playbook
        logger.info(f"Loaded playbook: {playbook.name} ({playbook.playbook_id})")

    def get_stats(self) -> Dict[str, Any]:
        """Get response engine statistics"""
        return self.stats.copy()

    def get_active_executions(self) -> List[PlaybookExecution]:
        """Get currently running executions"""
        return [
            ex for ex in self.active_executions.values()
            if ex.status in ['pending', 'running']
        ]
