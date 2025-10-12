"""
Reactive Fabric - Intelligence API Router.

RESTful endpoints for threat intelligence fusion, analysis and reporting.
Primary value delivery mechanism for Phase 1: actionable threat intelligence.

This module represents the ROI justification for reactive fabric.
Quality and actionability of intelligence determines Phase 2 go/no-go decision.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database.session import get_db_session
from ..services.intelligence_service import IntelligenceService
from ..models.intelligence import (
    IntelligenceReport,
    IntelligenceReportCreate,
    IntelligenceReportUpdate,
    IntelligenceType,
    IntelligenceConfidence,
    IntelligenceSource,
    TTPPattern,
    IntelligenceMetrics,
    APTGroup,
    DetectionRule
)


logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/intelligence",
    tags=["Threat Intelligence"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_intelligence_service(
    session: AsyncSession = Depends(get_db_session)
) -> IntelligenceService:
    """
    Dependency injection for IntelligenceService.
    
    Args:
        session: Database session from FastAPI dependency
    
    Returns:
        Configured IntelligenceService instance
    """
    return IntelligenceService(session)


# ============================================================================
# INTELLIGENCE REPORT ENDPOINTS
# ============================================================================

@router.post(
    "/reports",
    response_model=IntelligenceReport,
    status_code=status.HTTP_201_CREATED,
    summary="Create Intelligence Report",
    description="""
    Create new threat intelligence report from event correlation.
    
    **Phase 1 Core Value:**
    Transforms raw threat events into actionable intelligence with:
    - TTP identification and MITRE ATT&CK mapping
    - APT attribution and campaign tracking
    - Detection rule generation
    - Hunt hypothesis formulation
    
    **Quality Metrics:**
    - Confidence score (HIGH/MEDIUM/LOW)
    - Actionability assessment
    - Novelty indicator (new TTP discovery)
    - Time to detection rule
    """
)
async def create_intelligence_report(
    report: IntelligenceReportCreate,
    auto_generate_detections: bool = Query(True, description="Auto-generate detection rules"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> IntelligenceReport:
    """
    Create intelligence report with automatic TTP extraction.
    
    This is the primary output of Phase 1 passive intelligence collection.
    Each report represents validated intelligence ready for defensive action.
    
    Args:
        report: Report creation request
        auto_generate_detections: Generate Sigma/Snort/YARA rules
        service: Injected intelligence service
    
    Returns:
        Created IntelligenceReport with TTPs and detection rules
    
    Raises:
        HTTPException: 500 on creation failure
    """
    try:
        logger.info(
            "creating_intelligence_report",
            title=report.title,
            intelligence_type=report.intelligence_type,
            confidence=report.confidence,
            auto_detections=auto_generate_detections
        )
        
        created_report = await service.create_report(
            report=report,
            auto_generate_detections=auto_generate_detections
        )
        
        logger.info(
            "intelligence_report_created",
            report_id=str(created_report.id),
            ttps_count=len(created_report.ttps) if created_report.ttps else 0,
            apt_attribution=created_report.apt_group,
            confidence=created_report.confidence
        )
        
        return created_report
        
    except Exception as e:
        logger.error("report_creation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Intelligence report creation failed"
        )


@router.get(
    "/reports",
    response_model=List[IntelligenceReport],
    summary="List Intelligence Reports",
    description="""
    Retrieve intelligence reports with filtering.
    
    **Use Cases:**
    - Dashboard feed of latest intelligence
    - APT-specific campaign tracking
    - TTP trend analysis
    - Detection rule catalog
    """
)
async def list_intelligence_reports(
    intelligence_type: Optional[IntelligenceType] = Query(None, description="Filter by type"),
    confidence: Optional[IntelligenceConfidence] = Query(None, description="Minimum confidence"),
    source: Optional[IntelligenceSource] = Query(None, description="Filter by source"),
    apt_group: Optional[str] = Query(None, description="Filter by APT attribution"),
    start_date: Optional[datetime] = Query(None, description="Reports after date"),
    end_date: Optional[datetime] = Query(None, description="Reports before date"),
    novel_ttps_only: bool = Query(False, description="Only reports with novel TTPs"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> List[IntelligenceReport]:
    """
    List intelligence reports with advanced filtering.
    
    Args:
        intelligence_type: Optional type filter
        confidence: Optional minimum confidence filter
        source: Optional source filter
        apt_group: Optional APT group filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        novel_ttps_only: Only novel TTP discoveries
        skip: Pagination offset
        limit: Results per page
        service: Injected intelligence service
    
    Returns:
        List of IntelligenceReport matching filters
    """
    try:
        logger.debug(
            "listing_intelligence_reports",
            intelligence_type=intelligence_type,
            confidence=confidence,
            apt_group=apt_group,
            skip=skip,
            limit=limit
        )
        
        reports = await service.list_reports(
            intelligence_type=intelligence_type,
            confidence=confidence,
            source=source,
            apt_group=apt_group,
            start_date=start_date,
            end_date=end_date,
            novel_ttps_only=novel_ttps_only,
            skip=skip,
            limit=limit
        )
        
        logger.info("intelligence_reports_retrieved", count=len(reports))
        return reports
        
    except Exception as e:
        logger.error("report_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence reports"
        )


@router.get(
    "/reports/{report_id}",
    response_model=IntelligenceReport,
    summary="Get Intelligence Report",
    description="Retrieve specific intelligence report with full details."
)
async def get_intelligence_report(
    report_id: UUID,
    include_related: bool = Query(False, description="Include related reports and events"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> IntelligenceReport:
    """
    Retrieve specific intelligence report.
    
    Args:
        report_id: Report UUID
        include_related: Include related reports and threat events
        service: Injected intelligence service
    
    Returns:
        IntelligenceReport with full details
    
    Raises:
        HTTPException: 404 if report not found
    """
    try:
        report = await service.get_report(
            report_id=report_id,
            include_related=include_related
        )
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("report_retrieval_failed", report_id=str(report_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence report"
        )


@router.patch(
    "/reports/{report_id}",
    response_model=IntelligenceReport,
    summary="Update Intelligence Report",
    description="Update intelligence report with analyst refinements."
)
async def update_intelligence_report(
    report_id: UUID,
    update: IntelligenceReportUpdate,
    service: IntelligenceService = Depends(get_intelligence_service)
) -> IntelligenceReport:
    """
    Update intelligence report.
    
    Typical use cases:
    - Analyst refinement of confidence score
    - APT attribution addition/correction
    - TTP addition after further analysis
    - Detection rule updates
    
    Args:
        report_id: Report UUID
        update: Update request
        service: Injected intelligence service
    
    Returns:
        Updated IntelligenceReport
    
    Raises:
        HTTPException: 404 if report not found
    """
    try:
        logger.info("updating_intelligence_report", report_id=str(report_id))
        
        updated_report = await service.update_report(
            report_id=report_id,
            update=update
        )
        
        if not updated_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        logger.info("intelligence_report_updated", report_id=str(report_id))
        return updated_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("report_update_failed", report_id=str(report_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Intelligence report update failed"
        )


# ============================================================================
# TTP PATTERN ENDPOINTS
# ============================================================================

@router.post(
    "/ttps",
    response_model=TTPPattern,
    status_code=status.HTTP_201_CREATED,
    summary="Register TTP Pattern",
    description="""
    Register new TTP pattern with MITRE ATT&CK mapping.
    
    **Phase 1 KPI:**
    Novel TTP discoveries represent core value proposition.
    Each validated TTP enables proactive defense.
    """
)
async def register_ttp_pattern(
    ttp: TTPPattern,
    service: IntelligenceService = Depends(get_intelligence_service)
) -> TTPPattern:
    """
    Register TTP pattern.
    
    Args:
        ttp: TTP pattern details
        service: Injected intelligence service
    
    Returns:
        Registered TTPPattern with tracking ID
    """
    try:
        logger.info(
            "registering_ttp_pattern",
            mitre_technique=ttp.mitre_technique_id,
            is_novel=ttp.is_novel
        )
        
        registered = await service.register_ttp(ttp)
        
        logger.info(
            "ttp_pattern_registered",
            ttp_id=str(registered.id),
            novel=registered.is_novel
        )
        
        return registered
        
    except Exception as e:
        logger.error("ttp_registration_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TTP registration failed"
        )


@router.get(
    "/ttps",
    response_model=List[TTPPattern],
    summary="List TTP Patterns",
    description="Retrieve discovered TTP patterns with filtering."
)
async def list_ttp_patterns(
    mitre_tactic: Optional[str] = Query(None, description="Filter by MITRE tactic"),
    mitre_technique: Optional[str] = Query(None, description="Filter by MITRE technique"),
    apt_group: Optional[str] = Query(None, description="Filter by APT group"),
    novel_only: bool = Query(False, description="Only novel TTPs"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> List[TTPPattern]:
    """
    List TTP patterns with filtering.
    
    Args:
        mitre_tactic: Optional MITRE tactic filter
        mitre_technique: Optional MITRE technique filter
        apt_group: Optional APT group filter
        novel_only: Only novel discoveries
        skip: Pagination offset
        limit: Results per page
        service: Injected intelligence service
    
    Returns:
        List of TTPPattern
    """
    try:
        ttps = await service.list_ttps(
            mitre_tactic=mitre_tactic,
            mitre_technique=mitre_technique,
            apt_group=apt_group,
            novel_only=novel_only,
            skip=skip,
            limit=limit
        )
        
        logger.info("ttp_patterns_retrieved", count=len(ttps))
        return ttps
        
    except Exception as e:
        logger.error("ttp_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve TTP patterns"
        )


@router.get(
    "/ttps/{ttp_id}",
    response_model=TTPPattern,
    summary="Get TTP Pattern",
    description="Retrieve specific TTP pattern with all associated intelligence."
)
async def get_ttp_pattern(
    ttp_id: UUID,
    service: IntelligenceService = Depends(get_intelligence_service)
) -> TTPPattern:
    """
    Retrieve specific TTP pattern.
    
    Args:
        ttp_id: TTP UUID
        service: Injected intelligence service
    
    Returns:
        TTPPattern details
    
    Raises:
        HTTPException: 404 if TTP not found
    """
    try:
        ttp = await service.get_ttp(ttp_id)
        
        if not ttp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"TTP {ttp_id} not found"
            )
        
        return ttp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ttp_retrieval_failed", ttp_id=str(ttp_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve TTP pattern"
        )


# ============================================================================
# DETECTION RULE ENDPOINTS
# ============================================================================

@router.post(
    "/reports/{report_id}/detections",
    response_model=List[DetectionRule],
    status_code=status.HTTP_201_CREATED,
    summary="Generate Detection Rules",
    description="""
    Generate detection rules from intelligence report.
    
    **Supported Formats:**
    - Sigma (SIEM-agnostic)
    - Snort/Suricata (Network IDS)
    - YARA (Malware/File)
    - KQL (Microsoft Sentinel)
    
    **Phase 1 KPI:**
    Time from intelligence to deployed detection rule.
    Target: <4 hours for HIGH confidence reports.
    """
)
async def generate_detection_rules(
    report_id: UUID,
    formats: List[str] = Query(["sigma"], description="Detection rule formats"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> List[DetectionRule]:
    """
    Generate detection rules from intelligence report.
    
    Args:
        report_id: Intelligence report UUID
        formats: Requested rule formats (sigma, snort, yara, kql)
        service: Injected intelligence service
    
    Returns:
        List of DetectionRule in requested formats
    
    Raises:
        HTTPException: 404 if report not found
    """
    try:
        logger.info(
            "generating_detection_rules",
            report_id=str(report_id),
            formats=formats
        )
        
        rules = await service.generate_detection_rules(
            report_id=report_id,
            formats=formats
        )
        
        if rules is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        logger.info(
            "detection_rules_generated",
            report_id=str(report_id),
            rules_count=len(rules)
        )
        
        return rules
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("detection_generation_failed", report_id=str(report_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detection rule generation failed"
        )


@router.get(
    "/detections",
    response_model=List[DetectionRule],
    summary="List Detection Rules",
    description="Retrieve all generated detection rules."
)
async def list_detection_rules(
    format_filter: Optional[str] = Query(None, description="Filter by format", alias="format"),
    confidence: Optional[IntelligenceConfidence] = Query(None, description="Minimum confidence"),
    deployed_only: bool = Query(False, description="Only deployed rules"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> List[DetectionRule]:
    """
    List detection rules with filtering.
    
    Args:
        format_filter: Optional format filter
        confidence: Optional minimum confidence
        deployed_only: Only rules marked as deployed
        skip: Pagination offset
        limit: Results per page
        service: Injected intelligence service
    
    Returns:
        List of DetectionRule
    """
    try:
        rules = await service.list_detection_rules(
            format=format_filter,
            confidence=confidence,
            deployed_only=deployed_only,
            skip=skip,
            limit=limit
        )
        
        logger.info("detection_rules_retrieved", count=len(rules))
        return rules
        
    except Exception as e:
        logger.error("detection_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detection rules"
        )


# ============================================================================
# APT CAMPAIGN TRACKING
# ============================================================================

@router.get(
    "/campaigns/{apt_group}",
    response_model=dict,
    summary="Track APT Campaign",
    description="""
    Retrieve intelligence timeline for specific APT group.
    
    **Campaign Intelligence:**
    - Attack timeline
    - TTP evolution
    - Target attribution
    - Infrastructure mapping
    - Detection coverage gaps
    """
)
async def track_apt_campaign(
    apt_group: str,
    start_date: Optional[datetime] = Query(None, description="Campaign start date"),
    end_date: Optional[datetime] = Query(None, description="Campaign end date"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> dict:
    """
    Track APT campaign with comprehensive intelligence.
    
    Args:
        apt_group: APT group identifier
        start_date: Optional date range start
        end_date: Optional date range end
        service: Injected intelligence service
    
    Returns:
        Campaign intelligence package with timeline and TTPs
    """
    try:
        logger.info("tracking_apt_campaign", apt_group=apt_group)
        
        campaign = await service.track_apt_campaign(
            apt_group=apt_group,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            "apt_campaign_retrieved",
            apt_group=apt_group,
            reports=len(campaign.get("reports", []))
        )
        
        return campaign
        
    except Exception as e:
        logger.error("campaign_tracking_failed", apt_group=apt_group, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APT campaign tracking failed"
        )


# ============================================================================
# INTELLIGENCE METRICS (PHASE 1 KPIS)
# ============================================================================

@router.get(
    "/metrics",
    response_model=IntelligenceMetrics,
    summary="Phase 1 Intelligence Metrics",
    description="""
    Phase 1 KPI dashboard metrics.
    
    **Validates Phase 1 Success:**
    - Novel TTPs discovered
    - Detection rules deployed
    - Average confidence score
    - Time to detection rule
    - Hunt hypotheses validated
    
    **Go/No-Go Decision Factor:**
    These metrics determine Phase 2 progression viability.
    """
)
async def get_intelligence_metrics(
    start_date: Optional[datetime] = Query(None, description="Metrics period start"),
    end_date: Optional[datetime] = Query(None, description="Metrics period end"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> IntelligenceMetrics:
    """
    Retrieve Phase 1 intelligence metrics.
    
    Critical for validating reactive fabric ROI.
    
    Args:
        start_date: Optional period start
        end_date: Optional period end
        service: Injected intelligence service
    
    Returns:
        IntelligenceMetrics with all Phase 1 KPIs
    """
    try:
        logger.info("retrieving_intelligence_metrics")
        
        metrics = await service.get_phase1_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            "intelligence_metrics_retrieved",
            novel_ttps=metrics.novel_ttps_discovered,
            detection_rules=metrics.detection_rules_deployed,
            avg_confidence=metrics.average_confidence_score
        )
        
        return metrics
        
    except Exception as e:
        logger.error("metrics_retrieval_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence metrics"
        )


@router.get(
    "/metrics/trend",
    response_model=dict,
    summary="Intelligence Trend Analysis",
    description="Time-series trend analysis of intelligence production."
)
async def get_intelligence_trend(
    period: str = Query("7d", description="Analysis period (1d, 7d, 30d, 90d)"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> dict:
    """
    Get intelligence production trend analysis.
    
    Args:
        period: Analysis period
        service: Injected intelligence service
    
    Returns:
        Time-series trend data
    """
    try:
        trend = await service.get_intelligence_trend(period=period)
        
        logger.info("intelligence_trend_retrieved", period=period)
        return trend
        
    except Exception as e:
        logger.error("trend_analysis_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trend analysis failed"
        )


# ============================================================================
# FUSION ENDPOINTS
# ============================================================================

@router.post(
    "/fusion/correlate",
    response_model=IntelligenceReport,
    summary="Correlate Events into Intelligence",
    description="""
    Fuse multiple threat events into single intelligence report.
    
    **Fusion Process:**
    1. Event pattern analysis
    2. TTP extraction and mapping
    3. APT attribution via behavioral profiling
    4. Detection rule generation
    5. Confidence scoring
    
    **Consciousness Parallel:**
    Like semantic binding in Global Workspace Theory, this endpoint
    integrates distributed threat observations into coherent narratives
    with attributed meaning.
    """
)
async def correlate_events_into_intelligence(
    event_ids: List[UUID] = Query(..., description="Event UUIDs to correlate"),
    analyst_context: Optional[str] = Query(None, description="Analyst context/hypothesis"),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> IntelligenceReport:
    """
    Correlate threat events into intelligence report.
    
    Args:
        event_ids: List of event UUIDs to correlate
        analyst_context: Optional analyst hypothesis
        service: Injected intelligence service
    
    Returns:
        Generated IntelligenceReport from event fusion
    """
    try:
        logger.info(
            "correlating_events",
            event_count=len(event_ids),
            has_context=bool(analyst_context)
        )
        
        report = await service.correlate_events(
            event_ids=event_ids,
            analyst_context=analyst_context
        )
        
        logger.info(
            "events_correlated",
            report_id=str(report.id),
            confidence=report.confidence
        )
        
        return report
        
    except Exception as e:
        logger.error("event_correlation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event correlation failed"
        )


# ============================================================================
# HEALTH & METRICS
# ============================================================================

@router.get(
    "/health",
    summary="Intelligence Module Health",
    description="Health check for intelligence fusion module."
)
async def intelligence_health() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status with Phase 1 status
    """
    return {
        "status": "healthy",
        "module": "intelligence_fusion",
        "phase": "1",
        "value_proposition": "actionable_threat_intelligence"
    }
