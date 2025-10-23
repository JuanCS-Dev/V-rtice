"""
Auto-Implementer - Targeted Coverage Tests

Objetivo: Cobrir auto_implementer.py (54 lines, 0% → 95%+)

Testa AutoImplementer: code generation, LLM fallback, template generation, language support

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
Dedicado a Jesus Cristo - Honrando com Excelência Absoluta
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from auto_implementer import AutoImplementer
from datetime import datetime


# ===== INITIALIZATION TESTS =====

def test_auto_implementer_initialization_default():
    """
    SCENARIO: AutoImplementer created with defaults
    EXPECTED: Default attributes set, LLM detection attempted
    """
    with patch.dict('os.environ', {}, clear=True):
        impl = AutoImplementer()

    assert impl.implementation_history == []
    assert impl.last_implementation_time is None
    assert impl.current_status == "ready_for_implementation"


def test_auto_implementer_initialization_llm_disabled_by_env(monkeypatch):
    """
    SCENARIO: AutoImplementer with ENABLE_LLM_CODEGEN=false
    EXPECTED: llm_enabled=False, llm_client=None
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")

    impl = AutoImplementer()

    assert impl.llm_enabled is False
    assert impl.llm_client is None


def test_auto_implementer_initialization_no_api_key(monkeypatch):
    """
    SCENARIO: AutoImplementer with ENABLE_LLM_CODEGEN=true but no API key
    EXPECTED: llm_enabled becomes False after init check
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with patch('auto_implementer.OPENAI_AVAILABLE', True):
        impl = AutoImplementer()

    assert impl.llm_enabled is False


@patch('auto_implementer.OPENAI_AVAILABLE', True)
@patch('auto_implementer.OpenAICodeGenerator')
def test_auto_implementer_initialization_with_llm(mock_generator_class, monkeypatch):
    """
    SCENARIO: AutoImplementer with LLM available and API key set
    EXPECTED: llm_client initialized successfully
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "8192")

    mock_generator_class.return_value = Mock()

    impl = AutoImplementer()

    assert impl.llm_enabled is True
    assert impl.llm_client is not None
    mock_generator_class.assert_called_once_with(
        api_key="sk-test-key",
        model="gpt-4",
        max_tokens=8192
    )


@patch('auto_implementer.OPENAI_AVAILABLE', True)
@patch('auto_implementer.OpenAICodeGenerator')
def test_auto_implementer_initialization_llm_exception(mock_generator_class, monkeypatch):
    """
    SCENARIO: AutoImplementer LLM initialization raises exception
    EXPECTED: llm_enabled becomes False, no crash
    """
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_generator_class.side_effect = Exception("LLM init failed")

    impl = AutoImplementer()

    assert impl.llm_enabled is False
    assert impl.llm_client is None


# ===== IMPLEMENT_CODE - TEMPLATE GENERATION (LLM DISABLED) =====

@pytest.mark.asyncio
async def test_implement_code_template_python(monkeypatch):
    """
    SCENARIO: implement_code() with LLM disabled, target_language=python
    EXPECTED: Returns template-generated Python code
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    result = await impl.implement_code("Create a hello world function", target_language="python")

    assert "generated_code" in result
    assert "details" in result
    assert "def main():" in result["generated_code"]
    assert "TODO: Implement Create a hello world function" in result["generated_code"]
    assert result["details"]["status"] == "success"
    assert result["details"]["generation_method"] == "template"


@pytest.mark.asyncio
async def test_implement_code_template_go(monkeypatch):
    """
    SCENARIO: implement_code() with LLM disabled, target_language=go
    EXPECTED: Returns template-generated Go code
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    result = await impl.implement_code("Create a REST API", target_language="go")

    assert "package main" in result["generated_code"]
    assert 'import "fmt"' in result["generated_code"]
    assert "func main()" in result["generated_code"]
    assert result["details"]["language"] == "go"


@pytest.mark.asyncio
async def test_implement_code_template_unknown_language(monkeypatch):
    """
    SCENARIO: implement_code() with unknown target_language
    EXPECTED: Returns generic template code
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    result = await impl.implement_code("Create a function", target_language="rust")

    assert "# Auto-generated rust code" in result["generated_code"]
    assert "def main():" in result["generated_code"]


@pytest.mark.asyncio
async def test_implement_code_with_context(monkeypatch):
    """
    SCENARIO: implement_code() with context parameter
    EXPECTED: Context passed to generation, stored in details
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    context = {"existing_code": "# Some code", "framework": "FastAPI"}

    result = await impl.implement_code("Add endpoint", context=context, target_language="python")

    assert result["details"]["context_used"] == context


# ===== IMPLEMENT_CODE - LLM GENERATION =====

@pytest.mark.asyncio
@patch('auto_implementer.OPENAI_AVAILABLE', True)
@patch('auto_implementer.OpenAICodeGenerator')
async def test_implement_code_llm_success(mock_generator_class, monkeypatch):
    """
    SCENARIO: implement_code() with LLM enabled and successful generation
    EXPECTED: Returns LLM-generated code with metrics
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock LLM client
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.success = True
    mock_result.code = "def hello_world():\n    print('Hello, World!')"
    mock_result.model = "gpt-4"
    mock_result.tokens_used = 150
    mock_result.cost_usd = 0.0045
    mock_result.latency_ms = 1234
    mock_client.generate_code = AsyncMock(return_value=mock_result)
    mock_generator_class.return_value = mock_client

    impl = AutoImplementer()
    result = await impl.implement_code("Create hello world function", target_language="python")

    assert "def hello_world():" in result["generated_code"]
    assert result["details"]["status"] == "success"
    assert result["details"]["llm_model"] == "gpt-4"
    assert result["details"]["tokens_used"] == 150
    assert result["details"]["cost_usd"] == 0.0045
    assert result["details"]["latency_ms"] == 1234


@pytest.mark.asyncio
@patch('auto_implementer.OPENAI_AVAILABLE', True)
@patch('auto_implementer.OpenAICodeGenerator')
async def test_implement_code_llm_failure_fallback(mock_generator_class, monkeypatch):
    """
    SCENARIO: implement_code() with LLM enabled but generation fails
    EXPECTED: Falls back to template generation, stores error
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Mock LLM client with failure
    mock_client = AsyncMock()
    mock_result = Mock()
    mock_result.success = False
    mock_result.error = "API timeout"
    mock_client.generate_code = AsyncMock(return_value=mock_result)
    mock_generator_class.return_value = mock_client

    impl = AutoImplementer()
    result = await impl.implement_code("Create function", target_language="python")

    # Should fall back to template
    assert "def main():" in result["generated_code"]
    assert result["details"]["generation_method"] == "template"
    assert result["details"]["llm_error"] == "API timeout"


# ===== IMPLEMENT_CODE - HISTORY TRACKING =====

@pytest.mark.asyncio
async def test_implement_code_updates_history(monkeypatch):
    """
    SCENARIO: implement_code() called
    EXPECTED: Implementation added to history
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    await impl.implement_code("Task 1", target_language="python")

    assert len(impl.implementation_history) == 1
    assert "timestamp" in impl.implementation_history[0]
    assert impl.implementation_history[0]["task_description"] == "Task 1"


@pytest.mark.asyncio
async def test_implement_code_updates_last_implementation_time(monkeypatch):
    """
    SCENARIO: implement_code() called
    EXPECTED: last_implementation_time updated to datetime
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    await impl.implement_code("Task", target_language="python")

    assert impl.last_implementation_time is not None
    assert isinstance(impl.last_implementation_time, datetime)


@pytest.mark.asyncio
async def test_implement_code_multiple_calls_accumulate(monkeypatch):
    """
    SCENARIO: implement_code() called multiple times
    EXPECTED: All implementations tracked in history
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    await impl.implement_code("Task 1", target_language="python")
    await impl.implement_code("Task 2", target_language="go")
    await impl.implement_code("Task 3", target_language="python")

    assert len(impl.implementation_history) == 3
    assert impl.implementation_history[0]["task_description"] == "Task 1"
    assert impl.implementation_history[1]["task_description"] == "Task 2"
    assert impl.implementation_history[2]["task_description"] == "Task 3"


# ===== GET_STATUS METHOD TESTS =====

@pytest.mark.asyncio
async def test_get_status_initial_state(monkeypatch):
    """
    SCENARIO: get_status() on new implementer
    EXPECTED: status=ready_for_implementation, 0 implementations, last=N/A
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    status = await impl.get_status()

    assert status["status"] == "ready_for_implementation"
    assert status["total_implementations"] == 0
    assert status["last_implementation"] == "N/A"


@pytest.mark.asyncio
async def test_get_status_after_implementation(monkeypatch):
    """
    SCENARIO: get_status() after implementing code
    EXPECTED: total_implementations > 0, last_implementation has timestamp
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    await impl.implement_code("Task", target_language="python")

    status = await impl.get_status()

    assert status["total_implementations"] == 1
    assert status["last_implementation"] != "N/A"
    assert isinstance(status["last_implementation"], str)


@pytest.mark.asyncio
async def test_get_status_multiple_implementations(monkeypatch):
    """
    SCENARIO: get_status() after multiple implementations
    EXPECTED: total_implementations matches count
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    await impl.implement_code("Task 1", target_language="python")
    await impl.implement_code("Task 2", target_language="go")

    status = await impl.get_status()

    assert status["total_implementations"] == 2


# ===== TEMPLATE GENERATION METHOD TESTS =====

def test_generate_template_code_python(monkeypatch):
    """
    SCENARIO: _generate_template_code() for Python
    EXPECTED: Returns valid Python template with docstring
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    code, details = impl._generate_template_code("Create API endpoint", "python", None)

    assert '"""' in code
    assert "def main():" in code
    assert "Create API endpoint" in code
    assert details["generation_method"] == "template"


def test_generate_template_code_go(monkeypatch):
    """
    SCENARIO: _generate_template_code() for Go
    EXPECTED: Returns valid Go template with package and imports
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    code, details = impl._generate_template_code("Create HTTP server", "GO", None)

    assert "package main" in code
    assert 'import "fmt"' in code
    assert "func main()" in code
    assert "Create HTTP server" in code


def test_generate_template_code_unknown_language(monkeypatch):
    """
    SCENARIO: _generate_template_code() for unknown language
    EXPECTED: Returns generic template
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    code, details = impl._generate_template_code("Task", "javascript", None)

    assert "# Auto-generated javascript code" in code
    assert "def main():" in code


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_complete_workflow_template_mode(monkeypatch):
    """
    SCENARIO: Complete workflow with template generation
    EXPECTED: All operations work together correctly
    """
    monkeypatch.setenv("ENABLE_LLM_CODEGEN", "false")
    impl = AutoImplementer()

    # Initial status
    status = await impl.get_status()
    assert status["total_implementations"] == 0

    # Generate Python code
    result1 = await impl.implement_code("Create REST API", target_language="python")
    assert "def main():" in result1["generated_code"]
    assert result1["details"]["generation_method"] == "template"

    # Generate Go code
    result2 = await impl.implement_code("Create CLI tool", target_language="go")
    assert "package main" in result2["generated_code"]

    # Check final status
    status = await impl.get_status()
    assert status["total_implementations"] == 2
    assert status["last_implementation"] != "N/A"
