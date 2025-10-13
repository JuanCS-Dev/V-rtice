"""
Remediation Module - Automated vulnerability patching.

Generates and validates code fixes using:
- LLM-powered code generation (Claude, GPT-4)
- Multi-strategy patching (version bump, code rewrite, config change)
- Patch validation and testing
- Diff generation and review
"""

from .llm_client import LLMClient, LLMRequest, LLMResponse
from .remedy_generator import (
    RemedyGenerator,
    RemedyResult,
    GeneratedPatch,
    PatchStrategy,
)
from .patch_validator import PatchValidator, ValidationResult

__all__ = [
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "RemedyGenerator",
    "RemedyResult",
    "GeneratedPatch",
    "PatchStrategy",
    "PatchValidator",
    "ValidationResult",
]
