"""
SQLAlchemy Database Models for Cognitive Defense System.

Persistent storage for analysis history, source reputation tracking,
fact-check caching, and Bayesian belief updates.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================


class AnalysisStatusEnum(str, enum.Enum):
    """Analysis processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionTakenEnum(str, enum.Enum):
    """Actions taken on content."""

    ALLOWED = "allowed"
    FLAGGED = "flagged"
    WARNED = "warned"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"


# ============================================================================
# CORE TABLES
# ============================================================================


class AnalysisHistory(Base):
    """Historical record of all analyses performed."""

    __tablename__ = "analysis_history"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Input
    text_hash = Column(String(64), nullable=False, index=True)  # SHA256 for deduplication
    text = Column(Text, nullable=False)
    source_url = Column(String(2048), nullable=True)
    source_domain = Column(String(255), nullable=True, index=True)

    # Status
    status = Column(SQLEnum(AnalysisStatusEnum), default=AnalysisStatusEnum.PENDING, nullable=False)

    # Results
    threat_score = Column(Float, nullable=True)
    severity = Column(String(20), nullable=True)  # ManipulationSeverity
    recommended_action = Column(SQLEnum(ActionTakenEnum), nullable=True)
    confidence = Column(Float, nullable=True)

    # Module Scores
    credibility_score = Column(Float, nullable=True)
    emotional_score = Column(Float, nullable=True)
    logical_score = Column(Float, nullable=True)
    reality_score = Column(Float, nullable=True)

    # Full Report (JSONB for querying)
    report_json = Column(JSON, nullable=True)

    # Performance Metrics
    processing_time_ms = Column(Float, nullable=True)
    tier2_used = Column(Boolean, default=False)
    models_used = Column(ARRAY(String), nullable=True)

    # Relationships
    source_reputation_id = Column(UUID(as_uuid=True), ForeignKey("source_reputation.id"), nullable=True)
    source_reputation = relationship("SourceReputation", back_populates="analyses")

    # Constraints
    __table_args__ = (
        CheckConstraint("threat_score >= 0 AND threat_score <= 1", name="check_threat_score_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
        Index("idx_analysis_source_domain_created", "source_domain", "created_at"),
        Index("idx_analysis_threat_score", "threat_score"),
    )


class SourceReputation(Base):
    """Dynamic source credibility tracking with Bayesian updates."""

    __tablename__ = "source_reputation"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source Identification
    domain = Column(String(255), unique=True, nullable=False, index=True)
    domain_fingerprint = Column(String(128), nullable=True)  # MinHash LSH

    # NewsGuard Data
    newsguard_score = Column(Float, nullable=True)
    newsguard_rating = Column(String(50), nullable=True)
    newsguard_last_updated = Column(DateTime, nullable=True)
    newsguard_nutrition_label = Column(JSON, nullable=True)

    # Bayesian Credibility
    prior_credibility = Column(Float, default=0.5, nullable=False)
    posterior_credibility = Column(Float, default=0.5, nullable=False)
    alpha = Column(Float, default=1.0, nullable=False)  # Beta distribution parameter
    beta = Column(Float, default=1.0, nullable=False)  # Beta distribution parameter

    # Historical Statistics
    total_analyses = Column(Integer, default=0, nullable=False)
    false_content_count = Column(Integer, default=0, nullable=False)
    true_content_count = Column(Integer, default=0, nullable=False)
    last_false_content_date = Column(DateTime, nullable=True)

    # Domain Hopping Detection
    similar_domains = Column(ARRAY(String), nullable=True)
    cluster_id = Column(String(64), nullable=True, index=True)  # LSH cluster

    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_analyzed = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analyses = relationship("AnalysisHistory", back_populates="source_reputation")
    fact_checks = relationship("FactCheckCache", back_populates="source_reputation")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "prior_credibility >= 0 AND prior_credibility <= 1",
            name="check_prior_range",
        ),
        CheckConstraint(
            "posterior_credibility >= 0 AND posterior_credibility <= 1",
            name="check_posterior_range",
        ),
        CheckConstraint("alpha > 0", name="check_alpha_positive"),
        CheckConstraint("beta > 0", name="check_beta_positive"),
        Index("idx_source_posterior_credibility", "posterior_credibility"),
    )


class FactCheckCache(Base):
    """Cache for external fact-checking API results."""

    __tablename__ = "fact_check_cache"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Claim Identification
    claim_text_hash = Column(String(64), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)

    # Verification Result
    verification_status = Column(String(20), nullable=False)  # VerificationStatus
    confidence = Column(Float, nullable=False)

    # Source Attribution
    source_api = Column(String(50), nullable=False)  # 'google_factcheck', 'claimbuster', 'kg_sparql'
    source_url = Column(String(2048), nullable=True)
    rating_text = Column(String(255), nullable=True)

    # Full API Response
    api_response_json = Column(JSON, nullable=True)

    # Cache Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    source_reputation_id = Column(UUID(as_uuid=True), ForeignKey("source_reputation.id"), nullable=True)
    source_reputation = relationship("SourceReputation", back_populates="fact_checks")

    # Constraints
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_fc_confidence_range"),
        Index("idx_factcheck_claim_hash", "claim_text_hash"),
        Index("idx_factcheck_expires", "expires_at"),
    )


class EntityCache(Base):
    """Cache for entity linking results (DBpedia Spotlight)."""

    __tablename__ = "entity_cache"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Entity Identification
    surface_form = Column(String(255), nullable=False, index=True)
    context_hash = Column(String(64), nullable=False, index=True)  # Context for disambiguation

    # Linked Entity
    entity_uri = Column(String(512), nullable=False)
    entity_types = Column(ARRAY(String), nullable=True)
    confidence = Column(Float, nullable=False)
    support = Column(Integer, default=0)

    # Wikidata/DBpedia Metadata
    wikidata_id = Column(String(20), nullable=True)
    dbpedia_abstract = Column(Text, nullable=True)
    entity_metadata = Column(JSON, nullable=True)

    # Cache Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)

    # Constraints
    __table_args__ = (Index("idx_entity_surface_context", "surface_form", "context_hash", unique=True),)


class PropagandaPattern(Base):
    """Learned propaganda patterns for model improvement."""

    __tablename__ = "propaganda_patterns"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Pattern
    technique = Column(String(50), nullable=False, index=True)  # PropagandaTechnique
    pattern_text = Column(Text, nullable=False)
    pattern_embedding = Column(ARRAY(Float), nullable=True)  # 768-dim sentence embedding

    # Statistics
    occurrence_count = Column(Integer, default=1, nullable=False)
    false_positive_count = Column(Integer, default=0, nullable=False)
    precision = Column(Float, nullable=True)

    # Context
    typical_contexts = Column(ARRAY(String), nullable=True)
    language = Column(String(5), default="pt", nullable=False)

    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (Index("idx_propaganda_technique_precision", "technique", "precision"),)


class ArgumentFramework(Base):
    """Abstract Argumentation Framework instances for logical analysis."""

    __tablename__ = "argument_frameworks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Framework Metadata
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis_history.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Seriema Graph Reference
    neo4j_graph_id = Column(String(64), nullable=True, index=True)

    # Argumentation Structure (simplified JSON for quick access)
    arguments_json = Column(JSON, nullable=False)
    attacks_json = Column(JSON, nullable=False)

    # Computed Properties
    coherence_score = Column(Float, nullable=True)
    grounded_extensions = Column(JSON, nullable=True)
    preferred_extensions = Column(JSON, nullable=True)

    # Constraints
    __table_args__ = (Index("idx_af_analysis_id", "analysis_id"),)


class MLModelMetrics(Base):
    """MLOps metrics for model performance tracking."""

    __tablename__ = "ml_model_metrics"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Model Identification
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    task_type = Column(String(50), nullable=False)  # 'emotion', 'propaganda', 'fallacy', etc.

    # Performance Metrics
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)

    # Inference Performance
    avg_inference_time_ms = Column(Float, nullable=True)
    throughput_samples_per_sec = Column(Float, nullable=True)

    # Robustness
    adversarial_accuracy = Column(Float, nullable=True)
    certified_radius = Column(Float, nullable=True)

    # Data Drift
    feature_drift_detected = Column(Boolean, default=False)
    drift_score = Column(Float, nullable=True)

    # Metadata
    evaluation_dataset = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (Index("idx_ml_metrics_model_time", "model_name", "timestamp"),)


class AdversarialExample(Base):
    """Repository of adversarial examples for training."""

    __tablename__ = "adversarial_examples"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Original & Perturbed
    original_text = Column(Text, nullable=False)
    perturbed_text = Column(Text, nullable=False)
    perturbation_type = Column(String(50), nullable=False)  # 'char_swap', 'word_synonym', etc.

    # Model Fooling
    model_fooled = Column(String(100), nullable=False)
    original_prediction = Column(String(50), nullable=False)
    perturbed_prediction = Column(String(50), nullable=False)

    # Defense Training
    used_in_training = Column(Boolean, default=False)
    defense_effective = Column(Boolean, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (Index("idx_adv_model_type", "model_fooled", "perturbation_type"),)


# ============================================================================
# BACKGROUND TASK TRACKING
# ============================================================================


class BackgroundTask(Base):
    """Kafka/async task tracking."""

    __tablename__ = "background_tasks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Task Info
    task_type = Column(String(50), nullable=False, index=True)
    kafka_topic = Column(String(100), nullable=True)
    kafka_partition = Column(Integer, nullable=True)
    kafka_offset = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="pending", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Payload & Result
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Retry Logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Constraints
    __table_args__ = (Index("idx_task_status_created", "status", "created_at"),)
