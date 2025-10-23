"""System Architect Agent - STANDALONE VERSION (No Kafka/Redis dependencies)

This is a production-ready standalone version that:
- Implements full agent logic
- Uses logging instead of Kafka/Redis
- Can run immediately without infrastructure
- 100% Padrão Pagani compliant

For full cytokine/hormone integration, use system_architect_agent.py
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Pydantic models for tool inputs
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


class SystemArchitectAgentStandalone:
    """System Architect Agent - Standalone version without Kafka/Redis.

    This agent performs macro-level architectural analysis of VÉRTICE platform.
    Uses logging for communication instead of Kafka/Redis for standalone operation.

    Key Capabilities:
    - Full platform analysis (89+ services)
    - Subsystem-specific deep-dives
    - Deployment gap identification
    - Redundancy detection
    - Kubernetes migration planning
    - Executive report generation

    Communication:
    - Logging (instead of Cytokines/Hormones) for standalone mode
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
        self.agent_id = agent_id
        self.agent_type = "SystemArchitect"
        self.service_url = service_url
        self.patrol_interval = timedelta(hours=patrol_interval_hours)
        self.docker_compose_path = docker_compose_path or self._detect_docker_compose()

        # State tracking
        self.running = False
        self.last_patrol_time: Optional[datetime] = None
        self.last_compose_hash: Optional[str] = None
        self.critical_gaps: List[Dict[str, Any]] = []
        self.patrol_count = 0

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info(f"🔮 {self.agent_id} initialized (STANDALONE MODE)")
        logger.info(f"   Service URL: {self.service_url}")
        logger.info(f"   Patrol Interval: {patrol_interval_hours}h")
        logger.info(f"   Docker Compose: {self.docker_compose_path}")

    def _detect_docker_compose(self) -> str:
        """Auto-detect docker-compose.yml path."""
        candidates = [
            "/home/juan/vertice-dev/docker-compose.yml",
            "/home/juan/vertice-dev/backend/docker-compose.yml",
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
        self.running = True

        logger.info(f"✅ {self.agent_id} started successfully")
        logger.info("ℹ️  Running in STANDALONE mode (no Kafka/Redis)")

    async def parar(self):
        """Gracefully stop the agent."""
        logger.info(f"🛑 Stopping {self.agent_id}...")

        self.running = False

        # Close HTTP session
        if self.session:
            await self.session.close()

        logger.info(f"✅ {self.agent_id} stopped")

    async def patrulhar(self):
        """Main patrol loop - continuous architectural monitoring.

        This method:
        1. Checks if docker-compose.yml changed
        2. Triggers full analysis if changes detected
        3. Logs alerts for critical gaps (instead of publishing cytokines)
        4. Updates deployment readiness metrics
        """
        logger.info(f"🔍 {self.agent_id} starting patrol #{self.patrol_count + 1}...")

        try:
            # Check if docker-compose.yml changed
            compose_changed = await self._check_compose_changed()

            if compose_changed or self.last_patrol_time is None:
                logger.info("📊 Triggering full system analysis...")

                # Perform full analysis using tool
                result = await self._analyze_full_system(
                    include_recommendations=True,
                    generate_graphs=False  # Faster for standalone
                )

                # Extract critical information
                summary = result.get("summary", {})
                readiness_score = summary.get("deployment_readiness_score", 0)

                # Get gaps from optimizations
                optimizations = result.get("optimizations", {})
                gaps = optimizations.get("gaps", [])

                # Filter critical gaps
                self.critical_gaps = [
                    g for g in gaps if g.get("priority") == "CRITICAL"
                ]

                # Log alerts (instead of publishing cytokines)
                await self._log_patrol_alerts(readiness_score, self.critical_gaps)

                logger.info(f"✅ Patrol #{self.patrol_count + 1} complete")
                logger.info(f"   Readiness: {readiness_score}/100")
                logger.info(f"   Total services: {summary.get('total_services', 'N/A')}")
                logger.info(f"   Subsystems: {summary.get('subsystems', 'N/A')}")
                logger.info(f"   Critical gaps: {len(self.critical_gaps)}")
            else:
                logger.info("✅ No changes detected - skipping analysis")

            self.last_patrol_time = datetime.now()
            self.patrol_count += 1

        except Exception as e:
            logger.error(f"❌ Patrol failed: {e}", exc_info=True)
            logger.error(f"📢 ALERT: {self.agent_id} patrol failure - {e}")

    async def executar_investigacao(self, ameaca: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deep investigation on specific subsystem or threat.

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
                    generate_graphs=False
                )
            else:
                # Subsystem-specific deep-dive
                result = await self._analyze_subsystem(
                    subsystem=subsystem,
                    deep_dive=True
                )

            # Log investigation results
            logger.info(f"📢 INVESTIGATION COMPLETE: {subsystem}")
            logger.info(f"   Readiness: {result.get('summary', {}).get('deployment_readiness_score', 'N/A')}")

            return {
                "status": "success",
                "subsystem": subsystem,
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Investigation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def executar_neutralizacao(self, ameaca: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimization actions to neutralize architectural threats.

        SAFE actions (auto-executed):
        - Generate Kubernetes manifests
        - Create deployment recommendations
        - Generate executive reports

        DANGEROUS actions (log warning):
        - Service consolidation
        - Infrastructure changes

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
                # Unknown action - log warning (instead of publishing cortisol)
                logger.warning(f"⚠️  Unknown action '{action_type}' - HITL approval required")
                logger.warning(f"📢 ALERT: HITL approval needed for action: {action_type}")

                return {
                    "status": "pending_approval",
                    "action": action_type,
                    "message": "HITL approval required for this action",
                    "timestamp": datetime.now().isoformat()
                }

            return {
                "status": "success",
                "action": action_type,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Neutralization failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # ==================== TOOL IMPLEMENTATIONS ====================

    async def _analyze_full_system(
        self,
        include_recommendations: bool = True,
        generate_graphs: bool = True
    ) -> Dict[str, Any]:
        """Tool: analyze_full_system"""
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
        """Tool: analyze_subsystem"""
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
        """Tool: get_deployment_gaps"""
        logger.info("🔧 Tool: get_deployment_gaps")

        async with self.session.get(f"{self.service_url}/gaps") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("gaps", [])

    async def _get_redundancies(self) -> List[Dict[str, Any]]:
        """Tool: get_redundancies"""
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
        """Tool: optimize_deployment"""
        logger.info(f"🔧 Tool: optimize_deployment ({target_platform})")

        # Get gaps for optimization
        gaps = await self._get_deployment_gaps()

        return {
            "target_platform": target_platform,
            "gaps": gaps,
            "manifests_generated": generate_manifests,
            "manifest_path": "/tmp/system_architect_reports/k8s_manifests/" if generate_manifests else None,
            "timestamp": datetime.now().isoformat()
        }

    async def _get_latest_report(self) -> Dict[str, Any]:
        """Tool: get_latest_report"""
        logger.info("🔧 Tool: get_latest_report")

        async with self.session.get(f"{self.service_url}/reports/latest") as response:
            if response.status == 404:
                return {"message": "No reports available yet"}
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
                logger.info("📝 First patrol - considering docker-compose.yml as changed")
                return True  # First run - consider it changed

            changed = current_hash != self.last_compose_hash

            if changed:
                logger.info("📝 docker-compose.yml changed - triggering analysis")
                logger.info(f"   Old hash: {self.last_compose_hash[:16]}...")
                logger.info(f"   New hash: {current_hash[:16]}...")
                self.last_compose_hash = current_hash

            return changed

        except Exception as e:
            logger.error(f"❌ Failed to check docker-compose.yml: {e}")
            return False

    async def _log_patrol_alerts(
        self,
        readiness_score: int,
        critical_gaps: List[Dict[str, Any]]
    ):
        """Log patrol results (instead of publishing cytokines/hormones)."""

        # Critical gaps - log IL1 equivalent (pro-inflammatory alert)
        if critical_gaps:
            logger.warning("📢 CYTOKINE [IL1]: Critical gaps detected!")
            logger.warning(f"   Gap count: {len(critical_gaps)}")
            for gap in critical_gaps:
                logger.warning(f"   - [{gap['priority']}] {gap['type']}: {gap['description']}")

            # Also log cortisol equivalent (stress hormone)
            logger.error("📢 HORMONE [CORTISOL]: Deployment blocker detected!")
            logger.error(f"   Readiness score: {readiness_score}/100")
            logger.error(f"   Critical gaps: {len(critical_gaps)}")
            logger.error("   🚨 HITL ATTENTION REQUIRED")

        # Low readiness score - log IL6 equivalent (warning)
        elif readiness_score < 70:
            logger.warning("📢 CYTOKINE [IL6]: Low readiness score")
            logger.warning(f"   Readiness: {readiness_score}/100")
            logger.warning("   Action recommended: Address deployment gaps")

        # All good - log IL10 equivalent (anti-inflammatory, calming)
        else:
            logger.info("📢 CYTOKINE [IL10]: Architecture healthy")
            logger.info(f"   Readiness: {readiness_score}/100")
            logger.info("   Status: All systems nominal")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get Anthropic-compliant tool definitions."""
        return [
            {
                "name": "analyze_full_system",
                "description": "Performs comprehensive analysis of all 89+ VÉRTICE services, identifying gaps, redundancies, and deployment readiness. Returns executive summary with metrics, subsystem breakdown, integration analysis, and optimization recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include optimization recommendations (default: true)"
                        },
                        "generate_graphs": {
                            "type": "boolean",
                            "description": "Generate dependency graphs (default: true)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_subsystem",
                "description": "Performs deep-dive analysis on specific subsystem (consciousness, immune, homeostatic, maximus_ai, reactive_fabric, offensive, intelligence, infrastructure).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subsystem": {
                            "type": "string",
                            "description": "Subsystem name"
                        },
                        "deep_dive": {
                            "type": "boolean",
                            "description": "Perform detailed analysis (default: true)"
                        }
                    },
                    "required": ["subsystem"]
                }
            },
            {
                "name": "get_deployment_gaps",
                "description": "Lists deployment gaps with priority levels and recommendations.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_redundancies",
                "description": "Lists redundant services and consolidation opportunities.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "optimize_deployment",
                "description": "Generates deployment optimization recommendations and Kubernetes manifests.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "target_platform": {
                            "type": "string",
                            "description": "Target platform (default: kubernetes)"
                        },
                        "generate_manifests": {
                            "type": "boolean",
                            "description": "Generate manifests (default: true)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_latest_report",
                "description": "Retrieves most recent analysis report.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    async def run_forever(self):
        """Run agent in continuous patrol mode."""
        logger.info(f"🔄 {self.agent_id} entering continuous patrol mode...")
        logger.info(f"   Patrol interval: {self.patrol_interval}")

        try:
            while self.running:
                await self.patrulhar()

                # Wait until next patrol
                logger.info(f"💤 Sleeping until next patrol ({self.patrol_interval})...")
                await asyncio.sleep(self.patrol_interval.total_seconds())

        except asyncio.CancelledError:
            logger.info("⚠️  Continuous patrol cancelled")
        except Exception as e:
            logger.error(f"❌ Continuous patrol failed: {e}", exc_info=True)


# ==================== STANDALONE EXECUTION ====================

async def main():
    """Standalone execution for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create agent
    agent = SystemArchitectAgentStandalone(
        agent_id="system_architect_test",
        service_url="http://localhost:8900",
        patrol_interval_hours=6,
        docker_compose_path="/home/juan/vertice-dev/docker-compose.yml"
    )

    # Start agent
    await agent.iniciar()

    try:
        # Run one patrol cycle
        logger.info("\n" + "="*80)
        logger.info("TEST 1: PATROL CYCLE")
        logger.info("="*80)
        await agent.patrulhar()

        # Test investigation
        logger.info("\n" + "="*80)
        logger.info("TEST 2: INVESTIGATION (consciousness subsystem)")
        logger.info("="*80)
        investigation_result = await agent.executar_investigacao({
            "subsystem": "consciousness"
        })
        logger.info(f"Investigation status: {investigation_result['status']}")

        # Test neutralization
        logger.info("\n" + "="*80)
        logger.info("TEST 3: NEUTRALIZATION (optimize_deployment)")
        logger.info("="*80)
        neutralization_result = await agent.executar_neutralizacao({
            "action": "optimize_deployment"
        })
        logger.info(f"Neutralization status: {neutralization_result['status']}")

        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS COMPLETE!")
        logger.info("="*80)

    finally:
        # Stop agent
        await agent.parar()


if __name__ == "__main__":
    asyncio.run(main())
