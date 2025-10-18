"""
AST-grep Engine - MAXIMUS Eureka Vulnerability Confirmation.

Wrapper around ast-grep CLI for deterministic vulnerability pattern matching.
Enables syntactic analysis of codebase to confirm vulnerability presence.

Theoretical Foundation:
    AST (Abstract Syntax Tree) analysis provides language-aware pattern matching
    superior to regex-based approaches. ast-grep operates on parsed syntax trees,
    enabling semantically-aware queries that respect code structure.

    This approach reduces false positives by matching code patterns in their
    syntactic context, not mere text strings. Critical for confirming CVE
    descriptions map to actual vulnerable code instances.

ast-grep Reference: https://ast-grep.github.io/

Performance Targets:
    - Pattern execution < 100ms per file
    - Timeout protection (5s default)
    - Memory-efficient streaming of results

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Perfect in knowledge
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ASTGrepConfig:
    """
    Configuration for ast-grep engine.
    
    Attributes:
        ast_grep_binary: Path to ast-grep executable
        timeout_seconds: Maximum execution time per search
        max_matches: Maximum matches to return per search
        enable_debug: Enable ast-grep debug output
    """

    ast_grep_binary: str = "ast-grep"
    timeout_seconds: int = 5
    max_matches: int = 100
    enable_debug: bool = False


class ASTGrepMatch(BaseModel):
    """
    Single match result from ast-grep pattern search.
    
    Represents one location in codebase where pattern matched.
    
    Attributes:
        file_path: Absolute path to file containing match
        line_start: Starting line number of match
        line_end: Ending line number of match
        column_start: Starting column number
        column_end: Ending column number
        matched_text: Code text that matched pattern
        context_before: Lines before match (optional)
        context_after: Lines after match (optional)
    """

    model_config = ConfigDict(frozen=True)

    file_path: Path = Field(..., description="File containing match")
    line_start: int = Field(..., ge=1, description="Start line")
    line_end: int = Field(..., ge=1, description="End line")
    column_start: int = Field(..., ge=1, description="Start column")
    column_end: int = Field(..., ge=1, description="End column")
    matched_text: str = Field(..., description="Matched code snippet")
    context_before: Optional[str] = Field(
        default=None, description="Lines before match"
    )
    context_after: Optional[str] = Field(
        default=None, description="Lines after match"
    )


class ASTGrepEngine:
    """
    Wrapper for ast-grep CLI tool.
    
    Executes ast-grep patterns against codebase to confirm vulnerability presence.
    Handles subprocess execution, timeout, error handling, and result parsing.
    
    Design Philosophy:
        Thin wrapper that delegates to ast-grep CLI while providing:
        - Async execution via asyncio.subprocess
        - Structured error handling
        - Timeout protection
        - JSON result parsing
        - Validation of ast-grep installation
    
    Usage:
        >>> engine = ASTGrepEngine()
        >>> matches = await engine.search_pattern(
        ...     pattern="eval($ARG)",
        ...     file_paths=[Path("/app/views.py")],
        ...     language="python",
        ... )
        >>> for match in matches:
        ...     print(f"{match.file_path}:{match.line_start}")
    """

    def __init__(self, config: Optional[ASTGrepConfig] = None) -> None:
        """
        Initialize ast-grep engine.
        
        Args:
            config: Engine configuration (uses defaults if None)
        """
        self.config = config or ASTGrepConfig()
        self._validated: bool = False

        logger.info(
            "ASTGrepEngine initialized",
            extra={
                "binary": self.config.ast_grep_binary,
                "timeout": self.config.timeout_seconds,
            },
        )

    async def _validate_installation(self) -> None:
        """
        Validate ast-grep is installed and accessible.
        
        Raises:
            FileNotFoundError: If ast-grep binary not found
            RuntimeError: If ast-grep version check fails
        """
        if self._validated:
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                self.config.ast_grep_binary,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=5.0
            )

            if proc.returncode != 0:
                raise RuntimeError(
                    f"ast-grep version check failed: {stderr.decode()}"
                )

            version = stdout.decode().strip()
            logger.info(f"ast-grep validated: {version}")
            self._validated = True

        except FileNotFoundError:
            raise FileNotFoundError(
                f"ast-grep binary not found: {self.config.ast_grep_binary}. "
                "Install via: cargo install ast-grep"
            )
        except asyncio.TimeoutError:
            raise RuntimeError("ast-grep version check timed out")

    def _validate_pattern(self, pattern: str) -> None:
        """
        Validate ast-grep pattern syntax.
        
        Args:
            pattern: ast-grep pattern string
            
        Raises:
            ValueError: If pattern is empty or invalid
        """
        if not pattern or not pattern.strip():
            raise ValueError("Pattern cannot be empty")

        # Basic syntax validation
        if pattern.count("(") != pattern.count(")"):
            raise ValueError("Unbalanced parentheses in pattern")

        if pattern.count("{") != pattern.count("}"):
            raise ValueError("Unbalanced braces in pattern")

    async def search_pattern(
        self,
        pattern: str,
        file_paths: list[Path],
        language: str = "python",
        include_context: bool = False,
    ) -> list[ASTGrepMatch]:
        """
        Search for pattern in specified files.
        
        Args:
            pattern: ast-grep pattern (e.g., "eval($ARG)")
            file_paths: List of files to search
            language: Target language (python, javascript, etc.)
            include_context: Include surrounding lines in results
            
        Returns:
            List of matches found
            
        Raises:
            ValueError: If pattern is invalid
            FileNotFoundError: If ast-grep not installed
            RuntimeError: If ast-grep execution fails
            asyncio.TimeoutError: If search exceeds timeout
        """
        # Validate
        await self._validate_installation()
        self._validate_pattern(pattern)

        if not file_paths:
            logger.warning("No files specified for search")
            return []

        # Filter to existing files
        existing_files = [f for f in file_paths if f.exists()]
        if not existing_files:
            logger.warning("No existing files to search")
            return []

        # Build ast-grep command
        cmd = [
            self.config.ast_grep_binary,
            "scan",
            "--pattern",
            pattern,
            "--lang",
            language,
            "--json",  # JSON output for parsing
        ]

        if self.config.max_matches:
            cmd.extend(["--max-count", str(self.config.max_matches)])

        if include_context:
            cmd.extend(["--context", "3"])  # 3 lines before/after

        # Add file paths
        cmd.extend([str(f) for f in existing_files])

        logger.debug(
            f"Executing ast-grep: {' '.join(cmd)}",
            extra={
                "pattern": pattern,
                "files": len(existing_files),
                "language": language,
            },
        )

        try:
            # Execute ast-grep
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.config.timeout_seconds
            )

            # ast-grep returns 0 if matches found, 1 if no matches, >1 on error
            if proc.returncode > 1:
                raise RuntimeError(
                    f"ast-grep failed (exit {proc.returncode}): {stderr.decode()}"
                )

            # Parse JSON output
            matches = self._parse_output(stdout.decode(), include_context)

            logger.info(
                f"ast-grep search complete: {len(matches)} matches",
                extra={
                    "pattern": pattern,
                    "files_searched": len(existing_files),
                    "matches_found": len(matches),
                },
            )

            return matches

        except asyncio.TimeoutError:
            logger.error(
                f"ast-grep search timed out after {self.config.timeout_seconds}s"
            )
            raise
        except Exception as e:
            logger.error(f"ast-grep execution failed: {e}", exc_info=True)
            raise

    def _parse_output(
        self, output: str, include_context: bool
    ) -> list[ASTGrepMatch]:
        """
        Parse ast-grep JSON output into ASTGrepMatch objects.
        
        Args:
            output: JSON output from ast-grep
            include_context: Whether context was requested
            
        Returns:
            List of parsed matches
        """
        if not output.strip():
            return []

        try:
            data = json.loads(output)
            matches: list[ASTGrepMatch] = []

            # ast-grep JSON format: array of match objects
            for item in data:
                match = ASTGrepMatch(
                    file_path=Path(item["file"]),
                    line_start=item["range"]["start"]["line"],
                    line_end=item["range"]["end"]["line"],
                    column_start=item["range"]["start"]["column"],
                    column_end=item["range"]["end"]["column"],
                    matched_text=item["text"],
                    context_before=(
                        item.get("context", {}).get("before")
                        if include_context
                        else None
                    ),
                    context_after=(
                        item.get("context", {}).get("after")
                        if include_context
                        else None
                    ),
                )
                matches.append(match)

            return matches

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ast-grep JSON: {e}")
            return []
        except (KeyError, TypeError) as e:
            logger.error(f"Unexpected ast-grep JSON structure: {e}")
            return []

    async def search_directory(
        self,
        pattern: str,
        directory: Path,
        language: str = "python",
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[ASTGrepMatch]:
        """
        Search for pattern recursively in directory.
        
        Args:
            pattern: ast-grep pattern
            directory: Root directory to search
            language: Target language
            include_patterns: Glob patterns to include (e.g., ["*.py"])
            exclude_patterns: Glob patterns to exclude (e.g., ["tests/*"])
            
        Returns:
            List of matches found
        """
        await self._validate_installation()
        self._validate_pattern(pattern)

        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory}")

        # Build command for directory search
        cmd = [
            self.config.ast_grep_binary,
            "scan",
            "--pattern",
            pattern,
            "--lang",
            language,
            "--json",
            str(directory),
        ]

        if include_patterns:
            for pat in include_patterns:
                cmd.extend(["--include", pat])

        if exclude_patterns:
            for pat in exclude_patterns:
                cmd.extend(["--exclude", pat])

        logger.debug(
            f"Searching directory: {directory}",
            extra={
                "pattern": pattern,
                "language": language,
                "include": include_patterns,
                "exclude": exclude_patterns,
            },
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.config.timeout_seconds
            )

            if proc.returncode > 1:
                raise RuntimeError(
                    f"ast-grep failed: {stderr.decode()}"
                )

            matches = self._parse_output(stdout.decode(), False)

            logger.info(
                f"Directory search complete: {len(matches)} matches",
                extra={
                    "directory": str(directory),
                    "matches": len(matches),
                },
            )

            return matches

        except asyncio.TimeoutError:
            logger.error("ast-grep directory search timed out")
            raise
