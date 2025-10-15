"""
Integration Service - Complete Offensive AI System.

Integrates all agents (orchestrator, recon, exploit, postexploit, analysis)
into a cohesive autonomous offensive security system.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging

from orchestrator.core import MaximusOrchestratorAgent, Campaign, CampaignStatus
from agents.recon.agent import ReconAgent, ReconMission, ReconPhase
from agents.exploit.agent import ExploitAgent, ExploitMission, Vulnerability
from agents.postexploit.agent import PostExploitAgent, PostExploitMission, CompromisedHost
from agents.analysis.agent import AnalysisAgent, DifficultyLevel
from hotl.decision_system import HOTLDecisionSystem, ActionType

logger = logging.getLogger(__name__)


@dataclass
class IntegratedMission:
    """Integrated mission spanning all phases."""
    
    id: str
    objective: str
    scope: List[str]
    constraints: Dict[str, Any]
    status: str
    created_at: datetime
    campaign: Optional[Campaign] = None
    recon_results: Optional[Dict[str, Any]] = None
    exploit_results: Optional[Dict[str, Any]] = None
    postexploit_results: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None


class IntegrationService:
    """
    Integration Service - Complete Offensive AI System.
    
    Orchestrates the full offensive security workflow:
    1. Campaign Planning (Orchestrator)
    2. Reconnaissance (Recon Agent)
    3. Exploitation (Exploit Agent)
    4. Post-Exploitation (PostExploit Agent)
    5. Analysis & Learning (Analysis Agent)
    
    Features:
    - End-to-end automation
    - HOTL approval integration
    - Curriculum-based progression
    - Cross-agent coordination
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize integration service.
        
        Args:
            anthropic_api_key: API key for LLM
            config: Service configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize all agents
        self.orchestrator = MaximusOrchestratorAgent(api_key=anthropic_api_key)
        self.recon_agent = ReconAgent()
        self.exploit_agent = ExploitAgent()
        self.postexploit_agent = PostExploitAgent()
        self.analysis_agent = AnalysisAgent()
        self.hotl_system = HOTLDecisionSystem(
            auto_approve_test=self.config.get("auto_approve", False)
        )
        
        self.active_missions: Dict[str, IntegratedMission] = {}
    
    async def execute_integrated_mission(
        self,
        objective: str,
        scope: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute complete integrated mission.
        
        Args:
            objective: Mission objective
            scope: Target scope
            constraints: Operational constraints
            
        Returns:
            Complete mission results
        """
        constraints = constraints or {}
        
        # Create integrated mission
        mission = IntegratedMission(
            id=f"mission_{int(datetime.now().timestamp())}",
            objective=objective,
            scope=scope,
            constraints=constraints,
            status="planning",
            created_at=datetime.now()
        )
        
        self.active_missions[mission.id] = mission
        self.logger.info(f"Starting integrated mission: {mission.id}")
        
        try:
            # Phase 1: Campaign Planning
            self.logger.info("Phase 1: Campaign Planning")
            mission.status = "planning"
            campaign = await self.orchestrator.plan_campaign(
                objective=objective,
                scope=scope,
                constraints=constraints
            )
            mission.campaign = campaign
            
            # Phase 2: Reconnaissance
            self.logger.info("Phase 2: Reconnaissance")
            mission.status = "reconnaissance"
            recon_results = await self._execute_reconnaissance(campaign)
            mission.recon_results = recon_results
            
            # Phase 3: Exploitation (requires HOTL approval)
            self.logger.info("Phase 3: Exploitation")
            mission.status = "exploitation"
            
            approval_request = await self.hotl_system.request_approval(
                action=ActionType.EXECUTE_EXPLOIT,
                context={
                    "mission_id": mission.id,
                    "vulnerabilities_found": recon_results.get("findings_count", 0)
                },
                risk_level="high"
            )
            
            exploit_results: Dict[str, Any] = {}
            
            if approval_request.status.value == "approved":
                exploit_results = await self._execute_exploitation(recon_results)
                mission.exploit_results = exploit_results
            else:
                exploit_results = {
                    "status": "pending_approval",
                    "approval_request_id": approval_request.id
                }
                mission.exploit_results = exploit_results
            
            # Phase 4: Post-Exploitation (requires HOTL approval)
            if mission.exploit_results and mission.exploit_results.get("status") != "pending_approval":
                self.logger.info("Phase 4: Post-Exploitation")
                mission.status = "post_exploitation"
                
                approval_request = await self.hotl_system.request_approval(
                    action=ActionType.LATERAL_MOVEMENT,
                    context={
                        "mission_id": mission.id,
                        "exploits_successful": exploit_results.get("exploits_successful", 0)
                    },
                    risk_level="critical"
                )
                
                postexploit_results: Dict[str, Any] = {}
                
                if approval_request.status.value == "approved":
                    postexploit_results = await self._execute_postexploit(exploit_results)
                    mission.postexploit_results = postexploit_results
                else:
                    postexploit_results = {
                        "status": "pending_approval",
                        "approval_request_id": approval_request.id
                    }
                    mission.postexploit_results = postexploit_results
            else:
                postexploit_results = {
                    "status": "skipped",
                    "reason": "Exploitation not completed"
                }
            
            # Phase 5: Analysis & Learning
            self.logger.info("Phase 5: Analysis & Learning")
            mission.status = "analyzing"
            analysis_results = await self._execute_analysis(mission)
            mission.analysis_results = analysis_results
            
            mission.status = "completed"
            
            return {
                "mission_id": mission.id,
                "status": "completed",
                "objective": objective,
                "campaign": self._campaign_summary(campaign),
                "reconnaissance": recon_results,
                "exploitation": exploit_results,
                "post_exploitation": postexploit_results,
                "analysis": analysis_results
            }
            
        except Exception as e:
            self.logger.error(f"Mission {mission.id} failed: {e}")
            mission.status = "failed"
            raise
    
    async def _execute_reconnaissance(
        self,
        campaign: Campaign
    ) -> Dict[str, Any]:
        """
        Execute reconnaissance phase.
        
        Args:
            campaign: Planned campaign
            
        Returns:
            Reconnaissance results
        """
        recon_mission = ReconMission(
            id=f"recon_{int(datetime.now().timestamp())}",
            targets=[{"identifier": t, "target_type": "ip"} for t in campaign.scope],
            phases=[ReconPhase.PASSIVE, ReconPhase.ACTIVE],
            constraints=campaign.constraints,
            status="pending",
            created_at=datetime.now()
        )
        
        # Convert targets to proper format
        from agents.recon.agent import Target
        recon_mission.targets = [
            Target(identifier=t, target_type="ip", metadata={})
            for t in campaign.scope
        ]
        
        results = await self.recon_agent.execute_mission(recon_mission)
        return results
    
    async def _execute_exploitation(
        self,
        recon_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute exploitation phase.
        
        Args:
            recon_results: Reconnaissance results
            
        Returns:
            Exploitation results
        """
        # Extract vulnerabilities from recon findings
        findings = recon_results.get("findings", [])
        vulnerabilities = []
        
        for finding in findings[:5]:  # Limit to top 5
            vuln = Vulnerability(
                id=finding.get("id", "unknown"),
                target=finding.get("target", "unknown"),
                vuln_type=finding.get("type", "unknown"),
                severity="medium",
                confidence=finding.get("confidence", 0.5),
                metadata=finding
            )
            vulnerabilities.append(vuln)
        
        if not vulnerabilities:
            return {
                "status": "skipped",
                "reason": "No vulnerabilities found"
            }
        
        exploit_mission = ExploitMission(
            id=f"exploit_{int(datetime.now().timestamp())}",
            vulnerabilities=vulnerabilities,
            constraints={"safe_mode": True},
            status="pending",
            created_at=datetime.now(),
            requires_approval=False  # Already approved by HOTL
        )
        
        results = await self.exploit_agent.execute_mission(exploit_mission, approved=True)
        return results
    
    async def _execute_postexploit(
        self,
        exploit_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute post-exploitation phase.
        
        Args:
            exploit_results: Exploitation results
            
        Returns:
            Post-exploitation results
        """
        # Extract compromised hosts
        exploits = exploit_results.get("exploits", [])
        compromised_hosts = []
        
        for exploit in exploits:
            if exploit.get("status") == "success":
                host = CompromisedHost(
                    id=f"host_{len(compromised_hosts)}",
                    address=exploit.get("vulnerability_id", "unknown"),
                    privileges="user",
                    os_type="linux",
                    metadata=exploit
                )
                compromised_hosts.append(host)
        
        if not compromised_hosts:
            return {
                "status": "skipped",
                "reason": "No hosts compromised"
            }
        
        postexploit_mission = PostExploitMission(
            id=f"postexploit_{int(datetime.now().timestamp())}",
            compromised_hosts=compromised_hosts,
            objectives=["escalate_privileges", "establish_persistence"],
            constraints={},
            status="pending",
            created_at=datetime.now(),
            requires_approval=False  # Already approved by HOTL
        )
        
        results = await self.postexploit_agent.execute_mission(
            postexploit_mission,
            approved=True
        )
        return results
    
    async def _execute_analysis(
        self,
        mission: IntegratedMission
    ) -> Dict[str, Any]:
        """
        Execute analysis and learning phase.
        
        Args:
            mission: Integrated mission
            
        Returns:
            Analysis results
        """
        # Prepare campaign data for analysis
        campaign_data = {
            "campaign_id": mission.id,
            "success": mission.status == "completed",
            "duration": (datetime.now() - mission.created_at).total_seconds(),
            "findings_count": mission.recon_results.get("findings_count", 0) if mission.recon_results else 0,
            "exploits_successful": mission.exploit_results.get("exploits_successful", 0) if mission.exploit_results else 0,
            "actions_executed": mission.postexploit_results.get("actions_executed", 0) if mission.postexploit_results else 0,
            "metrics": {}
        }
        
        analysis = await self.analysis_agent.analyze_campaign(campaign_data)
        
        # Get curriculum progress
        progress = await self.analysis_agent.get_curriculum_progress()
        next_objective = await self.analysis_agent.get_next_objective()
        
        return {
            "analysis": analysis,
            "curriculum_progress": {
                "objectives_completed": len(progress.objectives_completed),
                "current_difficulty": progress.current_difficulty.value,
                "mastery_score": progress.mastery_score,
                "next_objective": next_objective.name if next_objective else None
            }
        }
    
    def _campaign_summary(self, campaign: Campaign) -> Dict[str, Any]:
        """
        Create campaign summary.
        
        Args:
            campaign: Campaign object
            
        Returns:
            Summary dictionary
        """
        return {
            "id": campaign.id,
            "objective": campaign.objective,
            "status": campaign.status.value,
            "phases_count": len(campaign.phases),
            "hotl_checkpoints": campaign.hotl_checkpoints
        }
    
    def get_mission_status(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Get mission status.
        
        Args:
            mission_id: Mission identifier
            
        Returns:
            Mission status or None
        """
        mission = self.active_missions.get(mission_id)
        if not mission:
            return None
        
        return {
            "mission_id": mission.id,
            "status": mission.status,
            "objective": mission.objective,
            "scope": mission.scope,
            "created_at": mission.created_at.isoformat()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_missions": len(self.active_missions),
            "active_missions": len([
                m for m in self.active_missions.values()
                if m.status not in ["completed", "failed"]
            ]),
            "completed_missions": len([
                m for m in self.active_missions.values()
                if m.status == "completed"
            ]),
            "analysis_stats": self.analysis_agent.get_statistics(),
            "rl_stats": self.postexploit_agent.get_rl_stats()
        }
