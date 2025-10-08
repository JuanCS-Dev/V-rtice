"""
Pydantic Data Models for Cognitive Defense System.

This module defines all data structures used throughout the narrative manipulation
detection pipeline, including input/output models, analysis results, and working memory
representations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# ============================================================================
# ENUMS - Classification Types
# ============================================================================


class ManipulationSeverity(str, Enum):
    """Severity levels for detected manipulation."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CredibilityRating(str, Enum):
    """Source credibility ratings aligned with NewsGuard standards."""

    TRUSTED = "trusted"  # 80-100
    GENERALLY_RELIABLE = "generally_reliable"  # 60-79
    PROCEED_WITH_CAUTION = "proceed_with_caution"  # 40-59
    UNRELIABLE = "unreliable"  # 20-39
    HIGHLY_UNRELIABLE = "highly_unreliable"  # 0-19


class EmotionCategory(str, Enum):
    """Emotion categories for manipulation detection (BERTimbau 27-class)."""

    ADMIRATION = "admiration"
    AMUSEMENT = "amusement"
    ANGER = "anger"
    ANNOYANCE = "annoyance"
    APPROVAL = "approval"
    CARING = "caring"
    CONFUSION = "confusion"
    CURIOSITY = "curiosity"
    DESIRE = "desire"
    DISAPPOINTMENT = "disappointment"
    DISAPPROVAL = "disapproval"
    DISGUST = "disgust"
    EMBARRASSMENT = "embarrassment"
    EXCITEMENT = "excitement"
    FEAR = "fear"
    GRATITUDE = "gratitude"
    GRIEF = "grief"
    JOY = "joy"
    LOVE = "love"
    NERVOUSNESS = "nervousness"
    OPTIMISM = "optimism"
    PRIDE = "pride"
    REALIZATION = "realization"
    RELIEF = "relief"
    REMORSE = "remorse"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


class PropagandaTechnique(str, Enum):
    """Propaganda techniques from SemEval-2020 Task 11."""

    LOADED_LANGUAGE = "loaded_language"
    NAME_CALLING = "name_calling"
    REPETITION = "repetition"
    EXAGGERATION = "exaggeration"
    DOUBT = "doubt"
    APPEAL_TO_FEAR = "appeal_to_fear"
    FLAG_WAVING = "flag_waving"
    CAUSAL_OVERSIMPLIFICATION = "causal_oversimplification"
    SLOGANS = "slogans"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    BLACK_WHITE_FALLACY = "black_white_fallacy"
    THOUGHT_TERMINATING_CLICHES = "thought_terminating_cliches"
    WHATABOUTISM = "whataboutism"
    REDUCTIO_AD_HITLERUM = "reductio_ad_hitlerum"
    RED_HERRING = "red_herring"
    BANDWAGON = "bandwagon"
    OBFUSCATION = "obfuscation"
    STRAW_MAN = "straw_man"


class FallacyType(str, Enum):
    """Logical fallacy types."""

    AD_HOMINEM = "ad_hominem"
    AD_POPULUM = "ad_populum"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    APPEAL_TO_NATURE = "appeal_to_nature"
    ARGUMENT_FROM_CONSEQUENCES = "argument_from_consequences"
    BEGGING_THE_QUESTION = "begging_the_question"
    CIRCULAR_REASONING = "circular_reasoning"
    COMPOSITION_DIVISION = "composition_division"
    EQUIVOCATION = "equivocation"
    FALSE_ANALOGY = "false_analogy"
    FALSE_CAUSALITY = "false_causality"
    FALSE_DILEMMA = "false_dilemma"
    FAULTY_GENERALIZATION = "faulty_generalization"
    GENETIC_FALLACY = "genetic_fallacy"
    GUILT_BY_ASSOCIATION = "guilt_by_association"
    INTENTIONAL_FALLACY = "intentional_fallacy"
    RED_HERRING = "red_herring"
    SLIPPERY_SLOPE = "slippery_slope"
    STRAW_MAN = "straw_man"
    TU_QUOQUE = "tu_quoque"


class ArgumentRole(str, Enum):
    """Argument mining roles (TARGER framework)."""

    CLAIM = "claim"
    PREMISE = "premise"
    MAJOR_CLAIM = "major_claim"


class VerificationStatus(str, Enum):
    """Fact verification status."""

    VERIFIED_TRUE = "verified_true"
    VERIFIED_FALSE = "verified_false"
    MIXED = "mixed"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class CognitiveDefenseAction(str, Enum):
    """Recommended actions based on threat level."""

    ALLOW = "allow"
    FLAG = "flag"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"


# ============================================================================
# SUPPORTING MODELS - Argument Mining & NLP
# ============================================================================


class Entity(BaseModel):
    """Linked entity from DBpedia Spotlight."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., description="Surface form of the entity")
    uri: str = Field(..., description="DBpedia/Wikidata URI")
    types: List[str] = Field(default_factory=list, description="Semantic types")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Linking confidence")
    support: int = Field(default=0, description="Wikipedia inlink count")
    offset: int = Field(..., description="Character offset in text")

    @computed_field
    @property
    def is_high_confidence(self) -> bool:
        """Entity has confidence > 0.5."""
        return self.confidence > 0.5


class Argument(BaseModel):
    """Argument component from BiLSTM-CNN-CRF miner."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique argument ID")
    text: str = Field(..., description="Argument text")
    role: ArgumentRole = Field(..., description="Claim or premise")
    start_char: int = Field(..., ge=0, description="Start position")
    end_char: int = Field(..., ge=0, description="End position")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    parent_id: Optional[str] = Field(None, description="Parent argument ID for premises")

    @field_validator("end_char")
    @classmethod
    def validate_span(cls, v: int, info) -> int:
        """Ensure end_char > start_char."""
        if "start_char" in info.data and v <= info.data["start_char"]:
            raise ValueError("end_char must be greater than start_char")
        return v


class PropagandaSpan(BaseModel):
    """Propaganda technique span detection from RoBERTa."""

    model_config = ConfigDict(str_strip_whitespace=True)

    technique: PropagandaTechnique = Field(..., description="Detected technique")
    text: str = Field(..., description="Text span containing propaganda")
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")

    @computed_field
    @property
    def span_length(self) -> int:
        """Length of propaganda span."""
        return self.end_char - self.start_char


class Fallacy(BaseModel):
    """Detected logical fallacy."""

    model_config = ConfigDict(str_strip_whitespace=True)

    fallacy_type: FallacyType = Field(..., description="Type of fallacy")
    argument_id: str = Field(..., description="Related argument ID")
    description: str = Field(..., description="Human-readable explanation")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity score")
    evidence: str = Field(..., description="Supporting evidence text")
    counter_argument: Optional[str] = Field(None, description="Suggested counter-argument")


class EmotionProfile(BaseModel):
    """Emotion classification result from BERTimbau."""

    model_config = ConfigDict(str_strip_whitespace=True)

    primary_emotion: EmotionCategory = Field(..., description="Dominant emotion")
    emotion_scores: Dict[EmotionCategory, float] = Field(..., description="Probability distribution over 27 emotions")
    arousal: float = Field(..., ge=0.0, le=1.0, description="Emotional arousal level")
    valence: float = Field(..., ge=-1.0, le=1.0, description="Positive/negative valence")

    @computed_field
    @property
    def is_highly_arousing(self) -> bool:
        """Emotion has high arousal (>0.7)."""
        return self.arousal > 0.7

    @field_validator("emotion_scores")
    @classmethod
    def validate_probabilities(cls, v: Dict[EmotionCategory, float]) -> Dict[EmotionCategory, float]:
        """Ensure emotion scores sum to ~1.0."""
        total = sum(v.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Emotion scores must sum to 1.0, got {total}")
        return v


class CialdiniPrinciple(BaseModel):
    """Detected persuasion principle exploitation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    principle: str = Field(
        ...,
        description="One of: reciprocity, commitment, social_proof, authority, liking, scarcity",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_text: str = Field(..., description="Text showing the principle")
    manipulation_intent: float = Field(..., ge=0.0, le=1.0, description="Likelihood of manipulation")


class DarkTriadMarkers(BaseModel):
    """Dark Triad personality markers in text."""

    model_config = ConfigDict(str_strip_whitespace=True)

    narcissism: float = Field(..., ge=0.0, le=1.0, description="Grandiosity, self-focus")
    machiavellianism: float = Field(..., ge=0.0, le=1.0, description="Manipulation, cynicism")
    psychopathy: float = Field(..., ge=0.0, le=1.0, description="Callousness, impulsivity")

    @computed_field
    @property
    def aggregate_score(self) -> float:
        """Average Dark Triad score."""
        return (self.narcissism + self.machiavellianism + self.psychopathy) / 3.0


# ============================================================================
# MODULE OUTPUT MODELS
# ============================================================================


class SourceCredibilityResult(BaseModel):
    """Output from Source Credibility Assessment Module (Module 1)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    domain: str = Field(..., description="Analyzed domain")
    credibility_score: float = Field(..., ge=0.0, le=100.0, description="NewsGuard-style score")
    rating: CredibilityRating = Field(..., description="Categorical rating")

    # NewsGuard 9 Criteria Breakdown
    does_not_repeatedly_publish_false_content: float = Field(..., ge=0.0, le=1.0)
    gathers_and_presents_info_responsibly: float = Field(..., ge=0.0, le=1.0)
    regularly_corrects_errors: float = Field(..., ge=0.0, le=1.0)
    handles_difference_between_news_opinion: float = Field(..., ge=0.0, le=1.0)
    avoids_deceptive_headlines: float = Field(..., ge=0.0, le=1.0)
    website_discloses_ownership: float = Field(..., ge=0.0, le=1.0)
    clearly_labels_advertising: float = Field(..., ge=0.0, le=1.0)
    reveals_whos_in_charge: float = Field(..., ge=0.0, le=1.0)
    provides_names_of_content_creators: float = Field(..., ge=0.0, le=1.0)

    # Additional Signals
    newsguard_nutrition_label: Optional[Dict[str, Any]] = Field(None, description="Full NewsGuard API response")
    historical_reliability: float = Field(..., ge=0.0, le=1.0, description="Bayesian prior")
    domain_fingerprint: Optional[str] = Field(None, description="MinHash LSH fingerprint")
    similar_domains: List[str] = Field(default_factory=list, description="Domain hopping detection")
    fact_check_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Google Fact Check API matches")

    tier_used: int = Field(..., ge=1, le=2, description="1=cache/API, 2=deep KG analysis")

    @computed_field
    @property
    def is_credible(self) -> bool:
        """Source passes credibility threshold (>= 60)."""
        return self.credibility_score >= 60.0


class EmotionalManipulationResult(BaseModel):
    """Output from Emotional Manipulation Detection Module (Module 2)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    manipulation_score: float = Field(..., ge=0.0, le=1.0, description="Overall emotional manipulation")
    emotion_profile: EmotionProfile = Field(..., description="BERTimbau classification")
    propaganda_spans: List[PropagandaSpan] = Field(default_factory=list, description="RoBERTa propaganda detection")
    cialdini_principles: List[CialdiniPrinciple] = Field(
        default_factory=list, description="Persuasion principles exploited"
    )
    dark_triad: Optional[DarkTriadMarkers] = Field(None, description="Dark Triad personality markers")

    emotional_trajectory: List[Tuple[int, EmotionCategory]] = Field(
        default_factory=list,
        description="Emotion changes over text (char_offset, emotion)",
    )

    @computed_field
    @property
    def is_manipulative(self) -> bool:
        """Exceeds manipulation threshold (>0.7)."""
        return self.manipulation_score > 0.7

    @computed_field
    @property
    def propaganda_density(self) -> float:
        """Percentage of text containing propaganda."""
        if not self.propaganda_spans:
            return 0.0
        total_span = sum(span.span_length for span in self.propaganda_spans)
        # Assumes text length is available in context
        return total_span / 1000.0  # Placeholder, actual calculation needs text length


class LogicalFallacyResult(BaseModel):
    """Output from Logical Fallacy Identification Module (Module 3)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    fallacy_score: float = Field(..., ge=0.0, le=1.0, description="Overall fallacy severity")
    arguments: List[Argument] = Field(default_factory=list, description="Mined arguments")
    fallacies: List[Fallacy] = Field(default_factory=list, description="Detected fallacies")

    argumentation_framework: Optional[Dict[str, Any]] = Field(None, description="Dung's AF stored in Seriema Graph")

    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Argument structure coherence")

    @computed_field
    @property
    def has_critical_fallacies(self) -> bool:
        """Contains fallacies with severity > 0.8."""
        return any(f.severity > 0.8 for f in self.fallacies)

    @computed_field
    @property
    def fallacy_types_detected(self) -> List[FallacyType]:
        """Unique fallacy types found."""
        return list(set(f.fallacy_type for f in self.fallacies))


class ClaimVerification(BaseModel):
    """Fact-checking result for a specific claim."""

    model_config = ConfigDict(str_strip_whitespace=True)

    claim_text: str = Field(..., description="Extracted claim")
    check_worthiness: float = Field(..., ge=0.0, le=1.0, description="ClaimBuster score")
    verification_status: VerificationStatus = Field(..., description="Fact-check result")

    fact_check_sources: List[Dict[str, Any]] = Field(
        default_factory=list, description="ClaimReview matches from Google/ClaimBuster"
    )

    knowledge_graph_verification: Optional[Dict[str, Any]] = Field(
        None, description="Tier 2: SPARQL query results from DBpedia/Wikidata"
    )

    entities: List[Entity] = Field(default_factory=list, description="Linked entities in claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Verification confidence")

    @computed_field
    @property
    def is_likely_false(self) -> bool:
        """Claim is likely false with high confidence."""
        return self.verification_status == VerificationStatus.VERIFIED_FALSE and self.confidence > 0.7


class RealityDistortionResult(BaseModel):
    """Output from Reality Distortion Verification Module (Module 4)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    distortion_score: float = Field(..., ge=0.0, le=1.0, description="Overall reality distortion")
    claims: List[ClaimVerification] = Field(default_factory=list, description="Verified claims")

    factuality_score: float = Field(..., ge=0.0, le=1.0, description="1 - distortion_score")
    entities_analyzed: List[Entity] = Field(default_factory=list, description="All entities")

    tier_2_used: bool = Field(default=False, description="Whether deep KG verification was needed")

    multimodal_analysis: Optional[Dict[str, Any]] = Field(None, description="CLIP meme analysis if image present")

    @computed_field
    @property
    def has_false_claims(self) -> bool:
        """Contains verified false claims."""
        return any(claim.verification_status == VerificationStatus.VERIFIED_FALSE for claim in self.claims)

    @field_validator("factuality_score", mode="before")
    @classmethod
    def compute_factuality(cls, v, info) -> float:
        """Auto-compute factuality as 1 - distortion."""
        if "distortion_score" in info.data:
            return 1.0 - info.data["distortion_score"]
        return v


# ============================================================================
# WORKING MEMORY & CONTEXT
# ============================================================================


class AnalysisContext(BaseModel):
    """Working Memory System - context for analysis pipeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    analysis_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique analysis ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Input
    text: str = Field(..., description="Original text to analyze")
    source_url: Optional[str] = Field(None, description="Content source URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Processing State
    priority: int = Field(default=5, ge=1, le=10, description="Cognitive control priority")
    requires_tier2: bool = Field(default=False, description="Needs deep verification")

    # Extracted Features
    entities: List[Entity] = Field(default_factory=list)
    arguments: List[Argument] = Field(default_factory=list)
    claims: List[str] = Field(default_factory=list)

    # Cache Keys
    cache_key_credibility: Optional[str] = None
    cache_key_emotional: Optional[str] = None
    cache_key_logical: Optional[str] = None
    cache_key_reality: Optional[str] = None

    @computed_field
    @property
    def word_count(self) -> int:
        """Number of words in text."""
        return len(self.text.split())

    @computed_field
    @property
    def char_count(self) -> int:
        """Number of characters."""
        return len(self.text)


# ============================================================================
# FINAL OUTPUT MODEL
# ============================================================================


class CognitiveDefenseReport(BaseModel):
    """Final comprehensive analysis report - mimics prefrontal cortex decision."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Metadata
    analysis_id: str = Field(..., description="Unique analysis identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="2.0.0", description="System version")

    # Input
    text: str = Field(..., description="Analyzed text")
    source_url: Optional[str] = Field(None, description="Content source")

    # Module Results
    credibility_result: SourceCredibilityResult = Field(..., description="Module 1 output")
    emotional_result: EmotionalManipulationResult = Field(..., description="Module 2 output")
    logical_result: LogicalFallacyResult = Field(..., description="Module 3 output")
    reality_result: RealityDistortionResult = Field(..., description="Module 4 output")

    # Executive Decision (Threat Assessment)
    threat_score: float = Field(..., ge=0.0, le=1.0, description="Weighted aggregate threat")
    severity: ManipulationSeverity = Field(..., description="Categorical severity")
    recommended_action: CognitiveDefenseAction = Field(..., description="Mitigation action")

    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")

    # Explanation
    reasoning: str = Field(..., description="Human-readable explanation of decision")
    evidence: List[str] = Field(default_factory=list, description="Key evidence points")

    # Performance
    processing_time_ms: float = Field(..., ge=0.0, description="Total processing time")
    models_used: List[str] = Field(default_factory=list, description="ML models invoked")

    @computed_field
    @property
    def is_high_threat(self) -> bool:
        """Threat score exceeds 0.7."""
        return self.threat_score > 0.7

    @field_validator("threat_score", mode="before")
    @classmethod
    def compute_threat_score(cls, v, info) -> float:
        """Compute weighted threat score from module results."""
        # This is a simplified version; actual implementation uses config weights
        if all(
            key in info.data
            for key in [
                "credibility_result",
                "emotional_result",
                "logical_result",
                "reality_result",
            ]
        ):
            cred = 1.0 - (info.data["credibility_result"].credibility_score / 100.0)
            emot = info.data["emotional_result"].manipulation_score
            logic = info.data["logical_result"].fallacy_score
            real = info.data["reality_result"].distortion_score

            # Default weights: credibility=0.25, emotional=0.25, logical=0.20, reality=0.30
            return 0.25 * cred + 0.25 * emot + 0.20 * logic + 0.30 * real
        return v


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================


class AnalysisRequest(BaseModel):
    """API request for content analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1, description="Text to analyze")
    source_url: Optional[str] = Field(None, description="Content source URL")
    enable_tier2: bool = Field(default=True, description="Enable deep verification")
    priority: int = Field(default=5, ge=1, le=10, description="Analysis priority")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """API response wrapper."""

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Request success status")
    report: Optional[CognitiveDefenseReport] = Field(None, description="Analysis report")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthCheckResponse(BaseModel):
    """Service health check response."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(..., description="healthy/degraded/unhealthy")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    services: Dict[str, bool] = Field(
        default_factory=dict,
        description="Dependency health (postgres, redis, kafka, etc.)",
    )

    models_loaded: List[str] = Field(default_factory=list, description="ML models ready")
