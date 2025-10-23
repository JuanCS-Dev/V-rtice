"""
OpenAI Client - Targeted Coverage Tests

Objetivo: Cobrir llm/openai_client.py (279 lines, 28% → 90%+)

Testa OpenAICodeGenerator: initialization, code generation, retry logic, cost tracking

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
Dedicado a Jesus Cristo - Honrando com Excelência Absoluta
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio


# ===== CODEGENERATIONRESULT TESTS =====

def test_code_generation_result_dataclass():
    """
    SCENARIO: CodeGenerationResult created with all fields
    EXPECTED: Dataclass stores all values correctly
    """
    from llm.openai_client import CodeGenerationResult

    result = CodeGenerationResult(
        code="def hello(): pass",
        model="gpt-4",
        tokens_used=150,
        cost_usd=0.0045,
        latency_ms=1234.5,
        success=True,
        error=None
    )

    assert result.code == "def hello(): pass"
    assert result.model == "gpt-4"
    assert result.tokens_used == 150
    assert result.cost_usd == 0.0045
    assert result.latency_ms == 1234.5
    assert result.success is True
    assert result.error is None


def test_code_generation_result_with_error():
    """
    SCENARIO: CodeGenerationResult with success=False and error message
    EXPECTED: Error field populated correctly
    """
    from llm.openai_client import CodeGenerationResult

    result = CodeGenerationResult(
        code="",
        model="gpt-4",
        tokens_used=0,
        cost_usd=0.0,
        latency_ms=500.0,
        success=False,
        error="API timeout"
    )

    assert result.success is False
    assert result.error == "API timeout"
    assert result.code == ""


# ===== INITIALIZATION TESTS =====

@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_openai_code_generator_initialization_with_api_key(mock_async_openai):
    """
    SCENARIO: OpenAICodeGenerator with api_key provided
    EXPECTED: Client initialized with correct parameters
    """
    from llm.openai_client import OpenAICodeGenerator

    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator(
        api_key="sk-test-key",
        model="gpt-4-turbo-preview",
        max_tokens=4096,
        temperature=0.2,
        max_retries=3
    )

    assert generator.api_key == "sk-test-key"
    assert generator.model == "gpt-4-turbo-preview"
    assert generator.max_tokens == 4096
    assert generator.temperature == 0.2
    assert generator.max_retries == 3
    assert generator.total_tokens_used == 0
    assert generator.total_cost_usd == 0.0
    assert generator.request_count == 0
    assert generator.error_count == 0

    mock_async_openai.assert_called_once_with(api_key="sk-test-key")


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_openai_code_generator_initialization_from_env(mock_async_openai, monkeypatch):
    """
    SCENARIO: OpenAICodeGenerator with api_key from environment
    EXPECTED: Client reads OPENAI_API_KEY env var
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()

    assert generator.api_key == "sk-env-key"
    mock_async_openai.assert_called_once_with(api_key="sk-env-key")


@patch('llm.openai_client.OPENAI_AVAILABLE', False)
def test_openai_code_generator_initialization_no_openai_package():
    """
    SCENARIO: OpenAICodeGenerator when openai package not installed
    EXPECTED: Raises ImportError with helpful message
    """
    from llm.openai_client import OpenAICodeGenerator

    with pytest.raises(ImportError, match="openai package not installed"):
        OpenAICodeGenerator(api_key="sk-test")


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_openai_code_generator_initialization_no_api_key(mock_async_openai, monkeypatch):
    """
    SCENARIO: OpenAICodeGenerator with no api_key provided or in env
    EXPECTED: Raises ValueError with helpful message
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OpenAI API key required"):
        OpenAICodeGenerator()


# ===== GENERATE_CODE - SUCCESS SCENARIOS =====

@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_generate_code_success_python(mock_async_openai, monkeypatch):
    """
    SCENARIO: generate_code() succeeds for Python
    EXPECTED: Returns CodeGenerationResult with code and metrics
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "def hello():\n    print('Hello, World!')"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 150
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 100

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator()
    result = await generator.generate_code("Create hello world function", "python")

    assert result.success is True
    assert "def hello():" in result.code
    assert result.model == "gpt-4-turbo-preview"
    assert result.tokens_used == 150
    assert result.cost_usd > 0
    assert result.latency_ms > 0
    assert result.error is None

    # Check metrics updated
    assert generator.total_tokens_used == 150
    assert generator.request_count == 1
    assert generator.error_count == 0


@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_generate_code_success_go(mock_async_openai, monkeypatch):
    """
    SCENARIO: generate_code() succeeds for Go
    EXPECTED: Returns Go code with correct system prompt used
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "package main\n\nfunc main() {}"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 200
    mock_response.usage.prompt_tokens = 60
    mock_response.usage.completion_tokens = 140

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator()
    result = await generator.generate_code("Create HTTP server", "go")

    assert result.success is True
    assert "package main" in result.code
    assert result.tokens_used == 200


@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_generate_code_with_context(mock_async_openai, monkeypatch):
    """
    SCENARIO: generate_code() with rich context (framework, dependencies, etc)
    EXPECTED: Context included in prompt
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "from fastapi import FastAPI"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 60

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    context = {
        "framework": "FastAPI",
        "dependencies": ["pydantic", "uvicorn"],
        "existing_code": "# Existing API code",
        "requirements": {"auth": "JWT", "database": "PostgreSQL"}
    }

    generator = OpenAICodeGenerator()
    result = await generator.generate_code("Add /users endpoint", "python", context)

    assert result.success is True
    # Verify context was passed to OpenAI
    call_args = mock_client.chat.completions.create.call_args
    user_prompt = call_args[1]["messages"][1]["content"]
    assert "FastAPI" in user_prompt
    assert "pydantic" in user_prompt
    assert "Existing API code" in user_prompt


# ===== GENERATE_CODE - RETRY LOGIC =====

@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_generate_code_retry_then_success(mock_async_openai, monkeypatch):
    """
    SCENARIO: generate_code() fails first attempt, succeeds on retry
    EXPECTED: Returns success after retry with exponential backoff
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # First call raises exception, second succeeds
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "def code(): pass"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 50
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 30

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("Rate limit exceeded"),
            mock_response  # Success on retry
        ]
    )
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator(max_retries=3)
    result = await generator.generate_code("Task", "python")

    assert result.success is True
    assert result.code == "def code(): pass"
    assert generator.error_count == 1  # First attempt failed


@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_generate_code_all_retries_fail(mock_async_openai, monkeypatch):
    """
    SCENARIO: generate_code() fails all retry attempts
    EXPECTED: Returns failure CodeGenerationResult with error message
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API unavailable")
    )
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator(max_retries=2)
    result = await generator.generate_code("Task", "python")

    assert result.success is False
    assert "API unavailable" in result.error
    assert result.code == ""
    assert result.tokens_used == 0
    assert result.cost_usd == 0.0
    assert generator.error_count == 2  # All retries failed


# ===== SYSTEM PROMPTS =====

@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_get_system_prompt_python(mock_async_openai, monkeypatch):
    """
    SCENARIO: _get_system_prompt() for Python
    EXPECTED: Returns Python-specific prompt with PEP 8 guidelines
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._get_system_prompt("python")

    assert "Python" in prompt
    assert "PEP 8" in prompt
    assert "type hints" in prompt
    assert "docstrings" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_get_system_prompt_go(mock_async_openai, monkeypatch):
    """
    SCENARIO: _get_system_prompt() for Go
    EXPECTED: Returns Go-specific prompt with Effective Go guidelines
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._get_system_prompt("go")

    assert "Go" in prompt
    assert "Effective Go" in prompt
    assert "errors explicitly" in prompt
    assert "godoc" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_get_system_prompt_unknown_language(mock_async_openai, monkeypatch):
    """
    SCENARIO: _get_system_prompt() for unknown language
    EXPECTED: Returns generic prompt with language name
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._get_system_prompt("rust")

    assert "rust" in prompt
    assert "production-ready" in prompt


# ===== BUILD_PROMPT TESTS =====

@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_build_prompt_basic(mock_async_openai, monkeypatch):
    """
    SCENARIO: _build_prompt() with minimal context
    EXPECTED: Returns basic prompt with task and language
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._build_prompt("Create REST API", "python", {})

    assert "python" in prompt
    assert "Create REST API" in prompt
    assert "production-ready" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_build_prompt_with_framework(mock_async_openai, monkeypatch):
    """
    SCENARIO: _build_prompt() with framework context
    EXPECTED: Framework included in prompt
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._build_prompt("Task", "python", {"framework": "FastAPI"})

    assert "Framework: FastAPI" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_build_prompt_with_dependencies(mock_async_openai, monkeypatch):
    """
    SCENARIO: _build_prompt() with dependencies list
    EXPECTED: Dependencies listed in prompt
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._build_prompt("Task", "go", {"dependencies": ["gin", "gorm"]})

    assert "gin" in prompt
    assert "gorm" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_build_prompt_with_existing_code(mock_async_openai, monkeypatch):
    """
    SCENARIO: _build_prompt() with existing_code context
    EXPECTED: Existing code included in prompt
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._build_prompt(
        "Task",
        "python",
        {"existing_code": "def old_func(): pass"}
    )

    assert "def old_func(): pass" in prompt


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_build_prompt_with_requirements(mock_async_openai, monkeypatch):
    """
    SCENARIO: _build_prompt() with requirements dict
    EXPECTED: Requirements listed in prompt
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    prompt = generator._build_prompt(
        "Task",
        "python",
        {"requirements": {"auth": "OAuth2", "database": "MongoDB"}}
    )

    assert "auth: OAuth2" in prompt
    assert "database: MongoDB" in prompt


# ===== COST CALCULATION =====

@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_calculate_cost_gpt4(mock_async_openai, monkeypatch):
    """
    SCENARIO: _calculate_cost() for gpt-4 model
    EXPECTED: Correct cost calculated based on GPT-4 pricing
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator(model="gpt-4")
    cost = generator._calculate_cost(1000, 1000)

    # gpt-4: input $0.03/1K, output $0.06/1K
    expected = (1000 / 1000) * 0.03 + (1000 / 1000) * 0.06
    assert cost == expected


@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_calculate_cost_unknown_model(mock_async_openai, monkeypatch):
    """
    SCENARIO: _calculate_cost() for unknown model
    EXPECTED: Uses default pricing
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator(model="gpt-unknown")
    cost = generator._calculate_cost(500, 500)

    # default: input $0.01/1K, output $0.03/1K
    expected = (500 / 1000) * 0.01 + (500 / 1000) * 0.03
    assert cost == expected


# ===== GET_METRICS =====

@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
def test_get_metrics_initial_state(mock_async_openai, monkeypatch):
    """
    SCENARIO: get_metrics() on new client
    EXPECTED: All metrics at zero
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_async_openai.return_value = Mock()

    generator = OpenAICodeGenerator()
    metrics = generator.get_metrics()

    assert metrics["total_tokens_used"] == 0
    assert metrics["total_cost_usd"] == 0.0
    assert metrics["request_count"] == 0
    assert metrics["error_count"] == 0
    assert metrics["success_rate"] == 0.0


@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_get_metrics_after_successful_request(mock_async_openai, monkeypatch):
    """
    SCENARIO: get_metrics() after successful generate_code()
    EXPECTED: Metrics updated with request data
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "code"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 200
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 150

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator()
    await generator.generate_code("Task", "python")

    metrics = generator.get_metrics()

    assert metrics["total_tokens_used"] == 200
    assert metrics["total_cost_usd"] > 0
    assert metrics["request_count"] == 1
    assert metrics["error_count"] == 0
    assert metrics["success_rate"] == 1.0


@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_get_metrics_with_failures(mock_async_openai, monkeypatch):
    """
    SCENARIO: get_metrics() after failed requests
    EXPECTED: error_count incremented, success_rate calculated correctly
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator(max_retries=2)
    await generator.generate_code("Task", "python")

    metrics = generator.get_metrics()

    assert metrics["error_count"] == 2  # All retries failed
    assert metrics["success_rate"] == 0.0


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
@patch('llm.openai_client.OPENAI_AVAILABLE', True)
@patch('llm.openai_client.AsyncOpenAI')
async def test_complete_workflow_multiple_requests(mock_async_openai, monkeypatch):
    """
    SCENARIO: Complete workflow with multiple generate_code() calls
    EXPECTED: All metrics accumulate correctly
    """
    from llm.openai_client import OpenAICodeGenerator

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "code"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100
    mock_response.usage.prompt_tokens = 30
    mock_response.usage.completion_tokens = 70

    mock_client = Mock()
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_async_openai.return_value = mock_client

    generator = OpenAICodeGenerator()

    # Generate multiple times
    await generator.generate_code("Task 1", "python")
    await generator.generate_code("Task 2", "go")
    await generator.generate_code("Task 3", "python")

    metrics = generator.get_metrics()

    assert metrics["request_count"] == 3
    assert metrics["total_tokens_used"] == 300  # 100 * 3
    assert metrics["error_count"] == 0
    assert metrics["success_rate"] == 1.0
