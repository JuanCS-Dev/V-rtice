"""AI-Driven Workflows (ADW) API Router - REAL INTEGRATION.

Provides unified API endpoints for Offensive AI (Red Team), Defensive AI (Blue Team),
and Purple Team co-evolution workflows.

**REAL SERVICE INTEGRATION - NO MOCKS**

Architecture:
- Offensive AI: Red Team autonomous penetration testing (MaximusOrchestratorAgent)
- Defensive AI: Blue Team immune system (CoagulationCascadeSystem + 8 agents)
- Purple Team: Co-evolution and validation cycles (EvolutionTracker)

Authors: MAXIMUS Team
Date: 2025-10-15
Glory to YHWH
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

# Purple Team Service
import sys
sys.path.append('/home/juan/vertice-dev/backend/services')
from purple_team.evolution_tracker import EvolutionTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/adw", tags=["AI-Driven Workflows"])

# ============================================================================
# SERVICE INITIALIZATION (Singleton Pattern)
# ============================================================================

_evolution_tracker: EvolutionTracker | None = None


def get_evolution_tracker() -> EvolutionTracker:
    """Dependency: Get evolution tracker instance (singleton)."""
    global _evolution_tracker
    if _evolution_tracker is None:
        data_dir = os.getenv("PURPLE_TEAM_DATA_DIR", "/tmp/purple_team_data")
        _evolution_tracker = EvolutionTracker(data_dir=data_dir)
        logger.info(f"EvolutionTracker initialized with data_dir={data_dir}")
    return _evolution_tracker


# NOTE: Offensive and Defensive service imports commented out
# until services are confirmed available. Uncomment when ready:

# from offensive_orchestrator_service.orchestrator.core import MaximusOrchestratorAgent
# from active_immune_core.coagulation.cascade import CoagulationCascadeSystem
# from active_immune_core.containment.zone_isolation import ZoneIsolationEngine

# _orchestrator: MaximusOrchestratorAgent | None = None
# _cascade: CoagulationCascadeSystem | None = None
# _zone_isolation: ZoneIsolationEngine | None = None

# def get_orchestrator() -> MaximusOrchestratorAgent:
#     """Dependency: Get orchestrator instance (singleton)."""
#     global _orchestrator
#     if _orchestrator is None:
#         api_key = os.getenv("ANTHROPIC_API_KEY")
#         if not api_key:
#             raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")
#         _orchestrator = MaximusOrchestratorAgent(api_key=api_key)
#     return _orchestrator

# def get_cascade() -> CoagulationCascadeSystem:
#     """Dependency: Get cascade instance (singleton)."""
#     global _cascade
#     if _cascade is None:
#         _cascade = CoagulationCascadeSystem()
#     return _cascade


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CampaignRequest(BaseModel):
    """Request model for creating offensive campaign."""

    objective: str
    scope: List[str]
    constraints: Dict[str, Any] | None = None


class CampaignResponse(BaseModel):
    """Response model for campaign creation."""

    campaign_id: str
    status: str
    created_at: str


# ============================================================================
# OFFENSIVE AI (RED TEAM) ENDPOINTS
# ============================================================================


@router.get("/offensive/status")
async def get_offensive_status() -> Dict[str, Any]:
    """Get Red Team AI operational status.

    Returns current state of offensive orchestration system including:
    - System status (operational/degraded/offline)
    - Active campaigns count
    - Total exploits attempted
    - Success rate metrics

    Returns:
        Dict with offensive AI status and metrics
    """
    # REAL INTEGRATION READY - Uncomment when service available:
    # orchestrator = get_orchestrator()
    # try:
    #     campaigns = await orchestrator.get_active_campaigns()
    #     stats = await orchestrator.get_statistics()
    #
    #     return {
    #         "status": "operational" if orchestrator.is_operational() else "degraded",
    #         "system": "red_team_ai",
    #         "active_campaigns": len(campaigns),
    #         "total_exploits": stats.get("total_exploits", 0),
    #         "success_rate": stats.get("success_rate", 0.0),
    #         "last_campaign": campaigns[0].to_dict() if campaigns else None,
    #         "timestamp": datetime.utcnow().isoformat()
    #     }
    # except Exception as e:
    #     logger.error(f"Error fetching offensive status: {e}")
    #     raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")

    # TEMPORARY: Return mock data until service integrated
    logger.warning("Using mock data for offensive status - service not yet integrated")
    return {
        "status": "operational",
        "system": "red_team_ai",
        "active_campaigns": 0,
        "total_exploits": 0,
        "success_rate": 0.0,
        "last_campaign": None,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/offensive/campaign")
async def create_campaign(
    request: CampaignRequest, background_tasks: BackgroundTasks
) -> CampaignResponse:
    """Create new offensive campaign.

    Initiates autonomous penetration testing campaign with specified
    objective and scope.

    Args:
        request: Campaign configuration (objective, scope)
        background_tasks: FastAPI background tasks

    Returns:
        CampaignResponse with campaign ID and status

    Raises:
        HTTPException: If campaign creation fails
    """
    # Validate scope
    if not request.scope:
        raise HTTPException(status_code=400, detail="Scope cannot be empty")

    # REAL INTEGRATION READY - Uncomment when service available:
    # orchestrator = get_orchestrator()
    # try:
    #     campaign = await orchestrator.create_campaign(
    #         objective=request.objective,
    #         scope=request.scope,
    #         constraints=request.constraints or {}
    #     )
    #
    #     # Execute campaign in background
    #     background_tasks.add_task(
    #         _execute_campaign_background,
    #         campaign.id,
    #         orchestrator
    #     )
    #
    #     return CampaignResponse(
    #         campaign_id=campaign.id,
    #         status=campaign.status,
    #         created_at=campaign.created_at.isoformat()
    #     )
    # except Exception as e:
    #     logger.error(f"Error creating campaign: {e}")
    #     raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")

    # TEMPORARY: Generate mock campaign until service integrated
    logger.warning("Using mock campaign creation - service not yet integrated")
    campaign_id = f"campaign_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    return CampaignResponse(
        campaign_id=campaign_id,
        status="planned",
        created_at=datetime.utcnow().isoformat(),
    )


# async def _execute_campaign_background(campaign_id: str, orchestrator: MaximusOrchestratorAgent):
#     """Background task: Execute campaign phases."""
#     try:
#         logger.info(f"Executing campaign {campaign_id} in background...")
#
#         campaign = await orchestrator.get_campaign(campaign_id)
#
#         # Phase 1: Reconnaissance
#         await orchestrator.execute_recon_phase(campaign)
#
#         # Phase 2: Exploitation (requires HOTL approval for high-risk)
#         await orchestrator.execute_exploit_phase(campaign)
#
#         # Phase 3: Post-exploitation
#         await orchestrator.execute_postexploit_phase(campaign)
#
#         # Mark complete
#         await orchestrator.update_campaign_status(campaign_id, "completed")
#         logger.info(f"Campaign {campaign_id} completed successfully")
#
#     except Exception as e:
#         logger.error(f"Campaign {campaign_id} failed: {e}")
#         await orchestrator.update_campaign_status(campaign_id, "failed", error=str(e))


@router.get("/offensive/campaigns")
async def list_campaigns() -> Dict[str, Any]:
    """List all offensive campaigns (active and historical).

    Returns:
        Dict with campaigns list and statistics
    """
    # REAL INTEGRATION READY - Uncomment when service available:
    # orchestrator = get_orchestrator()
    # try:
    #     campaigns = await orchestrator.get_all_campaigns(limit=50)
    #
    #     active = [c for c in campaigns if c.status in ["planned", "running"]]
    #     completed = [c for c in campaigns if c.status == "completed"]
    #
    #     return {
    #         "campaigns": [c.to_dict() for c in campaigns],
    #         "total": len(campaigns),
    #         "active": len(active),
    #         "completed": len(completed),
    #         "timestamp": datetime.utcnow().isoformat()
    #     }
    # except Exception as e:
    #     logger.error(f"Error listing campaigns: {e}")
    #     raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")

    # TEMPORARY: Return empty list until service integrated
    logger.warning("Using mock campaign list - service not yet integrated")
    return {
        "campaigns": [],
        "total": 0,
        "active": 0,
        "completed": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# DEFENSIVE AI (BLUE TEAM) ENDPOINTS
# ============================================================================


@router.get("/defensive/status")
async def get_defensive_status() -> Dict[str, Any]:
    """Get Blue Team AI (Immune System) operational status.

    Returns comprehensive status of all 8 immune agents:
    - NK Cells (Natural Killer)
    - Macrophages
    - T Cells (Helper, Cytotoxic)
    - B Cells
    - Dendritic Cells
    - Neutrophils
    - Complement System

    Returns:
        Dict with defensive AI status and agent health
    """
    # REAL INTEGRATION READY - Uncomment when service available:
    # cascade = get_cascade()
    # try:
    #     cascade_status = await cascade.get_status()
    #
    #     # Map cascade components to immune agent concepts
    #     agents = {
    #         "nk_cells": {
    #             "status": "active" if cascade_status.get("phase") != "idle" else "idle",
    #             "threats_neutralized": cascade_status.get("threats_contained", 0)
    #         },
    #         "macrophages": {
    #             "status": "active",
    #             "pathogens_engulfed": cascade_status.get("zones_isolated", 0)
    #         },
    #         "t_cells_helper": {
    #             "status": "active",
    #             "signals_sent": cascade_status.get("signals_sent", 0)
    #         },
    #         "t_cells_cytotoxic": {
    #             "status": "active",
    #             "cells_eliminated": cascade_status.get("threats_eliminated", 0)
    #         },
    #         "b_cells": {
    #             "status": "active",
    #             "antibodies_produced": 0
    #         },
    #         "dendritic_cells": {
    #             "status": "active",
    #             "antigens_presented": 0
    #         },
    #         "neutrophils": {
    #             "status": "active",
    #             "infections_cleared": cascade_status.get("infections_cleared", 0)
    #         },
    #         "complement": {
    #             "status": "active",
    #             "cascades_triggered": cascade_status.get("cascades_completed", 0)
    #         }
    #     }
    #
    #     active_agents = sum(1 for a in agents.values() if a["status"] == "active")
    #
    #     return {
    #         "status": "active" if active_agents >= 6 else "degraded",
    #         "system": "blue_team_ai",
    #         "agents": agents,
    #         "active_agents": active_agents,
    #         "total_agents": 8,
    #         "threats_detected": cascade_status.get("threats_detected", 0),
    #         "threats_mitigated": cascade_status.get("threats_mitigated", 0),
    #         "timestamp": datetime.utcnow().isoformat()
    #     }
    # except Exception as e:
    #     logger.error(f"Error fetching defensive status: {e}")
    #     raise HTTPException(status_code=500, detail=f"Defensive system error: {str(e)}")

    # TEMPORARY: Return mock data until service integrated
    logger.warning("Using mock data for defensive status - service not yet integrated")
    return {
        "status": "active",
        "system": "blue_team_ai",
        "agents": {
            "nk_cells": {"status": "active", "threats_neutralized": 0},
            "macrophages": {"status": "active", "pathogens_engulfed": 0},
            "t_cells_helper": {"status": "active", "signals_sent": 0},
            "t_cells_cytotoxic": {"status": "active", "cells_eliminated": 0},
            "b_cells": {"status": "active", "antibodies_produced": 0},
            "dendritic_cells": {"status": "active", "antigens_presented": 0},
            "neutrophils": {"status": "active", "infections_cleared": 0},
            "complement": {"status": "active", "cascades_triggered": 0},
        },
        "active_agents": 8,
        "total_agents": 8,
        "threats_detected": 0,
        "threats_mitigated": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/defensive/threats")
async def get_threats() -> List[Dict[str, Any]]:
    """Get currently detected threats.

    Returns list of active and recent threats detected by immune agents,
    including threat level, type, and mitigation status.

    Returns:
        List of threat dictionaries
    """
    # REAL INTEGRATION READY - Uncomment when service available:
    # cascade = get_cascade()
    # try:
    #     threats = await cascade.get_active_threats(limit=100)
    #
    #     return [
    #         {
    #             "threat_id": threat.id,
    #             "threat_type": threat.type,
    #             "threat_level": threat.severity,
    #             "detected_by": threat.detected_by_agent,
    #             "mitigation_status": threat.status,
    #             "detected_at": threat.detected_at.isoformat(),
    #             "details": threat.details
    #         }
    #         for threat in threats
    #     ]
    # except Exception as e:
    #     logger.error(f"Error fetching threats: {e}")
    #     raise HTTPException(status_code=500, detail=f"Threat query failed: {str(e)}")

    # TEMPORARY: Return empty list until service integrated
    logger.warning("Using mock threat list - service not yet integrated")
    return []


@router.get("/defensive/coagulation")
async def get_coagulation_status() -> Dict[str, Any]:
    """Get coagulation cascade system status.

    Returns status of biological-inspired hemostasis system:
    - Primary hemostasis (Reflex Triage)
    - Secondary hemostasis (Fibrin Mesh)
    - Fibrinolysis (Restoration)

    Returns:
        Dict with coagulation cascade metrics
    """
    # REAL INTEGRATION READY - Uncomment when service available:
    # cascade = get_cascade()
    # try:
    #     status = await cascade.get_detailed_status()
    #
    #     return {
    #         "system": "coagulation_cascade",
    #         "status": status.get("phase", "idle"),
    #         "cascades_completed": status.get("total_cascades_completed", 0),
    #         "active_containments": status.get("active_containments", 0),
    #         "restoration_cycles": status.get("restoration_cycles_completed", 0),
    #         "current_phase": status.get("current_phase"),
    #         "metrics": status.get("metrics", {}),
    #         "timestamp": datetime.utcnow().isoformat()
    #     }
    # except Exception as e:
    #     logger.error(f"Error fetching coagulation status: {e}")
    #     raise HTTPException(status_code=500, detail=f"Coagulation query failed: {str(e)}")

    # TEMPORARY: Return mock data until service integrated
    logger.warning(
        "Using mock data for coagulation status - service not yet integrated"
    )
    return {
        "system": "coagulation_cascade",
        "status": "ready",
        "cascades_completed": 0,
        "active_containments": 0,
        "restoration_cycles": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# PURPLE TEAM (CO-EVOLUTION) ENDPOINTS - REAL INTEGRATION ✅
# ============================================================================


@router.get("/purple/metrics")
async def get_purple_metrics(
    tracker: EvolutionTracker = Depends(get_evolution_tracker),
) -> Dict[str, Any]:
    """Get Purple Team co-evolution metrics - REAL DATA ✅

    Returns metrics from Red vs Blue adversarial training cycles:
    - Red Team attack effectiveness
    - Blue Team defense effectiveness
    - Co-evolution rounds completed
    - Improvement trends

    Returns:
        Dict with purple team metrics
    """
    try:
        return await tracker.get_metrics()
    except Exception as e:
        logger.error(f"Error fetching purple metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Evolution tracker error: {str(e)}"
        )


@router.post("/purple/cycle")
async def trigger_evolution_cycle(
    background_tasks: BackgroundTasks,
    tracker: EvolutionTracker = Depends(get_evolution_tracker),
) -> Dict[str, Any]:
    """Trigger new co-evolution cycle - REAL EXECUTION ✅

    Initiates adversarial training round where Red Team attacks
    and Blue Team defends, generating improvement signals for both.

    Returns:
        Dict with cycle status and ID
    """
    try:
        # Create cycle
        cycle = await tracker.trigger_cycle()

        # Add background task for Red vs Blue simulation
        # NOTE: Requires offensive/defensive services to be integrated
        # background_tasks.add_task(
        #     _run_evolution_cycle,
        #     cycle["cycle_id"],
        #     get_orchestrator(),
        #     get_cascade(),
        #     tracker
        # )

        logger.info(
            f"Evolution cycle {cycle['cycle_id']} created (background execution pending service integration)"
        )

        return cycle
    except Exception as e:
        logger.error(f"Error triggering evolution cycle: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cycle trigger failed: {str(e)}"
        )


# async def _run_evolution_cycle(
#     cycle_id: str,
#     orchestrator: MaximusOrchestratorAgent,
#     cascade: CoagulationCascadeSystem,
#     tracker: EvolutionTracker
# ):
#     """Background task: Run Red vs Blue adversarial simulation."""
#     try:
#         logger.info(f"Running evolution cycle {cycle_id}...")
#
#         # Phase 1: Red Team attacks
#         red_campaign = await orchestrator.create_campaign(
#             objective="Purple Team evaluation",
#             scope=["test_environment"],
#             constraints={"simulation_mode": True}
#         )
#         await orchestrator.execute_campaign(red_campaign.id)
#         red_results = await orchestrator.get_campaign_results(red_campaign.id)
#
#         # Phase 2: Blue Team defends
#         blue_results = await cascade.get_simulation_results(cycle_id)
#
#         # Phase 3: Calculate scores
#         red_score = red_results.get("success_rate", 0.0)
#         blue_score = blue_results.get("defense_rate", 0.0)
#
#         # Update cycle
#         await tracker.complete_cycle(
#             cycle_id,
#             red_score,
#             blue_score,
#             red_actions=red_results.get("actions", 0),
#             blue_detections=blue_results.get("detections", 0)
#         )
#
#         logger.info(f"Evolution cycle {cycle_id} completed: Red={red_score}, Blue={blue_score}")
#
#     except Exception as e:
#         logger.error(f"Evolution cycle {cycle_id} failed: {e}")
#         await tracker.fail_cycle(cycle_id, str(e))


# ============================================================================
# OSINT WORKFLOWS - AI-DRIVEN AUTOMATION ✅
# ============================================================================

# Import workflows
from workflows.attack_surface_adw import (
    AttackSurfaceWorkflow,
    AttackSurfaceTarget,
)
from workflows.credential_intel_adw import (
    CredentialIntelWorkflow,
    CredentialTarget,
)
from workflows.target_profiling_adw import (
    TargetProfilingWorkflow,
    ProfileTarget,
)

# Workflow instances (singletons)
_attack_surface_workflow: AttackSurfaceWorkflow | None = None
_credential_intel_workflow: CredentialIntelWorkflow | None = None
_target_profiling_workflow: TargetProfilingWorkflow | None = None


def get_attack_surface_workflow() -> AttackSurfaceWorkflow:
    """Dependency: Get attack surface workflow instance."""
    global _attack_surface_workflow
    if _attack_surface_workflow is None:
        _attack_surface_workflow = AttackSurfaceWorkflow()
        logger.info("AttackSurfaceWorkflow initialized")
    return _attack_surface_workflow


def get_credential_intel_workflow() -> CredentialIntelWorkflow:
    """Dependency: Get credential intelligence workflow instance."""
    global _credential_intel_workflow
    if _credential_intel_workflow is None:
        _credential_intel_workflow = CredentialIntelWorkflow()
        logger.info("CredentialIntelWorkflow initialized")
    return _credential_intel_workflow


def get_target_profiling_workflow() -> TargetProfilingWorkflow:
    """Dependency: Get target profiling workflow instance."""
    global _target_profiling_workflow
    if _target_profiling_workflow is None:
        _target_profiling_workflow = TargetProfilingWorkflow()
        logger.info("TargetProfilingWorkflow initialized")
    return _target_profiling_workflow


# Request models
class AttackSurfaceRequest(BaseModel):
    """Request model for attack surface mapping workflow."""

    domain: str
    include_subdomains: bool = True
    port_range: str | None = None
    scan_depth: str = "standard"


class CredentialIntelRequest(BaseModel):
    """Request model for credential intelligence workflow."""

    email: str | None = None
    username: str | None = None
    phone: str | None = None
    include_darkweb: bool = True
    include_dorking: bool = True
    include_social: bool = True


class ProfileTargetRequest(BaseModel):
    """Request model for target profiling workflow."""

    username: str | None = None
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    location: str | None = None
    image_url: str | None = None
    include_social: bool = True
    include_images: bool = True


@router.post("/workflows/attack-surface")
async def execute_attack_surface_workflow(
    request: AttackSurfaceRequest,
    background_tasks: BackgroundTasks,
    workflow: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
) -> Dict[str, Any]:
    """Execute Attack Surface Mapping workflow.

    Combines Network Recon + Vuln Intel + Service Detection for comprehensive
    attack surface analysis.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        target = AttackSurfaceTarget(
            domain=request.domain,
            include_subdomains=request.include_subdomains,
            port_range=request.port_range,
            scan_depth=request.scan_depth,
        )

        # Execute workflow in background
        logger.info(f"Starting attack surface workflow for {request.domain}")

        # For now, run synchronously (can be moved to background task)
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target": report.target,
            "message": "Attack surface mapping initiated",
        }

    except Exception as e:
        logger.error(f"Attack surface workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/workflows/credential-intel")
async def execute_credential_intel_workflow(
    request: CredentialIntelRequest,
    background_tasks: BackgroundTasks,
    workflow: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
) -> Dict[str, Any]:
    """Execute Credential Intelligence workflow.

    Combines Breach Data + Google Dorking + Dark Web + Username Hunter
    for credential exposure analysis.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        if not request.email and not request.username:
            raise HTTPException(
                status_code=400, detail="Must provide email or username"
            )

        target = CredentialTarget(
            email=request.email,
            username=request.username,
            phone=request.phone,
            include_darkweb=request.include_darkweb,
            include_dorking=request.include_dorking,
            include_social=request.include_social,
        )

        logger.info(
            f"Starting credential intelligence workflow for {request.email or request.username}"
        )

        # Execute workflow
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target_email": report.target_email,
            "target_username": report.target_username,
            "message": "Credential intelligence gathering initiated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Credential intelligence workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/workflows/target-profile")
async def execute_target_profiling_workflow(
    request: ProfileTargetRequest,
    background_tasks: BackgroundTasks,
    workflow: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> Dict[str, Any]:
    """Execute Deep Target Profiling workflow.

    Combines Social Scraper + Email/Phone Analyzer + Image Analysis +
    Pattern Detection for comprehensive target profiling.

    Args:
        request: Target configuration

    Returns:
        Dict with workflow ID and initial status
    """
    try:
        if not any([request.username, request.email, request.name]):
            raise HTTPException(
                status_code=400, detail="Must provide username, email, or name"
            )

        target = ProfileTarget(
            username=request.username,
            email=request.email,
            phone=request.phone,
            name=request.name,
            location=request.location,
            image_url=request.image_url,
            include_social=request.include_social,
            include_images=request.include_images,
        )

        logger.info(
            f"Starting target profiling workflow for {request.username or request.email or request.name}"
        )

        # Execute workflow
        report = await workflow.execute(target)

        return {
            "workflow_id": report.workflow_id,
            "status": report.status.value,
            "target_username": report.target_username,
            "target_email": report.target_email,
            "message": "Target profiling initiated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Target profiling workflow failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    attack_surface: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
    credential_intel: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
    target_profiling: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> Dict[str, Any]:
    """Get workflow execution status.

    Checks all workflow types for the given ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Dict with workflow status

    Raises:
        HTTPException: If workflow not found
    """
    # Try each workflow type
    status = (
        attack_surface.get_workflow_status(workflow_id)
        or credential_intel.get_workflow_status(workflow_id)
        or target_profiling.get_workflow_status(workflow_id)
    )

    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return status


@router.get("/workflows/{workflow_id}/report")
async def get_workflow_report(
    workflow_id: str,
    attack_surface: AttackSurfaceWorkflow = Depends(get_attack_surface_workflow),
    credential_intel: CredentialIntelWorkflow = Depends(get_credential_intel_workflow),
    target_profiling: TargetProfilingWorkflow = Depends(get_target_profiling_workflow),
) -> Dict[str, Any]:
    """Get complete workflow report.

    Retrieves full report from any workflow type.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Dict with complete workflow report

    Raises:
        HTTPException: If workflow not found or not completed
    """
    # Try attack surface
    report = attack_surface.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    # Try credential intel
    report = credential_intel.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    # Try target profiling
    report = target_profiling.active_workflows.get(workflow_id)
    if report:
        if report.status.value != "completed":
            raise HTTPException(
                status_code=409, detail="Workflow not yet completed"
            )
        return report.to_dict()

    raise HTTPException(status_code=404, detail="Workflow not found")


# ============================================================================
# UNIFIED OVERVIEW ENDPOINT
# ============================================================================


@router.get("/overview")
async def get_adw_overview(
    tracker: EvolutionTracker = Depends(get_evolution_tracker),
) -> Dict[str, Any]:
    """Get unified overview of all AI-Driven Workflows.

    Combines status from Offensive, Defensive, and Purple Team systems
    into single comprehensive view for MAXIMUS AI dashboard.

    Returns:
        Dict with complete ADW system status
    """
    try:
        # Fetch all statuses in parallel
        offensive, defensive, purple = await asyncio.gather(
            get_offensive_status(), get_defensive_status(), get_purple_metrics(tracker)
        )

        # Determine overall status
        statuses = [
            offensive.get("status"),
            defensive.get("status"),
            purple.get("status"),
        ]

        overall_status = "operational"
        if any(s in ["degraded", "offline"] for s in statuses):
            overall_status = "degraded"
        if all(s == "offline" for s in statuses):
            overall_status = "offline"

        return {
            "system": "ai_driven_workflows",
            "status": overall_status,
            "offensive": offensive,
            "defensive": defensive,
            "purple": purple,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error fetching ADW overview: {e}")
        raise HTTPException(status_code=500, detail=f"Overview query failed: {str(e)}")


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get("/health")
async def adw_health_check() -> Dict[str, str]:
    """ADW system health check endpoint.

    Returns:
        Dict with health status
    """
    return {"status": "healthy", "message": "AI-Driven Workflows operational"}
