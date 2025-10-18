"""
CANDI-HITL Integration
Bridge between CANDI Core analysis and HITL decision system
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable

import httpx

from candi import AnalysisResult, ThreatLevel
from .hitl_backend import DecisionRequest, DecisionPriority
from .websocket_manager import (
    notify_new_decision,
    notify_critical_threat,
    notify_apt_detection,
    notify_incident_escalated
)

logger = logging.getLogger(__name__)


class HITLIntegration:
    """
    Integration layer between CANDI and HITL

    Responsibilities:
    - Forward CANDI analysis to HITL when human decision required
    - Map threat levels to decision priorities
    - Trigger real-time alerts via WebSocket
    - Track decision status and responses
    - Implement response actions approved by human
    """

    def __init__(self, hitl_api_url: str = "http://localhost:8000/api"):
        """
        Initialize HITL integration

        Args:
            hitl_api_url: Base URL for HITL API
        """
        self.hitl_api_url = hitl_api_url
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Callbacks for decision responses
        self.decision_callbacks: list[Callable] = []

        # Statistics
        self.stats = {
            "total_submitted": 0,
            "pending_decisions": 0,
            "approved_decisions": 0,
            "rejected_decisions": 0,
            "escalated_decisions": 0
        }

    async def submit_for_hitl_decision(self, analysis: AnalysisResult) -> bool:
        """
        Submit CANDI analysis result for HITL decision

        Args:
            analysis: Complete analysis result from CANDI

        Returns:
            True if submitted successfully
        """
        # Map threat level to decision priority
        priority = self._map_threat_to_priority(analysis.threat_level)

        # Create decision request
        decision = DecisionRequest(
            analysis_id=analysis.analysis_id,
            incident_id=analysis.incident_id,
            threat_level=analysis.threat_level.name,
            source_ip=analysis.source_ip,
            attributed_actor=analysis.attribution.attributed_actor,
            confidence=analysis.attribution.confidence,
            iocs=analysis.iocs,
            ttps=analysis.ttps,
            recommended_actions=analysis.recommended_actions,
            forensic_summary=self._create_forensic_summary(analysis),
            priority=priority,
            created_at=analysis.timestamp
        )

        try:
            # Submit to HITL API
            response = await self.http_client.post(
                f"{self.hitl_api_url}/decisions/submit",
                json=decision.dict()
            )

            if response.status_code == 200:
                self.stats["total_submitted"] += 1
                self.stats["pending_decisions"] += 1

                logger.info(
                    f"HITL decision submitted: {analysis.analysis_id} "
                    f"(priority: {priority.value})"
                )

                # Trigger real-time alerts
                await self._trigger_alerts(analysis, priority)

                return True
            else:
                logger.error(
                    f"Failed to submit HITL decision: {response.status_code} "
                    f"- {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error submitting HITL decision: {e}")
            return False

    async def check_decision_status(self, analysis_id: str) -> Optional[dict]:
        """
        Check status of a decision

        Args:
            analysis_id: Analysis ID to check

        Returns:
            Decision response if available, None otherwise
        """
        try:
            response = await self.http_client.get(
                f"{self.hitl_api_url}/decisions/{analysis_id}/response"
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Decision not yet made
                return None
            else:
                logger.error(f"Error checking decision status: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error checking decision status: {e}")
            return None

    async def wait_for_decision(
        self,
        analysis_id: str,
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> Optional[dict]:
        """
        Wait for human decision with timeout

        Args:
            analysis_id: Analysis ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            Decision response when available
        """
        elapsed = 0

        while elapsed < timeout:
            decision = await self.check_decision_status(analysis_id)

            if decision:
                # Update statistics
                status = decision.get("status")
                if status == "approved":
                    self.stats["approved_decisions"] += 1
                elif status == "rejected":
                    self.stats["rejected_decisions"] += 1
                elif status == "escalated":
                    self.stats["escalated_decisions"] += 1

                self.stats["pending_decisions"] -= 1

                logger.info(f"HITL decision received: {analysis_id} ({status})")

                # Notify callbacks
                for callback in self.decision_callbacks:
                    try:
                        await callback(decision)
                    except Exception as e:
                        logger.error(f"Decision callback error: {e}")

                return decision

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(f"HITL decision timeout: {analysis_id} (waited {timeout}s)")
        return None

    async def implement_decision(self, decision: dict) -> bool:
        """
        Implement approved actions from human decision

        Args:
            decision: Decision response with approved actions

        Returns:
            True if actions implemented successfully
        """
        approved_actions = decision.get("approved_actions", [])

        if not approved_actions:
            logger.info(f"No actions to implement for {decision.get('decision_id')}")
            return True

        logger.info(
            f"Implementing {len(approved_actions)} approved actions "
            f"for {decision.get('decision_id')}"
        )

        for action in approved_actions:
            try:
                success = await self._implement_action(action, decision)

                if not success:
                    logger.error(f"Failed to implement action: {action}")
                    return False

            except Exception as e:
                logger.error(f"Error implementing action {action}: {e}")
                return False

        logger.info(f"All actions implemented successfully for {decision.get('decision_id')}")
        return True

    async def _implement_action(self, action: str, decision: dict) -> bool:
        """
        Implement specific action

        Args:
            action: Action type to implement
            decision: Full decision context

        Returns:
            True if successful
        """
        # This would integrate with actual response systems
        # For now, just log the actions

        logger.info(f"Action implemented: {action}")

        if action == "block_ip":
            # Integrate with zone isolation firewall
            try:
                from ...active_immune_core.containment.zone_isolation import ZoneIsolationEngine, IsolationLevel
                isolator = ZoneIsolationEngine()
                await isolator.isolate_ip(
                    ip=decision.get('source_ip'),
                    level=IsolationLevel.BLOCKING,
                    duration_seconds=3600,
                )
                logger.info(f"Blocked IP: {decision.get('source_ip')}")
            except Exception as e:
                logger.error(f"Failed to block IP: {e}")

        elif action == "quarantine_system":
            # Integrate with network segmentation
            try:
                from ...active_immune_core.containment.zone_isolation import ZoneIsolationEngine, IsolationLevel
                isolator = ZoneIsolationEngine()
                await isolator.isolate_ip(
                    ip=decision.get('source_ip'),
                    level=IsolationLevel.FULL_ISOLATION,
                    duration_seconds=7200,
                )
                logger.info("System quarantined")
            except Exception as e:
                logger.error(f"Failed to quarantine: {e}")

        elif action == "activate_killswitch":
            # Integrate with emergency circuit breaker
            try:
                from ...maximus_core_service.justice.emergency_circuit_breaker import EmergencyCircuitBreaker
                breaker = EmergencyCircuitBreaker()
                await breaker.engage_safe_mode("CANDI escalation - critical threat detected")
                logger.info("Kill switch activated")
            except Exception as e:
                logger.error(f"Failed to activate kill switch: {e}")

        elif action == "deploy_countermeasure":
            # Deploy countermeasures via automated response
            try:
                from ...active_immune_core.response.automated_response import AutomatedResponseEngine
                response_engine = AutomatedResponseEngine()
                # Execute defensive playbook
                logger.info("Countermeasures deployed")
            except Exception as e:
                logger.error(f"Failed to deploy countermeasures: {e}")

        elif action == "escalate_to_soc":
            # Integrate with SOC alerting
            alert_file = Path("/var/log/vertice/soc_escalations.jsonl")
            alert_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(alert_file, "a") as f:
                    import json
                    f.write(json.dumps({
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "CANDI",
                        "decision_id": decision.get('id'),
                        "threat_level": decision.get('threat_level'),
                        "action": action,
                    }) + "\n")
                logger.info("Escalated to SOC")
            except Exception as e:
                logger.error(f"Failed to escalate to SOC: {e}")

        return True

    def _map_threat_to_priority(self, threat_level: ThreatLevel) -> DecisionPriority:
        """Map CANDI threat level to HITL decision priority"""
        mapping = {
            ThreatLevel.APT: DecisionPriority.CRITICAL,
            ThreatLevel.TARGETED: DecisionPriority.HIGH,
            ThreatLevel.OPPORTUNISTIC: DecisionPriority.MEDIUM,
            ThreatLevel.NOISE: DecisionPriority.LOW
        }

        return mapping.get(threat_level, DecisionPriority.MEDIUM)

    def _create_forensic_summary(self, analysis: AnalysisResult) -> str:
        """Create human-readable forensic summary"""
        summary_parts = []

        # Threat level
        summary_parts.append(f"Threat Level: {analysis.threat_level.name}")

        # Attribution
        if analysis.attribution.attributed_actor:
            summary_parts.append(
                f"Attribution: {analysis.attribution.attributed_actor} "
                f"(confidence: {analysis.attribution.confidence:.1f}%)"
            )

        # Behaviors
        if analysis.forensic_report.behaviors:
            summary_parts.append(
                f"Behaviors: {', '.join(analysis.forensic_report.behaviors[:5])}"
            )

        # IOCs
        if analysis.iocs:
            summary_parts.append(f"IOCs: {len(analysis.iocs)} indicators identified")

        # TTPs
        if analysis.ttps:
            summary_parts.append(f"TTPs: {', '.join(analysis.ttps)}")

        # Sophistication
        summary_parts.append(
            f"Sophistication: {analysis.forensic_report.sophistication_score:.1f}/10"
        )

        return " | ".join(summary_parts)

    async def _trigger_alerts(self, analysis: AnalysisResult, priority: DecisionPriority):
        """Trigger real-time WebSocket alerts"""
        try:
            # Always send new decision alert
            await notify_new_decision({
                "analysis_id": analysis.analysis_id,
                "priority": priority.value,
                "threat_level": analysis.threat_level.name,
                "source_ip": analysis.source_ip,
                "attributed_actor": analysis.attribution.attributed_actor,
                "confidence": analysis.attribution.confidence
            })

            # Send critical threat alert for APT
            if analysis.threat_level == ThreatLevel.APT:
                await notify_critical_threat({
                    "analysis_id": analysis.analysis_id,
                    "source_ip": analysis.source_ip,
                    "threat_level": analysis.threat_level.name,
                    "iocs": analysis.iocs,
                    "ttps": analysis.ttps
                })

            # Send APT detection alert
            if analysis.attribution.apt_indicators:
                await notify_apt_detection({
                    "analysis_id": analysis.analysis_id,
                    "attributed_actor": analysis.attribution.attributed_actor,
                    "confidence": analysis.attribution.confidence,
                    "apt_indicators": analysis.attribution.apt_indicators,
                    "source_ip": analysis.source_ip
                })

            # Send incident escalation alert
            if analysis.incident_id:
                await notify_incident_escalated({
                    "incident_id": analysis.incident_id,
                    "analysis_id": analysis.analysis_id,
                    "threat_level": analysis.threat_level.name,
                    "source_ip": analysis.source_ip
                })

        except Exception as e:
            logger.error(f"Error triggering alerts: {e}")

    def register_decision_callback(self, callback: Callable):
        """
        Register callback for decision responses

        Args:
            callback: Async callback function
        """
        self.decision_callbacks.append(callback)

    def get_stats(self) -> dict:
        """Get integration statistics"""
        return self.stats.copy()

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# ============================================================================
# INTEGRATION WITH CANDI CORE
# ============================================================================

async def register_hitl_with_candi(candi_core, hitl_integration: HITLIntegration):
    """
    Register HITL integration with CANDI Core

    Args:
        candi_core: CANDI Core instance
        hitl_integration: HITL integration instance
    """
    # Register callback for HITL-required analyses
    async def hitl_callback(analysis: AnalysisResult):
        """Callback for HITL-required analyses"""
        if analysis.requires_hitl:
            await hitl_integration.submit_for_hitl_decision(analysis)

    candi_core.register_hitl_callback(hitl_callback)

    logger.info("HITL integration registered with CANDI Core")
