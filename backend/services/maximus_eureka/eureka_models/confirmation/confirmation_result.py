"""
Confirmation Result Models - MAXIMUS Eureka Adaptive Immunity.

Structured representations of vulnerability confirmation outcomes.
Links CVE metadata to concrete code locations where vulnerabilities exist.

Architectural Role:
    These models form the contract between confirmation and remediation phases.
    ConfirmationResult carries evidence required for informed remediation strategy
    selection, enabling context-aware patch generation.

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Source of all wisdom
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ConfirmationStatus(str, Enum):
    """
    Status of vulnerability confirmation attempt.
    
    Epistemic states reflecting confidence in vulnerability presence:
        - CONFIRMED: High-confidence evidence via ast-grep pattern match
        - FALSE_POSITIVE: CVE referenced but pattern not found in code
        - ERROR: Confirmation process failed (infrastructure/tooling issue)
        - PENDING: Confirmation queued but not yet executed
    """

    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    ERROR = "error"
    PENDING = "pending"


class VulnerableLocation(BaseModel):
    """
    Precise code location where vulnerability pattern was detected.
    
    Provides surgical targeting for remediation strategies, avoiding
    broad-spectrum changes that risk introducing regressions.
    
    Attributes:
        file_path: Absolute path to vulnerable file
        line_start: First line of vulnerable code block
        line_end: Last line of vulnerable code block
        code_snippet: Matched code (max 500 chars for context)
        pattern_matched: ast-grep pattern that matched
        confidence_score: Match confidence 0.0-1.0 (1.0 = exact match)
    """

    model_config = ConfigDict(frozen=True)

    file_path: Path = Field(
        ...,
        description="Absolute filesystem path to vulnerable file",
    )
    line_start: int = Field(
        ...,
        ge=1,
        description="Starting line number of vulnerable code",
    )
    line_end: int = Field(
        ...,
        ge=1,
        description="Ending line number of vulnerable code",
    )
    code_snippet: str = Field(
        ...,
        max_length=500,
        description="Vulnerable code excerpt for context",
    )
    pattern_matched: str = Field(
        ...,
        description="ast-grep pattern that matched this location",
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in match accuracy (1.0 = exact)",
    )


class ConfirmationMetadata(BaseModel):
    """
    Metadata about confirmation process execution.
    
    Enables observability, debugging, and continuous improvement of
    confirmation accuracy through pattern refinement.
    
    Attributes:
        confirmed_at: Timestamp of confirmation completion
        ast_grep_version: Version of ast-grep used
        patterns_tested: Number of ast-grep patterns attempted
        files_scanned: Number of files analyzed
        execution_time_ms: Time taken for confirmation (milliseconds)
    """

    model_config = ConfigDict(frozen=True)

    confirmed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when confirmation completed",
    )
    ast_grep_version: str = Field(
        default="unknown",
        description="Version of ast-grep CLI tool",
    )
    patterns_tested: int = Field(
        default=0,
        ge=0,
        description="Count of patterns attempted",
    )
    files_scanned: int = Field(
        default=0,
        ge=0,
        description="Count of files analyzed",
    )
    execution_time_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken in milliseconds",
    )


class ConfirmationResult(BaseModel):
    """
    Complete result of vulnerability confirmation process.
    
    Bridges gap between abstract CVE description and concrete code instances.
    Informs remediation strategy selection through status and location data.
    
    Design Philosophy:
        Immutable result object that can be cached, replayed, and audited.
        Contains both positive findings (vulnerable locations) and metadata
        for negative findings (false positives).
    
    Attributes:
        apv_id: ID of APV being confirmed (links to Oráculo APV)
        cve_id: CVE identifier (e.g., "CVE-2024-27351")
        status: Confirmation outcome
        vulnerable_locations: List of confirmed vulnerable code locations
        metadata: Process execution metadata
        error_message: Optional error description if status=ERROR
    
    Example:
        >>> result = ConfirmationResult(
        ...     apv_id="apv-001",
        ...     cve_id="CVE-2024-27351",
        ...     status=ConfirmationStatus.CONFIRMED,
        ...     vulnerable_locations=[
        ...         VulnerableLocation(
        ...             file_path=Path("/app/views.py"),
        ...             line_start=42,
        ...             line_end=45,
        ...             code_snippet="user_input = request.GET['id']",
        ...             pattern_matched="request.GET[$_]",
        ...         )
        ...     ],
        ... )
    """

    model_config = ConfigDict(frozen=True)

    apv_id: str = Field(
        ...,
        description="APV identifier from Oráculo",
    )
    cve_id: str = Field(
        ...,
        pattern=r"^CVE-\d{4}-\d{4,}$",
        description="CVE identifier",
    )
    status: ConfirmationStatus = Field(
        ...,
        description="Confirmation outcome status",
    )
    vulnerable_locations: list[VulnerableLocation] = Field(
        default_factory=list,
        description="List of confirmed vulnerable code locations",
    )
    metadata: ConfirmationMetadata = Field(
        default_factory=ConfirmationMetadata,
        description="Process execution metadata",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if status=ERROR",
    )

    @property
    def is_confirmed(self) -> bool:
        """Check if vulnerability was confirmed in codebase."""
        return self.status == ConfirmationStatus.CONFIRMED

    @property
    def location_count(self) -> int:
        """Count of vulnerable locations found."""
        return len(self.vulnerable_locations)

    @property
    def requires_remediation(self) -> bool:
        """Determine if remediation is required based on confirmation."""
        return self.is_confirmed and self.location_count > 0
