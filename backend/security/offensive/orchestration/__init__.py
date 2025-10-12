"""
Offensive Orchestration - AI-driven attack chain coordination.

Orchestrates multi-stage attacks with intelligent decision-making.
"""
from .attack_chain import AttackChain, AttackStage, ChainResult, StageType, StageStatus
from .campaign_manager import CampaignManager, Campaign, CampaignStatus, CampaignTarget, TargetPriority
from .intelligence_fusion import IntelligenceFusion, ThreatIntelligence, IntelligenceSource, ThreatLevel

__all__ = [
    "AttackChain",
    "AttackStage",
    "ChainResult",
    "StageType",
    "StageStatus",
    "CampaignManager",
    "Campaign",
    "CampaignStatus",
    "CampaignTarget",
    "TargetPriority",
    "IntelligenceFusion",
    "ThreatIntelligence",
    "IntelligenceSource",
    "ThreatLevel"
]
