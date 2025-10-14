"""
Tests for VectorStore (Qdrant vector database operations).

Covers:
- VectorStore initialization
- Collection initialization and management
- Campaign embedding storage
- Similarity search
- Campaign embedding retrieval
- Campaign embedding deletion
- Filter building
- Collection info retrieval
- Error handling
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from memory.vector_store import VectorStore
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse


@pytest.mark.unit
class TestVectorStoreInit:
    """Test VectorStore initialization."""

    def test_vector_store_init_default_config(self, test_vector_db_config):
        """Test creating vector store with default configuration."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=test_vector_db_config)

            assert store.config == test_vector_db_config
            assert store.client == mock_client
            assert store.COLLECTION_NAME == "campaigns"
            assert store.VECTOR_SIZE == 1536
            assert store.DISTANCE == qdrant_models.Distance.COSINE

            mock_client_class.assert_called_once_with(
                host=test_vector_db_config.host,
                port=test_vector_db_config.port,
                api_key=None,
                timeout=30.0,
            )

    def test_vector_store_init_with_api_key(self):
        """Test creating vector store with API key."""
        from config import VectorDBConfig

        config = VectorDBConfig(
            host="qdrant.cloud",
            port=6334,
            collection_name="prod_campaigns",
            api_key="secret_key_123",
        )

        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=config)

            assert store.config == config
            mock_client_class.assert_called_once_with(
                host="qdrant.cloud",
                port=6334,
                api_key="secret_key_123",
                timeout=30.0,
            )

    def test_vector_store_init_no_config(self):
        """Test creating vector store without explicit config (uses global)."""
        with patch('memory.vector_store.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.vector_db = Mock(
                host="localhost",
                port=6333,
                api_key=None,
            )
            mock_get_config.return_value = mock_config

            with patch('memory.vector_store.QdrantClient'):
                store = VectorStore()

                assert store.config == mock_config.vector_db


@pytest.mark.unit
class TestCollectionInit:
    """Test collection initialization."""

    @pytest.mark.asyncio
    async def test_init_collection_creates_new(self, test_vector_db_config):
        """Test initializing collection creates it when it doesn't exist."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock get_collections to return empty list
            mock_collections_response = Mock()
            mock_collections_response.collections = []
            mock_client.get_collections.return_value = mock_collections_response

            store = VectorStore(config=test_vector_db_config)
            await store.init_collection(recreate=False)

            # Should create collection
            mock_client.create_collection.assert_called_once()
            call_kwargs = mock_client.create_collection.call_args[1]
            assert call_kwargs["collection_name"] == "campaigns"
            assert call_kwargs["vectors_config"].size == 1536
            assert call_kwargs["vectors_config"].distance == qdrant_models.Distance.COSINE

    @pytest.mark.asyncio
    async def test_init_collection_already_exists(self, test_vector_db_config):
        """Test initializing collection when it already exists."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock get_collections to return existing collection
            mock_collection = Mock()
            mock_collection.name = "campaigns"
            mock_collections_response = Mock()
            mock_collections_response.collections = [mock_collection]
            mock_client.get_collections.return_value = mock_collections_response

            store = VectorStore(config=test_vector_db_config)
            await store.init_collection(recreate=False)

            # Should NOT create collection
            mock_client.create_collection.assert_not_called()
            mock_client.delete_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_collection_recreate(self, test_vector_db_config):
        """Test recreating collection deletes and creates."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock get_collections to return existing collection
            mock_collection = Mock()
            mock_collection.name = "campaigns"
            mock_collections_response = Mock()
            mock_collections_response.collections = [mock_collection]
            mock_client.get_collections.return_value = mock_collections_response

            store = VectorStore(config=test_vector_db_config)
            await store.init_collection(recreate=True)

            # Should delete and create collection
            mock_client.delete_collection.assert_called_once_with(collection_name="campaigns")
            mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_collection_error_handling(self, test_vector_db_config):
        """Test collection initialization error handling."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock get_collections to raise exception
            mock_client.get_collections.side_effect = Exception("Connection failed")

            store = VectorStore(config=test_vector_db_config)

            with pytest.raises(Exception) as exc_info:
                await store.init_collection()

            assert "Connection failed" in str(exc_info.value)


@pytest.mark.unit
class TestStoreCampaignEmbedding:
    """Test storing campaign embeddings."""

    @pytest.mark.asyncio
    async def test_store_campaign_embedding_success(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test successfully storing campaign embedding."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            metadata = {
                "target": "example.com",
                "objectives": ["test"],
                "action_types": ["reconnaissance"],
                "techniques": ["nmap"],
                "priority": 7,
            }

            vector_id = await store.store_campaign_embedding(
                campaign_id=campaign_id,
                embedding=mock_embedding_vector,
                metadata=metadata,
            )

            assert vector_id == str(campaign_id)
            mock_client.upsert.assert_called_once()

            # Verify point structure
            call_kwargs = mock_client.upsert.call_args[1]
            assert call_kwargs["collection_name"] == "campaigns"
            assert len(call_kwargs["points"]) == 1

            point = call_kwargs["points"][0]
            assert point.id == str(campaign_id)
            assert point.vector == mock_embedding_vector
            assert point.payload["campaign_id"] == str(campaign_id)
            assert point.payload["target"] == "example.com"

    @pytest.mark.asyncio
    async def test_store_campaign_embedding_wrong_dimension(self, test_vector_db_config):
        """Test storing embedding with wrong dimension raises error."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            wrong_embedding = [0.1] * 100  # Wrong size

            with pytest.raises(ValueError) as exc_info:
                await store.store_campaign_embedding(
                    campaign_id=campaign_id,
                    embedding=wrong_embedding,
                    metadata={},
                )

            assert "Embedding size mismatch" in str(exc_info.value)
            mock_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_campaign_embedding_upsert_error(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test handling upsert errors."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock upsert to raise exception
            mock_client.upsert.side_effect = Exception("Upsert failed")

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()

            with pytest.raises(Exception) as exc_info:
                await store.store_campaign_embedding(
                    campaign_id=campaign_id,
                    embedding=mock_embedding_vector,
                    metadata={},
                )

            assert "Upsert failed" in str(exc_info.value)


@pytest.mark.unit
class TestSearchSimilarCampaigns:
    """Test similarity search."""

    @pytest.mark.asyncio
    async def test_search_similar_campaigns_success(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test successful similarity search."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search results
            mock_point1 = Mock()
            mock_point1.id = "campaign-id-1"
            mock_point1.score = 0.95
            mock_point1.payload = {
                "campaign_id": "campaign-id-1",
                "target": "example.com",
                "success": True,
            }

            mock_point2 = Mock()
            mock_point2.id = "campaign-id-2"
            mock_point2.score = 0.85
            mock_point2.payload = {
                "campaign_id": "campaign-id-2",
                "target": "test.com",
                "success": True,
            }

            mock_client.search.return_value = [mock_point1, mock_point2]

            store = VectorStore(config=test_vector_db_config)

            results = await store.search_similar_campaigns(
                query_embedding=mock_embedding_vector,
                limit=5,
                score_threshold=0.7,
            )

            assert len(results) == 2
            assert results[0][0] == "campaign-id-1"
            assert results[0][1] == 0.95
            assert results[1][0] == "campaign-id-2"
            assert results[1][1] == 0.85

            mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_similar_campaigns_with_filters(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test similarity search with metadata filters."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.search.return_value = []

            store = VectorStore(config=test_vector_db_config)

            await store.search_similar_campaigns(
                query_embedding=mock_embedding_vector,
                limit=5,
                score_threshold=0.8,
                filters={"success": True, "priority": 8},
            )

            # Verify filter was passed
            call_kwargs = mock_client.search.call_args[1]
            assert call_kwargs["query_filter"] is not None

    @pytest.mark.asyncio
    async def test_search_similar_campaigns_wrong_dimension(self, test_vector_db_config):
        """Test search with wrong embedding dimension raises error."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=test_vector_db_config)

            wrong_embedding = [0.1] * 100  # Wrong size

            with pytest.raises(ValueError) as exc_info:
                await store.search_similar_campaigns(
                    query_embedding=wrong_embedding,
                    limit=5,
                )

            assert "Query embedding size mismatch" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_similar_campaigns_error(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test handling search errors."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search to raise exception
            mock_client.search.side_effect = Exception("Search failed")

            store = VectorStore(config=test_vector_db_config)

            with pytest.raises(Exception) as exc_info:
                await store.search_similar_campaigns(
                    query_embedding=mock_embedding_vector,
                    limit=5,
                )

            assert "Search failed" in str(exc_info.value)


@pytest.mark.unit
class TestGetCampaignEmbedding:
    """Test retrieving campaign embeddings."""

    @pytest.mark.asyncio
    async def test_get_campaign_embedding_success(
        self,
        test_vector_db_config,
        mock_embedding_vector,
    ):
        """Test successfully retrieving campaign embedding."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock retrieve result
            mock_point = Mock()
            mock_point.vector = mock_embedding_vector
            mock_point.payload = {"campaign_id": "test-id", "target": "example.com"}
            mock_client.retrieve.return_value = [mock_point]

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            result = await store.get_campaign_embedding(campaign_id)

            assert result is not None
            embedding, metadata = result
            assert embedding == mock_embedding_vector
            assert metadata["target"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_campaign_embedding_not_found(self, test_vector_db_config):
        """Test retrieving non-existent embedding returns None."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock retrieve to return empty list
            mock_client.retrieve.return_value = []

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            result = await store.get_campaign_embedding(campaign_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_campaign_embedding_error(self, test_vector_db_config):
        """Test handling retrieval errors."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock retrieve to raise exception
            mock_client.retrieve.side_effect = Exception("Retrieval failed")

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            result = await store.get_campaign_embedding(campaign_id)

            assert result is None  # Returns None on error


@pytest.mark.unit
class TestDeleteCampaignEmbedding:
    """Test deleting campaign embeddings."""

    @pytest.mark.asyncio
    async def test_delete_campaign_embedding_success(self, test_vector_db_config):
        """Test successfully deleting campaign embedding."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            success = await store.delete_campaign_embedding(campaign_id)

            assert success is True
            mock_client.delete.assert_called_once()

            # Verify delete parameters
            call_kwargs = mock_client.delete.call_args[1]
            assert call_kwargs["collection_name"] == "campaigns"
            assert call_kwargs["wait"] is True

    @pytest.mark.asyncio
    async def test_delete_campaign_embedding_error(self, test_vector_db_config):
        """Test handling deletion errors."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock delete to raise exception
            mock_client.delete.side_effect = Exception("Deletion failed")

            store = VectorStore(config=test_vector_db_config)

            campaign_id = uuid4()
            success = await store.delete_campaign_embedding(campaign_id)

            assert success is False  # Returns False on error


@pytest.mark.unit
class TestBuildFilter:
    """Test filter building."""

    def test_build_filter_bool(self, test_vector_db_config):
        """Test building filter with boolean value."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            filter_obj = store._build_filter({"success": True})

            assert isinstance(filter_obj, qdrant_models.Filter)
            assert len(filter_obj.must) == 1
            assert filter_obj.must[0].key == "success"

    def test_build_filter_int(self, test_vector_db_config):
        """Test building filter with integer value."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            filter_obj = store._build_filter({"priority": 8})

            assert isinstance(filter_obj, qdrant_models.Filter)
            assert len(filter_obj.must) == 1
            assert filter_obj.must[0].key == "priority"

    def test_build_filter_string(self, test_vector_db_config):
        """Test building filter with string value."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            filter_obj = store._build_filter({"target": "example.com"})

            assert isinstance(filter_obj, qdrant_models.Filter)
            assert len(filter_obj.must) == 1
            assert filter_obj.must[0].key == "target"

    def test_build_filter_list(self, test_vector_db_config):
        """Test building filter with list value (match any)."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            filter_obj = store._build_filter({"techniques": ["nmap", "sqlmap"]})

            assert isinstance(filter_obj, qdrant_models.Filter)
            assert len(filter_obj.must) == 1
            assert filter_obj.must[0].key == "techniques"

    def test_build_filter_multiple_conditions(self, test_vector_db_config):
        """Test building filter with multiple conditions."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            filter_obj = store._build_filter({
                "success": True,
                "priority": 8,
                "target": "example.com",
            })

            assert isinstance(filter_obj, qdrant_models.Filter)
            assert len(filter_obj.must) == 3


@pytest.mark.unit
class TestGetCollectionInfo:
    """Test getting collection info."""

    @pytest.mark.asyncio
    async def test_get_collection_info_success(self, test_vector_db_config):
        """Test successfully getting collection info."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock collection info
            mock_collection_info = Mock()
            mock_collection_info.vectors_count = 100
            mock_collection_info.points_count = 100
            mock_collection_info.status = "green"
            mock_client.get_collection.return_value = mock_collection_info

            store = VectorStore(config=test_vector_db_config)

            info = await store.get_collection_info()

            assert info["name"] == "campaigns"
            assert info["vectors_count"] == 100
            assert info["points_count"] == 100
            assert info["status"] == "green"
            assert info["config"]["vector_size"] == 1536

    @pytest.mark.asyncio
    async def test_get_collection_info_error(self, test_vector_db_config):
        """Test handling errors when getting collection info."""
        with patch('memory.vector_store.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock get_collection to raise exception
            mock_client.get_collection.side_effect = Exception("Info retrieval failed")

            store = VectorStore(config=test_vector_db_config)

            info = await store.get_collection_info()

            assert "error" in info
            assert "Info retrieval failed" in info["error"]


@pytest.mark.unit
class TestVectorStoreClose:
    """Test closing vector store."""

    def test_close(self, test_vector_db_config):
        """Test closing vector store connections."""
        with patch('memory.vector_store.QdrantClient'):
            store = VectorStore(config=test_vector_db_config)

            # Should not raise
            store.close()
