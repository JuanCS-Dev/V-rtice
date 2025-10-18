"""
Tests for AttackMemorySystem (high-level coordinator).

Covers:
- AttackMemorySystem initialization
- System initialization (database + vector store)
- Campaign storage (hybrid storage)
- Campaign retrieval
- Campaign status updates
- Similarity search
- Historical context generation
- Attack memory storage and search
- Statistics retrieval
- Helper functions (extract techniques, summarize results)
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from memory.attack_memory import AttackMemorySystem
from models import CampaignStatus


@pytest.mark.unit
class TestAttackMemorySystemInit:
    """Test AttackMemorySystem initialization."""

    def test_attack_memory_system_init_default(self):
        """Test creating attack memory system with default components."""
        with patch('memory.attack_memory.DatabaseManager') as mock_db_class, \
             patch('memory.attack_memory.VectorStore') as mock_vector_class, \
             patch('memory.attack_memory.EmbeddingGenerator') as mock_embed_class:

            mock_db = Mock()
            mock_vector = Mock()
            mock_embed = Mock()

            mock_db_class.return_value = mock_db
            mock_vector_class.return_value = mock_vector
            mock_embed_class.return_value = mock_embed

            system = AttackMemorySystem()

            assert system.db == mock_db
            assert system.vector_store == mock_vector
            assert system.embeddings == mock_embed

    def test_attack_memory_system_init_with_components(self):
        """Test creating attack memory system with provided components."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        assert system.db == mock_db
        assert system.vector_store == mock_vector
        assert system.embeddings == mock_embed


@pytest.mark.unit
class TestInitialize:
    """Test system initialization."""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful system initialization."""
        mock_db = Mock()
        mock_db.init_db = Mock()

        mock_vector = Mock()
        mock_vector.init_collection = AsyncMock()

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        await system.initialize()

        mock_db.init_db.assert_called_once()
        mock_vector.init_collection.assert_called_once_with(recreate=False)

    @pytest.mark.asyncio
    async def test_initialize_database_error(self):
        """Test handling database initialization error."""
        mock_db = Mock()
        mock_db.init_db = Mock(side_effect=Exception("DB init failed"))

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        with pytest.raises(Exception) as exc_info:
            await system.initialize()

        assert "DB init failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initialize_vector_store_error(self):
        """Test handling vector store initialization error."""
        mock_db = Mock()
        mock_db.init_db = Mock()

        mock_vector = Mock()
        mock_vector.init_collection = AsyncMock(side_effect=Exception("Vector init failed"))

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        with pytest.raises(Exception) as exc_info:
            await system.initialize()

        assert "Vector init failed" in str(exc_info.value)


@pytest.mark.unit
class TestStoreCampaign:
    """Test storing campaigns."""

    @pytest.mark.asyncio
    async def test_store_campaign_success(
        self,
        sample_campaign_plan,
        mock_embedding_vector,
    ):
        """Test successfully storing campaign."""
        # Mock database
        mock_campaign_db = Mock()
        mock_campaign_db.id = uuid4()

        mock_db = Mock()
        mock_db.create_campaign = AsyncMock(return_value=mock_campaign_db)

        # Mock vector store
        mock_vector = Mock()
        mock_vector.store_campaign_embedding = AsyncMock(return_value=str(mock_campaign_db.id))

        # Mock embeddings
        mock_embed = Mock()
        mock_embed.generate_campaign_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        campaign_id = await system.store_campaign(
            campaign=sample_campaign_plan,
            status=CampaignStatus.PLANNED,
        )

        assert campaign_id == mock_campaign_db.id
        mock_db.create_campaign.assert_called_once()
        mock_embed.generate_campaign_embedding.assert_called_once()
        mock_vector.store_campaign_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_campaign_database_error(self, sample_campaign_plan):
        """Test handling database error during storage."""
        mock_db = Mock()
        mock_db.create_campaign = AsyncMock(side_effect=Exception("DB error"))

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        with pytest.raises(Exception) as exc_info:
            await system.store_campaign(campaign=sample_campaign_plan)

        assert "DB error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_campaign_embedding_error(
        self,
        sample_campaign_plan,
        mock_embedding_vector,
    ):
        """Test handling embedding generation error."""
        mock_campaign_db = Mock()
        mock_campaign_db.id = uuid4()

        mock_db = Mock()
        mock_db.create_campaign = AsyncMock(return_value=mock_campaign_db)

        mock_vector = Mock()

        mock_embed = Mock()
        mock_embed.generate_campaign_embedding = AsyncMock(
            side_effect=Exception("Embedding failed")
        )

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        with pytest.raises(Exception) as exc_info:
            await system.store_campaign(campaign=sample_campaign_plan)

        assert "Embedding failed" in str(exc_info.value)


@pytest.mark.unit
class TestGetCampaign:
    """Test retrieving campaigns."""

    @pytest.mark.asyncio
    async def test_get_campaign_success(self):
        """Test successfully retrieving campaign."""
        campaign_id = uuid4()
        mock_campaign = Mock()

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(return_value=mock_campaign)

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        result = await system.get_campaign(campaign_id)

        assert result == mock_campaign
        mock_db.get_campaign.assert_called_once_with(campaign_id)

    @pytest.mark.asyncio
    async def test_get_campaign_not_found(self):
        """Test retrieving non-existent campaign returns None."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(return_value=None)

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        result = await system.get_campaign(campaign_id)

        assert result is None


@pytest.mark.unit
class TestUpdateCampaignStatus:
    """Test updating campaign status."""

    @pytest.mark.asyncio
    async def test_update_campaign_status_success(self, mock_embedding_vector):
        """Test successfully updating campaign status."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.update_campaign_status = AsyncMock(return_value=True)

        mock_vector = Mock()
        mock_vector.get_campaign_embedding = AsyncMock(return_value=None)

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        success = await system.update_campaign_status(
            campaign_id=campaign_id,
            status=CampaignStatus.IN_PROGRESS,
            results={"progress": "50%"},
        )

        assert success is True
        mock_db.update_campaign_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_campaign_status_completed_updates_vector(
        self,
        mock_embedding_vector,
    ):
        """Test updating to completed updates vector metadata."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.update_campaign_status = AsyncMock(return_value=True)

        # Mock vector store with existing embedding
        metadata = {"success": False, "target": "test.com"}
        mock_vector = Mock()
        mock_vector.get_campaign_embedding = AsyncMock(
            return_value=(mock_embedding_vector, metadata)
        )
        mock_vector.store_campaign_embedding = AsyncMock()

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        await system.update_campaign_status(
            campaign_id=campaign_id,
            status=CampaignStatus.COMPLETED,
        )

        # Should update vector metadata
        mock_vector.store_campaign_embedding.assert_called_once()
        call_kwargs = mock_vector.store_campaign_embedding.call_args[1]
        assert call_kwargs["metadata"]["success"] is True

    @pytest.mark.asyncio
    async def test_update_campaign_status_failed_updates_vector(
        self,
        mock_embedding_vector,
    ):
        """Test updating to failed updates vector metadata."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.update_campaign_status = AsyncMock(return_value=True)

        metadata = {"success": True, "target": "test.com"}
        mock_vector = Mock()
        mock_vector.get_campaign_embedding = AsyncMock(
            return_value=(mock_embedding_vector, metadata)
        )
        mock_vector.store_campaign_embedding = AsyncMock()

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        await system.update_campaign_status(
            campaign_id=campaign_id,
            status=CampaignStatus.FAILED,
        )

        # Should update vector metadata with success=False
        mock_vector.store_campaign_embedding.assert_called_once()
        call_kwargs = mock_vector.store_campaign_embedding.call_args[1]
        assert call_kwargs["metadata"]["success"] is False

    @pytest.mark.asyncio
    async def test_update_campaign_status_vector_error_handled(
        self,
        mock_embedding_vector,
    ):
        """Test vector metadata update error is handled gracefully."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.update_campaign_status = AsyncMock(return_value=True)

        mock_vector = Mock()
        mock_vector.get_campaign_embedding = AsyncMock(
            side_effect=Exception("Vector error")
        )

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        # Should not raise exception
        success = await system.update_campaign_status(
            campaign_id=campaign_id,
            status=CampaignStatus.COMPLETED,
        )

        assert success is True  # Database update still succeeded


@pytest.mark.unit
class TestFindSimilarCampaigns:
    """Test finding similar campaigns."""

    @pytest.mark.asyncio
    async def test_find_similar_campaigns_success(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test successfully finding similar campaigns."""
        campaign_id_1 = uuid4()
        campaign_id_2 = uuid4()

        mock_campaign_1 = Mock()
        mock_campaign_2 = Mock()

        # Mock database
        async def get_campaign_side_effect(cid):
            if str(cid) == str(campaign_id_1):
                return mock_campaign_1
            elif str(cid) == str(campaign_id_2):
                return mock_campaign_2
            return None

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(side_effect=get_campaign_side_effect)

        # Mock vector store
        vector_results = [
            (str(campaign_id_1), 0.95, {"target": "example.com"}),
            (str(campaign_id_2), 0.85, {"target": "test.com"}),
        ]
        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=vector_results)

        # Mock embeddings
        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        results = await system.find_similar_campaigns(
            objective=sample_campaign_objective,
            limit=5,
            score_threshold=0.7,
            success_only=True,
        )

        assert len(results) == 2
        assert results[0][0] == mock_campaign_1
        assert results[0][1] == 0.95
        assert results[1][0] == mock_campaign_2
        assert results[1][1] == 0.85

    @pytest.mark.asyncio
    async def test_find_similar_campaigns_empty_results(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test similarity search with no results."""
        mock_db = Mock()

        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=[])

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        results = await system.find_similar_campaigns(
            objective=sample_campaign_objective,
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_find_similar_campaigns_campaign_not_in_db(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test handling campaign found in vector but not in database."""
        campaign_id = uuid4()

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(return_value=None)

        vector_results = [(str(campaign_id), 0.95, {"target": "example.com"})]
        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=vector_results)

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        results = await system.find_similar_campaigns(
            objective=sample_campaign_objective,
        )

        # Should skip campaigns not found in database
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_find_similar_campaigns_error_handling(
        self,
        sample_campaign_objective,
    ):
        """Test error handling in similarity search."""
        mock_db = Mock()

        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(
            side_effect=Exception("Search failed")
        )

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(
            return_value=[0.1] * 1536
        )

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        # Should return empty list on error
        results = await system.find_similar_campaigns(
            objective=sample_campaign_objective,
        )

        assert results == []


@pytest.mark.unit
class TestGetHistoricalContext:
    """Test getting historical context."""

    @pytest.mark.asyncio
    async def test_get_historical_context_success(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test successfully generating historical context."""
        campaign_id = uuid4()

        mock_campaign = Mock()
        mock_campaign.target = "example.com"
        mock_campaign.objectives = ["test"]
        mock_campaign.status = CampaignStatus.COMPLETED
        mock_campaign.results = {"success_rate": 0.9, "phases_completed": 3}

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(return_value=mock_campaign)

        vector_results = [(str(campaign_id), 0.95, {"target": "example.com"})]
        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=vector_results)

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        context = await system.get_historical_context(
            objective=sample_campaign_objective,
            max_campaigns=3,
        )

        assert "Found 1 similar past campaigns" in context
        assert "example.com" in context
        assert "0.95" in context

    @pytest.mark.asyncio
    async def test_get_historical_context_no_campaigns(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test historical context with no similar campaigns."""
        mock_db = Mock()

        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=[])

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        context = await system.get_historical_context(
            objective=sample_campaign_objective,
        )

        assert context == "No similar past campaigns found."

    @pytest.mark.asyncio
    async def test_get_historical_context_error(
        self,
        sample_campaign_objective,
    ):
        """Test error handling in historical context generation."""
        # When find_similar_campaigns fails, it returns [] (empty list)
        # This causes get_historical_context to return "No similar past campaigns found."
        # NOT "Error retrieving historical context." - that only happens on outer exceptions

        mock_db = Mock()
        mock_vector = Mock()

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(
            side_effect=Exception("Embedding failed")
        )

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        context = await system.get_historical_context(
            objective=sample_campaign_objective,
        )

        # find_similar_campaigns catches the exception and returns []
        # So we get "no campaigns found" not "error retrieving"
        assert context == "No similar past campaigns found."

    @pytest.mark.asyncio
    async def test_get_historical_context_outer_exception(
        self,
        sample_campaign_objective,
        mock_embedding_vector,
    ):
        """Test outer exception handler in get_historical_context."""
        # Force exception after find_similar_campaigns but before formatting
        campaign_id = uuid4()

        # Mock campaign that will cause error during formatting
        mock_campaign = Mock()
        mock_campaign.target = "test.com"
        mock_campaign.objectives = None  # This will cause error in ', '.join()
        mock_campaign.status = "COMPLETED"
        mock_campaign.results = {}

        mock_db = Mock()
        mock_db.get_campaign = AsyncMock(return_value=mock_campaign)

        vector_results = [(str(campaign_id), 0.95, {"target": "test.com"})]
        mock_vector = Mock()
        mock_vector.search_similar_campaigns = AsyncMock(return_value=vector_results)

        mock_embed = Mock()
        mock_embed.generate_objective_embedding = AsyncMock(return_value=mock_embedding_vector)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        context = await system.get_historical_context(
            objective=sample_campaign_objective,
        )

        # Should catch outer exception and return error message
        assert context == "Error retrieving historical context."


@pytest.mark.unit
class TestStoreAttackMemory:
    """Test storing attack memory entries."""

    @pytest.mark.asyncio
    async def test_store_attack_memory_success(self):
        """Test successfully storing attack memory."""
        memory_id = uuid4()
        campaign_id = uuid4()

        mock_memory = Mock()
        mock_memory.id = memory_id

        mock_db = Mock()
        mock_db.store_attack_memory = AsyncMock(return_value=mock_memory)

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        result_id = await system.store_attack_memory(
            campaign_id=campaign_id,
            action_type="reconnaissance",
            target="example.com",
            technique="nmap",
            success=True,
            result={"ports": [80, 443]},
            lessons_learned="Test lesson",
        )

        assert result_id == memory_id
        mock_db.store_attack_memory.assert_called_once()


@pytest.mark.unit
class TestSearchAttackMemory:
    """Test searching attack memory."""

    @pytest.mark.asyncio
    async def test_search_attack_memory_success(self):
        """Test successfully searching attack memory."""
        memory_id = uuid4()
        campaign_id = uuid4()

        mock_memory = Mock()
        mock_memory.id = memory_id
        mock_memory.campaign_id = campaign_id
        mock_memory.action_type = "reconnaissance"
        mock_memory.target = "example.com"
        mock_memory.technique = "nmap"
        mock_memory.success = True
        mock_memory.result = {}
        mock_memory.lessons_learned = "Test"
        mock_memory.timestamp = datetime.utcnow()

        mock_db = Mock()
        mock_db.search_attack_memory = AsyncMock(return_value=[mock_memory])

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        results = await system.search_attack_memory(
            target="example",
            technique="nmap",
            success_only=True,
            limit=10,
        )

        assert len(results) == 1
        assert results[0]["action_type"] == "reconnaissance"
        assert results[0]["technique"] == "nmap"


@pytest.mark.unit
class TestGetStatistics:
    """Test getting statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self):
        """Test successfully getting statistics."""
        mock_campaigns = [Mock(), Mock(), Mock()]

        mock_db = Mock()
        mock_db.list_campaigns = AsyncMock(return_value=mock_campaigns)

        mock_vector_info = {
            "name": "campaigns",
            "vectors_count": 100,
            "points_count": 100,
        }
        mock_vector = Mock()
        mock_vector.get_collection_info = AsyncMock(return_value=mock_vector_info)

        mock_cache_stats = {"cache_size": 10}
        mock_embed = Mock()
        mock_embed.get_cache_stats = Mock(return_value=mock_cache_stats)

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        stats = await system.get_statistics()

        assert stats["database"]["total_campaigns"] == 3
        assert stats["vector_store"] == mock_vector_info
        assert stats["embeddings"] == mock_cache_stats

    @pytest.mark.asyncio
    async def test_get_statistics_error(self):
        """Test handling errors when getting statistics."""
        mock_db = Mock()
        mock_db.list_campaigns = AsyncMock(side_effect=Exception("Stats failed"))

        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        stats = await system.get_statistics()

        assert "error" in stats
        assert "Stats failed" in str(stats["error"])

    @pytest.mark.asyncio
    async def test_get_statistics_vector_error(self):
        """Test handling vector store error when getting statistics."""
        mock_db = Mock()
        mock_db.list_campaigns = AsyncMock(return_value=[Mock(), Mock()])

        mock_vector = Mock()
        mock_vector.get_collection_info = AsyncMock(side_effect=Exception("Vector error"))

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        stats = await system.get_statistics()

        assert "error" in stats
        assert "Vector error" in str(stats["error"])


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions."""

    def test_extract_action_types(self, sample_campaign_plan):
        """Test extracting action types from campaign."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        action_types = system._extract_action_types(sample_campaign_plan)

        assert isinstance(action_types, list)

    def test_extract_techniques(self, sample_campaign_plan):
        """Test extracting techniques from campaign."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        techniques = system._extract_techniques(sample_campaign_plan)

        assert isinstance(techniques, list)

    def test_summarize_results_success_rate(self):
        """Test summarizing results with success rate."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        summary = system._summarize_results({"success_rate": 0.9})

        assert "success_rate=0.9" in summary

    def test_summarize_results_phases(self):
        """Test summarizing results with phases completed."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        summary = system._summarize_results({"phases_completed": 3})

        assert "phases=3" in summary

    def test_summarize_results_findings(self):
        """Test summarizing results with findings."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        summary = system._summarize_results({"findings": ["vuln1", "vuln2"]})

        assert "findings=2" in summary

    def test_summarize_results_empty(self):
        """Test summarizing empty results."""
        mock_db = Mock()
        mock_vector = Mock()
        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        summary = system._summarize_results({})

        assert summary == "No summary available"


@pytest.mark.unit
class TestClose:
    """Test closing connections."""

    def test_close(self):
        """Test closing all connections."""
        mock_db = Mock()
        mock_db.close = Mock()

        mock_vector = Mock()
        mock_vector.close = Mock()

        mock_embed = Mock()

        system = AttackMemorySystem(
            db_manager=mock_db,
            vector_store=mock_vector,
            embedding_generator=mock_embed,
        )

        system.close()

        mock_db.close.assert_called_once()
        mock_vector.close.assert_called_once()
