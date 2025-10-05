"""FASE 8: Autonomous Investigation Service - FastAPI

REST API for threat actor profiling, campaign correlation, and autonomous investigations.

NO MOCKS - Production-ready investigation interface.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from investigation_core import (
    ThreatActorProfiler,
    CampaignCorrelator,
    AutonomousInvestigator,
    SecurityIncident,
    TTP,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
actor_profiler: Optional[ThreatActorProfiler] = None
campaign_correlator: Optional[CampaignCorrelator] = None
investigator: Optional[AutonomousInvestigator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global actor_profiler, campaign_correlator, investigator

    logger.info("Initializing Autonomous Investigation Service...")

    # Initialize components
    actor_profiler = ThreatActorProfiler()
    campaign_correlator = CampaignCorrelator()
    investigator = AutonomousInvestigator(actor_profiler, campaign_correlator)

    # Pre-populate with known threat actors
    _register_known_threat_actors()

    logger.info("All investigation components initialized")

    yield

    logger.info("Shutting down Autonomous Investigation Service...")


def _register_known_threat_actors():
    """Pre-register known threat actors (APT groups, etc)."""
    if actor_profiler is None:
        return

    # APT28 (Fancy Bear, Sofacy)
    actor_profiler.register_threat_actor(
        actor_id="APT28",
        actor_name="APT28 (Fancy Bear)",
        known_ttps=[
            TTP.PHISHING,
            TTP.EXPLOIT_PUBLIC_FACING,
            TTP.CREDENTIAL_DUMPING,
            TTP.LATERAL_MOVEMENT
        ],
        known_infrastructure=[
            "185.86.148.0/24",
            "fancy-bear.com"
        ],
        sophistication_score=0.9
    )

    # Lazarus Group
    actor_profiler.register_threat_actor(
        actor_id="LAZARUS",
        actor_name="Lazarus Group",
        known_ttps=[
            TTP.PHISHING,
            TTP.COMMAND_SCRIPTING,
            TTP.CREDENTIAL_DUMPING,
            TTP.EXFILTRATION_C2
        ],
        known_infrastructure=[
            "175.45.178.0/24"
        ],
        sophistication_score=0.95
    )

    # APT29 (Cozy Bear)
    actor_profiler.register_threat_actor(
        actor_id="APT29",
        actor_name="APT29 (Cozy Bear)",
        known_ttps=[
            TTP.EXPLOIT_PUBLIC_FACING,
            TTP.OBFUSCATED_FILES,
            TTP.CREDENTIAL_DUMPING,
            TTP.DATA_STAGED
        ],
        known_infrastructure=[
            "176.113.0.0/16"
        ],
        sophistication_score=0.95
    )

    logger.info("Pre-registered 3 known threat actors")


app = FastAPI(
    title="VÉRTICE Autonomous Investigation Service",
    description="Threat actor profiling and campaign correlation for attribution",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ThreatActorRegistrationRequest(BaseModel):
    """Request to register threat actor."""
    actor_id: str = Field(..., description="Unique actor ID")
    actor_name: str = Field(..., description="Actor name")
    known_ttps: List[str] = Field(..., description="Known TTP codes (T1566, etc)")
    known_infrastructure: List[str] = Field(default_factory=list, description="Known IPs/domains")
    sophistication_score: float = Field(0.5, ge=0.0, le=1.0, description="Sophistication (0-1)")


class SecurityIncidentRequest(BaseModel):
    """Request to ingest security incident."""
    incident_id: str = Field(..., description="Unique incident ID")
    timestamp: Optional[str] = Field(None, description="ISO timestamp (default: now)")
    incident_type: str = Field(..., description="Incident type")
    affected_assets: List[str] = Field(..., description="Affected assets")
    iocs: List[str] = Field(..., description="Indicators of Compromise")
    ttps_observed: List[str] = Field(..., description="Observed TTP codes")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity (0-1)")
    raw_evidence: Dict[str, Any] = Field(default_factory=dict, description="Raw evidence")


class AttributionResponse(BaseModel):
    """Response with attribution result."""
    incident_id: str
    attributed_actor_id: Optional[str]
    attributed_actor_name: Optional[str]
    confidence_score: float
    matching_ttps: List[str]
    timestamp: str


class CampaignResponse(BaseModel):
    """Response with campaign information."""
    campaign_id: str
    campaign_name: str
    incidents: List[str]
    attributed_actor: Optional[str]
    start_date: str
    last_activity: str
    ttps: List[str]
    targets: List[str]
    confidence_score: float
    campaign_pattern: str
    timestamp: str


class InvestigationResponse(BaseModel):
    """Response with investigation results."""
    investigation_id: str
    incident_id: str
    status: str
    findings: List[str]
    evidence_count: int
    attributed_actor: Optional[str]
    related_campaigns: List[str]
    confidence_score: float
    playbook_used: str
    duration_seconds: Optional[float]
    recommendations: List[str]


class ThreatActorProfileResponse(BaseModel):
    """Response with threat actor profile."""
    actor_id: str
    actor_name: str
    ttps: List[str]
    infrastructure: List[str]
    malware_families: List[str]
    targets: List[str]
    sophistication_score: float
    activity_count: int
    attribution_confidence: float


class StatusResponse(BaseModel):
    """Service status response."""
    service: str
    status: str
    components: Dict[str, Dict[str, Any]]
    timestamp: str


# ============================================================================
# Threat Actor Profiling Endpoints
# ============================================================================

@app.post("/actor/register")
async def register_threat_actor(request: ThreatActorRegistrationRequest):
    """Register known threat actor in database.

    Args:
        request: Actor profile details

    Returns:
        Registration confirmation
    """
    if actor_profiler is None:
        raise HTTPException(status_code=503, detail="Actor profiler not initialized")

    try:
        # Parse TTPs
        ttps = []
        for ttp_code in request.known_ttps:
            try:
                ttp = TTP(ttp_code)
                ttps.append(ttp)
            except ValueError:
                logger.warning(f"Invalid TTP code: {ttp_code}")

        # Register actor
        actor_profiler.register_threat_actor(
            actor_id=request.actor_id,
            actor_name=request.actor_name,
            known_ttps=ttps,
            known_infrastructure=request.known_infrastructure,
            sophistication_score=request.sophistication_score
        )

        return {
            "status": "success",
            "actor_id": request.actor_id,
            "actor_name": request.actor_name,
            "ttps_count": len(ttps),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error registering threat actor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/actor/{actor_id}", response_model=ThreatActorProfileResponse)
async def get_threat_actor_profile(actor_id: str):
    """Retrieve threat actor profile.

    Args:
        actor_id: Actor identifier

    Returns:
        Actor profile
    """
    if actor_profiler is None:
        raise HTTPException(status_code=503, detail="Actor profiler not initialized")

    try:
        profile = actor_profiler.get_actor_profile(actor_id)

        if profile is None:
            raise HTTPException(status_code=404, detail=f"Actor {actor_id} not found")

        return ThreatActorProfileResponse(
            actor_id=profile.actor_id,
            actor_name=profile.actor_name,
            ttps=[ttp.value for ttp in profile.ttps],
            infrastructure=list(profile.infrastructure),
            malware_families=list(profile.malware_families),
            targets=list(profile.targets),
            sophistication_score=profile.sophistication_score,
            activity_count=len(profile.activity_timeline),
            attribution_confidence=profile.attribution_confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving actor profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/actor", response_model=List[ThreatActorProfileResponse])
async def list_threat_actors():
    """List all registered threat actors.

    Returns:
        List of actor profiles
    """
    if actor_profiler is None:
        raise HTTPException(status_code=503, detail="Actor profiler not initialized")

    try:
        profiles = []

        for actor_id, profile in actor_profiler.actor_database.items():
            profiles.append(ThreatActorProfileResponse(
                actor_id=profile.actor_id,
                actor_name=profile.actor_name,
                ttps=[ttp.value for ttp in profile.ttps],
                infrastructure=list(profile.infrastructure),
                malware_families=list(profile.malware_families),
                targets=list(profile.targets),
                sophistication_score=profile.sophistication_score,
                activity_count=len(profile.activity_timeline),
                attribution_confidence=profile.attribution_confidence
            ))

        return profiles

    except Exception as e:
        logger.error(f"Error listing threat actors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Incident Attribution Endpoints
# ============================================================================

@app.post("/incident/ingest")
async def ingest_incident(request: SecurityIncidentRequest):
    """Ingest security incident for investigation.

    Args:
        request: Incident details

    Returns:
        Ingestion confirmation
    """
    if campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Campaign correlator not initialized")

    try:
        # Parse TTPs
        ttps = set()
        for ttp_code in request.ttps_observed:
            try:
                ttp = TTP(ttp_code)
                ttps.add(ttp)
            except ValueError:
                logger.warning(f"Invalid TTP code: {ttp_code}")

        # Parse timestamp
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)
        else:
            timestamp = datetime.now()

        # Create incident
        incident = SecurityIncident(
            incident_id=request.incident_id,
            timestamp=timestamp,
            incident_type=request.incident_type,
            affected_assets=request.affected_assets,
            iocs=request.iocs,
            ttps_observed=ttps,
            severity=request.severity,
            raw_evidence=request.raw_evidence
        )

        # Ingest into correlator
        campaign_correlator.ingest_incident(incident)

        return {
            "status": "success",
            "incident_id": request.incident_id,
            "ttps_count": len(ttps),
            "iocs_count": len(request.iocs),
            "timestamp": timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error ingesting incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/attribute", response_model=AttributionResponse)
async def attribute_incident(incident_id: str):
    """Attribute incident to threat actor.

    Args:
        incident_id: Incident to attribute

    Returns:
        Attribution result
    """
    if actor_profiler is None or campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Find incident
        incident = None
        for inc in campaign_correlator.incidents:
            if inc.incident_id == incident_id:
                incident = inc
                break

        if incident is None:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

        # Attribute incident
        actor_id, confidence = actor_profiler.attribute_incident(incident)

        # Get actor name
        actor_name = None
        matching_ttps = []

        if actor_id:
            profile = actor_profiler.get_actor_profile(actor_id)
            if profile:
                actor_name = profile.actor_name
                # Find matching TTPs
                matching_ttps = [
                    ttp.value for ttp in incident.ttps_observed
                    if ttp in profile.ttps
                ]

        return AttributionResponse(
            incident_id=incident_id,
            attributed_actor_id=actor_id,
            attributed_actor_name=actor_name,
            confidence_score=confidence,
            matching_ttps=matching_ttps,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attributing incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Campaign Correlation Endpoints
# ============================================================================

@app.post("/campaign/correlate", response_model=List[CampaignResponse])
async def correlate_campaigns(time_window_days: int = 30):
    """Correlate incidents into campaigns.

    Args:
        time_window_days: Time window for correlation

    Returns:
        List of identified campaigns
    """
    if campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Campaign correlator not initialized")

    try:
        # Correlate campaigns
        campaigns = campaign_correlator.correlate_campaigns(
            time_window_days=time_window_days
        )

        # Convert to response models
        responses = [
            CampaignResponse(
                campaign_id=campaign.campaign_id,
                campaign_name=campaign.campaign_name,
                incidents=campaign.incidents,
                attributed_actor=campaign.attributed_actor,
                start_date=campaign.start_date.isoformat(),
                last_activity=campaign.last_activity.isoformat(),
                ttps=[ttp.value for ttp in campaign.ttps],
                targets=list(campaign.targets),
                confidence_score=campaign.confidence_score,
                campaign_pattern=campaign.campaign_pattern,
                timestamp=campaign.timestamp.isoformat()
            )
            for campaign in campaigns
        ]

        return responses

    except Exception as e:
        logger.error(f"Error correlating campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaign/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    """Retrieve campaign by ID.

    Args:
        campaign_id: Campaign identifier

    Returns:
        Campaign details
    """
    if campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Campaign correlator not initialized")

    try:
        campaign = campaign_correlator.get_campaign(campaign_id)

        if campaign is None:
            raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

        return CampaignResponse(
            campaign_id=campaign.campaign_id,
            campaign_name=campaign.campaign_name,
            incidents=campaign.incidents,
            attributed_actor=campaign.attributed_actor,
            start_date=campaign.start_date.isoformat(),
            last_activity=campaign.last_activity.isoformat(),
            ttps=[ttp.value for ttp in campaign.ttps],
            targets=list(campaign.targets),
            confidence_score=campaign.confidence_score,
            campaign_pattern=campaign.campaign_pattern,
            timestamp=campaign.timestamp.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/campaign", response_model=List[CampaignResponse])
async def list_campaigns():
    """List all identified campaigns.

    Returns:
        List of campaigns
    """
    if campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Campaign correlator not initialized")

    try:
        campaigns = []

        for campaign in campaign_correlator.campaigns.values():
            campaigns.append(CampaignResponse(
                campaign_id=campaign.campaign_id,
                campaign_name=campaign.campaign_name,
                incidents=campaign.incidents,
                attributed_actor=campaign.attributed_actor,
                start_date=campaign.start_date.isoformat(),
                last_activity=campaign.last_activity.isoformat(),
                ttps=[ttp.value for ttp in campaign.ttps],
                targets=list(campaign.targets),
                confidence_score=campaign.confidence_score,
                campaign_pattern=campaign.campaign_pattern,
                timestamp=campaign.timestamp.isoformat()
            ))

        return campaigns

    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Autonomous Investigation Endpoints
# ============================================================================

@app.post("/investigation/initiate", response_model=InvestigationResponse)
async def initiate_investigation(
    incident_id: str,
    playbook: str = "standard"
):
    """Initiate autonomous investigation.

    Args:
        incident_id: Incident to investigate
        playbook: Investigation playbook

    Returns:
        Investigation results
    """
    if investigator is None or campaign_correlator is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Find incident
        incident = None
        for inc in campaign_correlator.incidents:
            if inc.incident_id == incident_id:
                incident = inc
                break

        if incident is None:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

        # Initiate investigation
        investigation = investigator.initiate_investigation(incident, playbook)

        # Calculate duration
        duration = None
        if investigation.end_time:
            duration = (investigation.end_time - investigation.start_time).total_seconds()

        return InvestigationResponse(
            investigation_id=investigation.investigation_id,
            incident_id=investigation.incident_id,
            status=investigation.status.value,
            findings=investigation.findings,
            evidence_count=len(investigation.evidence_chain),
            attributed_actor=investigation.attributed_actor,
            related_campaigns=investigation.related_campaigns,
            confidence_score=investigation.confidence_score,
            playbook_used=investigation.playbook_used,
            duration_seconds=duration,
            recommendations=investigation.recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/investigation/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(investigation_id: str):
    """Retrieve investigation by ID.

    Args:
        investigation_id: Investigation identifier

    Returns:
        Investigation details
    """
    if investigator is None:
        raise HTTPException(status_code=503, detail="Investigator not initialized")

    try:
        investigation = investigator.get_investigation(investigation_id)

        if investigation is None:
            raise HTTPException(
                status_code=404,
                detail=f"Investigation {investigation_id} not found"
            )

        # Calculate duration
        duration = None
        if investigation.end_time:
            duration = (investigation.end_time - investigation.start_time).total_seconds()

        return InvestigationResponse(
            investigation_id=investigation.investigation_id,
            incident_id=investigation.incident_id,
            status=investigation.status.value,
            findings=investigation.findings,
            evidence_count=len(investigation.evidence_chain),
            attributed_actor=investigation.attributed_actor,
            related_campaigns=investigation.related_campaigns,
            confidence_score=investigation.confidence_score,
            playbook_used=investigation.playbook_used,
            duration_seconds=duration,
            recommendations=investigation.recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving investigation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "autonomous_investigation",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Status of all components
    """
    components = {}

    # Actor profiler status
    if actor_profiler is not None:
        components["threat_actor_profiler"] = actor_profiler.get_status()

    # Campaign correlator status
    if campaign_correlator is not None:
        components["campaign_correlator"] = campaign_correlator.get_status()

    # Investigator status
    if investigator is not None:
        components["autonomous_investigator"] = investigator.get_status()

    return StatusResponse(
        service="autonomous_investigation",
        status="operational",
        components=components,
        timestamp=datetime.now().isoformat()
    )


@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics.

    Returns:
        Combined statistics from all components
    """
    stats = {
        "service": "autonomous_investigation",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Gather stats from all components
    if actor_profiler is not None:
        status = actor_profiler.get_status()
        stats["components"]["threat_actor_profiler"] = {
            "actors_tracked": status["actors_tracked"],
            "attributions_made": status["attributions_made"],
            "accuracy": status["accuracy"]
        }

    if campaign_correlator is not None:
        status = campaign_correlator.get_status()
        stats["components"]["campaign_correlator"] = {
            "incidents_ingested": status["incidents_ingested"],
            "campaigns_identified": status["campaigns_identified"],
            "active_campaigns": status["active_campaigns"]
        }

    if investigator is not None:
        status = investigator.get_status()
        stats["components"]["autonomous_investigator"] = {
            "investigations_completed": status["investigations_completed"],
            "active_investigations": status["active_investigations"]
        }

    return stats


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8017,
        log_level="info",
        access_log=True
    )
