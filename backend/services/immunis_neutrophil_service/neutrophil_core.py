"""Immunis Neutrophil Service - Production-Ready First Responder

Bio-inspired rapid response service (ephemeral, TTL 24h):
- Lightweight container (minimal resources)
- Auto-scaling based on threat load (HPA integration)
- Ephemeral lifecycle (24h TTL, then self-destruct)
- Integration with RTE for immediate threat response

Like biological neutrophils: First to arrive, short-lived, disposable.
NO MOCKS - Production-ready implementation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class NeutrophilCore:
    """Production-ready Neutrophil service for rapid threat response.

    Characteristics:
    - Lightweight and fast deployment
    - Auto-scales with threat load
    - Self-destructs after 24h (ephemeral)
    - Integrates with RTE for immediate action
    """

    def __init__(
        self,
        neutrophil_id: str,
        ttl_hours: int = 24,
        rte_endpoint: str = "http://reflex-triage-engine:8003"
    ):
        """Initialize Neutrophil.

        Args:
            neutrophil_id: Unique neutrophil instance ID
            ttl_hours: Time to live in hours (default 24)
            rte_endpoint: RTE service endpoint
        """
        self.neutrophil_id = neutrophil_id
        self.birth_time = datetime.now()
        self.death_time = self.birth_time + timedelta(hours=ttl_hours)
        self.rte_endpoint = rte_endpoint

        self.threats_engaged = []
        self.actions_taken = []
        self.status = "active"

        logger.info(f"Neutrophil {neutrophil_id} born (TTL: {ttl_hours}h, death at {self.death_time})")

    async def initiate_rapid_response(
        self,
        threat_id: str,
        threat_type: str,
        severity: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initiate rapid first-responder action against threat.

        Args:
            threat_id: Unique threat identifier
            threat_type: Type of threat
            severity: Threat severity
            details: Threat details

        Returns:
            Response outcome dictionary
        """
        if not self.is_alive():
            logger.warning(f"Neutrophil {self.neutrophil_id} expired - cannot respond")
            return {'status': 'expired', 'neutrophil_id': self.neutrophil_id}

        logger.info(f"Neutrophil {self.neutrophil_id} responding to threat {threat_id}")

        start_time = time.time()

        # Determine response action
        action = self._determine_action(threat_type, severity, details)

        # Execute via RTE autonomous response
        result = await self._execute_via_rte(action, threat_id, details)

        # Record engagement
        engagement = {
            'timestamp': datetime.now().isoformat(),
            'threat_id': threat_id,
            'threat_type': threat_type,
            'severity': severity,
            'action_taken': action,
            'result': result,
            'response_time_ms': (time.time() - start_time) * 1000
        }

        self.threats_engaged.append(engagement)
        self.actions_taken.append(action['type'])

        logger.info(
            f"Neutrophil {self.neutrophil_id} responded in "
            f"{engagement['response_time_ms']:.1f}ms (action: {action['type']})"
        )

        return engagement

    def _determine_action(
        self,
        threat_type: str,
        severity: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine appropriate rapid response action.

        Args:
            threat_type: Type of threat
            severity: Severity level
            details: Threat details

        Returns:
            Action dictionary
        """
        if severity == "critical" or threat_type == "malware":
            return {
                'type': 'isolate_and_quarantine',
                'target': details.get('host_id', 'unknown'),
                'level': 'full'
            }
        elif severity == "high" or threat_type == "intrusion":
            return {
                'type': 'block_network',
                'target': details.get('ip_address', 'unknown'),
                'duration': '1h'
            }
        elif threat_type == "process_anomaly":
            return {
                'type': 'kill_process',
                'target': details.get('process_id', 'unknown')
            }
        else:
            return {
                'type': 'monitor_intensively',
                'target': details.get('target', 'unknown'),
                'duration': '30m'
            }

    async def _execute_via_rte(
        self,
        action: Dict[str, Any],
        threat_id: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action via RTE autonomous response.

        Args:
            action: Action to execute
            threat_id: Threat ID
            details: Threat details

        Returns:
            Execution result
        """
        try:
            import httpx

            # Prepare RTE request
            rte_request = {
                'event_data': details.get('data', '').encode().hex() if isinstance(details.get('data'), str) else '',
                'event_metadata': {
                    'threat_id': threat_id,
                    'ip': details.get('ip_address'),
                    'process_id': details.get('process_id'),
                    **details
                },
                'auto_respond': True
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.rte_endpoint}/rte/scan",
                    json=rte_request,
                    timeout=5.0
                )

                if response.status_code == 200:
                    rte_result = response.json()
                    return {
                        'success': True,
                        'rte_decision': rte_result.get('decision'),
                        'rte_action': rte_result.get('action_taken'),
                        'latency_ms': rte_result.get('latency_ms')
                    }
                else:
                    return {
                        'success': False,
                        'error': f'RTE returned {response.status_code}'
                    }

        except Exception as e:
            logger.error(f"RTE execution failed: {e}")
            return {'success': False, 'error': str(e)}

    def is_alive(self) -> bool:
        """Check if neutrophil is alive (within TTL).

        Returns:
            True if alive, False if expired
        """
        return datetime.now() < self.death_time

    def remaining_lifetime_seconds(self) -> float:
        """Get remaining lifetime in seconds.

        Returns:
            Seconds until self-destruction
        """
        if not self.is_alive():
            return 0.0

        return (self.death_time - datetime.now()).total_seconds()

    async def self_destruct(self) -> Dict[str, Any]:
        """Self-destruct when TTL expires.

        Returns:
            Destruction summary
        """
        logger.info(f"Neutrophil {self.neutrophil_id} self-destructing (TTL expired)")

        self.status = "destroyed"

        summary = {
            'neutrophil_id': self.neutrophil_id,
            'birth_time': self.birth_time.isoformat(),
            'death_time': datetime.now().isoformat(),
            'lifetime_hours': (datetime.now() - self.birth_time).total_seconds() / 3600,
            'threats_engaged': len(self.threats_engaged),
            'actions_taken': len(self.actions_taken),
            'action_breakdown': {
                action: self.actions_taken.count(action)
                for action in set(self.actions_taken)
            }
        }

        # Clear memory
        self.threats_engaged.clear()
        self.actions_taken.clear()

        logger.info(
            f"Neutrophil {self.neutrophil_id} destroyed: "
            f"{summary['threats_engaged']} threats engaged in "
            f"{summary['lifetime_hours']:.1f}h"
        )

        return summary

    async def get_response_status(self, threat_id: str) -> Optional[Dict[str, Any]]:
        """Get status of response to specific threat.

        Args:
            threat_id: Threat ID to query

        Returns:
            Response status or None
        """
        for engagement in self.threats_engaged:
            if engagement.get('threat_id') == threat_id:
                return engagement
        return None

    async def get_status(self) -> Dict[str, Any]:
        """Get neutrophil status.

        Returns:
            Status dictionary
        """
        return {
            'neutrophil_id': self.neutrophil_id,
            'status': self.status,
            'is_alive': self.is_alive(),
            'birth_time': self.birth_time.isoformat(),
            'death_time': self.death_time.isoformat(),
            'remaining_lifetime_seconds': self.remaining_lifetime_seconds(),
            'threats_engaged': len(self.threats_engaged),
            'actions_taken': len(self.actions_taken),
            'rte_endpoint': self.rte_endpoint
        }
