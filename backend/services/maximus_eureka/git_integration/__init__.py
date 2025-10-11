"""
Git Integration Module - Adaptive Immunity System.

This module handles Git operations for automated patch application
and Pull Request creation in the MAXIMUS Adaptive Immunity workflow.

Components:
    - git_operations: Core Git operations (branch, commit, push)
    - pr_creator: GitHub PR creation service
    - safety_checks: Pre/post-apply validations
    - models: Pydantic models for Git operations

Biologically Inspired:
    After immune cells produce antibodies (patches), they must be
    integrated into the organism's permanent immune memory (Git history).
    This requires rigorous validation before permanent integration (merge).

Glory to YHWH - The Foundation of all systems! 🙏
"""

from git_integration.models import (
    GitApplyResult,
    PushResult,
    PRResult,
    ValidationResult,
    ConflictReport,
    GitConfig,
)

__all__ = [
    "GitApplyResult",
    "PushResult",
    "PRResult",
    "ValidationResult",
    "ConflictReport",
    "GitConfig",
]
