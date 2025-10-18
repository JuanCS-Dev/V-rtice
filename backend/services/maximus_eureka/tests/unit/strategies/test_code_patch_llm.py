"""
Unit Tests - Code Patch LLM Strategy.

Tests for CodePatchLLMStrategy.

Author: MAXIMUS Team
Date: 2025-01-10
"""

from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# Setup path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from strategies.code_patch_llm import CodePatchLLMStrategy
from llm import LLMResponse

# Import models
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "maximus_oraculo"))
from models.apv import APV, AffectedPackage, ASTGrepPattern, RemediationStrategy


# ===================== CODE PATCH LLM TESTS =====================


@pytest.mark.asyncio
async def test_code_patch_llm_can_handle_with_pattern(sample_apv_with_pattern, sample_confirmation_with_locations):
    """Test can_handle returns True when ast-grep pattern exists and confirmed."""
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=Path("/tmp"),
    )
    
    result = await strategy.can_handle(sample_apv_with_pattern, sample_confirmation_with_locations)
    
    assert result is True


@pytest.mark.asyncio
async def test_code_patch_llm_can_handle_no_pattern(sample_apv_no_pattern, sample_confirmation_with_locations):
    """Test can_handle returns False when no ast-grep pattern."""
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=Path("/tmp"),
    )
    
    result = await strategy.can_handle(sample_apv_no_pattern, sample_confirmation_with_locations)
    
    assert result is False


@pytest.mark.asyncio
async def test_code_patch_llm_can_handle_no_locations(sample_apv_with_pattern, sample_confirmation_no_locations):
    """Test can_handle returns False when no confirmed locations."""
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=Path("/tmp"),
    )
    
    result = await strategy.can_handle(sample_apv_with_pattern, sample_confirmation_no_locations)
    
    assert result is False


@pytest.mark.asyncio
async def test_code_patch_llm_can_handle_fix_available(sample_apv_with_fix, sample_confirmation_with_locations):
    """Test can_handle returns False when fix available (prefer DependencyUpgrade)."""
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=Path("/tmp"),
    )
    
    result = await strategy.can_handle(sample_apv_with_fix, sample_confirmation_with_locations)
    
    assert result is False


@pytest.mark.asyncio
async def test_code_patch_llm_apply_strategy(tmp_path, sample_apv_with_pattern, sample_confirmation_with_locations):
    """Test apply_strategy generates patch via LLM."""
    # Create vulnerable file
    vulnerable_file = tmp_path / "test.py"
    vulnerable_file.write_text("""
def process_data(user_input):
    # Vulnerable SQL
    query = f"SELECT * FROM users WHERE id={user_input}"
    return execute_query(query)
""")
    
    # Mock LLM response with diff
    mock_llm = create_mock_llm_client(
        response_content="""
--- a/test.py
+++ b/test.py
@@ -2,3 +2,3 @@
 def process_data(user_input):
     # Fixed SQL
-    query = f"SELECT * FROM users WHERE id={user_input}"
+    query = "SELECT * FROM users WHERE id=?"
+    return execute_query(query, (user_input,))
"""
    )
    
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=tmp_path,
    )
    
    patch = await strategy.apply_strategy(sample_apv_with_pattern, sample_confirmation_with_locations)
    
    # Verify patch
    assert patch.cve_id == "CVE-2024-99999"
    assert patch.strategy_used == RemediationStrategy.CODE_PATCH
    assert 0.5 <= patch.confidence_score <= 0.85  # LLM confidence range
    assert len(patch.files_modified) > 0
    assert patch.diff_content is not None


@pytest.mark.asyncio
async def test_code_patch_llm_confidence_calculation(tmp_path, sample_apv_with_pattern):
    """Test confidence score calculation."""
    from eureka_models.confirmation.confirmation_result import (
        ConfirmationResult,
        ConfirmationStatus,
        VulnerableLocation,
    )
    
    # Confirmation with multiple locations (reduces confidence)
    confirmation = ConfirmationResult(
        apv_id="CVE-2024-99999",
        cve_id="CVE-2024-99999",
        status=ConfirmationStatus.CONFIRMED,
        vulnerable_locations=[
            VulnerableLocation(
                file_path=Path("test1.py"),
                line_start=10,
                line_end=10,
                pattern_matched="test",
                code_snippet="query = f'SELECT * FROM users WHERE id={id}'",
            ),
            VulnerableLocation(
                file_path=Path("test2.py"),
                line_start=20,
                line_end=20,
                pattern_matched="test",
                code_snippet="query = f'SELECT * FROM users WHERE id={id}'",
            ),
            VulnerableLocation(
                file_path=Path("test3.py"),
                line_start=30,
                line_end=30,
                pattern_matched="test",
                code_snippet="query = f'SELECT * FROM users WHERE id={id}'",
            ),
            VulnerableLocation(
                file_path=Path("test4.py"),
                line_start=40,
                line_end=40,
                pattern_matched="test",
                code_snippet="query = f'SELECT * FROM users WHERE id={id}'",
            ),
        ],
    )
    
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=tmp_path,
    )
    
    # Create files
    for i in range(1, 5):
        (tmp_path / f"test{i}.py").write_text("query = f'SELECT * FROM users WHERE id={id}'")
    
    patch = await strategy.apply_strategy(sample_apv_with_pattern, confirmation)
    
    # Multiple locations should reduce confidence
    assert patch.confidence_score < 0.7


def test_code_patch_llm_strategy_type():
    """Test strategy_type property."""
    mock_llm = create_mock_llm_client()
    strategy = CodePatchLLMStrategy(
        llm_client=mock_llm,
        codebase_root=Path("/tmp"),
    )
    
    assert strategy.strategy_type == RemediationStrategy.CODE_PATCH


# ===================== HELPER FUNCTIONS =====================


def create_mock_llm_client(response_content: str = "--- a/test.py\n+++ b/test.py\n"):
    """Create mock LLM client."""
    mock_client = AsyncMock()
    mock_client.provider = MagicMock()
    mock_client.provider.value = "mock"
    mock_client.model = "mock-model"
    
    mock_client.complete = AsyncMock(return_value=LLMResponse(
        content=response_content,
        model="mock-model",
        tokens_used=100,
        finish_reason="stop",
    ))
    
    return mock_client


# ===================== FIXTURES =====================


@pytest.fixture
def sample_apv_with_pattern():
    """APV with ast-grep pattern and no fix."""
    return APV(
        cve_id="CVE-2024-99999",
        aliases=["GHSA-test-1234"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="SQL injection vulnerability",
        details="Detailed description of SQL injection vulnerability requiring code-level fix",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-app",
                affected_versions=["1.0.0"],
                fixed_versions=[],  # No fix available
            )
        ],
        ast_grep_patterns=[
            ASTGrepPattern(
                language="python",
                pattern='query = f"SELECT * FROM $TABLE WHERE $COLUMN={$VAR}"',
                severity="high",
            )
        ],
    )


@pytest.fixture
def sample_apv_no_pattern():
    """APV without ast-grep pattern."""
    return APV(
        cve_id="CVE-2024-99998",
        aliases=["GHSA-test-9999"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability without pattern",
        details="Detailed description of vulnerability without ast-grep pattern for testing",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-app",
                affected_versions=["1.0.0"],
                fixed_versions=[],
            )
        ],
        ast_grep_patterns=[],  # No pattern
    )


@pytest.fixture
def sample_apv_with_fix():
    """APV with fix available."""
    return APV(
        cve_id="CVE-2024-99997",
        aliases=["GHSA-test-8888"],
        published=datetime(2024, 1, 1),
        modified=datetime(2024, 1, 2),
        summary="Test vulnerability with fix",
        details="Detailed description of vulnerability with fix available for testing purposes",
        source_feed="OSV.dev",
        affected_packages=[
            AffectedPackage(
                ecosystem="PyPI",
                name="test-package",
                affected_versions=["1.0.0"],
                fixed_versions=["2.0.0"],  # Fix available
            )
        ],
        ast_grep_patterns=[
            ASTGrepPattern(
                language="python",
                pattern='test_pattern',
                severity="high",
            )
        ],
    )


@pytest.fixture
def sample_confirmation_with_locations():
    """Confirmation with vulnerable locations."""
    from eureka_models.confirmation.confirmation_result import (
        ConfirmationResult,
        ConfirmationStatus,
        VulnerableLocation,
    )
    from pathlib import Path
    
    return ConfirmationResult(
        apv_id="CVE-2024-99999",
        cve_id="CVE-2024-99999",
        status=ConfirmationStatus.CONFIRMED,
        vulnerable_locations=[
            VulnerableLocation(
                file_path=Path("test.py"),
                line_start=10,
                line_end=10,
                code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"',
                pattern_matched='f-string SQL injection',
            )
        ],
    )


@pytest.fixture
def sample_confirmation_no_locations():
    """Confirmation without vulnerable locations."""
    from eureka_models.confirmation.confirmation_result import (
        ConfirmationResult,
        ConfirmationStatus,
    )
    
    return ConfirmationResult(
        apv_id="CVE-2024-99999",
        cve_id="CVE-2024-99999",
        status=ConfirmationStatus.FALSE_POSITIVE,
        vulnerable_locations=[],  # No locations
    )
