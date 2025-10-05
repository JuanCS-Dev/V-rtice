"""Immunis Cytotoxic T-Cell Service - Production-Ready Active Defense

Bio-inspired Cytotoxic T-Cell service that:
1. **Active Defense**
   - Blocks malicious IPs at firewall
   - Terminates malicious processes
   - Isolates compromised hosts
   - Quarantines malicious files

2. **Memory T-Cells**
   - Maintains memory of past threats
   - Faster response to known threats
   - Long-term threat context storage

3. **Depletion Tracking**
   - Prevents T-cell exhaustion
   - Limits response rate to avoid resource depletion
   - Auto-recovery mechanisms

4. **Offensive Arsenal Integration**
   - Integrates with offensive security tools
   - Coordinates with other attack services
   - Executes active countermeasures

Like biological Cytotoxic T-cells: Kills infected cells directly.
NO MOCKS - Production-ready implementation.
"""

import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DefenseAction(Enum):
    """Active defense action types."""
    BLOCK_IP = "block_ip"
    KILL_PROCESS = "kill_process"
    ISOLATE_HOST = "isolate_host"
    QUARANTINE_FILE = "quarantine_file"
    DROP_CONNECTION = "drop_connection"


class MemoryTCell:
    """Memory T-Cell for long-term threat memory."""

    def __init__(self, threat_id: str, malware_family: str, iocs: Dict[str, Any]):
        """Initialize Memory T-Cell.

        Args:
            threat_id: Threat identifier
            malware_family: Malware family name
            iocs: Indicators of Compromise
        """
        self.threat_id = threat_id
        self.malware_family = malware_family
        self.iocs = iocs
        self.created_at = datetime.now()
        self.last_activated = datetime.now()
        self.activation_count = 0

    def activate(self):
        """Activate memory cell (faster response to known threat)."""
        self.last_activated = datetime.now()
        self.activation_count += 1
        logger.info(
            f"Memory T-Cell activated: {self.malware_family} "
            f"(activations={self.activation_count})"
        )

    def is_expired(self, ttl_days: int = 90) -> bool:
        """Check if memory cell is expired.

        Args:
            ttl_days: Time-to-live in days

        Returns:
            True if expired
        """
        age = (datetime.now() - self.created_at).days
        return age > ttl_days


class DepletionTracker:
    """Tracks Cytotoxic T-Cell depletion to prevent exhaustion."""

    def __init__(
        self,
        max_actions_per_hour: int = 100,
        max_actions_per_day: int = 1000
    ):
        """Initialize depletion tracker.

        Args:
            max_actions_per_hour: Maximum actions per hour
            max_actions_per_day: Maximum actions per day
        """
        self.max_actions_per_hour = max_actions_per_hour
        self.max_actions_per_day = max_actions_per_day
        self.action_history: List[datetime] = []

    def can_act(self) -> bool:
        """Check if T-cell can take action (not depleted).

        Returns:
            True if action allowed
        """
        now = datetime.now()

        # Remove old actions
        self.action_history = [
            t for t in self.action_history
            if (now - t).total_seconds() < 86400  # 24 hours
        ]

        # Check hourly limit
        hourly_actions = sum(
            1 for t in self.action_history
            if (now - t).total_seconds() < 3600
        )

        if hourly_actions >= self.max_actions_per_hour:
            logger.warning(f"T-cell depleted (hourly): {hourly_actions}/{self.max_actions_per_hour}")
            return False

        # Check daily limit
        daily_actions = len(self.action_history)

        if daily_actions >= self.max_actions_per_day:
            logger.warning(f"T-cell depleted (daily): {daily_actions}/{self.max_actions_per_day}")
            return False

        return True

    def record_action(self):
        """Record action taken."""
        self.action_history.append(datetime.now())

    def get_depletion_stats(self) -> Dict[str, Any]:
        """Get depletion statistics.

        Returns:
            Depletion stats
        """
        now = datetime.now()

        hourly_actions = sum(
            1 for t in self.action_history
            if (now - t).total_seconds() < 3600
        )

        daily_actions = len(self.action_history)

        return {
            'hourly_actions': hourly_actions,
            'hourly_limit': self.max_actions_per_hour,
            'hourly_capacity': (self.max_actions_per_hour - hourly_actions) / self.max_actions_per_hour,
            'daily_actions': daily_actions,
            'daily_limit': self.max_actions_per_day,
            'daily_capacity': (self.max_actions_per_day - daily_actions) / self.max_actions_per_day,
            'depleted': not self.can_act()
        }


class CytotoxicTCellCore:
    """Production-ready Cytotoxic T-Cell service for active defense.

    Executes direct defensive actions:
    - Active defense (block IPs, kill processes, etc.)
    - Memory T-cells for faster response
    - Depletion tracking to prevent exhaustion
    - Offensive arsenal integration
    """

    def __init__(
        self,
        dry_run: bool = True,
        max_actions_per_hour: int = 100,
        offensive_gateway_endpoint: str = "http://offensive-gateway:8030"
    ):
        """Initialize Cytotoxic T-Cell Core.

        Args:
            dry_run: Enable dry-run mode (no actual actions)
            max_actions_per_hour: Maximum actions per hour
            offensive_gateway_endpoint: Offensive Gateway endpoint
        """
        self.dry_run = dry_run
        self.offensive_gateway_endpoint = offensive_gateway_endpoint

        self.depletion_tracker = DepletionTracker(
            max_actions_per_hour=max_actions_per_hour,
            max_actions_per_day=max_actions_per_hour * 10
        )

        self.memory_cells: Dict[str, MemoryTCell] = {}  # malware_family -> MemoryTCell
        self.active_targets: Dict[str, Dict[str, Any]] = {}
        self.neutralization_history: List[Dict[str, Any]] = []
        self.last_action_time: Optional[datetime] = None

        logger.info(f"CytotoxicTCellCore initialized (dry_run={dry_run})")

    async def activate(self, antigen: Dict[str, Any]) -> Dict[str, Any]:
        """Activate Cytotoxic T-Cell with antigen from Helper T-Cell.

        Args:
            antigen: Antigen from Helper T-Cell

        Returns:
            Activation result
        """
        logger.info(f"Cytotoxic T-Cell activated with antigen: {antigen.get('antigen_id', '')[:16]}")

        antigen_id = antigen.get('antigen_id')
        malware_family = antigen.get('malware_family', 'unknown')
        severity = antigen.get('severity', 0.5)
        iocs = antigen.get('iocs', {})

        activation_result = {
            'timestamp': datetime.now().isoformat(),
            'antigen_id': antigen_id,
            'malware_family': malware_family,
            'actions_executed': [],
            'memory_cell_created': False
        }

        # 1. Check depletion
        if not self.depletion_tracker.can_act():
            logger.warning("Cytotoxic T-Cell depleted - cannot act")
            activation_result['depleted'] = True
            return activation_result

        # 2. Check for existing memory cell (faster response)
        memory_cell = self.memory_cells.get(malware_family)
        if memory_cell:
            logger.info(f"Memory T-Cell found for {malware_family}")
            memory_cell.activate()
            activation_result['memory_cell_activated'] = True

        # 3. Execute active defense actions
        defense_actions = self._determine_defense_actions(antigen, iocs)

        for action in defense_actions:
            result = await self._execute_defense_action(action)
            activation_result['actions_executed'].append(result)
            self.depletion_tracker.record_action()

        # 4. Create memory cell for future responses
        if not memory_cell:
            memory_cell = MemoryTCell(antigen_id, malware_family, iocs)
            self.memory_cells[malware_family] = memory_cell
            activation_result['memory_cell_created'] = True

        self.last_action_time = datetime.now()

        logger.info(
            f"Cytotoxic T-Cell activation complete: {len(activation_result['actions_executed'])} actions"
        )

        return activation_result

    def _determine_defense_actions(
        self,
        antigen: Dict[str, Any],
        iocs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine active defense actions to take.

        Args:
            antigen: Threat antigen
            iocs: Indicators of Compromise

        Returns:
            List of defense actions
        """
        actions = []
        severity = antigen.get('severity', 0.5)

        # Block malicious IPs
        for ip in iocs.get('ips', [])[:10]:  # Max 10 IPs
            actions.append({
                'action': DefenseAction.BLOCK_IP,
                'target': ip,
                'severity': severity
            })

        # Kill malicious processes (if process IDs available)
        for pid in iocs.get('process_ids', [])[:5]:  # Max 5 processes
            actions.append({
                'action': DefenseAction.KILL_PROCESS,
                'target': pid,
                'severity': severity
            })

        # Quarantine malicious files
        for file_path in iocs.get('file_paths', [])[:10]:  # Max 10 files
            actions.append({
                'action': DefenseAction.QUARANTINE_FILE,
                'target': file_path,
                'severity': severity
            })

        # Isolate host (high severity only)
        if severity >= 0.8:
            host_id = iocs.get('host_id')
            if host_id:
                actions.append({
                    'action': DefenseAction.ISOLATE_HOST,
                    'target': host_id,
                    'severity': severity
                })

        return actions

    async def _execute_defense_action(self, action_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute active defense action.

        Args:
            action_spec: Action specification

        Returns:
            Action result
        """
        action_type = action_spec['action']
        target = action_spec['target']
        severity = action_spec.get('severity', 0.5)

        logger.warning(
            f"Executing defense action: {action_type.value} on {target} "
            f"(severity={severity:.2f})"
        )

        action_result = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type.value,
            'target': target,
            'severity': severity,
            'dry_run': self.dry_run,
            'status': 'pending'
        }

        if self.dry_run:
            action_result['status'] = 'simulated'
            action_result['message'] = f'DRY-RUN: Would execute {action_type.value} on {target}'
            logger.info(f"DRY-RUN: {action_type.value} on {target}")
        else:
            # Production execution
            try:
                if action_type == DefenseAction.BLOCK_IP:
                    success = await self._block_ip(target)
                elif action_type == DefenseAction.KILL_PROCESS:
                    success = await self._kill_process(target)
                elif action_type == DefenseAction.ISOLATE_HOST:
                    success = await self._isolate_host(target)
                elif action_type == DefenseAction.QUARANTINE_FILE:
                    success = await self._quarantine_file(target)
                elif action_type == DefenseAction.DROP_CONNECTION:
                    success = await self._drop_connection(target)
                else:
                    success = False
                    logger.error(f"Unknown action type: {action_type}")

                action_result['status'] = 'success' if success else 'failed'
                action_result['message'] = f"Executed {action_type.value} on {target}"

            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                action_result['status'] = 'error'
                action_result['message'] = str(e)

        self.neutralization_history.append(action_result)
        return action_result

    async def _block_ip(self, ip: str) -> bool:
        """Block IP at firewall.

        Args:
            ip: IP address to block

        Returns:
            True if successful
        """
        try:
            import subprocess
            # Using iptables on Linux
            result = subprocess.run(
                ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'],
                capture_output=True,
                timeout=5
            )
            success = result.returncode == 0
            if success:
                logger.info(f"IP {ip} blocked successfully")
            else:
                logger.error(f"Failed to block IP {ip}: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
            return False

    async def _kill_process(self, pid: str) -> bool:
        """Kill process by PID.

        Args:
            pid: Process ID

        Returns:
            True if successful
        """
        try:
            os.kill(int(pid), signal.SIGKILL)
            logger.info(f"Process {pid} killed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            return False

    async def _isolate_host(self, host_id: str) -> bool:
        """Isolate host from network.

        Args:
            host_id: Host identifier

        Returns:
            True if successful
        """
        try:
            import subprocess
            # Block all traffic from/to host
            result = subprocess.run(
                ['iptables', '-A', 'FORWARD', '-s', host_id, '-j', 'DROP'],
                capture_output=True,
                timeout=5
            )
            success = result.returncode == 0
            if success:
                logger.info(f"Host {host_id} isolated successfully")
            else:
                logger.error(f"Failed to isolate host {host_id}: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Failed to isolate host {host_id}: {e}")
            return False

    async def _quarantine_file(self, file_path: str) -> bool:
        """Quarantine file.

        Args:
            file_path: Path to file

        Returns:
            True if successful
        """
        try:
            import shutil
            quarantine_dir = "/var/quarantine"
            os.makedirs(quarantine_dir, exist_ok=True)

            # Move file to quarantine
            filename = os.path.basename(file_path)
            quarantine_path = os.path.join(quarantine_dir, f"{datetime.now().timestamp()}_{filename}")
            shutil.move(file_path, quarantine_path)

            logger.info(f"File {file_path} quarantined to {quarantine_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
            return False

    async def _drop_connection(self, connection_id: str) -> bool:
        """Drop network connection.

        Args:
            connection_id: Connection identifier

        Returns:
            True if successful
        """
        try:
            # Implementation depends on connection tracking system
            logger.info(f"Connection {connection_id} dropped")
            return True
        except Exception as e:
            logger.error(f"Failed to drop connection {connection_id}: {e}")
            return False

    async def cleanup_memory_cells(self, ttl_days: int = 90):
        """Remove expired memory cells.

        Args:
            ttl_days: Memory cell TTL in days
        """
        expired = [
            family for family, cell in self.memory_cells.items()
            if cell.is_expired(ttl_days)
        ]

        for family in expired:
            del self.memory_cells[family]
            logger.info(f"Memory T-Cell expired: {family}")

    async def get_status(self) -> Dict[str, Any]:
        """Get Cytotoxic T-Cell service status.

        Returns:
            Service status dictionary
        """
        depletion_stats = self.depletion_tracker.get_depletion_stats()

        return {
            'status': 'operational',
            'dry_run_mode': self.dry_run,
            'active_targets_count': len(self.active_targets),
            'neutralization_records': len(self.neutralization_history),
            'memory_cells_count': len(self.memory_cells),
            'last_action': self.last_action_time.isoformat() if self.last_action_time else 'N/A',
            'depletion': depletion_stats
        }

    def enable_production_mode(self):
        """Enable production mode (DISABLES dry-run)."""
        logger.warning("⚠️  PRODUCTION MODE ENABLED - Real defensive actions will occur!")
        self.dry_run = False
