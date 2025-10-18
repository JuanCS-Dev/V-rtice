"""
Unit Tests - AST-grep Engine.

Tests for ASTGrepEngine covering:
- Installation validation
- Pattern validation and execution
- Output parsing
- Error handling (invalid patterns, timeouts)
- Real ast-grep CLI integration

Author: MAXIMUS Team
Date: 2025-01-10
Compliance: Doutrina MAXIMUS | ≥90% coverage | Production-Ready
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from confirmation.ast_grep_engine import (
    ASTGrepEngine,
    ASTGrepConfig,
    ASTGrepMatch,
)


# ===================== FIXTURES =====================


@pytest.fixture
def ast_grep_config() -> ASTGrepConfig:
    """AST-grep configuration for testing."""
    return ASTGrepConfig(
        ast_grep_binary="ast-grep",
        timeout_seconds=5,
        max_matches=100,
        enable_debug=False,
    )


@pytest.fixture
def engine(ast_grep_config: ASTGrepConfig) -> ASTGrepEngine:
    """AST-grep engine instance."""
    return ASTGrepEngine(ast_grep_config)


@pytest.fixture
def temp_python_file(tmp_path: Path) -> Path:
    """Create temporary Python file for testing."""
    file_path = tmp_path / "test.py"
    file_path.write_text(
        """
import os

def dangerous_function(user_input):
    result = eval(user_input)  # Dangerous!
    return result

def safe_function(data):
    return json.loads(data)
"""
    )
    return file_path


# ===================== INSTALLATION VALIDATION TESTS =====================


@pytest.mark.asyncio
async def test_validate_installation_success(engine: ASTGrepEngine) -> None:
    """Test successful ast-grep installation validation."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"ast-grep 0.15.0\n", b"")
        )
        mock_exec.return_value = mock_proc

        await engine._validate_installation()

        assert engine._validated is True
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_validate_installation_not_found(
    engine: ASTGrepEngine,
) -> None:
    """Test ast-grep not found raises FileNotFoundError."""
    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=FileNotFoundError("ast-grep not found"),
    ):
        with pytest.raises(FileNotFoundError) as exc_info:
            await engine._validate_installation()

        assert "ast-grep binary not found" in str(exc_info.value)
        assert "cargo install ast-grep" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_installation_timeout(engine: ASTGrepEngine) -> None:
    """Test ast-grep validation timeout."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_exec.return_value = mock_proc

        with pytest.raises(RuntimeError) as exc_info:
            await engine._validate_installation()

        assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_installation_nonzero_exit(
    engine: ASTGrepEngine,
) -> None:
    """Test ast-grep returns non-zero exit code."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(
            return_value=(b"", b"Error: command not found")
        )
        mock_exec.return_value = mock_proc

        with pytest.raises(RuntimeError) as exc_info:
            await engine._validate_installation()

        assert "version check failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_validate_installation_called_once(
    engine: ASTGrepEngine,
) -> None:
    """Test installation validation is cached."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"ast-grep 0.15.0\n", b"")
        )
        mock_exec.return_value = mock_proc

        # Call multiple times
        await engine._validate_installation()
        await engine._validate_installation()
        await engine._validate_installation()

        # Should only execute once
        assert mock_exec.call_count == 1


# ===================== PATTERN VALIDATION TESTS =====================


def test_validate_pattern_valid(engine: ASTGrepEngine) -> None:
    """Test valid pattern passes validation."""
    engine._validate_pattern("eval($ARG)")  # Should not raise


def test_validate_pattern_empty(engine: ASTGrepEngine) -> None:
    """Test empty pattern raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        engine._validate_pattern("")

    assert "Pattern cannot be empty" in str(exc_info.value)


def test_validate_pattern_whitespace_only(engine: ASTGrepEngine) -> None:
    """Test whitespace-only pattern raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        engine._validate_pattern("   ")

    assert "Pattern cannot be empty" in str(exc_info.value)


def test_validate_pattern_unbalanced_parens(engine: ASTGrepEngine) -> None:
    """Test unbalanced parentheses raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        engine._validate_pattern("eval($ARG")

    assert "Unbalanced parentheses" in str(exc_info.value)


def test_validate_pattern_unbalanced_braces(engine: ASTGrepEngine) -> None:
    """Test unbalanced braces raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        engine._validate_pattern("function() { code")

    assert "Unbalanced braces" in str(exc_info.value)


# ===================== OUTPUT PARSING TESTS =====================


def test_parse_output_empty(engine: ASTGrepEngine) -> None:
    """Test parsing empty output returns empty list."""
    matches = engine._parse_output("", include_context=False)
    assert matches == []


def test_parse_output_whitespace(engine: ASTGrepEngine) -> None:
    """Test parsing whitespace-only output."""
    matches = engine._parse_output("   \n   ", include_context=False)
    assert matches == []


def test_parse_output_valid_json(engine: ASTGrepEngine) -> None:
    """Test parsing valid ast-grep JSON output."""
    json_output = json.dumps(
        [
            {
                "file": "/app/test.py",
                "range": {
                    "start": {"line": 5, "column": 13},
                    "end": {"line": 5, "column": 30},
                },
                "text": "eval(user_input)",
            }
        ]
    )

    matches = engine._parse_output(json_output, include_context=False)

    assert len(matches) == 1
    match = matches[0]
    assert isinstance(match, ASTGrepMatch)
    assert match.file_path == Path("/app/test.py")
    assert match.line_start == 5
    assert match.line_end == 5
    assert match.column_start == 13
    assert match.column_end == 30
    assert match.matched_text == "eval(user_input)"
    assert match.context_before is None
    assert match.context_after is None


def test_parse_output_with_context(engine: ASTGrepEngine) -> None:
    """Test parsing output with context lines."""
    json_output = json.dumps(
        [
            {
                "file": "/app/test.py",
                "range": {
                    "start": {"line": 5, "column": 13},
                    "end": {"line": 5, "column": 30},
                },
                "text": "eval(user_input)",
                "context": {
                    "before": "def dangerous_function(user_input):\n",
                    "after": "    return result\n",
                },
            }
        ]
    )

    matches = engine._parse_output(json_output, include_context=True)

    assert len(matches) == 1
    match = matches[0]
    assert match.context_before == "def dangerous_function(user_input):\n"
    assert match.context_after == "    return result\n"


def test_parse_output_multiple_matches(engine: ASTGrepEngine) -> None:
    """Test parsing multiple matches."""
    json_output = json.dumps(
        [
            {
                "file": "/app/test1.py",
                "range": {
                    "start": {"line": 5, "column": 1},
                    "end": {"line": 5, "column": 10},
                },
                "text": "eval(x)",
            },
            {
                "file": "/app/test2.py",
                "range": {
                    "start": {"line": 10, "column": 5},
                    "end": {"line": 10, "column": 15},
                },
                "text": "eval(y)",
            },
        ]
    )

    matches = engine._parse_output(json_output, include_context=False)

    assert len(matches) == 2
    assert matches[0].file_path == Path("/app/test1.py")
    assert matches[1].file_path == Path("/app/test2.py")


def test_parse_output_invalid_json(engine: ASTGrepEngine) -> None:
    """Test parsing invalid JSON returns empty list."""
    matches = engine._parse_output("{ invalid json }", include_context=False)
    assert matches == []


def test_parse_output_unexpected_structure(engine: ASTGrepEngine) -> None:
    """Test parsing unexpected JSON structure."""
    json_output = json.dumps([{"unexpected": "structure"}])
    matches = engine._parse_output(json_output, include_context=False)
    assert matches == []


# ===================== SEARCH PATTERN TESTS =====================


@pytest.mark.asyncio
async def test_search_pattern_no_files(engine: ASTGrepEngine) -> None:
    """Test search with no files returns empty list."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        matches = await engine.search_pattern(
            pattern="eval($ARG)",
            file_paths=[],
            language="python",
        )

    assert matches == []


@pytest.mark.asyncio
async def test_search_pattern_nonexistent_files(
    engine: ASTGrepEngine,
) -> None:
    """Test search with nonexistent files returns empty."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        matches = await engine.search_pattern(
            pattern="eval($ARG)",
            file_paths=[Path("/nonexistent/file.py")],
            language="python",
        )

    assert matches == []


@pytest.mark.asyncio
async def test_search_pattern_success(
    engine: ASTGrepEngine, temp_python_file: Path
) -> None:
    """Test successful pattern search."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            json_output = json.dumps(
                [
                    {
                        "file": str(temp_python_file),
                        "range": {
                            "start": {"line": 5, "column": 13},
                            "end": {"line": 5, "column": 30},
                        },
                        "text": "eval(user_input)",
                    }
                ]
            )
            mock_proc.communicate = AsyncMock(
                return_value=(json_output.encode(), b"")
            )
            mock_exec.return_value = mock_proc

            matches = await engine.search_pattern(
                pattern="eval($ARG)",
                file_paths=[temp_python_file],
                language="python",
            )

            assert len(matches) == 1
            assert matches[0].matched_text == "eval(user_input)"


@pytest.mark.asyncio
async def test_search_pattern_no_matches(
    engine: ASTGrepEngine, temp_python_file: Path
) -> None:
    """Test search with no matches (exit code 1)."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 1  # ast-grep returns 1 for no matches
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = mock_proc

            matches = await engine.search_pattern(
                pattern="nonexistent_pattern",
                file_paths=[temp_python_file],
                language="python",
            )

            assert matches == []


@pytest.mark.asyncio
async def test_search_pattern_timeout(
    engine: ASTGrepEngine, temp_python_file: Path
) -> None:
    """Test search timeout raises asyncio.TimeoutError."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(
                side_effect=asyncio.TimeoutError()
            )
            mock_exec.return_value = mock_proc

            with pytest.raises(asyncio.TimeoutError):
                await engine.search_pattern(
                    pattern="eval($ARG)",
                    file_paths=[temp_python_file],
                    language="python",
                )


@pytest.mark.asyncio
async def test_search_pattern_error_exit_code(
    engine: ASTGrepEngine, temp_python_file: Path
) -> None:
    """Test search with error exit code raises RuntimeError."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 2  # Error exit code
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"Syntax error in pattern")
            )
            mock_exec.return_value = mock_proc

            with pytest.raises(RuntimeError) as exc_info:
                await engine.search_pattern(
                    pattern="invalid pattern",
                    file_paths=[temp_python_file],
                    language="python",
                )

            assert "ast-grep failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_pattern_with_context(
    engine: ASTGrepEngine, temp_python_file: Path
) -> None:
    """Test search with context enabled."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0

            json_output = json.dumps(
                [
                    {
                        "file": str(temp_python_file),
                        "range": {
                            "start": {"line": 5, "column": 13},
                            "end": {"line": 5, "column": 30},
                        },
                        "text": "eval(user_input)",
                        "context": {
                            "before": "def dangerous():\n",
                            "after": "    return result\n",
                        },
                    }
                ]
            )
            mock_proc.communicate = AsyncMock(
                return_value=(json_output.encode(), b"")
            )
            mock_exec.return_value = mock_proc

            matches = await engine.search_pattern(
                pattern="eval($ARG)",
                file_paths=[temp_python_file],
                language="python",
                include_context=True,
            )

            assert len(matches) == 1
            assert matches[0].context_before is not None
            assert matches[0].context_after is not None


# ===================== SEARCH DIRECTORY TESTS =====================


@pytest.mark.asyncio
async def test_search_directory_invalid_path(
    engine: ASTGrepEngine,
) -> None:
    """Test search directory with invalid path raises ValueError."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with pytest.raises(ValueError) as exc_info:
            await engine.search_directory(
                pattern="eval($ARG)",
                directory=Path("/nonexistent"),
                language="python",
            )

        assert "Invalid directory" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_directory_success(
    engine: ASTGrepEngine, tmp_path: Path
) -> None:
    """Test successful directory search."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("result = eval(user_input)")

    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0

            json_output = json.dumps(
                [
                    {
                        "file": str(test_file),
                        "range": {
                            "start": {"line": 1, "column": 10},
                            "end": {"line": 1, "column": 27},
                        },
                        "text": "eval(user_input)",
                    }
                ]
            )
            mock_proc.communicate = AsyncMock(
                return_value=(json_output.encode(), b"")
            )
            mock_exec.return_value = mock_proc

            matches = await engine.search_directory(
                pattern="eval($ARG)",
                directory=tmp_path,
                language="python",
            )

            assert len(matches) == 1


@pytest.mark.asyncio
async def test_search_directory_with_filters(
    engine: ASTGrepEngine, tmp_path: Path
) -> None:
    """Test directory search with include/exclude patterns."""
    with patch.object(engine, "_validate_installation", AsyncMock()):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 1  # No matches
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            mock_exec.return_value = mock_proc

            await engine.search_directory(
                pattern="eval($ARG)",
                directory=tmp_path,
                language="python",
                include_patterns=["*.py"],
                exclude_patterns=["tests/*", "venv/*"],
            )

            # Verify command includes filters
            call_args = mock_exec.call_args[0]
            assert "--include" in call_args
            assert "--exclude" in call_args


# ===================== REAL INTEGRATION TEST (requires ast-grep) =====================


@pytest.mark.integration
@pytest.mark.skipif(
    not Path("/usr/bin/ast-grep").exists()
    and not Path("/usr/local/bin/ast-grep").exists(),
    reason="ast-grep not installed",
)
@pytest.mark.asyncio
async def test_real_ast_grep_execution(tmp_path: Path) -> None:
    """Integration test with real ast-grep CLI."""
    # Create test file
    test_file = tmp_path / "vulnerable.py"
    test_file.write_text(
        """
def dangerous():
    result = eval(user_input)
    return result
"""
    )

    engine = ASTGrepEngine()

    matches = await engine.search_pattern(
        pattern="eval($ARG)",
        file_paths=[test_file],
        language="python",
    )

    # Should find the eval() call
    assert len(matches) >= 1
    assert any("eval" in m.matched_text for m in matches)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=confirmation", "--cov-report=term-missing"])
