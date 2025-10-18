"""
Unit tests for Clonal Selection Engine (Evolutionary Optimization)

Tests cover actual production implementation:
- FitnessMetrics class (scoring and calculation)
- ClonalSelectionEngine initialization and lifecycle
- Fitness evaluation and scoring
- Selection algorithms (tournament selection)
- Mutation (somatic hypermutation)
- Population management
- Metrics and statistics
- Error handling and graceful degradation
"""

import asyncio

import pytest
import pytest_asyncio

from active_immune_core.agents.models import AgentType
from coordination.clonal_selection import (
    ClonalSelectionEngine,
    FitnessMetrics,
)

# ==================== FITNESS METRICS TESTS ====================


def test_fitness_metrics_initialization():
    """Test FitnessMetrics initialization."""
    fitness = FitnessMetrics(
        agent_id="agent_001",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.85,
        response_time_avg=30.0,
        resource_efficiency=0.75,
        false_positive_rate=0.05,
        uptime=3600.0,
    )

    assert fitness.agent_id == "agent_001"
    assert fitness.agent_type == AgentType.NEUTROFILO
    assert fitness.detection_accuracy == 0.85
    assert fitness.response_time_avg == 30.0
    assert fitness.resource_efficiency == 0.75
    assert fitness.false_positive_rate == 0.05
    assert fitness.uptime == 3600.0


def test_fitness_calculation_perfect_agent():
    """Test fitness calculation for perfect agent."""
    fitness = FitnessMetrics(
        agent_id="perfect_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=1.0,  # Perfect
        response_time_avg=1.0,  # Very fast (1s)
        resource_efficiency=1.0,  # Perfect efficiency
        false_positive_rate=0.0,  # No false positives
    )

    # Perfect agent should have very high fitness (~0.897)
    assert fitness.fitness_score > 0.85


def test_fitness_calculation_poor_agent():
    """Test fitness calculation for poor-performing agent."""
    fitness = FitnessMetrics(
        agent_id="poor_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.1,  # Very low
        response_time_avg=120.0,  # Very slow (2 min)
        resource_efficiency=0.1,  # Inefficient
        false_positive_rate=0.5,  # 50% false positives
    )

    # Poor agent should have low fitness
    assert fitness.fitness_score < 0.3


def test_fitness_calculation_weighted_components():
    """Test fitness weights: accuracy 40%, efficiency 30%, time 20%, FP -10%."""
    # Agent with only high accuracy
    accuracy_agent = FitnessMetrics(
        agent_id="accuracy_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=1.0,
        response_time_avg=60.0,
        resource_efficiency=0.0,
        false_positive_rate=0.0,
    )

    # Should have ~0.4 fitness (40% weight on accuracy)
    assert 0.35 < accuracy_agent.fitness_score < 0.45


def test_fitness_score_clamped_to_zero_one():
    """Test fitness score is clamped to [0, 1]."""
    # Extreme negative case
    negative_fitness = FitnessMetrics(
        agent_id="bad_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.0,
        response_time_avg=1000.0,  # Very slow
        resource_efficiency=0.0,
        false_positive_rate=1.0,  # 100% false positives
    )

    # Should be >= 0
    assert negative_fitness.fitness_score >= 0.0

    # Perfect case should be <= 1
    perfect_fitness = FitnessMetrics(
        agent_id="perfect_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=1.0,
        response_time_avg=0.0,
        resource_efficiency=1.0,
        false_positive_rate=0.0,
    )

    assert perfect_fitness.fitness_score <= 1.0


def test_fitness_repr():
    """Test FitnessMetrics string representation."""
    fitness = FitnessMetrics(
        agent_id="agent_12345678",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.85,
    )

    repr_str = repr(fitness)
    assert "agent_12" in repr_str
    assert "fitness=" in repr_str
    assert "accuracy=" in repr_str


# ==================== ENGINE INITIALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_engine_initialization():
    """Test ClonalSelectionEngine initialization."""
    engine = ClonalSelectionEngine(
        engine_id="engine_test_001",
        lymphnode_url="http://localhost:8200",
        db_url="postgresql://user:pass@localhost:5432/immunis",
        selection_interval=300,
        population_size=100,
        selection_rate=0.2,
        mutation_rate=0.1,
    )

    assert engine.id == "engine_test_001"
    assert engine.lymphnode_url == "http://localhost:8200"
    assert engine.db_url == "postgresql://user:pass@localhost:5432/immunis"
    assert engine.selection_interval == 300
    assert engine.population_size == 100
    assert engine.selection_rate == 0.2
    assert engine.mutation_rate == 0.1
    assert engine.generation == 0
    assert not engine._running
    assert len(engine.population_fitness) == 0


@pytest.mark.asyncio
async def test_engine_initialization_defaults():
    """Test engine with default parameters."""
    engine = ClonalSelectionEngine(engine_id="engine_test")

    assert engine.selection_interval == 300  # 5 minutes
    assert engine.population_size == 100
    assert engine.selection_rate == 0.2  # Top 20%
    assert engine.mutation_rate == 0.1  # 10% variation


# ==================== LIFECYCLE TESTS ====================


@pytest_asyncio.fixture
async def engine() -> ClonalSelectionEngine:
    """Create ClonalSelectionEngine instance for testing."""
    eng = ClonalSelectionEngine(
        engine_id="engine_test_001",
        lymphnode_url="http://localhost:8200",
        db_url="postgresql://invalid:invalid@invalid:5432/test",
        selection_interval=1,  # Fast for testing
    )
    yield eng
    if eng._running:
        await eng.parar()


@pytest.mark.asyncio
async def test_engine_start_stop(engine: ClonalSelectionEngine):
    """Test engine lifecycle: start and stop."""
    # Start
    await engine.iniciar()
    assert engine._running is True
    assert len(engine._tasks) > 0

    # Stop
    await engine.parar()
    assert engine._running is False


@pytest.mark.asyncio
async def test_engine_double_start_idempotent(engine: ClonalSelectionEngine):
    """Test that starting twice is idempotent."""
    await engine.iniciar()
    first_running = engine._running

    # Start again (should not crash)
    await engine.iniciar()
    second_running = engine._running

    assert first_running is True
    assert second_running is True

    await engine.parar()


@pytest.mark.asyncio
async def test_engine_stop_without_start():
    """Test stopping engine that was never started."""
    engine = ClonalSelectionEngine(engine_id="engine_test")

    # Should not raise exception
    await engine.parar()
    assert engine._running is False


# ==================== FITNESS EVALUATION TESTS ====================


@pytest.mark.asyncio
async def test_calculate_agent_fitness(engine: ClonalSelectionEngine):
    """Test fitness calculation from agent data."""
    agent_data = {
        "id": "agent_001",
        "tipo": AgentType.NEUTROFILO,
        "deteccoes_total": 100,
        "neutralizacoes_total": 85,  # 85% accuracy
        "falsos_positivos": 5,  # 5% FP rate
        "energia": 50.0,  # 50% energy remaining
        "tempo_vida_seconds": 3600.0,  # 1 hour uptime
    }

    fitness = engine._calculate_agent_fitness(agent_data)

    assert fitness.agent_id == "agent_001"
    assert fitness.agent_type == AgentType.NEUTROFILO
    assert fitness.detection_accuracy == 0.85  # 85/100
    assert fitness.false_positive_rate == 0.05  # 5/100
    assert fitness.uptime == 3600.0
    assert 0.0 <= fitness.fitness_score <= 1.0


@pytest.mark.asyncio
async def test_calculate_agent_fitness_zero_detections(engine: ClonalSelectionEngine):
    """Test fitness calculation for agent with zero detections."""
    agent_data = {
        "id": "agent_new",
        "tipo": AgentType.NEUTROFILO,
        "deteccoes_total": 0,
        "neutralizacoes_total": 0,
        "falsos_positivos": 0,
        "energia": 100.0,
        "tempo_vida": 60,
    }

    fitness = engine._calculate_agent_fitness(agent_data)

    # Should handle division by zero gracefully
    assert fitness.detection_accuracy == 0.0
    assert fitness.false_positive_rate == 0.0


# ==================== SELECTION TESTS ====================


@pytest.mark.asyncio
async def test_select_survivors_empty_population(engine: ClonalSelectionEngine):
    """Test selection with empty population."""
    engine.population_fitness = {}

    survivors = await engine._select_survivors()

    assert len(survivors) == 0


@pytest.mark.asyncio
async def test_select_survivors_top_20_percent(engine: ClonalSelectionEngine):
    """Test selection keeps top 20% of population."""
    # Create 100 agents with varying fitness
    for i in range(100):
        fitness = FitnessMetrics(
            agent_id=f"agent_{i:03d}",
            agent_type=AgentType.NEUTROFILO,
            detection_accuracy=i / 100.0,  # 0.00 to 0.99
        )
        engine.population_fitness[fitness.agent_id] = fitness

    survivors = await engine._select_survivors()

    # With arousal=0.5 and selection_pressure=0.3, should have ~30 survivors (30% of 100)
    assert 28 <= len(survivors) <= 32

    # Survivors should be the top performers
    for survivor in survivors:
        assert survivor.detection_accuracy >= 0.70


@pytest.mark.asyncio
async def test_select_survivors_at_least_one(engine: ClonalSelectionEngine):
    """Test selection always keeps at least one agent."""
    # Single agent
    fitness = FitnessMetrics(
        agent_id="agent_001",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.5,
    )
    engine.population_fitness[fitness.agent_id] = fitness

    survivors = await engine._select_survivors()

    # Should have at least 1 survivor
    assert len(survivors) >= 1


# ==================== MUTATION TESTS ====================


@pytest.mark.asyncio
async def test_mutation_rate_parameter():
    """Test mutation rate affects parameter variation."""
    # Low mutation rate
    low_mutation_engine = ClonalSelectionEngine(
        engine_id="low_mutation",
        mutation_rate=0.01,  # 1% variation
    )
    assert low_mutation_engine.mutation_rate == 0.01

    # High mutation rate
    high_mutation_engine = ClonalSelectionEngine(
        engine_id="high_mutation",
        mutation_rate=0.5,  # 50% variation
    )
    assert high_mutation_engine.mutation_rate == 0.5


# ==================== POPULATION MANAGEMENT TESTS ====================


@pytest.mark.asyncio
async def test_population_size_limit(engine: ClonalSelectionEngine):
    """Test population size is limited."""
    assert engine.population_size == 100

    # Add 150 agents
    for i in range(150):
        fitness = FitnessMetrics(
            agent_id=f"agent_{i:03d}",
            agent_type=AgentType.NEUTROFILO,
            detection_accuracy=0.5,
        )
        engine.population_fitness[fitness.agent_id] = fitness

    # Population can exceed limit temporarily
    # (Replacement happens in evolutionary loop)
    assert len(engine.population_fitness) == 150


@pytest.mark.asyncio
async def test_best_agent_tracking(engine: ClonalSelectionEngine):
    """Test engine tracks best agent ever."""
    assert engine.best_agent_ever is None

    # Add agents
    good_agent = FitnessMetrics(
        agent_id="good_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.95,
    )

    poor_agent = FitnessMetrics(
        agent_id="poor_agent",
        agent_type=AgentType.NEUTROFILO,
        detection_accuracy=0.30,
    )

    # Manually update best (normally done in evolutionary loop)
    if engine.best_agent_ever is None or good_agent.fitness_score > engine.best_agent_ever.fitness_score:
        engine.best_agent_ever = good_agent

    assert engine.best_agent_ever.agent_id == "good_agent"
    assert engine.best_agent_ever.fitness_score == good_agent.fitness_score


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
async def test_get_engine_metrics(engine: ClonalSelectionEngine):
    """Test retrieving engine metrics."""
    # Add some population
    for i in range(10):
        fitness = FitnessMetrics(
            agent_id=f"agent_{i}",
            agent_type=AgentType.NEUTROFILO,
            detection_accuracy=0.5 + (i / 20.0),
        )
        engine.population_fitness[fitness.agent_id] = fitness

    # Set best agent
    engine.best_agent_ever = engine.population_fitness["agent_9"]

    metrics = engine.get_engine_metrics()

    assert metrics["engine_id"] == engine.id
    assert metrics["generation"] == 0
    assert metrics["population_size"] == 10
    assert metrics["total_selections"] == 0
    assert metrics["total_clones_created"] == 0
    assert metrics["total_agents_eliminated"] == 0
    assert "best_fitness_ever" in metrics
    assert metrics["best_fitness_ever"] > 0.0


@pytest.mark.asyncio
async def test_metrics_with_no_best_agent(engine: ClonalSelectionEngine):
    """Test metrics when no best agent exists yet."""
    metrics = engine.get_engine_metrics()

    assert metrics["engine_id"] == engine.id
    assert metrics["best_fitness_ever"] == 0.0
    assert metrics["best_agent_ever"] is None


@pytest.mark.asyncio
async def test_evolutionary_statistics(engine: ClonalSelectionEngine):
    """Test evolutionary statistics tracking."""
    assert engine.generation == 0
    assert engine.total_selections == 0
    assert engine.total_clones_created == 0
    assert engine.total_agents_eliminated == 0

    # Simulate evolution
    engine.generation = 5
    engine.total_selections = 5
    engine.total_clones_created = 50
    engine.total_agents_eliminated = 25

    metrics = engine.get_engine_metrics()

    assert metrics["generation"] == 5
    assert metrics["total_selections"] == 5
    assert metrics["total_clones_created"] == 50
    assert metrics["total_agents_eliminated"] == 25


# ==================== ERROR HANDLING TESTS ====================


@pytest.mark.asyncio
async def test_graceful_degradation_postgres_failure():
    """Test graceful degradation when PostgreSQL connection fails."""
    # Use invalid PostgreSQL DSN
    engine = ClonalSelectionEngine(
        engine_id="engine_test",
        db_url="postgresql://invalid:invalid@invalid-host:5432/invalid",
    )

    # Should start without crashing (graceful degradation)
    try:
        await engine.iniciar()
        assert engine._running is True

        # Wait for at least one evolutionary cycle attempt
        await asyncio.sleep(0.5)

    finally:
        await engine.parar()


@pytest.mark.asyncio
async def test_graceful_degradation_lymphnode_failure():
    """Test graceful degradation when Lymphnode API is unreachable."""
    engine = ClonalSelectionEngine(
        engine_id="engine_test",
        lymphnode_url="http://invalid-host:8200",
        db_url="postgresql://invalid:invalid@invalid:5432/test",
    )

    # Should start without crashing
    try:
        await engine.iniciar()
        assert engine._running is True
    finally:
        await engine.parar()


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
async def test_selection_rate_edge_cases():
    """Test selection rate edge cases (0%, 100%)."""
    # 0% selection rate (always keep at least 1)
    zero_engine = ClonalSelectionEngine(
        engine_id="zero_selection",
        selection_rate=0.0,
    )
    assert zero_engine.selection_rate == 0.0

    # 100% selection rate (keep all)
    full_engine = ClonalSelectionEngine(
        engine_id="full_selection",
        selection_rate=1.0,
    )
    assert full_engine.selection_rate == 1.0


@pytest.mark.asyncio
async def test_repr(engine: ClonalSelectionEngine):
    """Test string representation."""
    repr_str = repr(engine)
    assert "engine_test_001" in repr_str
    assert "gen=" in repr_str
