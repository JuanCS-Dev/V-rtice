"""
MAXIMUS Offensive Orchestrator Core.

Central orchestrator using LLM (Anthropic Claude) to coordinate
specialized agents for offensive security operations.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import anthropic
import json
import logging

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Campaign execution status."""
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentType(Enum):
    """Available agent types."""
    RECON = "recon"
    EXPLOIT = "exploit"
    POSTEXPLOIT = "postexploit"


@dataclass
class Campaign:
    """Offensive security campaign."""
    
    id: str
    objective: str
    scope: List[str]
    constraints: Dict[str, Any]
    status: CampaignStatus
    created_at: datetime
    phases: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessment: Optional[Dict[str, Any]] = None
    hotl_checkpoints: List[str] = field(default_factory=list)


@dataclass
class AgentCommand:
    """Command for specialized agent."""
    
    agent_type: AgentType
    action: str
    parameters: Dict[str, Any]
    priority: int = 5
    requires_approval: bool = False


class MaximusOrchestratorAgent:
    """
    Central orchestrator using LLM (Anthropic Claude).
    Coordinates specialized agents for offensive operations.
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        """
        Initialize orchestrator.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    async def plan_campaign(
        self,
        objective: str,
        scope: List[str],
        constraints: Dict[str, Any]
    ) -> Campaign:
        """
        Plan offensive campaign using LLM.
        
        Args:
            objective: Campaign objective
            scope: Target scope (IPs, domains, etc.)
            constraints: Operational constraints
            
        Returns:
            Planned campaign with phases and commands
        """
        prompt = f"""You are MAXIMUS Offensive Orchestrator.

Objective: {objective}
Scope: {scope}
Constraints: {constraints}

Create detailed attack campaign plan.
Output valid JSON with:
{{
  "campaign_id": "unique_id",
  "phases": [
    {{
      "name": "phase_name",
      "objectives": ["obj1", "obj2"],
      "estimated_duration": "1h"
    }}
  ],
  "agent_commands": [
    {{
      "agent_type": "recon|exploit|postexploit",
      "action": "specific_action",
      "parameters": {{}},
      "requires_approval": true|false
    }}
  ],
  "risk_assessment": {{
    "level": "low|medium|high|critical",
    "factors": ["factor1", "factor2"]
  }},
  "hotl_checkpoints": ["checkpoint1", "checkpoint2"]
}}

Be specific and tactical. Focus on reconnaissance first."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract text from content block
            content_block = message.content[0]
            if hasattr(content_block, 'text'):
                plan_text = content_block.text
            else:
                plan_text = str(content_block)
            
            self.logger.info(f"LLM plan response: {plan_text}")
            
            # Extract JSON from response
            json_start = plan_text.find('{')
            json_end = plan_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                plan_data = json.loads(plan_text[json_start:json_end])
            else:
                raise ValueError("No valid JSON in LLM response")
            
        except Exception as e:
            self.logger.error(f"LLM planning failed: {e}")
            # Fallback to basic plan
            plan_data = {
                "campaign_id": f"camp_{int(datetime.now().timestamp())}",
                "phases": [
                    {
                        "name": "reconnaissance",
                        "objectives": ["Network mapping", "Service enumeration"],
                        "estimated_duration": "2h"
                    }
                ],
                "agent_commands": [],
                "risk_assessment": {"level": "medium", "factors": ["Unknown scope"]},
                "hotl_checkpoints": ["Before exploitation", "Before lateral movement"]
            }
        
        campaign = Campaign(
            id=plan_data.get("campaign_id", f"camp_{int(datetime.now().timestamp())}"),
            objective=objective,
            scope=scope,
            constraints=constraints,
            status=CampaignStatus.PLANNED,
            created_at=datetime.now(),
            phases=plan_data.get("phases", []),
            risk_assessment=plan_data.get("risk_assessment"),
            hotl_checkpoints=plan_data.get("hotl_checkpoints", [])
        )
        
        return campaign
    
    async def coordinate_agents(
        self,
        campaign: Campaign
    ) -> List[AgentCommand]:
        """
        Generate commands for specialized agents.
        
        Args:
            campaign: Campaign to execute
            
        Returns:
            List of agent commands
        """
        commands: List[AgentCommand] = []
        
        # Phase 1: Always start with recon
        commands.append(AgentCommand(
            agent_type=AgentType.RECON,
            action="execute_recon_mission",
            parameters={
                "targets": campaign.scope,
                "objective": campaign.objective,
                "constraints": campaign.constraints
            },
            priority=10,
            requires_approval=False
        ))
        
        # Add commands based on campaign phases
        for phase in campaign.phases:
            phase_name = phase.get("name", "").lower()
            
            if "exploit" in phase_name:
                commands.append(AgentCommand(
                    agent_type=AgentType.EXPLOIT,
                    action="prepare_exploitation",
                    parameters={
                        "phase": phase,
                        "scope": campaign.scope
                    },
                    priority=5,
                    requires_approval=True
                ))
            
            if "post" in phase_name or "lateral" in phase_name:
                commands.append(AgentCommand(
                    agent_type=AgentType.POSTEXPLOIT,
                    action="prepare_postexploit",
                    parameters={
                        "phase": phase,
                        "scope": campaign.scope
                    },
                    priority=3,
                    requires_approval=True
                ))
        
        # Sort by priority
        commands.sort(key=lambda x: x.priority, reverse=True)
        
        return commands
    
    async def analyze_results(
        self,
        campaign: Campaign,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze campaign results using LLM.
        
        Args:
            campaign: Executed campaign
            results: Results from agents
            
        Returns:
            Analysis and recommendations
        """
        prompt = f"""Analyze offensive campaign results.

Campaign: {campaign.objective}
Scope: {campaign.scope}
Results: {json.dumps(results, indent=2)}

Provide:
1. Success metrics
2. Key findings
3. Vulnerabilities discovered
4. Recommendations for next phase
5. Risk updates

Output as JSON."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract text from content block
            content_block = message.content[0]
            if hasattr(content_block, 'text'):
                analysis_text = content_block.text
            else:
                analysis_text = str(content_block)
            
            # Extract JSON
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(analysis_text[json_start:json_end])
            else:
                analysis = {"raw_analysis": analysis_text}
                
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            analysis = {
                "error": str(e),
                "results": results
            }
        
        return analysis
