"""
Defensive Tools API Routes.

FastAPI routes para ferramentas defensive: Behavioral Analyzer e Encrypted Traffic.
Integração com Active Immune Core e métricas Prometheus.

Philosophy: Production-ready endpoints with complete type safety.
"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, validator
import structlog

from detection.behavioral_analyzer import (
    BehavioralAnalyzer,
    BehaviorEvent
)
from detection.encrypted_traffic_analyzer import (
    EncryptedTrafficAnalyzer,
    NetworkFlow
)

log = structlog.get_logger()

# Prometheus Metrics
DEFENSIVE_REQUESTS = Counter(
    "defensive_tools_requests_total",
    "Total defensive tool requests",
    ["tool", "operation"]
)
DEFENSIVE_LATENCY = Histogram(
    "defensive_tools_latency_seconds",
    "Defensive tool operation latency",
    ["tool", "operation"]
)
ANOMALIES_DETECTED = Counter(
    "defensive_anomalies_detected_total",
    "Total anomalies detected",
    ["tool", "risk_level"]
)

# Router
router = APIRouter(
    prefix="/defensive",
    tags=["Defensive Tools"],
    responses={404: {"description": "Not found"}}
)

# Global instances (singleton pattern para performance)
_behavioral_analyzer: Optional[BehavioralAnalyzer] = None
_traffic_analyzer: Optional[EncryptedTrafficAnalyzer] = None


def get_behavioral_analyzer() -> BehavioralAnalyzer:
    """Get or create behavioral analyzer instance."""
    global _behavioral_analyzer
    if _behavioral_analyzer is None:
        _behavioral_analyzer = BehavioralAnalyzer()
    return _behavioral_analyzer


def get_traffic_analyzer() -> EncryptedTrafficAnalyzer:
    """Get or create traffic analyzer instance."""
    global _traffic_analyzer
    if _traffic_analyzer is None:
        _traffic_analyzer = EncryptedTrafficAnalyzer()
    return _traffic_analyzer


# ============================================================================
# Pydantic Models - Request/Response
# ============================================================================

class BehaviorEventRequest(BaseModel):
    """Behavior event for analysis."""
    entity_id: str = Field(..., description="Entity identifier (user, IP, etc)")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict, description="Event metadata")

    @validator('entity_id')
    def validate_entity_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError("entity_id must be at least 3 characters")
        return v


class BehaviorEventBatchRequest(BaseModel):
    """Batch of behavior events."""
    events: List[BehaviorEventRequest] = Field(..., min_items=1, max_items=1000)


class AnomalyDetectionResponse(BaseModel):
    """Anomaly detection result."""
    is_anomalous: bool
    anomaly_score: float
    risk_level: str
    explanation: str
    timestamp: datetime
    entity_id: str
    features_analyzed: int

    class Config:
        json_schema_extra = {
            "example": {
                "is_anomalous": True,
                "anomaly_score": 0.87,
                "risk_level": "high",
                "explanation": "Unusual access pattern detected: 43 login attempts in 5 minutes",
                "timestamp": "2025-10-12T22:00:00Z",
                "entity_id": "user_123",
                "features_analyzed": 8
            }
        }


class BaselineStatus(BaseModel):
    """Baseline training status."""
    is_trained: bool
    training_samples: int
    last_updated: Optional[datetime]
    feature_count: int


class TrafficPatternRequest(BaseModel):
    """Traffic pattern for analysis."""
    source_ip: str = Field(..., description="Source IP address")
    dest_ip: str = Field(..., description="Destination IP address")
    source_port: int = Field(..., ge=0, le=65535)
    dest_port: int = Field(..., ge=0, le=65535)
    protocol: str = Field(..., description="Protocol (TCP/UDP/etc)")
    packet_count: int = Field(default=1, gt=0)
    byte_count: int = Field(default=1500, gt=0)
    duration_seconds: float = Field(default=1.0, gt=0)
    flags: str = Field(default="", description="TCP flags if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrafficPatternBatchRequest(BaseModel):
    """Batch of traffic patterns."""
    patterns: List[TrafficPatternRequest] = Field(..., min_items=1, max_items=1000)


class EncryptedTrafficAnomalyResponse(BaseModel):
    """Encrypted traffic anomaly result."""
    is_threat: bool
    threat_score: float
    confidence_level: str
    threat_types: List[str]
    explanation: str
    timestamp: datetime
    source_ip: str
    dest_ip: str

    class Config:
        json_schema_extra = {
            "example": {
                "is_threat": True,
                "threat_score": 0.92,
                "confidence_level": "HIGH",
                "threat_types": ["data_exfiltration", "c2_communication"],
                "explanation": "Suspicious encrypted tunnel detected with unusual patterns",
                "timestamp": "2025-10-12T22:00:00Z",
                "source_ip": "192.168.1.100",
                "dest_ip": "203.0.113.42"
            }
        }


class MetricsResponse(BaseModel):
    """Tool metrics."""
    total_analyzed: int
    anomalies_detected: int
    false_positive_rate: float
    avg_processing_time_ms: float


# ============================================================================
# Behavioral Analyzer Endpoints
# ============================================================================

@router.post(
    "/behavioral/analyze",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze single behavior event"
)
async def analyze_behavior_event(
    event: BehaviorEventRequest,
    analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
) -> AnomalyDetectionResponse:
    """
    Analyze single behavior event for anomalies.
    
    Detects:
    - Unusual access patterns
    - Privilege escalation attempts
    - Data exfiltration indicators
    - Insider threat behaviors
    
    Requires baseline training before first use.
    """
    DEFENSIVE_REQUESTS.labels(tool="behavioral", operation="analyze").inc()
    
    try:
        with DEFENSIVE_LATENCY.labels(tool="behavioral", operation="analyze").time():
            # Convert to internal format
            behavior_event = BehaviorEvent(
                entity_id=event.entity_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                metadata=event.metadata
            )
            
            # Analyze
            result = analyzer.analyze_event(behavior_event)
            
            # Track anomalies
            if result.is_anomalous:
                ANOMALIES_DETECTED.labels(
                    tool="behavioral",
                    risk_level=result.risk_level
                ).inc()
                
                log.info(
                    "behavioral_anomaly_detected",
                    entity_id=event.entity_id,
                    score=result.anomaly_score,
                    risk=result.risk_level
                )
            
            return AnomalyDetectionResponse(
                is_anomalous=result.is_anomalous,
                anomaly_score=result.anomaly_score,
                risk_level=result.risk_level,
                explanation=result.explanation,
                timestamp=result.timestamp,
                entity_id=event.entity_id,
                features_analyzed=len(behavior_event.to_feature_vector())
            )
            
    except Exception as e:
        log.error("behavioral_analysis_failed", error=str(e), entity_id=event.entity_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Behavioral analysis failed: {str(e)}"
        )


@router.post(
    "/behavioral/analyze-batch",
    response_model=List[AnomalyDetectionResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze batch of behavior events"
)
async def analyze_behavior_batch(
    batch: BehaviorEventBatchRequest,
    analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
) -> List[AnomalyDetectionResponse]:
    """
    Analyze batch of behavior events for anomalies.
    
    Efficient for processing large event streams.
    Maximum 1000 events per batch.
    """
    DEFENSIVE_REQUESTS.labels(tool="behavioral", operation="batch_analyze").inc()
    
    try:
        with DEFENSIVE_LATENCY.labels(tool="behavioral", operation="batch_analyze").time():
            # Convert to internal format
            events = [
                BehaviorEvent(
                    entity_id=e.entity_id,
                    event_type=e.event_type,
                    timestamp=e.timestamp,
                    metadata=e.metadata
                )
                for e in batch.events
            ]
            
            # Batch analyze
            results = analyzer.analyze_batch(events)
            
            # Track anomalies
            for result in results:
                if result.is_anomalous:
                    ANOMALIES_DETECTED.labels(
                        tool="behavioral",
                        risk_level=result.risk_level
                    ).inc()
            
            return [
                AnomalyDetectionResponse(
                    is_anomalous=r.is_anomalous,
                    anomaly_score=r.anomaly_score,
                    risk_level=r.risk_level,
                    explanation=r.explanation,
                    timestamp=r.timestamp,
                    entity_id=events[i].entity_id,
                    features_analyzed=len(events[i].to_feature_vector())
                )
                for i, r in enumerate(results)
            ]
            
    except Exception as e:
        log.error("behavioral_batch_analysis_failed", error=str(e), batch_size=len(batch.events))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.post(
    "/behavioral/train-baseline",
    response_model=BaselineStatus,
    status_code=status.HTTP_200_OK,
    summary="Train behavioral baseline"
)
async def train_behavioral_baseline(
    training_data: BehaviorEventBatchRequest,
    analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
) -> BaselineStatus:
    """
    Train behavioral baseline from normal activity.
    
    Requires minimum 50 samples for valid baseline.
    Updates existing baseline if already trained.
    """
    DEFENSIVE_REQUESTS.labels(tool="behavioral", operation="train").inc()
    
    try:
        with DEFENSIVE_LATENCY.labels(tool="behavioral", operation="train").time():
            # Convert to internal format
            events = [
                BehaviorEvent(
                    entity_id=e.entity_id,
                    event_type=e.event_type,
                    timestamp=e.timestamp,
                    metadata=e.metadata
                )
                for e in training_data.events
            ]
            
            # Train
            analyzer.learn_baseline(events)
            
            log.info("behavioral_baseline_trained", samples=len(events))
            
            return BaselineStatus(
                is_trained=True,
                training_samples=len(events),
                last_updated=datetime.utcnow(),
                feature_count=len(events[0].to_feature_vector()) if events else 0
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        log.error("baseline_training_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Baseline training failed: {str(e)}"
        )


@router.get(
    "/behavioral/baseline-status",
    response_model=BaselineStatus,
    status_code=status.HTTP_200_OK,
    summary="Get baseline status"
)
async def get_baseline_status(
    analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
) -> BaselineStatus:
    """Get current baseline training status."""
    # Check if baseline is trained (simplified check)
    is_trained = hasattr(analyzer, '_baseline_model') and analyzer._baseline_model is not None
    
    return BaselineStatus(
        is_trained=is_trained,
        training_samples=0,  # Would need to track in analyzer
        last_updated=None,
        feature_count=8  # Standard feature count
    )


@router.get(
    "/behavioral/metrics",
    response_model=MetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get behavioral analyzer metrics"
)
async def get_behavioral_metrics(
    analyzer: BehavioralAnalyzer = Depends(get_behavioral_analyzer)
) -> MetricsResponse:
    """Get performance and accuracy metrics."""
    metrics = analyzer.get_metrics()
    
    return MetricsResponse(
        total_analyzed=metrics["total_analyzed"],
        anomalies_detected=metrics["anomalies_detected"],
        false_positive_rate=0.0,  # Would need tracking system
        avg_processing_time_ms=0.0  # Would need timing tracking
    )


# ============================================================================
# Encrypted Traffic Analyzer Endpoints
# ============================================================================

@router.post(
    "/traffic/analyze",
    response_model=EncryptedTrafficAnomalyResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze encrypted traffic pattern"
)
async def analyze_traffic_pattern(
    pattern: TrafficPatternRequest,
    analyzer: EncryptedTrafficAnalyzer = Depends(get_traffic_analyzer)
) -> EncryptedTrafficAnomalyResponse:
    """
    Analyze encrypted traffic for anomalies.
    
    Detects:
    - Malicious encrypted tunnels
    - C2 communication patterns
    - Data exfiltration via encryption
    - Unusual traffic behaviors
    """
    DEFENSIVE_REQUESTS.labels(tool="traffic", operation="analyze").inc()
    
    try:
        with DEFENSIVE_LATENCY.labels(tool="traffic", operation="analyze").time():
            # Convert to internal format
            network_flow = NetworkFlow(
                source_ip=pattern.source_ip,
                dest_ip=pattern.dest_ip,
                source_port=pattern.source_port,
                dest_port=pattern.dest_port,
                protocol=pattern.protocol,
                packet_count=pattern.packet_count,
                byte_count=pattern.byte_count,
                duration_seconds=pattern.duration_seconds,
                flags=pattern.flags,
                timestamp=pattern.timestamp
            )
            
            # Analyze
            result = analyzer.analyze_flow(network_flow)
            
            # Track threats
            if result.is_threat:
                ANOMALIES_DETECTED.labels(
                    tool="traffic",
                    risk_level=result.confidence_level.value
                ).inc()
                
                log.warning(
                    "traffic_threat_detected",
                    source=pattern.source_ip,
                    dest=pattern.dest_ip,
                    score=result.threat_score,
                    confidence=result.confidence_level.value
                )
            
            return EncryptedTrafficAnomalyResponse(
                is_threat=result.is_threat,
                threat_score=result.threat_score,
                confidence_level=result.confidence_level.value,
                threat_types=[t.value for t in result.threat_types],
                explanation=result.explanation,
                timestamp=result.timestamp,
                source_ip=pattern.source_ip,
                dest_ip=pattern.dest_ip
            )
            
    except Exception as e:
        log.error("traffic_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Traffic analysis failed: {str(e)}"
        )


@router.post(
    "/traffic/analyze-batch",
    response_model=List[EncryptedTrafficAnomalyResponse],
    status_code=status.HTTP_200_OK,
    summary="Analyze batch of traffic patterns"
)
async def analyze_traffic_batch(
    batch: TrafficPatternBatchRequest,
    analyzer: EncryptedTrafficAnalyzer = Depends(get_traffic_analyzer)
) -> List[EncryptedTrafficAnomalyResponse]:
    """
    Analyze batch of traffic patterns.
    
    Efficient for processing network captures.
    Maximum 1000 patterns per batch.
    """
    DEFENSIVE_REQUESTS.labels(tool="traffic", operation="batch_analyze").inc()
    
    try:
        with DEFENSIVE_LATENCY.labels(tool="traffic", operation="batch_analyze").time():
            # Convert to internal format
            flows = [
                NetworkFlow(
                    source_ip=p.source_ip,
                    dest_ip=p.dest_ip,
                    source_port=p.source_port,
                    dest_port=p.dest_port,
                    protocol=p.protocol,
                    packet_count=p.packet_count,
                    byte_count=p.byte_count,
                    duration_seconds=p.duration_seconds,
                    flags=p.flags,
                    timestamp=p.timestamp
                )
                for p in batch.patterns
            ]
            
            # Batch analyze
            results = analyzer.analyze_flows(flows)
            
            # Track threats
            for result in results:
                if result.is_threat:
                    ANOMALIES_DETECTED.labels(
                        tool="traffic",
                        risk_level=result.confidence_level.value
                    ).inc()
            
            return [
                EncryptedTrafficAnomalyResponse(
                    is_threat=r.is_threat,
                    threat_score=r.threat_score,
                    confidence_level=r.confidence_level.value,
                    threat_types=[t.value for t in r.threat_types],
                    explanation=r.explanation,
                    timestamp=r.timestamp,
                    source_ip=flows[i].source_ip,
                    dest_ip=flows[i].dest_ip
                )
                for i, r in enumerate(results)
            ]
            
    except Exception as e:
        log.error("traffic_batch_analysis_failed", error=str(e), batch_size=len(batch.patterns))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get(
    "/traffic/metrics",
    response_model=MetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get traffic analyzer metrics"
)
async def get_traffic_metrics(
    analyzer: EncryptedTrafficAnalyzer = Depends(get_traffic_analyzer)
) -> MetricsResponse:
    """Get performance and detection metrics."""
    metrics = analyzer.get_metrics()
    
    return MetricsResponse(
        total_analyzed=metrics["total_analyzed"],
        anomalies_detected=metrics["anomalies_detected"],
        false_positive_rate=0.0,  # Would need tracking
        avg_processing_time_ms=0.0  # Would need timing
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check() -> Dict:
    """Health check for defensive tools."""
    return {
        "status": "healthy",
        "tools": {
            "behavioral_analyzer": "operational",
            "traffic_analyzer": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
