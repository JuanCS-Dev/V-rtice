"""
Eureka Service - Vulnerability Surgeon.

Responsible for:
- APV consumption from Oráculo
- Vulnerability confirmation (static + dynamic analysis)
- Remedy generation (LLM-powered code fixes)
- Pull Request creation (GitHub/GitLab)
- Status callbacks to Oráculo

Components:
- confirmation: Static/dynamic analysis engines, scoring
- remediation: LLM integration, patch generation, validation
- vcs: Version control system integration (GitHub, GitLab)
- callback_client: Status updates back to Oráculo
"""

# Confirmation module
from .confirmation import (
    StaticAnalyzer,
    StaticAnalysisResult,
    StaticFinding,
    DynamicAnalyzer,
    DynamicAnalysisResult,
    DynamicTest,
    ConfirmationEngine,
    ConfirmationResult,
)

# Remediation module
from .remediation import (
    LLMClient,
    LLMRequest,
    LLMResponse,
    RemedyGenerator,
    RemedyResult,
    GeneratedPatch,
    PatchStrategy,
    PatchValidator,
    ValidationResult,
)

# VCS module
from .vcs import (
    GitHubClient,
    GitHubRepository,
    PullRequest,
    PRDescriptionGenerator,
    PRDescriptionContext,
)

# Callback client
from .callback_client import CallbackClient, APVStatusUpdate

# Orchestrator
from .eureka_orchestrator import EurekaOrchestrator, EurekaConfig

__all__ = [
    # Confirmation
    "StaticAnalyzer",
    "StaticAnalysisResult",
    "StaticFinding",
    "DynamicAnalyzer",
    "DynamicAnalysisResult",
    "DynamicTest",
    "ConfirmationEngine",
    "ConfirmationResult",
    # Remediation
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "RemedyGenerator",
    "RemedyResult",
    "GeneratedPatch",
    "PatchStrategy",
    "PatchValidator",
    "ValidationResult",
    # VCS
    "GitHubClient",
    "GitHubRepository",
    "PullRequest",
    "PRDescriptionGenerator",
    "PRDescriptionContext",
    # Callbacks
    "CallbackClient",
    "APVStatusUpdate",
    # Orchestrator
    "EurekaOrchestrator",
    "EurekaConfig",
]
