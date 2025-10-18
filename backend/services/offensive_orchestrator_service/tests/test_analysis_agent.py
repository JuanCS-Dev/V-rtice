"""Complete tests for Analysis Agent - 100% coverage."""

import pytest
from agents.analysis.agent import (
    AnalysisAgent,
    Curriculum,
    CampaignResult,
    LearningObjective,
    CurriculumProgress,
    DifficultyLevel,
    AnalysisMetric
)


@pytest.fixture
def analysis_agent() -> AnalysisAgent:
    """Create analysis agent instance."""
    return AnalysisAgent()


@pytest.fixture
def sample_campaign_data() -> dict:
    """Create sample campaign data."""
    return {
        "campaign_id": "camp_001",
        "success": True,
        "duration": 120.5,
        "findings_count": 10,
        "exploits_successful": 3,
        "actions_executed": 5,
        "metrics": {"stealth_score": 0.85}
    }


@pytest.fixture
def sample_results() -> list[CampaignResult]:
    """Create sample results."""
    return [
        CampaignResult(
            id="r001",
            campaign_id="c001",
            success=True,
            duration=100.0,
            findings_count=8,
            exploits_successful=2,
            actions_executed=4,
            metrics={}
        ),
        CampaignResult(
            id="r002",
            campaign_id="c002",
            success=True,
            duration=150.0,
            findings_count=12,
            exploits_successful=4,
            actions_executed=6,
            metrics={}
        ),
        CampaignResult(
            id="r003",
            campaign_id="c003",
            success=False,
            duration=80.0,
            findings_count=5,
            exploits_successful=0,
            actions_executed=2,
            metrics={}
        )
    ]


@pytest.mark.asyncio
async def test_analyze_campaign(
    analysis_agent: AnalysisAgent,
    sample_campaign_data: dict
) -> None:
    """Test campaign analysis."""
    result = await analysis_agent.analyze_campaign(sample_campaign_data)
    
    assert result["campaign_id"] == "camp_001"
    assert result["success"] is True
    assert "metrics" in result
    assert "patterns" in result
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_analyze_campaign_creates_result(
    analysis_agent: AnalysisAgent,
    sample_campaign_data: dict
) -> None:
    """Test campaign analysis creates result."""
    initial_count = len(analysis_agent.results_history)
    
    await analysis_agent.analyze_campaign(sample_campaign_data)
    
    assert len(analysis_agent.results_history) == initial_count + 1


def test_calculate_metrics_empty(analysis_agent: AnalysisAgent) -> None:
    """Test metrics calculation with no results."""
    metrics = analysis_agent._calculate_metrics([])
    
    assert metrics == {}


def test_calculate_metrics(
    analysis_agent: AnalysisAgent,
    sample_results: list[CampaignResult]
) -> None:
    """Test metrics calculation."""
    metrics = analysis_agent._calculate_metrics(sample_results)
    
    assert "success_rate" in metrics
    assert "avg_duration" in metrics
    assert "avg_findings" in metrics
    assert "avg_exploits" in metrics
    assert metrics["success_rate"] == 2/3  # 2 successful out of 3
    assert metrics["total_campaigns"] == 3


def test_identify_patterns_insufficient_data(analysis_agent: AnalysisAgent) -> None:
    """Test pattern identification with insufficient data."""
    results = [
        CampaignResult(
            id="r001",
            campaign_id="c001",
            success=True,
            duration=100.0,
            findings_count=5,
            exploits_successful=1,
            actions_executed=2,
            metrics={}
        )
    ]
    
    patterns = analysis_agent._identify_patterns(results)
    
    assert len(patterns) == 0


def test_identify_patterns_improving_success(analysis_agent: AnalysisAgent) -> None:
    """Test pattern identification for improving success."""
    results = [
        CampaignResult(id="r1", campaign_id="c1", success=True,
                      duration=100.0, findings_count=5, exploits_successful=1,
                      actions_executed=2, metrics={}),
        CampaignResult(id="r2", campaign_id="c2", success=True,
                      duration=100.0, findings_count=5, exploits_successful=1,
                      actions_executed=2, metrics={}),
        CampaignResult(id="r3", campaign_id="c3", success=True,
                      duration=100.0, findings_count=5, exploits_successful=1,
                      actions_executed=2, metrics={})
    ]
    
    patterns = analysis_agent._identify_patterns(results)
    
    assert len(patterns) > 0
    assert any(p["type"] == "improving_success" for p in patterns)


def test_identify_patterns_consistent_failure(analysis_agent: AnalysisAgent) -> None:
    """Test pattern identification for consistent failure."""
    results = [
        CampaignResult(id="r1", campaign_id="c1", success=False,
                      duration=100.0, findings_count=5, exploits_successful=0,
                      actions_executed=2, metrics={}),
        CampaignResult(id="r2", campaign_id="c2", success=False,
                      duration=100.0, findings_count=5, exploits_successful=0,
                      actions_executed=2, metrics={}),
        CampaignResult(id="r3", campaign_id="c3", success=False,
                      duration=100.0, findings_count=5, exploits_successful=0,
                      actions_executed=2, metrics={})
    ]
    
    patterns = analysis_agent._identify_patterns(results)
    
    assert len(patterns) > 0
    assert any(p["type"] == "consistent_failure" for p in patterns)


def test_generate_recommendations_low_success(analysis_agent: AnalysisAgent) -> None:
    """Test recommendations for low success rate."""
    metrics = {"success_rate": 0.3}
    patterns = []
    
    recommendations = analysis_agent._generate_recommendations(metrics, patterns)
    
    assert len(recommendations) > 0
    assert any("difficulty" in r.lower() for r in recommendations)


def test_generate_recommendations_high_success(analysis_agent: AnalysisAgent) -> None:
    """Test recommendations for high success rate."""
    metrics = {"success_rate": 0.95}
    patterns = []
    
    recommendations = analysis_agent._generate_recommendations(metrics, patterns)
    
    assert len(recommendations) > 0
    assert any("increase" in r.lower() for r in recommendations)


def test_generate_recommendations_with_patterns(analysis_agent: AnalysisAgent) -> None:
    """Test recommendations based on patterns."""
    metrics = {"success_rate": 0.5}
    patterns = [{"type": "consistent_failure", "description": "test", "confidence": 0.9}]
    
    recommendations = analysis_agent._generate_recommendations(metrics, patterns)
    
    assert len(recommendations) > 0
    assert any("exploit" in r.lower() or "payload" in r.lower() for r in recommendations)


@pytest.mark.asyncio
async def test_get_curriculum_progress_empty(analysis_agent: AnalysisAgent) -> None:
    """Test curriculum progress with no history."""
    progress = await analysis_agent.get_curriculum_progress()
    
    assert isinstance(progress, CurriculumProgress)
    assert progress.current_difficulty == DifficultyLevel.BEGINNER
    assert len(progress.objectives_completed) == 0


@pytest.mark.asyncio
async def test_get_curriculum_progress_with_results(analysis_agent: AnalysisAgent) -> None:
    """Test curriculum progress with results."""
    # Add successful results
    for i in range(10):
        analysis_agent.results_history.append(
            CampaignResult(
                id=f"r{i}",
                campaign_id=f"c{i}",
                success=True,
                duration=100.0,
                findings_count=10,
                exploits_successful=2,
                actions_executed=5,
                metrics={}
            )
        )
    
    progress = await analysis_agent.get_curriculum_progress()
    
    assert progress.mastery_score >= 0.0
    assert progress.mastery_score <= 1.0


@pytest.mark.asyncio
async def test_get_next_objective(analysis_agent: AnalysisAgent) -> None:
    """Test getting next objective."""
    objective = await analysis_agent.get_next_objective()
    
    # Should return beginner objective
    assert objective is not None
    assert objective.difficulty == DifficultyLevel.BEGINNER


def test_get_statistics_empty(analysis_agent: AnalysisAgent) -> None:
    """Test statistics with no history."""
    stats = analysis_agent.get_statistics()
    
    assert stats["total_campaigns"] == 0
    assert stats["success_rate"] == 0.0


def test_get_statistics_with_results(
    analysis_agent: AnalysisAgent,
    sample_results: list[CampaignResult]
) -> None:
    """Test statistics with results."""
    analysis_agent.results_history = sample_results
    
    stats = analysis_agent.get_statistics()
    
    assert stats["total_campaigns"] == 3
    assert "success_rate" in stats
    assert "total_findings" in stats
    assert stats["total_findings"] == 25  # 8 + 12 + 5


def test_curriculum_initialization() -> None:
    """Test curriculum initialization."""
    curriculum = Curriculum()
    
    assert len(curriculum.objectives) > 0
    assert "basic_recon" in curriculum.objectives
    assert "stealth_operations" in curriculum.objectives


def test_curriculum_get_next_objective_beginner() -> None:
    """Test getting next objective for beginner."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=[],
        current_difficulty=DifficultyLevel.BEGINNER,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    objective = curriculum.get_next_objective(progress)
    
    assert objective is not None
    assert objective.difficulty == DifficultyLevel.BEGINNER
    assert len(objective.prerequisites) == 0


def test_curriculum_get_next_objective_with_prereqs() -> None:
    """Test getting next objective with prerequisites."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=["basic_recon", "port_scanning"],
        current_difficulty=DifficultyLevel.INTERMEDIATE,
        mastery_score=0.3,
        objectives_remaining=[]
    )
    
    objective = curriculum.get_next_objective(progress)
    
    assert objective is not None


def test_curriculum_get_next_objective_all_completed() -> None:
    """Test getting next objective when all completed."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=list(curriculum.objectives.keys()),
        current_difficulty=DifficultyLevel.EXPERT,
        mastery_score=1.0,
        objectives_remaining=[]
    )
    
    objective = curriculum.get_next_objective(progress)
    
    assert objective is None


def test_curriculum_check_objective_completion_empty() -> None:
    """Test objective completion with no results."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_recon"]
    
    completed = curriculum.check_objective_completion(objective, [])
    
    assert completed is False


def test_curriculum_check_objective_completion_success() -> None:
    """Test objective completion with sufficient results."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_recon"]
    
    results = [
        CampaignResult(
            id=f"r{i}",
            campaign_id=f"c{i}",
            success=True,
            duration=100.0,
            findings_count=10,
            exploits_successful=1,
            actions_executed=3,
            metrics={}
        )
        for i in range(5)
    ]
    
    completed = curriculum.check_objective_completion(objective, results)
    
    assert completed is True


def test_curriculum_check_objective_completion_insufficient() -> None:
    """Test objective completion with insufficient results."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_recon"]
    
    results = [
        CampaignResult(
            id="r1",
            campaign_id="c1",
            success=False,
            duration=100.0,
            findings_count=2,
            exploits_successful=0,
            actions_executed=1,
            metrics={}
        )
    ]
    
    completed = curriculum.check_objective_completion(objective, results)
    
    assert completed is False


def test_curriculum_calculate_mastery_empty() -> None:
    """Test mastery calculation with no completion."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=[],
        current_difficulty=DifficultyLevel.BEGINNER,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    mastery = curriculum.calculate_mastery(progress, [])
    
    assert mastery == 0.0


def test_curriculum_calculate_mastery_partial() -> None:
    """Test mastery calculation with partial completion."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=["basic_recon", "port_scanning"],
        current_difficulty=DifficultyLevel.BEGINNER,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    mastery = curriculum.calculate_mastery(progress, [])
    
    assert 0.0 < mastery < 1.0


def test_curriculum_calculate_mastery_full() -> None:
    """Test mastery calculation with full completion."""
    curriculum = Curriculum()
    progress = CurriculumProgress(
        objectives_completed=list(curriculum.objectives.keys()),
        current_difficulty=DifficultyLevel.EXPERT,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    mastery = curriculum.calculate_mastery(progress, [])
    
    assert mastery == 1.0


def test_analysis_agent_initialization() -> None:
    """Test agent initialization with config."""
    config = {"test": "value"}
    agent = AnalysisAgent(config=config)
    
    assert agent.config == config
    assert isinstance(agent.curriculum, Curriculum)
    assert len(agent.results_history) == 0


def test_analysis_agent_initialization_default() -> None:
    """Test agent initialization with defaults."""
    agent = AnalysisAgent()
    
    assert agent.config == {}
    assert isinstance(agent.curriculum, Curriculum)


def test_campaign_result_creation() -> None:
    """Test CampaignResult dataclass."""
    result = CampaignResult(
        id="r001",
        campaign_id="c001",
        success=True,
        duration=120.5,
        findings_count=8,
        exploits_successful=3,
        actions_executed=5,
        metrics={"test": "value"}
    )
    
    assert result.id == "r001"
    assert result.success is True
    assert result.duration == 120.5


def test_learning_objective_creation() -> None:
    """Test LearningObjective dataclass."""
    objective = LearningObjective(
        id="test_obj",
        name="Test Objective",
        difficulty=DifficultyLevel.INTERMEDIATE,
        prerequisites=["prereq1"],
        success_criteria={"success_rate": 0.8}
    )
    
    assert objective.id == "test_obj"
    assert objective.difficulty == DifficultyLevel.INTERMEDIATE
    assert objective.completed is False


def test_curriculum_progress_creation() -> None:
    """Test CurriculumProgress dataclass."""
    progress = CurriculumProgress(
        objectives_completed=["obj1", "obj2"],
        current_difficulty=DifficultyLevel.ADVANCED,
        mastery_score=0.75,
        objectives_remaining=["obj3"]
    )
    
    assert len(progress.objectives_completed) == 2
    assert progress.mastery_score == 0.75


def test_difficulty_level_enum() -> None:
    """Test DifficultyLevel enum."""
    assert DifficultyLevel.BEGINNER.value == "beginner"
    assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
    assert DifficultyLevel.ADVANCED.value == "advanced"
    assert DifficultyLevel.EXPERT.value == "expert"


def test_analysis_metric_enum() -> None:
    """Test AnalysisMetric enum."""
    assert AnalysisMetric.SUCCESS_RATE.value == "success_rate"
    assert AnalysisMetric.TIME_TO_COMPROMISE.value == "time_to_compromise"
    assert AnalysisMetric.STEALTH_SCORE.value == "stealth_score"


@pytest.mark.asyncio
async def test_analyze_campaign_default_values(analysis_agent: AnalysisAgent) -> None:
    """Test campaign analysis with missing data."""
    minimal_data = {}
    
    result = await analysis_agent.analyze_campaign(minimal_data)
    
    assert "result_id" in result
    assert result["campaign_id"] == "unknown"
    assert result["success"] is False


def test_curriculum_check_completion_exploits_criteria() -> None:
    """Test objective completion with exploits criteria."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_exploit"]
    
    results = [
        CampaignResult(
            id=f"r{i}",
            campaign_id=f"c{i}",
            success=True,
            duration=100.0,
            findings_count=5,
            exploits_successful=2,
            actions_executed=3,
            metrics={}
        )
        for i in range(3)
    ]
    
    completed = curriculum.check_objective_completion(objective, results)
    
    # Should pass exploits_successful criteria
    assert completed is True


def test_curriculum_check_completion_findings_insufficient() -> None:
    """Test objective completion with insufficient findings."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_recon"]
    
    # Results with low success rate
    results = [
        CampaignResult(
            id=f"r{i}",
            campaign_id=f"c{i}",
            success=True,
            duration=100.0,
            findings_count=2,  # Below threshold of 5
            exploits_successful=1,
            actions_executed=2,
            metrics={}
        )
        for i in range(3)
    ]
    
    completed = curriculum.check_objective_completion(objective, results)
    
    assert completed is False


def test_curriculum_check_completion_exploits_insufficient() -> None:
    """Test objective completion with insufficient exploits."""
    curriculum = Curriculum()
    objective = curriculum.objectives["basic_exploit"]
    
    # Results with no exploits
    results = [
        CampaignResult(
            id=f"r{i}",
            campaign_id=f"c{i}",
            success=True,
            duration=100.0,
            findings_count=10,
            exploits_successful=0,  # Below threshold of 1
            actions_executed=3,
            metrics={}
        )
        for i in range(3)
    ]
    
    completed = curriculum.check_objective_completion(objective, results)
    
    assert completed is False


def test_curriculum_calculate_mastery_no_objectives() -> None:
    """Test mastery calculation with no objectives."""
    curriculum = Curriculum()
    curriculum.objectives = {}  # Empty objectives
    
    progress = CurriculumProgress(
        objectives_completed=[],
        current_difficulty=DifficultyLevel.BEGINNER,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    mastery = curriculum.calculate_mastery(progress, [])
    
    assert mastery == 0.0


def test_curriculum_calculate_mastery_weighted() -> None:
    """Test mastery calculation with weighted difficulty."""
    curriculum = Curriculum()
    
    # Complete some beginner and expert objectives
    progress = CurriculumProgress(
        objectives_completed=["basic_recon", "stealth_operations"],
        current_difficulty=DifficultyLevel.EXPERT,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    mastery = curriculum.calculate_mastery(progress, [])
    
    # Expert objectives should weight more
    assert 0.0 < mastery < 1.0


def test_curriculum_calculate_mastery_zero_weight() -> None:
    """Test mastery calculation fallback to completion score."""
    # Create a new Curriculum instance
    curriculum = Curriculum()
    
    # Create progress with all objectives "completed"
    # but then clear the objectives dictionary
    all_obj_ids = list(curriculum.objectives.keys())
    progress = CurriculumProgress(
        objectives_completed=all_obj_ids,
        current_difficulty=DifficultyLevel.EXPERT,
        mastery_score=0.0,
        objectives_remaining=[]
    )
    
    # Now clear objectives to force edge case
    curriculum.objectives = {}
    
    # This will cause total_weight = 0 (no objectives to add weight from)
    # and completion_score calculation will use 0 in denominator
    mastery = curriculum.calculate_mastery(progress, [])
    
    # Should return 0.0 from early check since objectives is empty
    assert mastery == 0.0
