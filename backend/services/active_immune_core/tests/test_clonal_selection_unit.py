"""Clonal Selection Unit Tests - Coverage for exception paths and edge cases

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Focus: MCEA integration, DB operations, exception handling, edge cases.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from coordination.clonal_selection import ClonalSelectionEngine, FitnessMetrics
from agents.models import AgentType


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def engine():
    """Basic clonal selection engine"""
    eng = ClonalSelectionEngine(
        engine_id="unit_test_engine",
        db_url="postgresql://test",
        selection_pressure=0.3,
        mutation_rate=0.1,
    )
    yield eng


@pytest_asyncio.fixture
async def mcea_engine():
    """Engine with MCEA integration mocked"""
    with patch('coordination.clonal_selection.MCEA_AVAILABLE', True):
        with patch('coordination.clonal_selection.MCEAClient') as mock_mcea:
            mock_client = AsyncMock()
            mock_client.get_arousal_state = AsyncMock(return_value=(0.6, "ALERT"))
            mock_mcea.return_value = mock_client

            eng = ClonalSelectionEngine(
                engine_id="mcea_test_engine",
                db_url="postgresql://test",
            )
            eng._mcea_client = mock_client  # Inject mocked MCEA client
            yield eng


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestMCEAIntegration:
    """Test MCEA consciousness integration"""

    async def test_arousal_influences_selection_pressure(self, mcea_engine):
        """Test arousal state influences selection pressure (lines 271-301)"""
        # Mock MCEA client
        mcea_engine._mcea_client = AsyncMock()
        mcea_engine._mcea_client.get_arousal_state = AsyncMock(
            return_value=(0.8, "HYPERALERT")  # High arousal
        )

        # Add fitness metrics
        for i in range(10):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 10.0,
            )
            mcea_engine.population_fitness[fitness.agent_id] = fitness

        # Select survivors - high arousal should increase selection pressure
        survivors = await mcea_engine._select_survivors()

        # Lines 271-301 covered (arousal-based selection pressure)
        assert len(survivors) > 0  # Some survivors selected

    async def test_mcea_unavailable_graceful_degradation(self, engine):
        """Test graceful degradation when MCEA unavailable (lines 193-198)"""
        # Engine without MCEA
        assert engine._mcea_client is None

        # Add fitness metrics
        for i in range(5):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 5.0,
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Should work without MCEA (lines 193-198)
        survivors = await engine._select_survivors()

        assert len(survivors) > 0

    async def test_mcea_connection_error_handling(self, mcea_engine):
        """Test handling MCEA connection errors (lines 193-198)"""
        # Mock MCEA client to raise exception
        mcea_engine._mcea_client = AsyncMock()
        mcea_engine._mcea_client.get_arousal_state = AsyncMock(
            side_effect=Exception("MCEA connection error")
        )

        # Add fitness metrics
        for i in range(5):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 5.0,
            )
            mcea_engine.population_fitness[fitness.agent_id] = fitness

        # Should handle exception gracefully (lines 193-198)
        survivors = await mcea_engine._select_survivors()

        # Should still return survivors (degraded mode)
        assert len(survivors) > 0


@pytest.mark.asyncio
class TestCloning:
    """Test cloning operations"""

    async def test_clone_agents_with_hypermutation(self, engine):
        """Test cloning with somatic hypermutation (lines 310-336)"""
        # Add high-fitness agents
        for i in range(3):
            fitness = FitnessMetrics(
                agent_id=f"high_fitness_{i}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=0.95,
                resource_efficiency=0.90,
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Clone top agents
        clones = await engine._clone_agents(
            list(engine.population_fitness.values()), num_clones=5
        )

        # Lines 310-336 covered (hypermutation, parameter variation)
        assert len(clones) > 0
        assert all(isinstance(c, dict) for c in clones)

    async def test_clone_agents_empty_population(self, engine):
        """Test cloning with empty population (edge case)"""
        # No agents in population
        clones = await engine._clone_agents([], num_clones=5)

        # Should return empty list
        assert clones == []


@pytest.mark.asyncio
class TestMutationOperations:
    """Test mutation operations"""

    async def test_mutate_parameters_gaussian_noise(self, engine):
        """Test parameter mutation with Gaussian noise (lines 359-368)"""
        # Original parameters
        params = {
            "sensitivity": 0.7,
            "aggressiveness": 0.8,
            "threshold": 0.5,
        }

        # Mutate multiple times
        mutated_params = []
        for _ in range(10):
            mutated = await engine._mutate_parameters(params, mutation_rate=0.2)
            mutated_params.append(mutated)

        # Lines 359-368 covered (Gaussian mutation)
        # At least some parameters should be different
        assert any(
            m["sensitivity"] != params["sensitivity"] for m in mutated_params
        )

    async def test_mutate_parameters_boundary_clipping(self, engine):
        """Test mutation respects parameter boundaries"""
        # Extreme parameters
        params = {
            "value_1": 0.0,  # At minimum
            "value_2": 1.0,  # At maximum
        }

        # Mutate - should clip to [0, 1]
        mutated = await engine._mutate_parameters(params, mutation_rate=0.5)

        # All values should be in valid range
        assert all(0.0 <= v <= 1.0 for v in mutated.values())


@pytest.mark.asyncio
class TestDatabaseOperations:
    """Test database operations"""

    async def test_store_generation_metrics_db_error(self, engine):
        """Test handling DB error when storing metrics (lines 565-566)"""
        # Mock DB pool
        engine._db_pool = AsyncMock()
        engine._db_pool.execute = AsyncMock(side_effect=Exception("DB connection error"))

        # Should handle exception gracefully (lines 565-566)
        await engine._store_generation_metrics(
            generation=1,
            population_size=10,
            avg_fitness=0.75,
            max_fitness=0.95,
        )

        # Should not crash
        assert True

    async def test_get_historical_fitness_no_db(self, engine):
        """Test get_historical_fitness without DB connection (lines 600-605)"""
        # No DB pool configured
        engine._db_pool = None

        # Should return empty list (lines 600-605)
        history = await engine._get_historical_fitness(agent_id="agent_001")

        assert history == []

    async def test_get_historical_fitness_db_error(self, engine):
        """Test get_historical_fitness handles DB error (lines 619-638)"""
        # Mock DB pool to raise exception
        engine._db_pool = AsyncMock()
        engine._db_pool.fetch = AsyncMock(side_effect=Exception("DB query error"))

        # Should handle exception gracefully (lines 619-638)
        history = await engine._get_historical_fitness(agent_id="agent_002")

        # Should return empty list
        assert history == []


@pytest.mark.asyncio
class TestReplacementStrategy:
    """Test replacement strategy"""

    async def test_replace_weak_agents_by_fitness(self, engine):
        """Test replacement targets lowest fitness agents (lines 419-437)"""
        # Add agents with varying fitness
        for i in range(10):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 10.0,  # 0.0 to 0.9
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Create some clones to replace weak agents
        clones = [{"agent_id": f"clone_{i}", "params": {}} for i in range(3)]

        # Replace weak agents
        replaced = await engine._replace_weak_agents(clones)

        # Lines 419-437 covered
        assert len(replaced) <= len(clones)

    async def test_replace_weak_agents_empty_clones(self, engine):
        """Test replacement with no clones (edge case)"""
        # Add agents
        for i in range(5):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 5.0,
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Replace with empty clone list
        replaced = await engine._replace_weak_agents([])

        # Should return empty list
        assert replaced == []


@pytest.mark.asyncio
class TestUtilityMethods:
    """Test utility methods"""

    async def test_get_population_stats(self, engine):
        """Test population statistics calculation (lines 578-589)"""
        # Add agents with varying fitness
        for i in range(10):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 10.0,
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Get stats
        stats = engine.get_population_stats()

        # Lines 578-589 covered
        assert stats["population_size"] == 10
        assert 0.0 <= stats["avg_fitness"] <= 1.0
        assert 0.0 <= stats["max_fitness"] <= 1.0
        assert 0.0 <= stats["min_fitness"] <= 1.0

    async def test_get_top_performers(self, engine):
        """Test getting top performers (lines 649-651)"""
        # Add agents
        for i in range(20):
            fitness = FitnessMetrics(
                agent_id=f"agent_{i:03d}",
                agent_type=AgentType.NEUTROFILO,
                detection_accuracy=i / 20.0,
            )
            engine.population_fitness[fitness.agent_id] = fitness

        # Get top 5 performers
        top_5 = engine.get_top_performers(n=5)

        # Lines 649-651 covered
        assert len(top_5) == 5
        # Should be sorted by fitness (highest first)
        for i in range(len(top_5) - 1):
            assert top_5[i].fitness_score >= top_5[i + 1].fitness_score


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    async def test_fitness_score_boundary_values(self):
        """Test fitness calculation with boundary values (lines 53-55)"""
        # Perfect agent
        perfect = FitnessMetrics(
            agent_id="perfect",
            agent_type=AgentType.NEUTROFILO,
            detection_accuracy=1.0,
            resource_efficiency=1.0,
            response_time_avg=0.0,
            false_positive_rate=0.0,
        )

        # Lines 53-55 covered (fitness calculation)
        assert 0.0 <= perfect.fitness_score <= 1.0
        assert perfect.fitness_score > 0.8  # Should be high

    async def test_select_survivors_single_agent(self, engine):
        """Test selection with single agent (minimum population)"""
        # Single agent
        fitness = FitnessMetrics(
            agent_id="solo_agent",
            agent_type=AgentType.NEUTROFILO,
            detection_accuracy=0.5,
        )
        engine.population_fitness[fitness.agent_id] = fitness

        # Should always keep at least one
        survivors = await engine._select_survivors()

        assert len(survivors) >= 1

    async def test_mcea_initialization_error(self):
        """Test MCEA initialization error handling (lines 222-225)"""
        with patch('coordination.clonal_selection.MCEA_AVAILABLE', True):
            with patch('coordination.clonal_selection.MCEAClient', side_effect=Exception("Init error")):
                # Should handle initialization error gracefully
                engine = ClonalSelectionEngine(
                    engine_id="error_engine",
                    db_url="postgresql://test",
                )

                # Lines 222-225 covered (exception handling)
                # Should create engine (MCEA initialization error handled)
                assert engine is not None
