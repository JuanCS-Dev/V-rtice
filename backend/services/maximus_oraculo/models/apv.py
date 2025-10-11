"""APV (Actionable Prioritized Vulnerability) Pydantic models.

This module defines the core data structures for the MAXIMUS Adaptive Immunity
System. APV extends CVE JSON 5.1.1 schema with actionable fields for automated
remediation.

Theoretical Foundation:
- OSV Schema (ossf.github.io/osv-schema)
- CVE JSON 5.1.1 (github.com/CVEProject/cve-schema)
- APPATCH methodology (automated program patching)

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator, computed_field


class PriorityLevel(str, Enum):
    """
    Priority levels for APV triage.
    
    Based on CVSS score + MAXIMUS context (affected services, exploitability).
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RemediationStrategy(str, Enum):
    """
    Available remediation strategies.
    
    Strategy selection based on:
    - Availability of fixed version (dependency_upgrade)
    - Code pattern detectability (code_patch)
    - Zero-day status (coagulation_waf)
    - Complexity threshold (manual_review)
    """
    DEPENDENCY_UPGRADE = "dependency_upgrade"
    CODE_PATCH = "code_patch"
    COAGULATION_WAF = "coagulation_waf"
    MANUAL_REVIEW = "manual_review"


class RemediationComplexity(str, Enum):
    """Estimated complexity of remediation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CVSSScore(BaseModel):
    """
    CVSS (Common Vulnerability Scoring System) score.
    
    Normalized representation supporting CVSS 3.1 and 4.0.
    """
    version: str = Field(..., description="CVSS version (3.1, 4.0)")
    base_score: float = Field(..., ge=0.0, le=10.0, description="Base score (0.0-10.0)")
    severity: str = Field(..., description="Severity: NONE, LOW, MEDIUM, HIGH, CRITICAL")
    vector_string: str = Field(..., description="CVSS vector string")
    
    # Optional detailed metrics
    exploitability_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    impact_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v.upper() not in valid:
            raise ValueError(f"Severity must be one of {valid}, got {v}")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "3.1",
                "base_score": 9.8,
                "severity": "CRITICAL",
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "exploitability_score": 3.9,
                "impact_score": 5.9
            }
        }


class ASTGrepPattern(BaseModel):
    """
    ast-grep pattern for deterministic vulnerability confirmation.
    
    Used by Eureka to scan codebase and confirm vulnerability presence.
    """
    language: str = Field(default="python", description="Target language")
    pattern: str = Field(..., description="ast-grep pattern string")
    severity: str = Field(..., description="Match severity")
    description: Optional[str] = Field(None, description="Pattern explanation")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate supported languages."""
        supported = ['python', 'javascript', 'typescript', 'go', 'rust', 'java']
        if v.lower() not in supported:
            raise ValueError(f"Language {v} not in supported: {supported}")
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "python",
                "pattern": "eval($ARG)",
                "severity": "critical",
                "description": "Detects dangerous eval() usage"
            }
        }


class AffectedPackage(BaseModel):
    """
    Package affected by vulnerability.
    
    Tracks ecosystem, name, affected versions, and fixed versions.
    """
    ecosystem: str = Field(..., description="Package ecosystem")
    name: str = Field(..., description="Package name")
    affected_versions: List[str] = Field(..., description="Affected version ranges")
    fixed_versions: List[str] = Field(default_factory=list, description="Fixed versions")
    
    # Optional fields
    purl: Optional[str] = Field(None, description="Package URL (purl)")
    introduced: Optional[str] = Field(None, description="Version where vuln was introduced")
    last_affected: Optional[str] = Field(None, description="Last affected version")
    
    @field_validator('ecosystem')
    @classmethod
    def validate_ecosystem(cls, v: str) -> str:
        """Validate ecosystem."""
        valid = ['PyPI', 'npm', 'Go', 'Maven', 'Docker', 'RubyGems', 'NuGet', 'Cargo']
        if v not in valid:
            raise ValueError(f"Ecosystem must be one of {valid}, got {v}")
        return v
    
    @computed_field
    @property
    def has_fix(self) -> bool:
        """Check if fixed version is available."""
        return len(self.fixed_versions) > 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "ecosystem": "PyPI",
                "name": "django",
                "affected_versions": [">=3.0,<4.2.8"],
                "fixed_versions": ["4.2.8", "5.0.0"],
                "purl": "pkg:pypi/django"
            }
        }


class APV(BaseModel):
    """
    Actionable Prioritized Vulnerability (APV).
    
    Core data structure for MAXIMUS Adaptive Immunity System.
    Extends CVE JSON 5.1.1 with actionable remediation fields.
    
    Flow:
    1. Oráculo ingests CVE from threat feeds (OSV.dev, NVD)
    2. Oráculo enriches with CVSS, CWE, signatures
    3. Oráculo filters by relevance (dependency graph)
    4. Oráculo generates APV object
    5. APV published to Kafka
    6. Eureka consumes and remediates
    
    Theoretical Foundation:
    - IIT (Integrated Information Theory): APV as integrated information unit
    - GWT (Global Workspace Theory): APV broadcast for distributed remediation
    - Biological analogy: APV as "antigen presentation" to immune T-cells (Eureka)
    """
    
    # ==================== IDENTIFICATION ====================
    
    cve_id: str = Field(..., description="CVE identifier (e.g., CVE-2024-12345)")
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative identifiers (GHSA, OSV, etc.)"
    )
    
    # ==================== TEMPORAL METADATA ====================
    
    published: datetime = Field(..., description="Original publication date")
    modified: datetime = Field(..., description="Last modification date")
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Oráculo processing timestamp"
    )
    
    # ==================== DESCRIPTION ====================
    
    summary: str = Field(..., min_length=10, description="Executive summary")
    details: str = Field(..., min_length=20, description="Technical description")
    
    # ==================== SEVERITY & PRIORITY ====================
    
    cvss: Optional[CVSSScore] = Field(None, description="CVSS score")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="MAXIMUS calculated priority")
    
    # ==================== AFFECTED PACKAGES ====================
    
    affected_packages: List[AffectedPackage] = Field(
        ...,
        min_length=1,
        description="Affected packages and versions"
    )
    
    # ==================== CONFIRMATION ====================
    
    ast_grep_patterns: List[ASTGrepPattern] = Field(
        default_factory=list,
        description="Patterns for deterministic confirmation"
    )
    
    # ==================== REMEDIATION ====================
    
    recommended_strategy: RemediationStrategy = Field(
        default=RemediationStrategy.MANUAL_REVIEW,
        description="Recommended remediation strategy"
    )
    remediation_complexity: RemediationComplexity = Field(
        default=RemediationComplexity.MEDIUM,
        description="Estimated remediation complexity"
    )
    remediation_notes: Optional[str] = Field(
        None,
        description="Additional remediation guidance"
    )
    
    # ==================== MAXIMUS CONTEXT ====================
    
    maximus_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="MAXIMUS-specific context for decision making"
    )
    
    # ==================== SOURCE TRACKING ====================
    
    source_feed: str = Field(..., description="Threat feed source")
    oraculo_version: str = Field(default="1.0.0", description="Oráculo version")
    
    # ==================== VALIDATORS ====================
    
    @field_validator('priority', mode='before')
    @classmethod
    def calculate_priority(cls, v: Optional[str], info) -> str:
        """
        Calculate priority if not explicitly set.
        
        Priority calculation algorithm:
        1. CVSS >= 9.0 + public exploits → CRITICAL
        2. CVSS >= 7.0 + affected_services > 3 → HIGH
        3. CVSS >= 4.0 → MEDIUM
        4. Else → LOW
        
        Args:
            v: Priority value (if already set)
            info: Validation context with other fields
            
        Returns:
            PriorityLevel value
        """
        if v:  # Already set manually
            return v
        
        data = info.data
        cvss = data.get('cvss')
        
        if not cvss:
            return PriorityLevel.LOW
        
        score = cvss.base_score
        context = data.get('maximus_context', {})
        affected_count = len(context.get('affected_services', []))
        has_exploit = context.get('exploit_available', False)
        
        # Priority logic
        if score >= 9.0 and has_exploit:
            return PriorityLevel.CRITICAL
        elif score >= 9.0:
            return PriorityLevel.CRITICAL
        elif score >= 7.0 and affected_count > 3:
            return PriorityLevel.HIGH
        elif score >= 7.0:
            return PriorityLevel.HIGH
        elif score >= 4.0:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    @field_validator('recommended_strategy', mode='before')
    @classmethod
    def calculate_strategy(cls, v: Optional[str], info) -> str:
        """
        Calculate recommended remediation strategy if not set.
        
        Strategy selection algorithm:
        1. Has fixed version available → DEPENDENCY_UPGRADE
        2. Has ast-grep pattern + LLM confidence → CODE_PATCH
        3. Zero-day without fix → COAGULATION_WAF
        4. Complexity CRITICAL → MANUAL_REVIEW
        
        Args:
            v: Strategy value (if already set)
            info: Validation context
            
        Returns:
            RemediationStrategy value
        """
        if v:  # Already set
            return v
        
        data = info.data
        complexity = data.get('remediation_complexity', 'MEDIUM')
        affected = data.get('affected_packages', [])
        patterns = data.get('ast_grep_patterns', [])
        
        # Critical complexity requires manual review
        if complexity == 'CRITICAL':
            return RemediationStrategy.MANUAL_REVIEW
        
        # Check if any package has a fixed version
        has_fixed = any(pkg.has_fix for pkg in affected if hasattr(pkg, 'has_fix'))
        if has_fixed:
            return RemediationStrategy.DEPENDENCY_UPGRADE
        
        # If has patterns, try code patch
        if patterns:
            return RemediationStrategy.CODE_PATCH
        
        # Fallback: WAF rule
        return RemediationStrategy.COAGULATION_WAF
    
    @field_validator('remediation_complexity', mode='before')
    @classmethod
    def calculate_complexity(cls, v: Optional[str], info) -> str:
        """
        Calculate remediation complexity if not set.
        
        Complexity factors:
        - Breaking changes in upgrade: HIGH
        - Multiple affected packages: MEDIUM
        - Single package upgrade: LOW
        - Zero-day without pattern: CRITICAL
        
        Args:
            v: Complexity value (if already set)
            info: Validation context
            
        Returns:
            RemediationComplexity value
        """
        if v:
            return v
        
        data = info.data
        affected = data.get('affected_packages', [])
        context = data.get('maximus_context', {})
        patterns = data.get('ast_grep_patterns', [])
        
        # Multiple packages = higher complexity
        if len(affected) > 3:
            return RemediationComplexity.HIGH
        elif len(affected) > 1:
            return RemediationComplexity.MEDIUM
        
        # Breaking changes flag
        if context.get('breaking_changes_likely', False):
            return RemediationComplexity.HIGH
        
        # Zero-day without pattern
        has_fix = any(pkg.has_fix for pkg in affected if hasattr(pkg, 'has_fix'))
        if not has_fix and not patterns:
            return RemediationComplexity.CRITICAL
        
        # Default: simple single package upgrade
        return RemediationComplexity.LOW
    
    # ==================== COMPUTED FIELDS ====================
    
    @computed_field
    @property
    def is_critical(self) -> bool:
        """Check if vulnerability is critical priority."""
        return self.priority == PriorityLevel.CRITICAL
    
    @computed_field
    @property
    def requires_immediate_action(self) -> bool:
        """Check if requires immediate remediation (CRITICAL or HIGH)."""
        return self.priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]
    
    @computed_field
    @property
    def has_automated_fix(self) -> bool:
        """Check if automated fix is possible."""
        return self.recommended_strategy in [
            RemediationStrategy.DEPENDENCY_UPGRADE,
            RemediationStrategy.CODE_PATCH
        ]
    
    @computed_field
    @property
    def affected_services(self) -> List[str]:
        """Extract affected services from context."""
        return self.maximus_context.get('affected_services', [])
    
    # ==================== METHODS ====================
    
    def to_kafka_message(self) -> Dict[str, Any]:
        """
        Serialize APV for Kafka publishing.
        
        Returns:
            Dict suitable for Kafka JSON serialization
        """
        return self.model_dump(mode='json')
    
    def to_database_record(self) -> Dict[str, Any]:
        """
        Prepare APV for PostgreSQL insertion.
        
        Returns:
            Dict with JSONB-compatible structure
        """
        return {
            'cve_id': self.cve_id,
            'raw_vulnerability': {},  # Populated by Oráculo
            'enriched_vulnerability': self.model_dump(
                include={'cvss', 'ast_grep_patterns', 'affected_packages'}
            ),
            'apv_object': self.model_dump(mode='json'),
            'priority': self.priority.value,
            'source_feed': self.source_feed,
            'oraculo_version': self.oraculo_version,
            'affected_services': self.affected_services,
            'remediation_strategy': self.recommended_strategy.value
        }
    
    class Config:
        json_schema_extra = {
            "example": {
                "cve_id": "CVE-2024-12345",
                "aliases": ["GHSA-xxxx-yyyy-zzzz", "OSV-2024-1234"],
                "published": "2024-10-01T00:00:00Z",
                "modified": "2024-10-05T12:00:00Z",
                "summary": "SQL Injection in Django ORM raw() method",
                "details": "Django versions < 4.2.8 are vulnerable to SQL injection when using Model.objects.raw() with user-controlled input...",
                "cvss": {
                    "version": "3.1",
                    "base_score": 9.8,
                    "severity": "CRITICAL",
                    "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                },
                "priority": "critical",
                "affected_packages": [{
                    "ecosystem": "PyPI",
                    "name": "django",
                    "affected_versions": [">=3.0,<4.2.8"],
                    "fixed_versions": ["4.2.8", "5.0.0"]
                }],
                "ast_grep_patterns": [{
                    "language": "python",
                    "pattern": "Model.objects.raw($QUERY)",
                    "severity": "critical"
                }],
                "recommended_strategy": "dependency_upgrade",
                "remediation_complexity": "low",
                "maximus_context": {
                    "affected_services": ["maximus_core_service", "maximus_api_gateway"],
                    "deployment_impact": "medium",
                    "rollback_available": True,
                    "exploit_available": False
                },
                "source_feed": "OSV.dev",
                "oraculo_version": "1.0.0"
            }
        }


# Type alias for convenience
ActionablePrioritizedVulnerability = APV
