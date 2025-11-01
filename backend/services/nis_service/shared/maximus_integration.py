"""
MAXIMUS Integration Helper Mixin

This module provides helper utilities for subordinate services to integrate
with MAXIMUS Core, including tool registration, decision requests, and
HITL (Human-in-the-Loop) governance integration.

Key Features:
- Tool registration with MAXIMUS
- Decision request submission to HITL framework
- Automatic tool manifest generation
- Context sharing with MAXIMUS
- Governance compliance checking

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool categories for MAXIMUS integration."""

    BROWSER = "browser"  # MABA tools
    VISION = "vision"  # MVP tools
    HEALING = "healing"  # PENELOPE tools
    ANALYSIS = "analysis"
    AUTOMATION = "automation"


class RiskLevel(str, Enum):
    """Risk levels for HITL decision requests."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MaximusIntegrationMixin:
    """
    Mixin class providing MAXIMUS integration utilities.

    This mixin should be used by subordinate services to register tools,
    submit decisions to HITL, and maintain integration with MAXIMUS Core.

    Usage:
        class MABAService(SubordinateServiceBase, MaximusIntegrationMixin):
            async def initialize(self):
                await self.register_tools_with_maximus(self.get_tool_manifest())
    """

    async def register_tools_with_maximus(self, tools: list[dict[str, Any]]) -> bool:
        """
        Register tools with MAXIMUS Core.

        Args:
            tools: List of tool definitions

        Returns:
            True if registration succeeded, False otherwise
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return False

        try:
            payload = {
                "service_name": self.service_name,
                "tools": tools,
                "timestamp": datetime.utcnow().isoformat(),
            }

            response = await self.call_maximus(
                endpoint="/api/v1/tools/register", method="POST", payload=payload
            )

            if response and response.get("status") == "success":
                logger.info(
                    f"✅ Registered {len(tools)} tools with MAXIMUS "
                    f"for service '{self.service_name}'"
                )
                return True
            else:
                logger.error(f"❌ Tool registration failed: {response}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to register tools with MAXIMUS: {e}")
            return False

    async def submit_hitl_decision(
        self,
        decision_context: dict[str, Any],
        risk_level: RiskLevel,
        requires_approval: bool = True,
    ) -> str | None:
        """
        Submit a decision to MAXIMUS HITL (Human-in-the-Loop) framework.

        Args:
            decision_context: Context information for the decision
            risk_level: Risk level of the decision
            requires_approval: Whether human approval is required

        Returns:
            Decision ID if submitted successfully, None otherwise
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return None

        try:
            payload = {
                "service_name": self.service_name,
                "decision_context": decision_context,
                "risk_level": risk_level.value,
                "requires_approval": requires_approval,
                "submitted_at": datetime.utcnow().isoformat(),
            }

            response = await self.call_maximus(
                endpoint="/api/v1/governance/decisions", method="POST", payload=payload
            )

            if response and response.get("decision_id"):
                decision_id = response["decision_id"]
                logger.info(f"✅ HITL decision submitted: {decision_id}")
                return decision_id
            else:
                logger.error(f"❌ HITL decision submission failed: {response}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to submit HITL decision: {e}")
            return None

    async def check_decision_status(self, decision_id: str) -> dict[str, Any] | None:
        """
        Check the status of a HITL decision.

        Args:
            decision_id: Decision ID to check

        Returns:
            Decision status information or None on error
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return None

        try:
            response = await self.call_maximus(
                endpoint=f"/api/v1/governance/decisions/{decision_id}", method="GET"
            )

            if response:
                logger.debug(f"Decision {decision_id} status: {response.get('status')}")
                return response
            else:
                logger.error(f"Failed to retrieve decision status for {decision_id}")
                return None

        except Exception as e:
            logger.error(f"Error checking decision status: {e}")
            return None

    async def send_context_to_maximus(
        self, context_type: str, context_data: dict[str, Any]
    ) -> bool:
        """
        Send context information to MAXIMUS for awareness.

        Args:
            context_type: Type of context (e.g., "browser_state", "healing_action")
            context_data: Context data payload

        Returns:
            True if context sent successfully, False otherwise
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return False

        try:
            payload = {
                "service_name": self.service_name,
                "context_type": context_type,
                "context_data": context_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            response = await self.call_maximus(
                endpoint="/api/v1/context", method="POST", payload=payload
            )

            if response and response.get("status") == "received":
                logger.debug(f"Context '{context_type}' sent to MAXIMUS")
                return True
            else:
                logger.warning(f"Failed to send context to MAXIMUS: {response}")
                return False

        except Exception as e:
            logger.error(f"Error sending context to MAXIMUS: {e}")
            return False

    def create_tool_definition(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        parameters: dict[str, Any],
        handler: Callable,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> dict[str, Any]:
        """
        Create a standardized tool definition for MAXIMUS.

        Args:
            name: Tool name (unique identifier)
            description: Human-readable description
            category: Tool category
            parameters: JSON schema for parameters
            handler: Async function to handle tool invocation
            risk_level: Risk level for HITL governance

        Returns:
            Tool definition dict
        """
        return {
            "name": name,
            "description": description,
            "category": category.value,
            "service": self.service_name,
            "parameters": parameters,
            "risk_level": risk_level.value,
            "handler_endpoint": f"/api/v1/tools/{name}/invoke",
            "version": (
                self.service_version if hasattr(self, "service_version") else "1.0.0"
            ),
            "metadata": {
                "requires_approval": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
                "timeout_seconds": 300,
                "retryable": risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM],
            },
        }

    async def notify_maximus_event(
        self, event_type: str, event_data: dict[str, Any], priority: str = "normal"
    ) -> bool:
        """
        Send event notification to MAXIMUS.

        Args:
            event_type: Type of event (e.g., "error", "success", "warning")
            event_data: Event data payload
            priority: Event priority (low, normal, high, critical)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return False

        try:
            payload = {
                "service_name": self.service_name,
                "event_type": event_type,
                "event_data": event_data,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
            }

            response = await self.call_maximus(
                endpoint="/api/v1/events", method="POST", payload=payload
            )

            if response and response.get("status") == "received":
                logger.debug(f"Event '{event_type}' sent to MAXIMUS")
                return True
            else:
                logger.warning(f"Failed to send event to MAXIMUS: {response}")
                return False

        except Exception as e:
            logger.error(f"Error sending event to MAXIMUS: {e}")
            return False

    async def request_maximus_decision(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Request a decision from MAXIMUS Core.

        This is useful when a subordinate service needs MAXIMUS to make
        a complex decision based on available context.

        Args:
            query: Natural language query for MAXIMUS
            context: Additional context for decision making

        Returns:
            MAXIMUS response or None on error
        """
        if not hasattr(self, "call_maximus"):
            logger.error("MaximusIntegrationMixin requires SubordinateServiceBase")
            return None

        try:
            payload = {
                "query": query,
                "context": context or {},
                "source_service": self.service_name,
            }

            response = await self.call_maximus(
                endpoint="/query", method="POST", payload=payload
            )

            if response:
                logger.info(
                    f"Received decision from MAXIMUS for query: {query[:50]}..."
                )
                return response
            else:
                logger.error("No response from MAXIMUS")
                return None

        except Exception as e:
            logger.error(f"Error requesting MAXIMUS decision: {e}")
            return None
