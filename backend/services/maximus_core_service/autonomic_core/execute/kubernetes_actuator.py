"""Kubernetes Actuator - K8s API Integration"""

import logging
import subprocess
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)


class KubernetesActuator:
    """Execute resource changes via Kubernetes API."""

    def __init__(self, dry_run_mode: bool = True):
        self.dry_run_mode = dry_run_mode
        self.action_log = []

    def adjust_hpa(self, service: str, min_replicas: int, max_replicas: int) -> Dict:
        """Adjust Horizontal Pod Autoscaler."""
        cmd = f"kubectl autoscale deployment {service} --min={min_replicas} --max={max_replicas}"
        return self._execute(cmd, 'hpa_adjust')

    def update_resource_limits(self, service: str, cpu_limit: str, memory_limit: str) -> Dict:
        """Update resource limits."""
        cmd = f"kubectl set resources deployment {service} --limits=cpu={cpu_limit},memory={memory_limit}"
        return self._execute(cmd, 'resource_limits')

    def restart_pod(self, service: str) -> Dict:
        """Rolling restart."""
        cmd = f"kubectl rollout restart deployment/{service}"
        return self._execute(cmd, 'pod_restart')

    def _execute(self, cmd: str, action_type: str) -> Dict:
        """Execute with safety checks and logging."""
        if self.dry_run_mode:
            logger.info(f"DRY-RUN: {cmd}")
            self.action_log.append({'cmd': cmd, 'executed': False, 'dry_run': True})
            return {'success': True, 'dry_run': True}

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            success = result.returncode == 0

            self.action_log.append({
                'cmd': cmd,
                'executed': True,
                'success': success,
                'output': result.stdout.decode() if success else result.stderr.decode()
            })

            return {'success': success, 'output': result.stdout.decode()}

        except Exception as e:
            logger.error(f"K8s actuator error: {e}")
            return {'success': False, 'error': str(e)}
