"""
Pydantic models for APV (Ameaça Potencial Verificada).

APV represents a matched vulnerability to a dependency in our codebase.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class APVBase(BaseModel):
    """Base APV model with common fields."""

    priority: int = Field(
        ..., ge=1, le=10, description="Priority level (1=critical, 10=low)"
    )
    vulnerable_code_signature: str | None = Field(
        None, description="Regex or AST pattern for code matching"
    )
    vulnerable_code_type: str | None = Field(
        None, description="Type: 'regex', 'ast-grep', 'semgrep'"
    )
    affected_files: list[str] | None = Field(
        default_factory=list, description="Potential affected files"
    )
    exploitation_difficulty: str | None = Field(
        None, description="Difficulty: 'easy', 'medium', 'hard'"
    )
    exploitability_score: float | None = Field(
        None, ge=0.0, le=10.0, description="Exploitability score 0-10"
    )
    requires_human_review: bool = Field(
        default=False, description="Requires HITL approval"
    )

    @field_validator("vulnerable_code_type")
    @classmethod
    def validate_code_type(cls, v: str | None) -> str | None:
        """Validate vulnerable code type."""
        if v is not None and v not in ("regex", "ast-grep", "semgrep"):
            raise ValueError(
                "vulnerable_code_type must be 'regex', 'ast-grep', or 'semgrep'"
            )
        return v

    @field_validator("exploitation_difficulty")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str | None:
        """Validate exploitation difficulty."""
        if v is not None and v not in ("easy", "medium", "hard", "unknown"):
            raise ValueError(
                "exploitation_difficulty must be 'easy', 'medium', 'hard', or 'unknown'"
            )
        return v


class APVCreate(APVBase):
    """Create APV request model."""

    threat_id: UUID = Field(..., description="Reference to threat (CVE)")
    dependency_id: UUID = Field(..., description="Reference to dependency")
    apv_code: str = Field(
        ..., max_length=50, description="Unique APV code (APV-YYYYMMDD-NNN)"
    )

    @field_validator("apv_code")
    @classmethod
    def validate_apv_code(cls, v: str) -> str:
        """Validate APV code format."""
        if not v.startswith("APV-"):
            raise ValueError("apv_code must start with 'APV-'")
        return v


class APVUpdate(BaseModel):
    """Update APV request model (all fields optional)."""

    priority: int | None = Field(None, ge=1, le=10)
    status: str | None = None
    vulnerable_code_signature: str | None = None
    vulnerable_code_type: str | None = None
    affected_files: list[str] | None = None
    exploitation_difficulty: str | None = None
    exploitability_score: float | None = Field(None, ge=0.0, le=10.0)
    requires_human_review: bool | None = None
    dispatched_to_eureka_at: datetime | None = None
    confirmed_at: datetime | None = None
    human_decision: str | None = None
    human_decision_by: str | None = None
    human_decision_at: datetime | None = None
    human_decision_notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate APV status."""
        valid_statuses = (
            "pending",
            "dispatched",
            "confirmed",
            "false_positive",
            "remediated",
        )
        if v is not None and v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("human_decision")
    @classmethod
    def validate_human_decision(cls, v: str | None) -> str | None:
        """Validate human decision."""
        if v is not None and v not in ("approved", "rejected", "deferred"):
            raise ValueError(
                "human_decision must be 'approved', 'rejected', or 'deferred'"
            )
        return v


class APVModel(APVBase):
    """Complete APV model (for internal use)."""

    id: UUID
    threat_id: UUID
    dependency_id: UUID
    apv_code: str
    status: str = "pending"
    dispatched_to_eureka_at: datetime | None = None
    confirmed_at: datetime | None = None
    human_decision: str | None = None
    human_decision_by: str | None = None
    human_decision_at: datetime | None = None
    human_decision_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class ThreatSummary(BaseModel):
    """Threat summary for APV response."""

    cve_id: str
    title: str
    severity: str | None = None
    cvss_score: float | None = None

    class Config:
        from_attributes = True


class DependencySummary(BaseModel):
    """Dependency summary for APV response."""

    project_name: str
    package_name: str
    package_version: str
    ecosystem: str

    class Config:
        from_attributes = True


class APVResponse(APVModel):
    """API response model for APV (includes related data)."""

    threat: ThreatSummary | None = None
    dependency: DependencySummary | None = None

    class Config:
        from_attributes = True


class APVDispatchMessage(BaseModel):
    """
    RabbitMQ message format for dispatching APV to Eureka.

    This is the contract between Oráculo and Eureka services.
    """

    apv_id: UUID = Field(..., description="APV unique identifier")
    apv_code: str = Field(..., description="APV code (APV-YYYYMMDD-NNN)")
    priority: int = Field(..., ge=1, le=10, description="Priority level")

    # Threat information
    cve_id: str = Field(..., description="CVE identifier")
    cve_title: str = Field(..., description="CVE title")
    cve_description: str = Field(..., description="CVE description")
    cvss_score: float | None = Field(None, description="CVSS score")
    severity: str | None = Field(None, description="Severity level")

    # Dependency information
    project_name: str = Field(..., description="Project name")
    package_name: str = Field(..., description="Package name")
    package_version: str = Field(..., description="Package version")
    ecosystem: str = Field(..., description="Package ecosystem (npm, pypi, etc.)")

    # Vulnerability signature for confirmation
    vulnerable_code_signature: str | None = Field(
        None, description="Code pattern to search for"
    )
    vulnerable_code_type: str | None = Field(
        None, description="Pattern type (regex, ast-grep)"
    )
    affected_files: list[str] = Field(
        default_factory=list, description="Potential affected files"
    )

    # Exploitation metadata
    exploitation_difficulty: str | None = Field(None, description="Difficulty level")
    exploitability_score: float | None = Field(None, description="Exploitability score")

    # Timestamps
    dispatched_at: datetime = Field(
        default_factory=datetime.utcnow, description="Dispatch timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "apv_id": "550e8400-e29b-41d4-a716-446655440000",
                "apv_code": "APV-20251013-001",
                "priority": 2,
                "cve_id": "CVE-2021-44228",
                "cve_title": "Apache Log4j2 Remote Code Execution",
                "cve_description": "Apache Log4j2 <=2.14.1 JNDI features do not protect against attacker controlled LDAP...",
                "cvss_score": 10.0,
                "severity": "critical",
                "project_name": "backend-api",
                "package_name": "log4j-core",
                "package_version": "2.14.0",
                "ecosystem": "maven",
                "vulnerable_code_signature": "\\$\\{jndi:",
                "vulnerable_code_type": "regex",
                "affected_files": ["src/main/java/com/example/Logger.java"],
                "exploitation_difficulty": "easy",
                "exploitability_score": 9.8,
                "dispatched_at": "2025-10-13T14:30:00Z",
            }
        }


class APVStatusUpdate(BaseModel):
    """
    RabbitMQ message format for status updates from Eureka → Oráculo.
    """

    apv_id: UUID = Field(..., description="APV unique identifier")
    apv_code: str = Field(..., description="APV code")
    status: str = Field(..., description="New status")
    confirmed: bool = Field(
        default=False, description="Vulnerability confirmed by AST scan"
    )
    confirmation_details: dict | None = Field(None, description="AST scan results")
    updated_by: str = Field(default="eureka", description="Service that updated status")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status."""
        valid_statuses = (
            "received",
            "scanning",
            "confirmed",
            "false_positive",
            "error",
        )
        if v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v
