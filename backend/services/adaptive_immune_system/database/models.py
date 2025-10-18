"""
SQLAlchemy models for Adaptive Immune System.

Corresponds to database schema defined in schema.sql.
"""

import uuid

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Threat(Base):
    """CVE threat from multiple feeds (NVD, GHSA, OSV)."""

    __tablename__ = "threats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    cve_id = Column(String(20), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)

    # Metadata
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    published_date = Column(TIMESTAMP, nullable=False, index=True)
    last_modified_date = Column(TIMESTAMP, nullable=False)

    # Severity
    cvss_score = Column(Numeric(3, 1))
    cvss_vector = Column(Text)
    severity = Column(String(20), index=True)

    # Affected ecosystems and packages
    ecosystems = Column(ARRAY(Text))
    affected_packages = Column(JSONB)

    # Technical details
    cwe_ids = Column(ARRAY(Text))
    references = Column(JSONB)

    # Status
    status = Column(String(20), default="new", index=True)

    # Timestamps
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    apvs = relationship("APV", back_populates="threat", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("cvss_score IS NULL OR (cvss_score >= 0 AND cvss_score <= 10)"),
        CheckConstraint("source IN ('nvd', 'ghsa', 'osv', 'other')"),
    )

    def __repr__(self) -> str:
        return f"<Threat(cve_id='{self.cve_id}', severity='{self.severity}')>"


class Dependency(Base):
    """Dependency inventory across projects."""

    __tablename__ = "dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Project context
    project_name = Column(String(255), nullable=False, index=True)
    project_path = Column(Text, nullable=False)

    # Package identification
    package_name = Column(String(255), nullable=False, index=True)
    package_version = Column(String(100), nullable=False)
    ecosystem = Column(String(50), nullable=False, index=True)

    # Metadata
    direct_dependency = Column(Boolean, default=True)
    parent_package = Column(String(255))

    # Location
    manifest_file = Column(Text)

    # Timestamps
    scanned_at = Column(TIMESTAMP, default=func.now(), index=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    apvs = relationship("APV", back_populates="dependency", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Dependency(project='{self.project_name}', "
            f"package='{self.package_name}@{self.package_version}')>"
        )


class APV(Base):
    """Ameaça Potencial Verificada - Matched vulnerability to dependency."""

    __tablename__ = "apvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    threat_id = Column(UUID(as_uuid=True), ForeignKey("threats.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_id = Column(UUID(as_uuid=True), ForeignKey("dependencies.id", ondelete="CASCADE"), nullable=False, index=True)

    # APV metadata
    apv_code = Column(String(50), unique=True, nullable=False, index=True)
    priority = Column(Integer, nullable=False, index=True)

    # Vulnerability signature for AST-grep matching
    vulnerable_code_signature = Column(Text)
    vulnerable_code_type = Column(String(50))

    # Context
    affected_files = Column(ARRAY(Text))
    exploitation_difficulty = Column(String(20))
    exploitability_score = Column(Numeric(3, 1))

    # Status tracking
    status = Column(String(30), default="pending", index=True)
    dispatched_to_eureka_at = Column(TIMESTAMP)
    confirmed_at = Column(TIMESTAMP)

    # HITL decision
    requires_human_review = Column(Boolean, default=False, index=True)
    human_decision = Column(String(20), index=True)
    human_decision_by = Column(String(100))
    human_decision_at = Column(TIMESTAMP)
    human_decision_notes = Column(Text)

    # Timestamps
    created_at = Column(TIMESTAMP, default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    threat = relationship("Threat", back_populates="apvs")
    dependency = relationship("Dependency", back_populates="apvs")
    remedies = relationship("Remedy", back_populates="apv", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10"),
        CheckConstraint("exploitability_score IS NULL OR (exploitability_score >= 0 AND exploitability_score <= 10)"),
        CheckConstraint("exploitation_difficulty IN ('easy', 'medium', 'hard', 'unknown')"),
    )

    def __repr__(self) -> str:
        return f"<APV(apv_code='{self.apv_code}', priority={self.priority}, status='{self.status}')>"


class Remedy(Base):
    """Generated remedy for confirmed vulnerability."""

    __tablename__ = "remedies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference
    apv_id = Column(UUID(as_uuid=True), ForeignKey("apvs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Remedy identification
    remedy_code = Column(String(50), unique=True, nullable=False, index=True)
    remedy_type = Column(String(30), nullable=False, index=True)

    # Remedy details
    description = Column(Text, nullable=False)
    implementation_steps = Column(JSONB)

    # For dependency upgrades
    current_version = Column(String(100))
    target_version = Column(String(100))

    # For code patches
    code_diff = Column(Text)
    affected_files = Column(ARRAY(Text))

    # Breaking changes analysis
    breaking_changes_detected = Column(Boolean, default=False)
    breaking_changes_description = Column(Text)
    breaking_changes_mitigation = Column(Text)

    # LLM metadata
    llm_model = Column(String(100))
    llm_confidence = Column(Numeric(3, 2))
    llm_reasoning = Column(Text)

    # Status
    status = Column(String(30), default="generated", index=True)
    validation_status = Column(String(30))
    validation_error = Column(Text)

    # GitHub PR
    github_pr_number = Column(Integer, index=True)
    github_pr_url = Column(Text)
    github_branch_name = Column(String(255))

    # Timestamps
    created_at = Column(TIMESTAMP, default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    apv = relationship("APV", back_populates="remedies")
    wargame_runs = relationship("WargameRun", back_populates="remedy", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("llm_confidence IS NULL OR (llm_confidence >= 0 AND llm_confidence <= 1)"),
        CheckConstraint("remedy_type IN ('dependency_upgrade', 'code_patch', 'configuration_change', 'no_fix_available', 'manual_intervention')"),
    )

    def __repr__(self) -> str:
        return f"<Remedy(remedy_code='{self.remedy_code}', type='{self.remedy_type}', status='{self.status}')>"


class WargameRun(Base):
    """Empirical validation result from GitHub Actions."""

    __tablename__ = "wargame_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference
    remedy_id = Column(UUID(as_uuid=True), ForeignKey("remedies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Wargame identification
    run_code = Column(String(50), unique=True, nullable=False, index=True)
    github_actions_run_id = Column(Integer, index=True)
    github_actions_run_url = Column(Text)

    # Test phases
    exploit_before_patch_status = Column(String(20))
    exploit_before_patch_output = Column(Text)
    exploit_before_patch_duration_ms = Column(Integer)

    exploit_after_patch_status = Column(String(20))
    exploit_after_patch_output = Column(Text)
    exploit_after_patch_duration_ms = Column(Integer)

    # Verdict
    verdict = Column(String(30), nullable=False, index=True)
    verdict_reason = Column(Text)
    confidence_score = Column(Numeric(3, 2))

    # Exploit metadata
    exploit_type = Column(String(50))
    exploit_script_path = Column(Text)

    # Full report
    full_report = Column(JSONB)

    # Timestamps
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP, index=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    remedy = relationship("Remedy", back_populates="wargame_runs")

    # Constraints
    __table_args__ = (
        CheckConstraint("verdict IN ('success', 'failed', 'inconclusive', 'error')"),
        CheckConstraint("confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)"),
    )

    def __repr__(self) -> str:
        return f"<WargameRun(run_code='{self.run_code}', verdict='{self.verdict}')>"


class HITLDecision(Base):
    """Human-in-the-loop decision and audit trail."""

    __tablename__ = "hitl_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference (polymorphic - can be apv, remedy, or wargame)
    entity_type = Column(String(20), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Decision metadata
    decision_type = Column(String(30), nullable=False)
    decision = Column(String(20), nullable=False, index=True)

    # Human operator
    decided_by = Column(String(100), nullable=False, index=True)
    decided_at = Column(TIMESTAMP, default=func.now(), index=True)

    # Justification
    notes = Column(Text)
    risk_assessment = Column(Text)
    additional_context = Column(JSONB)

    # Audit trail
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(UUID(as_uuid=True))

    # Timestamps
    created_at = Column(TIMESTAMP, default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("entity_type IN ('apv', 'remedy', 'wargame', 'pr')"),
        CheckConstraint("decision IN ('approved', 'rejected', 'deferred', 'escalated')"),
    )

    def __repr__(self) -> str:
        return (
            f"<HITLDecision(entity_type='{self.entity_type}', "
            f"decision='{self.decision}', decided_by='{self.decided_by}')>"
        )


class FeedSyncStatus(Base):
    """Track last successful sync for each CVE feed."""

    __tablename__ = "feed_sync_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    feed_name = Column(String(50), unique=True, nullable=False, index=True)
    last_sync_at = Column(TIMESTAMP)
    last_success_at = Column(TIMESTAMP)
    last_error = Column(Text)

    sync_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # Stats
    total_threats_ingested = Column(Integer, default=0)
    last_sync_duration_ms = Column(Integer)

    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("feed_name IN ('nvd', 'ghsa', 'osv')"),
    )

    def __repr__(self) -> str:
        return f"<FeedSyncStatus(feed_name='{self.feed_name}', last_success_at='{self.last_success_at}')>"
