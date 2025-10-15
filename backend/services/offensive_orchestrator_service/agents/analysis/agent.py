"""
Analysis Agent - Campaign Analysis and Curriculum Learning.

Analyzes campaign results, identifies patterns, and implements
curriculum learning for progressive difficulty scaling.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Campaign difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AnalysisMetric(Enum):
    """Analysis metrics."""
    SUCCESS_RATE = "success_rate"
    TIME_TO_COMPROMISE = "time_to_compromise"
    STEALTH_SCORE = "stealth_score"
    TECHNIQUES_USED = "techniques_used"
    VULNERABILITIES_FOUND = "vulnerabilities_found"


@dataclass
class CampaignResult:
    """Campaign execution result."""
    
    id: str
    campaign_id: str
    success: bool
    duration: float
    findings_count: int
    exploits_successful: int
    actions_executed: int
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningObjective:
    """Curriculum learning objective."""
    
    id: str
    name: str
    difficulty: DifficultyLevel
    prerequisites: List[str]
    success_criteria: Dict[str, float]
    completed: bool = False


@dataclass
class CurriculumProgress:
    """Progress through curriculum."""
    
    objectives_completed: List[str]
    current_difficulty: DifficultyLevel
    mastery_score: float
    objectives_remaining: List[str]


class Curriculum:
    """
    Curriculum Learning System.
    
    Implements progressive difficulty scaling based on
    agent performance.
    """
    
    def __init__(self) -> None:
        """Initialize curriculum."""
        self.logger = logging.getLogger(__name__)
        self.objectives: Dict[str, LearningObjective] = {}
        self._initialize_objectives()
    
    def _initialize_objectives(self) -> None:
        """Initialize learning objectives."""
        # Beginner objectives
        self.objectives["basic_recon"] = LearningObjective(
            id="basic_recon",
            name="Basic Reconnaissance",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisites=[],
            success_criteria={"success_rate": 0.7, "findings": 5}
        )
        
        self.objectives["port_scanning"] = LearningObjective(
            id="port_scanning",
            name="Port Scanning",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisites=[],
            success_criteria={"success_rate": 0.75, "ports_found": 3}
        )
        
        # Intermediate objectives
        self.objectives["service_enum"] = LearningObjective(
            id="service_enum",
            name="Service Enumeration",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=["port_scanning"],
            success_criteria={"success_rate": 0.8, "services_found": 3}
        )
        
        self.objectives["basic_exploit"] = LearningObjective(
            id="basic_exploit",
            name="Basic Exploitation",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=["basic_recon", "service_enum"],
            success_criteria={"success_rate": 0.6, "exploits_successful": 1}
        )
        
        # Advanced objectives
        self.objectives["priv_escalation"] = LearningObjective(
            id="priv_escalation",
            name="Privilege Escalation",
            difficulty=DifficultyLevel.ADVANCED,
            prerequisites=["basic_exploit"],
            success_criteria={"success_rate": 0.7, "root_access": 1}
        )
        
        self.objectives["lateral_movement"] = LearningObjective(
            id="lateral_movement",
            name="Lateral Movement",
            difficulty=DifficultyLevel.ADVANCED,
            prerequisites=["priv_escalation"],
            success_criteria={"success_rate": 0.65, "hosts_compromised": 2}
        )
        
        # Expert objectives
        self.objectives["persistence"] = LearningObjective(
            id="persistence",
            name="Persistence Mechanisms",
            difficulty=DifficultyLevel.EXPERT,
            prerequisites=["lateral_movement"],
            success_criteria={"success_rate": 0.8, "persistence_established": 1}
        )
        
        self.objectives["stealth_operations"] = LearningObjective(
            id="stealth_operations",
            name="Stealth Operations",
            difficulty=DifficultyLevel.EXPERT,
            prerequisites=["persistence"],
            success_criteria={"success_rate": 0.75, "stealth_score": 0.9}
        )
    
    def get_next_objective(
        self,
        progress: CurriculumProgress
    ) -> Optional[LearningObjective]:
        """
        Get next objective based on progress.
        
        Args:
            progress: Current progress
            
        Returns:
            Next objective or None
        """
        # Find objectives with satisfied prerequisites
        available = []
        
        for obj_id, objective in self.objectives.items():
            # Skip completed
            if obj_id in progress.objectives_completed:
                continue
            
            # Check prerequisites
            prereqs_met = all(
                prereq in progress.objectives_completed
                for prereq in objective.prerequisites
            )
            
            if prereqs_met:
                available.append(objective)
        
        if not available:
            return None
        
        # Return lowest difficulty available
        available.sort(key=lambda x: list(DifficultyLevel).index(x.difficulty))
        return available[0]
    
    def check_objective_completion(
        self,
        objective: LearningObjective,
        results: List[CampaignResult]
    ) -> bool:
        """
        Check if objective is completed.
        
        Args:
            objective: Objective to check
            results: Campaign results
            
        Returns:
            True if objective completed
        """
        if not results:
            return False
        
        # Calculate metrics
        success_rate = sum(1 for r in results if r.success) / len(results)
        
        # Check success criteria
        for criterion, threshold in objective.success_criteria.items():
            if criterion == "success_rate":
                if success_rate < threshold:
                    return False
            
            elif criterion == "findings":
                avg_findings = sum(r.findings_count for r in results) / len(results)
                if avg_findings < threshold:
                    return False
            
            elif criterion == "exploits_successful":
                total_exploits = sum(r.exploits_successful for r in results)
                if total_exploits < threshold:
                    return False
        
        return True
    
    def calculate_mastery(
        self,
        progress: CurriculumProgress,
        results: List[CampaignResult]
    ) -> float:
        """
        Calculate overall mastery score.
        
        Args:
            progress: Current progress
            results: Campaign results
            
        Returns:
            Mastery score (0-1)
        """
        if not self.objectives:
            return 0.0
        
        completed_count = len(progress.objectives_completed)
        total_count = len(self.objectives)
        
        # Base score: completion percentage
        completion_score = completed_count / total_count
        
        # Weighted by difficulty
        difficulty_weights = {
            DifficultyLevel.BEGINNER: 1.0,
            DifficultyLevel.INTERMEDIATE: 1.5,
            DifficultyLevel.ADVANCED: 2.0,
            DifficultyLevel.EXPERT: 3.0
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for obj_id in progress.objectives_completed:
            obj = self.objectives.get(obj_id)
            if obj:
                weight = difficulty_weights[obj.difficulty]
                weighted_score += weight
                total_weight += weight
        
        # Add remaining objectives to total weight
        for obj_id, obj in self.objectives.items():
            if obj_id not in progress.objectives_completed:
                total_weight += difficulty_weights[obj.difficulty]
        
        mastery = weighted_score / total_weight if total_weight > 0 else completion_score
        
        return min(mastery, 1.0)


class AnalysisAgent:
    """
    Analysis Agent - Campaign Analysis and Curriculum Learning.
    
    Features:
    - Campaign result analysis
    - Performance metric calculation
    - Pattern identification
    - Curriculum learning
    - Progressive difficulty scaling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize analysis agent.
        
        Args:
            config: Agent configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.curriculum = Curriculum()
        self.results_history: List[CampaignResult] = []
    
    async def analyze_campaign(
        self,
        campaign_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze campaign results.
        
        Args:
            campaign_data: Campaign execution data
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing campaign: {campaign_data.get('campaign_id')}")
        
        # Create result record
        result = CampaignResult(
            id=f"result_{int(datetime.now().timestamp())}",
            campaign_id=campaign_data.get("campaign_id", "unknown"),
            success=campaign_data.get("success", False),
            duration=campaign_data.get("duration", 0.0),
            findings_count=campaign_data.get("findings_count", 0),
            exploits_successful=campaign_data.get("exploits_successful", 0),
            actions_executed=campaign_data.get("actions_executed", 0),
            metrics=campaign_data.get("metrics", {})
        )
        
        self.results_history.append(result)
        
        # Calculate metrics
        metrics = self._calculate_metrics([result])
        
        # Identify patterns
        patterns = self._identify_patterns(self.results_history[-10:])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, patterns)
        
        return {
            "result_id": result.id,
            "campaign_id": result.campaign_id,
            "success": result.success,
            "metrics": metrics,
            "patterns": patterns,
            "recommendations": recommendations
        }
    
    def _calculate_metrics(
        self,
        results: List[CampaignResult]
    ) -> Dict[str, float]:
        """
        Calculate performance metrics.
        
        Args:
            results: Campaign results
            
        Returns:
            Calculated metrics
        """
        if not results:
            return {}
        
        success_rate = sum(1 for r in results if r.success) / len(results)
        avg_duration = sum(r.duration for r in results) / len(results)
        avg_findings = sum(r.findings_count for r in results) / len(results)
        avg_exploits = sum(r.exploits_successful for r in results) / len(results)
        
        return {
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "avg_findings": avg_findings,
            "avg_exploits": avg_exploits,
            "total_campaigns": len(results)
        }
    
    def _identify_patterns(
        self,
        results: List[CampaignResult]
    ) -> List[Dict[str, Any]]:
        """
        Identify patterns in results.
        
        Args:
            results: Campaign results
            
        Returns:
            Identified patterns
        """
        patterns: List[Dict[str, Any]] = []
        
        if len(results) < 3:
            return patterns
        
        # Pattern: Improving success rate
        recent = results[-3:]
        success_trend = [r.success for r in recent]
        if sum(success_trend) == len(success_trend):
            patterns.append({
                "type": "improving_success",
                "description": "Success rate improving",
                "confidence": 0.8
            })
        
        # Pattern: Consistent failures
        if sum(success_trend) == 0:
            patterns.append({
                "type": "consistent_failure",
                "description": "Multiple consecutive failures",
                "confidence": 0.9
            })
        
        return patterns
    
    def _generate_recommendations(
        self,
        metrics: Dict[str, float],
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on analysis.
        
        Args:
            metrics: Performance metrics
            patterns: Identified patterns
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Success rate based
        success_rate = metrics.get("success_rate", 0.0)
        if success_rate < 0.5:
            recommendations.append("Reduce campaign difficulty")
            recommendations.append("Focus on reconnaissance phase")
        elif success_rate > 0.9:
            recommendations.append("Increase campaign difficulty")
            recommendations.append("Attempt more complex objectives")
        
        # Pattern based
        for pattern in patterns:
            if pattern["type"] == "consistent_failure":
                recommendations.append("Review exploit payloads")
                recommendations.append("Check target configuration")
        
        return recommendations
    
    async def get_curriculum_progress(self) -> CurriculumProgress:
        """
        Get current curriculum progress.
        
        Returns:
            Progress information
        """
        completed = []
        
        # Check each objective
        for obj_id, objective in self.curriculum.objectives.items():
            if self.curriculum.check_objective_completion(objective, self.results_history):
                completed.append(obj_id)
                objective.completed = True
        
        # Determine current difficulty
        if not completed:
            current_difficulty = DifficultyLevel.BEGINNER
        else:
            # Highest difficulty of completed objectives
            completed_objs = [
                self.curriculum.objectives[oid]
                for oid in completed
            ]
            difficulties = [obj.difficulty for obj in completed_objs]
            current_difficulty = max(
                difficulties,
                key=lambda d: list(DifficultyLevel).index(d)
            )
        
        # Calculate mastery
        progress = CurriculumProgress(
            objectives_completed=completed,
            current_difficulty=current_difficulty,
            mastery_score=0.0,
            objectives_remaining=[]
        )
        
        progress.mastery_score = self.curriculum.calculate_mastery(
            progress,
            self.results_history
        )
        
        # Get remaining objectives
        progress.objectives_remaining = [
            obj_id for obj_id in self.curriculum.objectives
            if obj_id not in completed
        ]
        
        return progress
    
    async def get_next_objective(self) -> Optional[LearningObjective]:
        """
        Get next learning objective.
        
        Returns:
            Next objective or None
        """
        progress = await self.get_curriculum_progress()
        return self.curriculum.get_next_objective(progress)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get analysis statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.results_history:
            return {
                "total_campaigns": 0,
                "success_rate": 0.0,
                "objectives_completed": 0
            }
        
        metrics = self._calculate_metrics(self.results_history)
        
        return {
            "total_campaigns": len(self.results_history),
            "success_rate": metrics.get("success_rate", 0.0),
            "avg_duration": metrics.get("avg_duration", 0.0),
            "total_findings": sum(r.findings_count for r in self.results_history),
            "total_exploits": sum(r.exploits_successful for r in self.results_history)
        }
