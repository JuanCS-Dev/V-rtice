"""
Tests for embedding generator (Gemini text-embedding-004).

Covers:
- EmbeddingGenerator initialization
- Text embedding generation
- Campaign embedding generation
- Objective embedding generation
- Caching behavior
- Retry logic
- Error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from memory.embeddings import EmbeddingGenerator
from models import CampaignObjective, CampaignPlan, RiskLevel
from uuid import uuid4
from datetime import datetime


@pytest.mark.unit
class TestEmbeddingGeneratorInit:
    """Test EmbeddingGenerator initialization."""

    def test_embedding_generator_init(self, test_llm_config):
        """Test creating embedding generator."""
        gen = EmbeddingGenerator(config=test_llm_config)

        assert gen.config == test_llm_config
        assert gen.EMBEDDING_MODEL == "models/text-embedding-004"
        assert gen.EMBEDDING_DIMENSION == 1536
        assert gen._embedding_cache == {}

    def test_embedding_generator_init_no_api_key(self):
        """Test initialization fails without API key."""
        from config import LLMConfig

        config = LLMConfig(api_key="", model="gemini-1.5-pro")

        with pytest.raises(ValueError) as exc_info:
            EmbeddingGenerator(config=config)

        assert "API key is required" in str(exc_info.value)


@pytest.mark.unit
class TestGenerateEmbedding:
    """Test embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_embedding_basic(self, test_llm_config, mock_embedding_vector):
        """Test basic embedding generation."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)
            embedding = await gen.generate_embedding("test text")

            assert embedding == mock_embedding_vector
            assert len(embedding) == 1536
            mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_with_cache(self, test_llm_config, mock_embedding_vector):
        """Test embedding generation uses cache."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)

            # First call - should call API
            embedding1 = await gen.generate_embedding("test text", use_cache=True)
            assert mock_embed.call_count == 1

            # Second call - should use cache
            embedding2 = await gen.generate_embedding("test text", use_cache=True)
            assert mock_embed.call_count == 1  # No new API call
            assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_generate_embedding_bypass_cache(self, test_llm_config, mock_embedding_vector):
        """Test bypassing cache."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)

            # First call
            await gen.generate_embedding("test text", use_cache=False)
            assert mock_embed.call_count == 1

            # Second call without cache
            await gen.generate_embedding("test text", use_cache=False)
            assert mock_embed.call_count == 2  # New API call


@pytest.mark.unit
class TestCampaignEmbedding:
    """Test campaign plan embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_campaign_embedding(
        self,
        test_llm_config,
        mock_embedding_vector,
        sample_campaign_plan,
    ):
        """Test generating embedding for campaign plan."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)
            embedding = await gen.generate_campaign_embedding(sample_campaign_plan)

            assert embedding == mock_embedding_vector
            assert len(embedding) == 1536
            mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_serialize_campaign(self, test_llm_config, sample_campaign_plan):
        """Test campaign serialization for embedding."""
        gen = EmbeddingGenerator(config=test_llm_config)
        text = gen._serialize_campaign(sample_campaign_plan)

        assert isinstance(text, str)
        assert sample_campaign_plan.target in text
        # Should contain target and objective information
        assert len(text) > 20  # Non-trivial serialization
        assert "Target:" in text


@pytest.mark.unit
class TestObjectiveEmbedding:
    """Test campaign objective embedding generation."""

    @pytest.mark.asyncio
    async def test_generate_objective_embedding(
        self,
        test_llm_config,
        mock_embedding_vector,
        sample_campaign_objective,
    ):
        """Test generating embedding for campaign objective."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)
            embedding = await gen.generate_objective_embedding(sample_campaign_objective)

            assert embedding == mock_embedding_vector
            assert len(embedding) == 1536
            mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_serialize_objective(self, test_llm_config, sample_campaign_objective):
        """Test objective serialization for embedding."""
        gen = EmbeddingGenerator(config=test_llm_config)
        text = gen._serialize_objective(sample_campaign_objective)

        assert isinstance(text, str)
        assert sample_campaign_objective.target in text
        assert all(obj in text for obj in sample_campaign_objective.objectives)
        assert len(text) > 20
        assert "Target:" in text


@pytest.mark.unit
class TestEmbeddingErrorHandling:
    """Test error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, test_llm_config):
        """Test handling of API errors."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.side_effect = Exception("API Error")

            gen = EmbeddingGenerator(config=test_llm_config)

            with pytest.raises(Exception) as exc_info:
                await gen.generate_embedding("test text")

            assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, test_llm_config):
        """Test handling of empty text input."""
        gen = EmbeddingGenerator(config=test_llm_config)

        # Empty text should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await gen.generate_embedding("")

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embedding_text_truncation(self, test_llm_config, mock_embedding_vector):
        """Test text truncation for very long inputs."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)

            # Create text longer than MAX_INPUT_TOKENS * 4
            very_long_text = "x" * (gen.MAX_INPUT_TOKENS * 4 + 1000)

            embedding = await gen.generate_embedding(very_long_text)

            assert embedding == mock_embedding_vector
            # Should have been truncated
            call_args = mock_embed.call_args[1]
            assert len(call_args["content"]) == gen.MAX_INPUT_TOKENS * 4

    @pytest.mark.asyncio
    async def test_generate_embedding_wrong_dimension(self, test_llm_config):
        """Test handling of wrong embedding dimension."""
        with patch('google.generativeai.embed_content') as mock_embed:
            # Return wrong dimension
            mock_embed.return_value = {"embedding": [0.1] * 100}  # Wrong size

            gen = EmbeddingGenerator(config=test_llm_config)

            with pytest.raises(ValueError) as exc_info:
                await gen.generate_embedding("test text")

            assert "Unexpected embedding dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embedding_google_api_error(self, test_llm_config):
        """Test handling of Google API errors."""
        from google.api_core import exceptions as google_exceptions

        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.side_effect = google_exceptions.ResourceExhausted("Quota exceeded")

            gen = EmbeddingGenerator(config=test_llm_config)

            with pytest.raises(google_exceptions.ResourceExhausted):
                await gen.generate_embedding("test text")


@pytest.mark.unit
class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache(self, test_llm_config):
        """Test clearing embedding cache."""
        gen = EmbeddingGenerator(config=test_llm_config)

        # Add some cached items
        gen._embedding_cache["key1"] = [0.1] * 1536
        gen._embedding_cache["key2"] = [0.2] * 1536

        assert len(gen._embedding_cache) == 2

        # Clear cache
        gen.clear_cache()

        assert len(gen._embedding_cache) == 0

    def test_get_cache_stats(self, test_llm_config):
        """Test getting cache statistics."""
        gen = EmbeddingGenerator(config=test_llm_config)

        # Add cached items
        gen._embedding_cache["key1"] = [0.1] * 1536
        gen._embedding_cache["key2"] = [0.2] * 1536

        stats = gen.get_cache_stats()

        assert stats["cache_size"] == 2
        assert stats["embedding_dimension"] == 1536
        assert stats["model"] == "models/text-embedding-004"


@pytest.mark.unit
class TestEmbeddingBatchOperations:
    """Test batch embedding operations."""

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(
        self,
        test_llm_config,
        mock_embedding_vector,
    ):
        """Test generating multiple embeddings at once."""
        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.return_value = {"embedding": mock_embedding_vector}

            gen = EmbeddingGenerator(config=test_llm_config)

            texts = ["text1", "text2", "text3"]
            embeddings = await gen.generate_batch_embeddings(texts)

            assert len(embeddings) == 3
            assert all(len(emb) == 1536 for emb in embeddings)
            assert mock_embed.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings_with_failures(
        self,
        test_llm_config,
        mock_embedding_vector,
    ):
        """Test batch generation handles failures gracefully."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API Error")
            return {"embedding": mock_embedding_vector}

        with patch('google.generativeai.embed_content') as mock_embed:
            mock_embed.side_effect = side_effect

            gen = EmbeddingGenerator(config=test_llm_config)

            texts = ["text1", "text2", "text3"]
            embeddings = await gen.generate_batch_embeddings(texts)

            assert len(embeddings) == 3
            # Second embedding should be zero vector (fallback)
            assert embeddings[1] == [0.0] * 1536
            # First and third should be valid
            assert embeddings[0] == mock_embedding_vector
            assert embeddings[2] == mock_embedding_vector
