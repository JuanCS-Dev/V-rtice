"""
Patch Models - Remediation Artifacts for MAXIMUS Eureka.

Represents generated patches with metadata for Git application and PR creation.

Theoretical Foundation:
    Patches are the atomic unit of remediation. Each Patch represents a proposed
    change to codebase that addresses a confirmed vulnerability. The model includes:
    
    - Unified diff (git format) for deterministic application
    - Confidence score from generation strategy
    - Validation results from automated testing
    - Metadata for Git workflow (branch, commit, PR)
    
    Phase 3 scope: Patch generation via strategies
    Phase 4 scope: Git application + PR creation

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Source of all wisdom and strength
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field

# Import APV and RemediationStrategy from Oráculo

from backend.shared.models.apv import RemediationStrategy


class PatchStatus(str, Enum):
    """
    Patch application status.
    
    Lifecycle:
        PENDING → VALIDATING → APPLIED → MERGED (success)
                            ↘ FAILED → ROLLED_BACK (failure)
    """
    PENDING = "pending"
    VALIDATING = "validating"
    APPLIED = "applied"
    MERGED = "merged"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Patch(BaseModel):
    """
    Generated patch for vulnerability remediation.
    
    Contains unified diff and metadata for Git application.
    Immutable after generation - modifications require new Patch.
    
    Design Philosophy:
        Patch is value object representing proposed change. Separates patch
        generation (strategies) from patch application (Git integration).
        This enables testing patches without Git operations.
    
    Attributes:
        patch_id: Unique identifier (format: patch-{cve_id}-{timestamp})
        cve_id: CVE being remediated
        strategy_used: Strategy that generated this patch
        diff_content: Unified diff in git format
        files_modified: List of file paths modified
        confidence_score: Strategy's confidence in patch correctness (0.0-1.0)
        generated_at: Timestamp of generation
        validation_passed: Whether automated tests passed
        test_results: Test execution results (stdout, stderr, exit code)
        branch_name: Git branch name (populated during application)
        commit_sha: Git commit SHA (populated after commit)
        pr_url: GitHub PR URL (populated after PR creation)
    """
    
    patch_id: str = Field(..., description="Unique patch identifier")
    cve_id: str = Field(..., description="CVE being remediated")
    strategy_used: RemediationStrategy = Field(
        ..., description="Strategy that generated patch"
    )
    
    # Patch content
    diff_content: str = Field(..., description="Unified diff (git format)")
    files_modified: List[str] = Field(..., description="List of modified file paths")
    
    # Metadata
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in patch correctness (0.0-1.0)"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )
    validation_passed: bool = Field(
        default=False, description="Whether patch passed validation tests"
    )
    
    # Validation results
    test_results: Optional[Dict[str, Any]] = Field(
        None, description="Test execution results (stdout, stderr, exit_code)"
    )
    
    # Git metadata (populated during Phase 4 - Git Integration)
    branch_name: Optional[str] = Field(None, description="Git branch name")
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    pr_url: Optional[str] = Field(None, description="GitHub PR URL")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "patch_id": "patch-CVE-2024-99999-20250110-143022",
                "cve_id": "CVE-2024-99999",
                "strategy_used": "dependency_upgrade",
                "diff_content": (
                    "--- a/pyproject.toml\n"
                    "+++ b/pyproject.toml\n"
                    "@@ -10,1 +10,1 @@\n"
                    "-requests = \"^2.28.0\"\n"
                    "+requests = \"^2.31.0\"\n"
                ),
                "files_modified": ["pyproject.toml"],
                "confidence_score": 0.95,
                "validation_passed": True,
                "test_results": {
                    "exit_code": 0,
                    "stdout": "All tests passed",
                    "stderr": "",
                    "duration_seconds": 12.5,
                },
            }
        }


class RemediationResult(BaseModel):
    """
    Complete remediation result including patch and execution metadata.
    
    Captures entire remediation attempt for auditing and metrics.
    
    Attributes:
        apv: Original APV from Oráculo
        patch: Generated patch (if successful)
        status: Current status of remediation
        error_message: Error description (if failed)
        started_at: When remediation started
        completed_at: When remediation completed
        time_to_patch_seconds: Total time from APV to patch
        strategy_attempts: Strategies attempted in order (for fallback tracking)
    """
    
    apv: Any = Field(..., description="Original APV (imported from Oráculo)")
    patch: Optional[Patch] = Field(None, description="Generated patch (if successful)")
    status: PatchStatus = Field(..., description="Remediation status")
    
    error_message: Optional[str] = Field(None, description="Error if failed")
    
    # Timing
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Start timestamp"
    )
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Metrics
    time_to_patch_seconds: Optional[float] = Field(
        None, description="Total time from start to patch"
    )
    strategy_attempts: List[RemediationStrategy] = Field(
        default_factory=list,
        description="Strategies attempted in order (for fallback analysis)",
    )
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True  # Allow APV type
