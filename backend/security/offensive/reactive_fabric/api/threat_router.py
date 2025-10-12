"""
Reactive Fabric - Threat Event API Router.

RESTful endpoints for threat event ingestion, enrichment and analysis.
Phase 1 passive intelligence collection pipeline.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database.session import get_db_session
from ..services.threat_service import ThreatEventService
from ..models.threat import (
    ThreatEvent,
    ThreatEventCreate,
    ThreatEventUpdate,
    ThreatEventQuery,
    ThreatSeverity,
    ThreatCategory,
    ThreatIndicator,
    DetectionSource
)


logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/threats",
    tags=["Threat Events"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_threat_service(
    session: AsyncSession = Depends(get_db_session)
) -> ThreatEventService:
    """
    Dependency injection for ThreatEventService.
    
    Args:
        session: Database session from FastAPI dependency
    
    Returns:
        Configured ThreatEventService instance
    """
    return ThreatEventService(session)


# ============================================================================
# THREAT EVENT ENDPOINTS
# ============================================================================

@router.post(
    "/events",
    response_model=ThreatEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Create Threat Event",
    description="""
    Ingest new threat event with automatic enrichment.
    
    **Phase 1 Philosophy:**
    Every event is passive observation. Zero automated responses.
    All events flow to intelligence analysis for human review.
    
    **Enrichment Pipeline:**
    - Geolocation lookup
    - Threat intel correlation
    - MITRE ATT&CK mapping
    - Automatic IOC extraction
    """
)
async def create_threat_event(
    event: ThreatEventCreate,
    auto_enrich: bool = Query(True, description="Run enrichment pipeline automatically"),
    service: ThreatEventService = Depends(get_threat_service)
) -> ThreatEvent:
    """
    Create new threat event with optional enrichment.
    
    Primary ingestion point for all detection sources:
    - Honeypots
    - IDS/IPS
    - SIEM alerts
    - Deception asset interactions
    - External threat feeds
    
    Args:
        event: Event creation request
        auto_enrich: Enable automatic enrichment
        service: Injected threat service
    
    Returns:
        Created and enriched ThreatEvent
    
    Raises:
        HTTPException: 500 on creation failure
    """
    try:
        logger.info(
            "creating_threat_event",
            source=event.source,
            severity=event.severity,
            category=event.category,
            auto_enrich=auto_enrich
        )
        
        created_event = await service.create_event(
            event=event,
            auto_enrich=auto_enrich
        )
        
        logger.info(
            "threat_event_created",
            event_id=str(created_event.id),
            enriched=created_event.enriched,
            mitre_tactics=len(created_event.mitre_tactics) if created_event.mitre_tactics else 0
        )
        
        return created_event
        
    except Exception as e:
        logger.error("threat_event_creation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Threat event creation failed"
        )


@router.get(
    "/events",
    response_model=List[ThreatEvent],
    summary="List Threat Events",
    description="Retrieve threat events with advanced filtering and correlation."
)
async def list_threat_events(
    severity: Optional[ThreatSeverity] = Query(None, description="Filter by severity"),
    category: Optional[ThreatCategory] = Query(None, description="Filter by category"),
    source: Optional[DetectionSource] = Query(None, description="Filter by detection source"),
    start_date: Optional[datetime] = Query(None, description="Filter events after date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before date"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP"),
    enriched_only: bool = Query(False, description="Only return enriched events"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    service: ThreatEventService = Depends(get_threat_service)
) -> List[ThreatEvent]:
    """
    List threat events with comprehensive filtering.
    
    Args:
        severity: Optional severity filter
        category: Optional category filter
        source: Optional detection source filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        source_ip: Optional source IP filter
        enriched_only: Only enriched events
        skip: Pagination offset
        limit: Results per page
        service: Injected threat service
    
    Returns:
        List of ThreatEvent matching filters
    """
    try:
        logger.debug(
            "listing_threat_events",
            severity=severity,
            category=category,
            source=source,
            skip=skip,
            limit=limit
        )
        
        query = ThreatEventQuery(
            severity=severity,
            category=category,
            source=source,
            start_date=start_date,
            end_date=end_date,
            source_ip=source_ip,
            enriched_only=enriched_only
        )
        
        events = await service.list_events(
            query=query,
            skip=skip,
            limit=limit
        )
        
        logger.info("threat_events_retrieved", count=len(events))
        return events
        
    except Exception as e:
        logger.error("threat_event_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve threat events"
        )


@router.get(
    "/events/{event_id}",
    response_model=ThreatEvent,
    summary="Get Threat Event",
    description="Retrieve specific threat event by ID with full enrichment data."
)
async def get_threat_event(
    event_id: UUID,
    service: ThreatEventService = Depends(get_threat_service)
) -> ThreatEvent:
    """
    Retrieve specific threat event.
    
    Args:
        event_id: Event UUID
        service: Injected threat service
    
    Returns:
        ThreatEvent details with enrichment
    
    Raises:
        HTTPException: 404 if event not found
    """
    try:
        event = await service.get_event(event_id)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("threat_event_retrieval_failed", event_id=str(event_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve threat event"
        )


@router.patch(
    "/events/{event_id}",
    response_model=ThreatEvent,
    summary="Update Threat Event",
    description="Update threat event metadata or analysis results."
)
async def update_threat_event(
    event_id: UUID,
    update: ThreatEventUpdate,
    service: ThreatEventService = Depends(get_threat_service)
) -> ThreatEvent:
    """
    Update threat event with new information.
    
    Typically used for:
    - Adding analyst notes
    - Updating severity after investigation
    - Marking as false positive
    - Adding correlation references
    
    Args:
        event_id: Event UUID
        update: Update request
        service: Injected threat service
    
    Returns:
        Updated ThreatEvent
    
    Raises:
        HTTPException: 404 if event not found
    """
    try:
        logger.info("updating_threat_event", event_id=str(event_id))
        
        updated_event = await service.update_event(
            event_id=event_id,
            update=update
        )
        
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        logger.info("threat_event_updated", event_id=str(event_id))
        return updated_event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("threat_event_update_failed", event_id=str(event_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Threat event update failed"
        )


# ============================================================================
# ENRICHMENT ENDPOINTS
# ============================================================================

@router.post(
    "/events/{event_id}/enrich",
    response_model=ThreatEvent,
    summary="Enrich Threat Event",
    description="""
    Manually trigger enrichment pipeline for threat event.
    
    **Enrichment Steps:**
    1. Geolocation lookup (IP → Country/City/ASN)
    2. Threat intel correlation (known malicious indicators)
    3. MITRE ATT&CK technique mapping
    4. IOC extraction and normalization
    5. Related event correlation
    """
)
async def enrich_threat_event(
    event_id: UUID,
    service: ThreatEventService = Depends(get_threat_service)
) -> ThreatEvent:
    """
    Manually trigger enrichment for threat event.
    
    Args:
        event_id: Event UUID
        service: Injected threat service
    
    Returns:
        Enriched ThreatEvent
    
    Raises:
        HTTPException: 404 if event not found
    """
    try:
        logger.info("enriching_threat_event", event_id=str(event_id))
        
        enriched_event = await service.enrich_event(event_id)
        
        if not enriched_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        logger.info(
            "threat_event_enriched",
            event_id=str(event_id),
            mitre_tactics=len(enriched_event.mitre_tactics) if enriched_event.mitre_tactics else 0
        )
        
        return enriched_event
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("threat_event_enrichment_failed", event_id=str(event_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Threat event enrichment failed"
        )


# ============================================================================
# CORRELATION ENDPOINTS
# ============================================================================

@router.get(
    "/events/{event_id}/correlations",
    response_model=List[ThreatEvent],
    summary="Find Correlated Events",
    description="""
    Find threat events correlated with target event.
    
    **Correlation Factors:**
    - Same source IP or subnet
    - Similar MITRE ATT&CK tactics
    - Temporal proximity
    - Shared IOCs
    - Campaign attribution
    """
)
async def get_correlated_events(
    event_id: UUID,
    max_results: int = Query(50, ge=1, le=500, description="Maximum correlated events"),
    service: ThreatEventService = Depends(get_threat_service)
) -> List[ThreatEvent]:
    """
    Find events correlated with target event.
    
    Critical for attack chain reconstruction and campaign tracking.
    
    Args:
        event_id: Target event UUID
        max_results: Maximum number of correlations
        service: Injected threat service
    
    Returns:
        List of correlated ThreatEvent
    
    Raises:
        HTTPException: 404 if event not found
    """
    try:
        logger.info("finding_correlated_events", event_id=str(event_id))
        
        correlated = await service.find_correlated_events(
            event_id=event_id,
            max_results=max_results
        )
        
        logger.info("correlations_found", event_id=str(event_id), count=len(correlated))
        return correlated
        
    except Exception as e:
        logger.error("correlation_search_failed", event_id=str(event_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Correlation search failed"
        )


# ============================================================================
# IOC EXTRACTION ENDPOINTS
# ============================================================================

@router.get(
    "/events/{event_id}/indicators",
    response_model=List[ThreatIndicator],
    summary="Extract Threat Indicators",
    description="""
    Extract and normalize threat indicators from event.
    
    **Supported IOC Types:**
    - IP addresses (IPv4/IPv6)
    - Domain names
    - URLs
    - File hashes (MD5/SHA1/SHA256)
    - Email addresses
    - User agents
    """
)
async def extract_threat_indicators(
    event_id: UUID,
    service: ThreatEventService = Depends(get_threat_service)
) -> List[ThreatIndicator]:
    """
    Extract normalized threat indicators from event.
    
    Args:
        event_id: Event UUID
        service: Injected threat service
    
    Returns:
        List of ThreatIndicator with confidence scores
    
    Raises:
        HTTPException: 404 if event not found
    """
    try:
        indicators = await service.extract_indicators(event_id)
        
        if indicators is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
        
        logger.info("indicators_extracted", event_id=str(event_id), count=len(indicators))
        return indicators
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("indicator_extraction_failed", event_id=str(event_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indicator extraction failed"
        )


# ============================================================================
# MITRE ATT&CK ENDPOINTS
# ============================================================================

@router.get(
    "/events/mitre/tactics",
    response_model=dict,
    summary="Get MITRE ATT&CK Tactic Distribution",
    description="Statistical distribution of MITRE ATT&CK tactics across events."
)
async def get_mitre_tactic_distribution(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    service: ThreatEventService = Depends(get_threat_service)
) -> dict:
    """
    Get MITRE ATT&CK tactic distribution statistics.
    
    Args:
        start_date: Optional start date
        end_date: Optional end date
        service: Injected threat service
    
    Returns:
        Tactic distribution with counts and percentages
    """
    try:
        distribution = await service.get_mitre_tactic_distribution(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("mitre_distribution_retrieved", tactics=len(distribution))
        return distribution
        
    except Exception as e:
        logger.error("mitre_distribution_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve MITRE distribution"
        )


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get(
    "/statistics",
    response_model=dict,
    summary="Threat Event Statistics",
    description="Aggregate statistics on threat events for dashboards."
)
async def get_threat_statistics(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    service: ThreatEventService = Depends(get_threat_service)
) -> dict:
    """
    Get aggregate threat event statistics.
    
    Returns:
        - Total events by severity
        - Events by category
        - Top source IPs
        - Top MITRE tactics
        - Enrichment coverage
        - Detection source breakdown
    
    Args:
        start_date: Optional date range start
        end_date: Optional date range end
        service: Injected threat service
    
    Returns:
        Statistics dictionary
    """
    try:
        stats = await service.get_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("threat_statistics_retrieved")
        return stats
        
    except Exception as e:
        logger.error("statistics_retrieval_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# ============================================================================
# HEALTH & METRICS
# ============================================================================

@router.get(
    "/health",
    summary="Threat Module Health",
    description="Health check for threat event module."
)
async def threat_health() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "module": "threat_events",
        "phase": "1",
        "enrichment": "active"
    }
