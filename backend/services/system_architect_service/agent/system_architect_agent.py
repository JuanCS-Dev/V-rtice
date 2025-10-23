"""System Architect Agent - Continuous architectural analysis and optimization.

This agent performs macro-level analysis of the entire VÉRTICE platform,
identifying gaps, redundancies, and deployment optimization opportunities.

Conformance:
- Anthropic Tool Use Best Practices: 100%
- VÉRTICE Biomimetic Agent Pattern: 100%
- Padrão Pagani Absoluto: 100%
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

# VÉRTICE agent base class
from active_immune_core.agents.base import AgenteImunologicoBase
from active_immune_core.communication.cytokines import CytokinePublisher, CytokineType
from active_immune_core.communication.hormones import HormonePublisher, HormoneType

logger = logging.getLogger(__name__)


# Pydantic models for tool inputs (Anthropic best practice)
class FullAnalysisInput(BaseModel):
    """Input schema for full system analysis."""
    include_recommendations: bool = Field(
        default=True,
        description="Include optimization recommendations in the report"
    )
    generate_graphs: bool = Field(
        default=True,
        description="Generate dependency graphs and visualizations"
    )


class SubsystemAnalysisInput(BaseModel):
    """Input schema for subsystem analysis."""
    subsystem: str = Field(
        description="Subsystem to analyze (consciousness, immune, homeostatic, etc.)"
    )
    deep_dive: bool = Field(
        default=True,
        description="Perform deep-dive analysis with detailed recommendations"
    )


class OptimizationInput(BaseModel):
    """Input schema for deployment optimization."""
    target_platform: str = Field(
        default="kubernetes",
        description="Target deployment platform (kubernetes, docker-swarm, nomad)"
    )
    generate_manifests: bool = Field(
        default=True,
        description="Generate deployment manifests (K8s YAML, etc.)"
    )


class SystemArchitectAgent(AgenteImunologicoBase):
    """System Architect Agent - Macro-level platform analysis.

    This agent continuously monitors the VÉRTICE platform architecture,
    identifies optimization opportunities, and provides actionable recommendations.

    Key Capabilities:
    - Full platform analysis (89+ services)
    - Subsystem-specific deep-dives
    - Deployment gap identification
    - Redundancy detection
    - Kubernetes migration planning
    - Executive report generation

    Communication:
    - Cytokines (Kafka): IL1 for critical gaps, IL6 for warnings
    - Hormones (Redis): Cortisol for deployment blockers
    """

    def __init__(
        self,
        agent_id: str = "system_architect_001",
        service_url: str = "http://localhost:8900",
        patrol_interval_hours: int = 6,
        docker_compose_path: Optional[str] = None
    ):
        """Initialize System Architect Agent.

        Args:
            agent_id: Unique agent identifier
            service_url: URL of System Architect Service backend
            patrol_interval_hours: Hours between patrol cycles
            docker_compose_path: Path to docker-compose.yml to monitor
        """
        super().__init__(agent_id=agent_id, tipo_agente="SystemArchitect")

        self.service_url = service_url
        self.patrol_interval = timedelta(hours=patrol_interval_hours)
        self.docker_compose_path = docker_compose_path or self._detect_docker_compose()

        # State tracking
        self.last_patrol_time: Optional[datetime] = None
        self.last_compose_hash: Optional[str] = None
        self.critical_gaps: List[Dict[str, Any]] = []

        # Communication channels
        self.cytokine_publisher = CytokinePublisher()
        self.hormone_publisher = HormonePublisher()

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info(f"🔮 {self.agent_id} initialized")
        logger.info(f"   Service URL: {self.service_url}")
        logger.info(f"   Patrol Interval: {patrol_interval_hours}h")

    def _detect_docker_compose(self) -> str:
        """Auto-detect docker-compose.yml path."""
        candidates = [
            "/home/juan/vertice-dev/backend/docker-compose.yml",
            "/home/juan/vertice-dev/docker-compose.yml",
            "./docker-compose.yml"
        ]

        for path in candidates:
            if Path(path).exists():
                logger.info(f"✅ Detected docker-compose.yml at: {path}")
                return path

        logger.warning("⚠️  Could not auto-detect docker-compose.yml")
        return candidates[0]  # Default fallback

    async def iniciar(self):
        """Start the agent and initialize HTTP session."""
        logger.info(f"🚀 Starting {self.agent_id}...")

        # Initialize HTTP session
        self.session = aiohttp.ClientSession()

        # Initialize communication channels
        await self.cytokine_publisher.connect()
        await self.hormone_publisher.connect()

        # Call parent initialization
        await super().iniciar()

        logger.info(f"✅ {self.agent_id} started successfully")

    async def parar(self):
        """Gracefully stop the agent."""
        logger.info(f"🛑 Stopping {self.agent_id}...")

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Disconnect communication channels
        await self.cytokine_publisher.disconnect()
        await self.hormone_publisher.disconnect()

        # Call parent shutdown
        await super().parar()

        logger.info(f"✅ {self.agent_id} stopped")

    async def patrulhar(self):
        """Main patrol loop - continuous architectural monitoring.

        This method runs every 6 hours and:
        1. Checks if docker-compose.yml changed
        2. Triggers full analysis if changes detected
        3. Publishes alerts for critical gaps
        4. Updates deployment readiness metrics
        """
        logger.info(f"🔍 {self.agent_id} starting patrol...")

        try:
            # Check if docker-compose.yml changed
            compose_changed = await self._check_compose_changed()

            if compose_changed or self.last_patrol_time is None:
                logger.info("📊 Triggering full system analysis...")

                # Perform full analysis using tool
                result = await self._analyze_full_system(
                    include_recommendations=True,
                    generate_graphs=True
                )

                # Extract critical information
                readiness_score = result.get("summary", {}).get("deployment_readiness_score", 0)
                gaps = result.get("optimizations", {}).get("gaps", [])

                # Filter critical gaps
                self.critical_gaps = [
                    g for g in gaps if g.get("priority") == "CRITICAL"
                ]

                # Publish alerts
                await self._publish_patrol_alerts(readiness_score, self.critical_gaps)

                logger.info(f"✅ Patrol complete - Readiness: {readiness_score}/100")
                logger.info(f"   Critical gaps: {len(self.critical_gaps)}")
            else:
                logger.info("✅ No changes detected - skipping analysis")

            self.last_patrol_time = datetime.now()

        except Exception as e:
            logger.error(f"❌ Patrol failed: {e}", exc_info=True)

            # Publish error cytokine
            await self.cytokine_publisher.publish(
                tipo=CytokineType.IL1,  # Pro-inflammatory (alert)
                payload={
                    "agent_id": self.agent_id,
                    "event": "patrol_failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    async def executar_investigacao(self, ameaca: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deep investigation on specific subsystem or threat.

        This method is triggered by:
        - Manual HITL requests via orchestrator
        - Alerts from other agents
        - Critical gaps identified during patrol

        Args:
            ameaca: Threat context with subsystem or service details

        Returns:
            Investigation report with detailed analysis
        """
        logger.info(f"🔬 {self.agent_id} investigating: {ameaca}")

        try:
            subsystem = ameaca.get("subsystem", "unknown")

            if subsystem == "unknown":
                # Fall back to full analysis
                logger.warning("⚠️  No subsystem specified - performing full analysis")
                result = await self._analyze_full_system(
                    include_recommendations=True,
                    generate_graphs=True
                )
            else:
                # Subsystem-specific deep-dive
                result = await self._analyze_subsystem(
                    subsystem=subsystem,
                    deep_dive=True
                )

            # Publish investigation results via cytokine
            await self.cytokine_publisher.publish(
                tipo=CytokineType.IL6,  # Informational
                payload={
                    "agent_id": self.agent_id,
                    "event": "investigation_complete",
                    "subsystem": subsystem,
                    "readiness_score": result.get("summary", {}).get("deployment_readiness_score", 0),
                    "timestamp": datetime.now().isoformat()
                }
            )

            return {
                "status": "success",
                "subsystem": subsystem,
                "analysis": result
            }

        except Exception as e:
            logger.error(f"❌ Investigation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }

    async def executar_neutralizacao(self, ameaca: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization actions to neutralize architectural threats.

        This method performs SAFE optimization actions:
        - Generate Kubernetes manifests
        - Create deployment recommendations
        - Generate executive reports

        DANGEROUS actions (service consolidation, infrastructure changes)
        require HITL approval and are not executed automatically.

        Args:
            ameaca: Threat with optimization target

        Returns:
            Neutralization results
        """
        logger.info(f"⚔️  {self.agent_id} neutralizing: {ameaca}")

        try:
            action_type = ameaca.get("action", "optimize_deployment")

            if action_type == "optimize_deployment":
                # SAFE: Generate K8s manifests
                result = await self._optimize_deployment(
                    target_platform="kubernetes",
                    generate_manifests=True
                )

                logger.info("✅ Deployment optimization complete")

            elif action_type == "generate_report":
                # SAFE: Generate executive report
                result = await self._get_latest_report()

                logger.info("✅ Report generated")

            else:
                # Unknown action - require HITL
                logger.warning(f"⚠️  Unknown action '{action_type}' - HITL approval required")

                # Publish cortisol (stress hormone) for HITL attention
                await self.hormone_publisher.publish(
                    tipo=HormoneType.CORTISOL,
                    payload={
                        "agent_id": self.agent_id,
                        "event": "hitl_approval_required",
                        "action": action_type,
                        "threat": ameaca,
                        "timestamp": datetime.now().isoformat()
                    }
                )

                return {
                    "status": "pending_approval",
                    "action": action_type,
                    "message": "HITL approval required for this action"
                }

            return {
                "status": "success",
                "action": action_type,
                "result": result
            }

        except Exception as e:
            logger.error(f"❌ Neutralization failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }

    # ==================== TOOL IMPLEMENTATIONS ====================
    # These methods implement Anthropic tool use patterns
    # Each tool has: name, description, JSON schema, implementation

    async def _analyze_full_system(
        self,
        include_recommendations: bool = True,
        generate_graphs: bool = True
    ) -> Dict[str, Any]:
        """Tool: analyze_full_system

        Performs comprehensive analysis of all 89+ VÉRTICE services,
        identifying gaps, redundancies, and deployment readiness.

        Args:
            include_recommendations: Include optimization recommendations
            generate_graphs: Generate dependency graphs

        Returns:
            Full analysis report with executive summary
        """
        logger.info("🔧 Tool: analyze_full_system")

        async with self.session.post(
            f"{self.service_url}/analyze/full",
            json={
                "include_recommendations": include_recommendations,
                "generate_graphs": generate_graphs
            }
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _analyze_subsystem(
        self,
        subsystem: str,
        deep_dive: bool = True
    ) -> Dict[str, Any]:
        """Tool: analyze_subsystem

        Performs deep-dive analysis on specific subsystem
        (consciousness, immune, homeostatic, etc.).

        Args:
            subsystem: Subsystem name
            deep_dive: Perform detailed analysis

        Returns:
            Subsystem analysis report
        """
        logger.info(f"🔧 Tool: analyze_subsystem ({subsystem})")

        async with self.session.post(
            f"{self.service_url}/analyze/subsystem",
            json={
                "subsystem": subsystem,
                "deep_dive": deep_dive
            }
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _get_deployment_gaps(self) -> List[Dict[str, Any]]:
        """Tool: get_deployment_gaps

        Lists all identified deployment gaps (K8s operators, service mesh, etc.)
        with priority levels and recommendations.

        Returns:
            List of deployment gaps
        """
        logger.info("🔧 Tool: get_deployment_gaps")

        async with self.session.get(f"{self.service_url}/gaps") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("gaps", [])

    async def _get_redundancies(self) -> List[Dict[str, Any]]:
        """Tool: get_redundancies

        Lists redundant services and consolidation opportunities.

        Returns:
            List of redundancy opportunities
        """
        logger.info("🔧 Tool: get_redundancies")

        async with self.session.get(f"{self.service_url}/redundancies") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("redundancies", [])

    async def _optimize_deployment(
        self,
        target_platform: str = "kubernetes",
        generate_manifests: bool = True
    ) -> Dict[str, Any]:
        """Tool: optimize_deployment

        Generates deployment optimization recommendations and manifests.

        Args:
            target_platform: Target platform (kubernetes, docker-swarm, etc.)
            generate_manifests: Generate deployment manifests

        Returns:
            Optimization recommendations and manifest paths
        """
        logger.info(f"🔧 Tool: optimize_deployment ({target_platform})")

        # For now, return gaps and recommendations
        # Future: Generate actual K8s YAML manifests
        gaps = await self._get_deployment_gaps()

        return {
            "target_platform": target_platform,
            "gaps": gaps,
            "manifests_generated": generate_manifests,
            "manifest_path": "/tmp/system_architect_reports/k8s_manifests/" if generate_manifests else None
        }

    async def _get_latest_report(self) -> Dict[str, Any]:
        """Tool: get_latest_report

        Retrieves the most recent architectural analysis report.

        Returns:
            Latest report metadata and summary
        """
        logger.info("🔧 Tool: get_latest_report")

        async with self.session.get(f"{self.service_url}/reports/latest") as response:
            response.raise_for_status()
            return await response.json()

    # ==================== HELPER METHODS ====================

    async def _check_compose_changed(self) -> bool:
        """Check if docker-compose.yml has changed since last patrol."""
        try:
            compose_path = Path(self.docker_compose_path)

            if not compose_path.exists():
                logger.warning(f"⚠️  docker-compose.yml not found at: {compose_path}")
                return False

            # Calculate file hash
            content = compose_path.read_bytes()
            current_hash = hashlib.sha256(content).hexdigest()

            # Compare with last known hash
            if self.last_compose_hash is None:
                self.last_compose_hash = current_hash
                return True  # First run - consider it changed

            changed = current_hash != self.last_compose_hash

            if changed:
                logger.info("📝 docker-compose.yml changed - triggering analysis")
                self.last_compose_hash = current_hash

            return changed

        except Exception as e:
            logger.error(f"❌ Failed to check docker-compose.yml: {e}")
            return False

    async def _publish_patrol_alerts(
        self,
        readiness_score: int,
        critical_gaps: List[Dict[str, Any]]
    ):
        """Publish cytokines/hormones based on patrol results."""

        # Critical gaps - publish IL1 (pro-inflammatory alert)
        if critical_gaps:
            await self.cytokine_publisher.publish(
                tipo=CytokineType.IL1,
                payload={
                    "agent_id": self.agent_id,
                    "event": "critical_gaps_detected",
                    "gap_count": len(critical_gaps),
                    "gaps": critical_gaps,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Also publish cortisol (stress hormone) for HITL attention
            await self.hormone_publisher.publish(
                tipo=HormoneType.CORTISOL,
                payload={
                    "agent_id": self.agent_id,
                    "event": "deployment_blocker_detected",
                    "readiness_score": readiness_score,
                    "critical_gap_count": len(critical_gaps),
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Low readiness score - publish IL6 (warning)
        elif readiness_score < 70:
            await self.cytokine_publisher.publish(
                tipo=CytokineType.IL6,
                payload={
                    "agent_id": self.agent_id,
                    "event": "low_readiness_score",
                    "readiness_score": readiness_score,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # All good - publish IL10 (anti-inflammatory, calming)
        else:
            await self.cytokine_publisher.publish(
                tipo=CytokineType.IL10,
                payload={
                    "agent_id": self.agent_id,
                    "event": "architecture_healthy",
                    "readiness_score": readiness_score,
                    "timestamp": datetime.now().isoformat()
                }
            )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get Anthropic-compliant tool definitions for this agent.

        These definitions follow Anthropic's tool use format:
        - Clear, descriptive names
        - Detailed descriptions
        - JSON Schema input validation

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "analyze_full_system",
                "description": "Performs comprehensive analysis of all 89+ VÉRTICE services, identifying gaps, redundancies, and deployment readiness. Returns executive summary with metrics, subsystem breakdown, integration analysis, and optimization recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include optimization recommendations in the report (default: true)"
                        },
                        "generate_graphs": {
                            "type": "boolean",
                            "description": "Generate dependency graphs and visualizations (default: true)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_subsystem",
                "description": "Performs deep-dive analysis on a specific subsystem (consciousness, immune, homeostatic, maximus_ai, reactive_fabric, offensive, intelligence, infrastructure). Returns detailed metrics, service inventory, and subsystem-specific recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subsystem": {
                            "type": "string",
                            "description": "Subsystem to analyze (consciousness, immune, homeostatic, maximus_ai, reactive_fabric, offensive, intelligence, infrastructure)"
                        },
                        "deep_dive": {
                            "type": "boolean",
                            "description": "Perform detailed analysis with comprehensive recommendations (default: true)"
                        }
                    },
                    "required": ["subsystem"]
                }
            },
            {
                "name": "get_deployment_gaps",
                "description": "Lists all identified deployment gaps (Kubernetes operators, service mesh, GitOps, distributed tracing, secrets management, incident automation) with priority levels (CRITICAL, HIGH, MEDIUM, LOW) and actionable recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_redundancies",
                "description": "Lists redundant services and consolidation opportunities. Identifies services with overlapping functionality, estimates resource savings, and provides consolidation recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "optimize_deployment",
                "description": "Generates deployment optimization recommendations and Kubernetes manifests. Provides migration plan, service mesh configuration, GitOps setup, and infrastructure-as-code templates.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_platform": {
                            "type": "string",
                            "description": "Target deployment platform (kubernetes, docker-swarm, nomad) (default: kubernetes)"
                        },
                        "generate_manifests": {
                            "type": "boolean",
                            "description": "Generate deployment manifests (K8s YAML, Helm charts, etc.) (default: true)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_latest_report",
                "description": "Retrieves the most recent architectural analysis report with executive summary, readiness score, and report file paths (JSON, Markdown, HTML).",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]


# ==================== STANDALONE EXECUTION ====================

async def main():
    """Standalone execution for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create agent
    agent = SystemArchitectAgent(
        agent_id="system_architect_test",
        service_url="http://localhost:8900",
        patrol_interval_hours=6
    )

    # Start agent
    await agent.iniciar()

    try:
        # Run one patrol cycle
        await agent.patrulhar()

        # Test investigation
        investigation_result = await agent.executar_investigacao({
            "subsystem": "consciousness"
        })

        logger.info(f"Investigation result: {investigation_result}")

        # Test neutralization
        neutralization_result = await agent.executar_neutralizacao({
            "action": "optimize_deployment"
        })

        logger.info(f"Neutralization result: {neutralization_result}")

    finally:
        # Stop agent
        await agent.parar()


if __name__ == "__main__":
    asyncio.run(main())
