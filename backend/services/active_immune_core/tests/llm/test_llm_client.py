"""Tests for LLM Client implementation.

Tests unified LLM interface, provider-specific implementations,
and fallback mechanisms.

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.llm_client import (
    AnthropicClient,
    BaseLLMClient,
    FallbackLLMClient,
    LLMAPIError,
    LLMProviderUnavailable,
    LLMResponse,
    OpenAIClient,
)


class TestLLMResponse:
    """Test LLMResponse dataclass."""
    
    def test_llm_response_creation(self):
        """Test LLMResponse instantiation."""
        response = LLMResponse(
            content="Test content",
            provider="openai",
            model="gpt-4o",
            tokens_used=100,
            prompt_tokens=50,
            completion_tokens=50,
            latency_ms=250.5
        )
        
        assert response.content == "Test content"
        assert response.provider == "openai"
        assert response.tokens_used == 100
        assert response.latency_ms == 250.5


class TestOpenAIClient:
    """Test OpenAI client implementation."""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("llm.llm_client.openai")
    def test_initialization_with_env_key(self, mock_openai):
        """Test initialization with environment API key."""
        client = OpenAIClient()
        
        assert client.api_key == "test-key"
        assert client.model == "gpt-4o"
        assert mock_openai.api_key == "test-key"
    
    @patch("llm.llm_client.openai")
    def test_initialization_with_explicit_key(self, mock_openai):
        """Test initialization with explicit API key."""
        client = OpenAIClient(api_key="explicit-key", model="gpt-4-turbo")
        
        assert client.api_key == "explicit-key"
        assert client.model == "gpt-4-turbo"
    
    @patch.dict(os.environ, {}, clear=True)
    @patch("llm.llm_client.openai")
    def test_initialization_without_key_raises(self, mock_openai):
        """Test initialization fails without API key."""
        with pytest.raises(LLMProviderUnavailable, match="API key not found"):
            OpenAIClient()
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.openai")
    async def test_generate_success(self, mock_openai):
        """Test successful generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Generated text"))
        ]
        mock_response.usage = MagicMock(
            total_tokens=100,
            prompt_tokens=50,
            completion_tokens=50
        )
        
        mock_openai.ChatCompletion.acreate = AsyncMock(return_value=mock_response)
        
        client = OpenAIClient(api_key="test-key")
        response = await client.generate("Test prompt", max_tokens=100)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Generated text"
        assert response.provider == "openai"
        assert response.tokens_used == 100
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 50
        
        # Verify API call
        mock_openai.ChatCompletion.acreate.assert_called_once()
        call_kwargs = mock_openai.ChatCompletion.acreate.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["max_tokens"] == 100
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.openai")
    async def test_generate_with_system_prompt(self, mock_openai):
        """Test generation with system prompt."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Response"))
        ]
        mock_response.usage = MagicMock(
            total_tokens=50, prompt_tokens=25, completion_tokens=25
        )
        
        mock_openai.ChatCompletion.acreate = AsyncMock(return_value=mock_response)
        
        client = OpenAIClient(api_key="test-key")
        await client.generate(
            "Test prompt",
            system_prompt="You are a security analyst."
        )
        
        # Verify system message included
        call_kwargs = mock_openai.ChatCompletion.acreate.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.openai")
    async def test_generate_api_error_raises(self, mock_openai):
        """Test generation raises on API error."""
        mock_openai.ChatCompletion.acreate = AsyncMock(
            side_effect=Exception("API error")
        )
        
        client = OpenAIClient(api_key="test-key")
        
        with pytest.raises(LLMAPIError, match="OpenAI generation failed"):
            await client.generate("Test prompt")
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.openai")
    async def test_is_available(self, mock_openai):
        """Test availability check."""
        client = OpenAIClient(api_key="test-key")
        
        assert await client.is_available() is True


class TestAnthropicClient:
    """Test Anthropic client implementation."""
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("llm.llm_client.AsyncAnthropic")
    def test_initialization_with_env_key(self, mock_anthropic):
        """Test initialization with environment API key."""
        client = AnthropicClient()
        
        assert client.api_key == "test-key"
        assert client.model == "claude-3-5-sonnet-20241022"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch("llm.llm_client.AsyncAnthropic")
    def test_initialization_with_explicit_key(self, mock_anthropic):
        """Test initialization with explicit API key."""
        client = AnthropicClient(api_key="explicit-key", model="claude-3-opus")
        
        assert client.api_key == "explicit-key"
        assert client.model == "claude-3-opus"
    
    @patch.dict(os.environ, {}, clear=True)
    @patch("llm.llm_client.AsyncAnthropic")
    def test_initialization_without_key_raises(self, mock_anthropic):
        """Test initialization fails without API key."""
        with pytest.raises(LLMProviderUnavailable, match="API key not found"):
            AnthropicClient()
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.AsyncAnthropic")
    async def test_generate_success(self, mock_anthropic_class):
        """Test successful generation."""
        # Mock response
        mock_content = MagicMock()
        mock_content.text = "Generated text"
        
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_message.usage = MagicMock(
            input_tokens=50,
            output_tokens=50
        )
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicClient(api_key="test-key")
        response = await client.generate("Test prompt", max_tokens=100)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Generated text"
        assert response.provider == "anthropic"
        assert response.tokens_used == 100
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 50
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.AsyncAnthropic")
    async def test_generate_with_system_prompt(self, mock_anthropic_class):
        """Test generation with system prompt."""
        mock_content = MagicMock()
        mock_content.text = "Response"
        
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_message.usage = MagicMock(input_tokens=25, output_tokens=25)
        
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicClient(api_key="test-key")
        await client.generate(
            "Test prompt",
            system_prompt="You are a security analyst."
        )
        
        # Verify system parameter included
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == "You are a security analyst."
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.AsyncAnthropic")
    async def test_generate_api_error_raises(self, mock_anthropic_class):
        """Test generation raises on API error."""
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=Exception("API error"))
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicClient(api_key="test-key")
        
        with pytest.raises(LLMAPIError, match="Anthropic generation failed"):
            await client.generate("Test prompt")
    
    @pytest.mark.asyncio
    @patch("llm.llm_client.AsyncAnthropic")
    async def test_is_available(self, mock_anthropic_class):
        """Test availability check."""
        client = AnthropicClient(api_key="test-key")
        
        assert await client.is_available() is True


class TestFallbackLLMClient:
    """Test fallback LLM client."""
    
    @pytest.mark.asyncio
    async def test_uses_primary_when_available(self):
        """Test uses primary client when available."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=True)
        mock_primary.generate = AsyncMock(
            return_value=LLMResponse(
                content="Primary response",
                provider="primary",
                model="test",
                tokens_used=50,
                prompt_tokens=25,
                completion_tokens=25,
                latency_ms=100.0
            )
        )
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        response = await client.generate("Test prompt")
        
        assert response.content == "Primary response"
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_uses_fallback_on_primary_failure(self):
        """Test uses fallback when primary fails."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=True)
        mock_primary.generate = AsyncMock(side_effect=LLMAPIError("Primary failed"))
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        mock_fallback.is_available = AsyncMock(return_value=True)
        mock_fallback.generate = AsyncMock(
            return_value=LLMResponse(
                content="Fallback response",
                provider="fallback",
                model="test",
                tokens_used=50,
                prompt_tokens=25,
                completion_tokens=25,
                latency_ms=100.0
            )
        )
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        response = await client.generate("Test prompt")
        
        assert response.content == "Fallback response"
        mock_primary.generate.assert_called_once()
        mock_fallback.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_raises_when_all_fail(self):
        """Test raises when both primary and fallback fail."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=True)
        mock_primary.generate = AsyncMock(side_effect=LLMAPIError("Primary failed"))
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        mock_fallback.is_available = AsyncMock(return_value=True)
        mock_fallback.generate = AsyncMock(
            side_effect=LLMAPIError("Fallback failed")
        )
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        
        with pytest.raises(LLMAPIError, match="All LLM providers failed"):
            await client.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_is_available_primary(self):
        """Test availability when primary is available."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=True)
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        mock_fallback.is_available = AsyncMock(return_value=False)
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        
        assert await client.is_available() is True
    
    @pytest.mark.asyncio
    async def test_is_available_fallback(self):
        """Test availability when only fallback available."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=False)
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        mock_fallback.is_available = AsyncMock(return_value=True)
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        
        assert await client.is_available() is True
    
    @pytest.mark.asyncio
    async def test_is_available_none(self):
        """Test availability when neither available."""
        mock_primary = MagicMock(spec=BaseLLMClient)
        mock_primary.is_available = AsyncMock(return_value=False)
        
        mock_fallback = MagicMock(spec=BaseLLMClient)
        mock_fallback.is_available = AsyncMock(return_value=False)
        
        client = FallbackLLMClient(primary=mock_primary, fallback=mock_fallback)
        
        assert await client.is_available() is False


@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests with real LLM APIs (skipped by default)."""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_openai_real_call(self):
        """Test real OpenAI API call."""
        client = OpenAIClient()
        response = await client.generate(
            "Say 'test successful' in exactly 2 words.",
            max_tokens=10,
            temperature=0.0
        )
        
        assert "test successful" in response.content.lower()
        assert response.tokens_used > 0
    
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_anthropic_real_call(self):
        """Test real Anthropic API call."""
        client = AnthropicClient()
        response = await client.generate(
            "Say 'test successful' in exactly 2 words.",
            max_tokens=10,
            temperature=0.0
        )
        
        assert "test successful" in response.content.lower()
        assert response.tokens_used > 0
