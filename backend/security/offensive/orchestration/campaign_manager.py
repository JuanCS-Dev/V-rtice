"""
Campaign Manager - Long-term offensive campaign orchestration.

Manages multi-target campaigns with persistent tracking,
scheduling, and adaptive strategy adjustments.
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError
from .attack_chain import AttackChain, ChainResult


class CampaignStatus(Enum):
    """Campaign execution status."""
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TargetPriority(Enum):
    """Target priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class CampaignTarget:
    """Target within a campaign."""
    identifier: str
    priority: TargetPriority
    attack_chain: str
    metadata: Dict = field(default_factory=dict)
    
    # Execution tracking
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    success: bool = False
    results: List[ChainResult] = field(default_factory=list)


@dataclass
class Campaign:
    """
    Offensive campaign.
    
    Represents a coordinated operation against multiple targets
    with strategic objectives and success criteria.
    """
    name: str
    description: str
    objectives: List[str]
    targets: List[CampaignTarget]
    start_date: datetime
    end_date: Optional[datetime] = None
    
    # Configuration
    max_concurrent: int = 5
    retry_failed: bool = True
    max_retries: int = 3
    retry_delay: timedelta = timedelta(hours=1)
    
    # State
    status: CampaignStatus = CampaignStatus.PLANNED
    active_targets: Set[str] = field(default_factory=set)
    completed_targets: Set[str] = field(default_factory=set)
    failed_targets: Set[str] = field(default_factory=set)


class CampaignManager(OffensiveTool):
    """
    AI-enhanced campaign manager.
    
    Orchestrates long-term offensive campaigns across multiple targets
    with intelligent scheduling, resource allocation, and adaptive strategies.
    """
    
    def __init__(self) -> None:
        """Initialize campaign manager."""
        super().__init__(
            name="campaign_manager",
            category="orchestration"
        )
        
        self.campaigns: Dict[str, Campaign] = {}
        self.attack_chains: Dict[str, AttackChain] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_campaign(self, campaign: Campaign) -> None:
        """
        Create new campaign.
        
        Args:
            campaign: Campaign configuration
        """
        if campaign.name in self.campaigns:
            raise OffensiveToolError(
                f"Campaign already exists: {campaign.name}",
                tool_name=self.name
            )
        
        self.campaigns[campaign.name] = campaign
    
    def register_attack_chain(self, chain: AttackChain) -> None:
        """
        Register attack chain for campaigns.
        
        Args:
            chain: Attack chain instance
        """
        self.attack_chains[chain.chain_name] = chain
    
    async def execute(
        self,
        campaign_name: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute campaign.
        
        Args:
            campaign_name: Campaign to execute
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with campaign results
            
        Raises:
            OffensiveToolError: If campaign execution fails
        """
        if campaign_name not in self.campaigns:
            raise OffensiveToolError(
                f"Campaign not found: {campaign_name}",
                tool_name=self.name
            )
        
        campaign = self.campaigns[campaign_name]
        
        if campaign.status not in [CampaignStatus.PLANNED, CampaignStatus.PAUSED]:
            raise OffensiveToolError(
                f"Campaign cannot be executed in {campaign.status.value} state",
                tool_name=self.name
            )
        
        try:
            campaign.status = CampaignStatus.ACTIVE
            
            # Execute campaign
            await self._execute_campaign(campaign)
            
            # Determine final status
            if all(t.identifier in campaign.completed_targets for t in campaign.targets):
                campaign.status = CampaignStatus.COMPLETED
            elif campaign.failed_targets:
                campaign.status = CampaignStatus.FAILED
            
            return ToolResult(
                success=campaign.status == CampaignStatus.COMPLETED,
                data=campaign,
                message=f"Campaign {campaign.status.value}",
                metadata=self._create_metadata(campaign)
            )
            
        except Exception as e:
            campaign.status = CampaignStatus.FAILED
            raise OffensiveToolError(
                f"Campaign execution failed: {str(e)}",
                tool_name=self.name,
                details={"campaign": campaign_name}
            )
    
    async def _execute_campaign(self, campaign: Campaign) -> None:
        """
        Execute campaign against all targets.
        
        Args:
            campaign: Campaign to execute
        """
        # Sort targets by priority
        sorted_targets = sorted(
            campaign.targets,
            key=lambda t: t.priority.value
        )
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(campaign.max_concurrent)
        
        async def execute_target(target: CampaignTarget) -> None:
            async with semaphore:
                await self._execute_target(campaign, target)
        
        # Execute all targets
        tasks = [execute_target(t) for t in sorted_targets]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_target(
        self,
        campaign: Campaign,
        target: CampaignTarget
    ) -> None:
        """
        Execute attack chain against single target.
        
        Args:
            campaign: Parent campaign
            target: Target to attack
        """
        campaign.active_targets.add(target.identifier)
        
        try:
            # Get attack chain
            chain = self.attack_chains.get(target.attack_chain)
            if not chain:
                raise OffensiveToolError(
                    f"Attack chain not found: {target.attack_chain}",
                    tool_name=self.name
                )
            
            # Execute with retries
            max_attempts = campaign.max_retries if campaign.retry_failed else 1
            
            for attempt in range(max_attempts):
                target.attempts += 1
                target.last_attempt = datetime.utcnow()
                
                # Execute chain
                result = await chain.execute(
                    target=target.identifier,
                    initial_context=target.metadata
                )
                
                # Store result
                if isinstance(result.data, ChainResult):
                    target.results.append(result.data)
                
                if result.success:
                    target.success = True
                    campaign.completed_targets.add(target.identifier)
                    break
                
                # Wait before retry
                if attempt < max_attempts - 1:
                    await asyncio.sleep(campaign.retry_delay.total_seconds())
            
            # Mark as failed if all attempts exhausted
            if not target.success:
                campaign.failed_targets.add(target.identifier)
        
        finally:
            campaign.active_targets.discard(target.identifier)
    
    async def pause_campaign(self, campaign_name: str) -> None:
        """
        Pause running campaign.
        
        Args:
            campaign_name: Campaign to pause
        """
        if campaign_name not in self.campaigns:
            raise OffensiveToolError(
                f"Campaign not found: {campaign_name}",
                tool_name=self.name
            )
        
        campaign = self.campaigns[campaign_name]
        
        if campaign.status != CampaignStatus.ACTIVE:
            raise OffensiveToolError(
                f"Campaign is not active: {campaign_name}",
                tool_name=self.name
            )
        
        campaign.status = CampaignStatus.PAUSED
        
        # Cancel running tasks
        if campaign_name in self.running_tasks:
            self.running_tasks[campaign_name].cancel()
    
    async def resume_campaign(self, campaign_name: str) -> ToolResult:
        """
        Resume paused campaign.
        
        Args:
            campaign_name: Campaign to resume
            
        Returns:
            ToolResult
        """
        if campaign_name not in self.campaigns:
            raise OffensiveToolError(
                f"Campaign not found: {campaign_name}",
                tool_name=self.name
            )
        
        campaign = self.campaigns[campaign_name]
        
        if campaign.status != CampaignStatus.PAUSED:
            raise OffensiveToolError(
                f"Campaign is not paused: {campaign_name}",
                tool_name=self.name
            )
        
        return await self.execute(campaign_name)
    
    def get_campaign_status(self, campaign_name: str) -> Dict:
        """
        Get campaign status.
        
        Args:
            campaign_name: Campaign name
            
        Returns:
            Status dictionary
        """
        if campaign_name not in self.campaigns:
            raise OffensiveToolError(
                f"Campaign not found: {campaign_name}",
                tool_name=self.name
            )
        
        campaign = self.campaigns[campaign_name]
        
        total_targets = len(campaign.targets)
        completed = len(campaign.completed_targets)
        failed = len(campaign.failed_targets)
        active = len(campaign.active_targets)
        
        return {
            "name": campaign.name,
            "status": campaign.status.value,
            "progress": {
                "total": total_targets,
                "completed": completed,
                "failed": failed,
                "active": active,
                "remaining": total_targets - completed - failed
            },
            "success_rate": completed / total_targets if total_targets > 0 else 0.0,
            "objectives_met": self._check_objectives(campaign)
        }
    
    def _check_objectives(self, campaign: Campaign) -> List[bool]:
        """
        Check if campaign objectives are met.
        
        Args:
            campaign: Campaign to check
            
        Returns:
            List of boolean values for each objective
        """
        # Simplified objective checking
        # In production, this would evaluate actual objective criteria
        objectives_met = []
        
        for _ in campaign.objectives:
            # Check if enough targets completed
            success_rate = len(campaign.completed_targets) / len(campaign.targets)
            objectives_met.append(success_rate >= 0.8)
        
        return objectives_met
    
    def _create_metadata(self, campaign: Campaign) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            campaign: Campaign
            
        Returns:
            Tool metadata
        """
        total = len(campaign.targets)
        completed = len(campaign.completed_targets)
        
        return ToolMetadata(
            tool_name=self.name,
            execution_time=0.0,
            success_rate=completed / total if total > 0 else 0.0,
            confidence_score=0.9 if campaign.status == CampaignStatus.COMPLETED else 0.5,
            resource_usage={
                "total_targets": total,
                "attack_chains": len(self.attack_chains)
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate campaign manager.
        
        Returns:
            True if validation passes
        """
        # Validate all registered chains
        for chain in self.attack_chains.values():
            if not await chain.validate():
                return False
        
        return True
