"""MVP Pydantic Models and Service Implementation.

Author: Vértice Platform Team
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# Core module imports
from core.narrative_engine import NarrativeEngine
from core.system_observer import SystemObserver
from shared.maximus_integration import MaximusIntegrationMixin, RiskLevel, ToolCategory

# Shared library imports (work when in ~/vertice-dev/backend/services/)
from shared.subordinate_service import SubordinateServiceBase

logger = logging.getLogger(__name__)


class NarrativeType(str, Enum):
    """Types of narratives."""

    REALTIME = "realtime"
    SUMMARY = "summary"
    ALERT = "alert"
    BRIEFING = "briefing"


class NarrativeRequest(BaseModel):
    """Request for narrative generation."""

    narrative_type: NarrativeType = Field(..., description="Type of narrative")
    time_range_minutes: int = Field(default=60, description="Time range for analysis")
    focus_areas: list[str] | None = Field(
        default=None, description="Specific areas to focus on"
    )


class NarrativeResponse(BaseModel):
    """Narrative generation response."""

    narrative: str = Field(..., description="Generated narrative")
    metrics_analyzed: int = Field(..., description="Number of metrics analyzed")
    anomalies_detected: int = Field(default=0, description="Anomalies found")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MVPService(SubordinateServiceBase, MaximusIntegrationMixin):
    """MVP (MAXIMUS Vision Protocol) Service Implementation."""

    def __init__(
        self,
        service_name: str,
        service_version: str,
        maximus_endpoint: str | None = None,
    ):
        super().__init__(service_name, service_version, maximus_endpoint)
        self.narrative_engine: NarrativeEngine | None = None
        self.system_observer: SystemObserver | None = None

    async def initialize(self) -> bool:
        try:
            self.narrative_engine = NarrativeEngine(
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("NARRATIVE_MODEL", "claude-sonnet-4.5-20250929"),
            )
            await self.narrative_engine.initialize()
            logger.info("✅ Narrative engine initialized")

            self.system_observer = SystemObserver(
                prometheus_url=os.getenv(
                    "PROMETHEUS_URL", "http://vertice-prometheus:9090"
                ),
                influxdb_url=os.getenv("INFLUXDB_URL", "http://vertice-influxdb:8086"),
            )
            await self.system_observer.initialize()
            logger.info("✅ System observer initialized")

            tools = self._get_tool_manifest()
            await self.register_tools_with_maximus(tools)

            return True
        except Exception as e:
            logger.error(f"Failed to initialize MVP: {e}", exc_info=True)
            return False

    async def shutdown(self) -> None:
        try:
            if self.narrative_engine:
                await self.narrative_engine.shutdown()
            if self.system_observer:
                await self.system_observer.shutdown()
        except Exception as e:
            logger.error(f"Error during MVP shutdown: {e}")

    async def health_check(self) -> dict[str, Any]:
        base_health = await self.get_base_health_info()
        components = {}

        if self.narrative_engine:
            components["narrative_engine"] = await self.narrative_engine.health_check()
        else:
            components["narrative_engine"] = {"status": "not_initialized"}

        if self.system_observer:
            components["system_observer"] = await self.system_observer.health_check()
        else:
            components["system_observer"] = {"status": "not_initialized"}

        base_health["components"] = components
        return base_health

    def _get_tool_manifest(self) -> list[dict[str, Any]]:
        return [
            self.create_tool_definition(
                name="generate_narrative",
                description="Generate real-time narrative about system state",
                category=ToolCategory.VISION,
                parameters={"narrative_type": {"type": "string", "required": True}},
                handler=None,
                risk_level=RiskLevel.LOW,
            ),
            self.create_tool_definition(
                name="detect_anomalies",
                description="Detect anomalies in system metrics",
                category=ToolCategory.ANALYSIS,
                parameters={
                    "time_range_minutes": {"type": "integer", "required": False}
                },
                handler=None,
                risk_level=RiskLevel.MEDIUM,
            ),
        ]
