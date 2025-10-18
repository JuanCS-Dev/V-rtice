"""
Reactive Fabric - Deception Asset API Router.

RESTful endpoints for deception asset management and interaction tracking.
Phase 1 compliant: manual approval flows for critical operations.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..database.session import get_db_session
from ..services.deception_service import DeceptionAssetService
from ..models.deception import (
    DeceptionAsset,
    DeceptionAssetCreate,
    DeceptionAssetUpdate,
    AssetType,
    AssetStatus,
    AssetInteractionLevel,
    AssetInteractionEvent,
    AssetCredibility
)


logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/deception",
    tags=["Deception Assets"],
    responses={
        404: {"description": "Resource not found"},
        403: {"description": "Operation forbidden by Phase 1 constraints"},
        500: {"description": "Internal server error"}
    }
)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_deception_service(
    session: AsyncSession = Depends(get_db_session)
) -> DeceptionAssetService:
    """
    Dependency injection for DeceptionAssetService.
    
    Args:
        session: Database session from FastAPI dependency
    
    Returns:
        Configured DeceptionAssetService instance
    """
    return DeceptionAssetService(session)


# ============================================================================
# DECEPTION ASSET ENDPOINTS
# ============================================================================

@router.post(
    "/assets",
    response_model=DeceptionAsset,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy Deception Asset",
    description="""
    Deploy new deception asset to Sacrifice Island.
    
    **Phase 1 Constraints:**
    - Only LOW/MEDIUM interaction levels allowed
    - Requires human approval in production
    - Automatic credibility monitoring enabled
    
    **Critical Success Factor:**
    Asset credibility determines intelligence quality.
    """
)
async def deploy_deception_asset(
    asset: DeceptionAssetCreate,
    validate_phase1: bool = Query(True, description="Enforce Phase 1 safety constraints"),
    service: DeceptionAssetService = Depends(get_deception_service)
) -> DeceptionAsset:
    """
    Deploy new deception asset with Phase 1 validation.
    
    Implements "Paradoxo do Realismo": maintaining convincing deception
    requires continuous curation, not "configure and forget".
    
    Args:
        asset: Asset creation request
        validate_phase1: Enforce Phase 1 constraints
        service: Injected deception service
    
    Returns:
        Deployed DeceptionAsset with initial credibility assessment
    
    Raises:
        HTTPException: 403 if Phase 1 constraints violated
        HTTPException: 500 on deployment failure
    """
    try:
        logger.info(
            "deploying_deception_asset",
            asset_type=asset.asset_type,
            interaction_level=asset.interaction_level,
            phase1_validation=validate_phase1
        )
        
        deployed_asset = await service.deploy_asset(
            asset=asset,
            validate_phase1_constraints=validate_phase1
        )
        
        logger.info(
            "deception_asset_deployed",
            asset_id=str(deployed_asset.id),
            credibility_score=deployed_asset.credibility_score
        )
        
        return deployed_asset
        
    except ValueError as e:
        # Phase 1 constraint violation
        logger.warning("phase1_constraint_violation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Phase 1 constraint violation: {str(e)}"
        )
    except Exception as e:
        logger.error("asset_deployment_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Asset deployment failed"
        )


@router.get(
    "/assets",
    response_model=List[DeceptionAsset],
    summary="List Deception Assets",
    description="Retrieve all deployed deception assets with filters."
)
async def list_deception_assets(
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    status_filter: Optional[AssetStatus] = Query(None, description="Filter by status", alias="status"),
    interaction_level: Optional[AssetInteractionLevel] = Query(None, description="Filter by interaction level"),
    min_credibility: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum credibility score"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page"),
    service: DeceptionAssetService = Depends(get_deception_service)
) -> List[DeceptionAsset]:
    """
    List deployed deception assets with filtering and pagination.
    
    Args:
        asset_type: Optional asset type filter
        status_filter: Optional status filter
        interaction_level: Optional interaction level filter
        min_credibility: Optional minimum credibility filter
        skip: Pagination offset
        limit: Results per page
        service: Injected deception service
    
    Returns:
        List of DeceptionAsset matching filters
    """
    try:
        logger.debug(
            "listing_deception_assets",
            asset_type=asset_type,
            status=status_filter,
            interaction_level=interaction_level,
            skip=skip,
            limit=limit
        )
        
        assets = await service.list_assets(
            asset_type=asset_type,
            status=status_filter,
            interaction_level=interaction_level,
            min_credibility=min_credibility,
            skip=skip,
            limit=limit
        )
        
        logger.info("assets_retrieved", count=len(assets))
        return assets
        
    except Exception as e:
        logger.error("asset_listing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assets"
        )


@router.get(
    "/assets/{asset_id}",
    response_model=DeceptionAsset,
    summary="Get Deception Asset",
    description="Retrieve specific deception asset by ID."
)
async def get_deception_asset(
    asset_id: UUID,
    service: DeceptionAssetService = Depends(get_deception_service)
) -> DeceptionAsset:
    """
    Retrieve specific deception asset.
    
    Args:
        asset_id: Asset UUID
        service: Injected deception service
    
    Returns:
        DeceptionAsset details
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        asset = await service.get_asset(asset_id)
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("asset_retrieval_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset"
        )


@router.patch(
    "/assets/{asset_id}",
    response_model=DeceptionAsset,
    summary="Update Deception Asset",
    description="""
    Update deception asset configuration.
    
    **Phase 1 Requirement:** Manual approval for critical modifications.
    """
)
async def update_deception_asset(
    asset_id: UUID,
    update: DeceptionAssetUpdate,
    service: DeceptionAssetService = Depends(get_deception_service)
) -> DeceptionAsset:
    """
    Update deception asset with Phase 1 validation.
    
    Args:
        asset_id: Asset UUID
        update: Update request
        service: Injected deception service
    
    Returns:
        Updated DeceptionAsset
    
    Raises:
        HTTPException: 404 if asset not found
        HTTPException: 403 if Phase 1 constraints violated
    """
    try:
        logger.info("updating_deception_asset", asset_id=str(asset_id))
        
        updated_asset = await service.update_asset(
            asset_id=asset_id,
            update=update
        )
        
        if not updated_asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        logger.info("deception_asset_updated", asset_id=str(asset_id))
        return updated_asset
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("phase1_constraint_violation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Phase 1 constraint violation: {str(e)}"
        )
    except Exception as e:
        logger.error("asset_update_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Asset update failed"
        )


@router.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Decommission Deception Asset",
    description="Mark deception asset for decommissioning (soft delete)."
)
async def decommission_deception_asset(
    asset_id: UUID,
    service: DeceptionAssetService = Depends(get_deception_service)
) -> None:
    """
    Decommission deception asset (soft delete).
    
    Args:
        asset_id: Asset UUID
        service: Injected deception service
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        logger.info("decommissioning_asset", asset_id=str(asset_id))
        
        success = await service.decommission_asset(asset_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        logger.info("asset_decommissioned", asset_id=str(asset_id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("asset_decommission_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Asset decommission failed"
        )


# ============================================================================
# ASSET INTERACTION ENDPOINTS
# ============================================================================

@router.post(
    "/assets/{asset_id}/interactions",
    response_model=AssetInteractionEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Record Asset Interaction",
    description="""
    Record attacker interaction with deception asset.
    
    **Phase 1 Core Function:** Passive intelligence collection.
    All interactions logged for analysis, zero automated response.
    """
)
async def record_asset_interaction(
    asset_id: UUID,
    interaction: AssetInteractionEvent,
    service: DeceptionAssetService = Depends(get_deception_service)
) -> AssetInteractionEvent:
    """
    Record attacker interaction with deception asset.
    
    Critical Phase 1 function: every interaction is intelligence signal.
    
    Args:
        asset_id: Target asset UUID
        interaction: Interaction event details
        service: Injected deception service
    
    Returns:
        Recorded interaction event with correlation data
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        logger.info(
            "recording_asset_interaction",
            asset_id=str(asset_id),
            source_ip=interaction.source_ip,
            interaction_type=interaction.interaction_type
        )
        
        recorded = await service.record_interaction(
            asset_id=asset_id,
            interaction=interaction
        )
        
        if not recorded:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        logger.info("interaction_recorded", interaction_id=str(recorded.id))
        return recorded
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("interaction_recording_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interaction recording failed"
        )


@router.get(
    "/assets/{asset_id}/interactions",
    response_model=List[AssetInteractionEvent],
    summary="List Asset Interactions",
    description="Retrieve interaction history for specific deception asset."
)
async def list_asset_interactions(
    asset_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Filter interactions after date"),
    end_date: Optional[datetime] = Query(None, description="Filter interactions before date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DeceptionAssetService = Depends(get_deception_service)
) -> List[AssetInteractionEvent]:
    """
    List interaction history for deception asset.
    
    Args:
        asset_id: Asset UUID
        start_date: Optional start date filter
        end_date: Optional end date filter
        skip: Pagination offset
        limit: Results per page
        service: Injected deception service
    
    Returns:
        List of AssetInteractionEvent
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        interactions = await service.list_interactions(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        logger.info("interactions_retrieved", asset_id=str(asset_id), count=len(interactions))
        return interactions
        
    except Exception as e:
        logger.error("interaction_listing_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interactions"
        )


# ============================================================================
# CREDIBILITY ASSESSMENT ENDPOINTS
# ============================================================================

@router.get(
    "/assets/{asset_id}/credibility",
    response_model=AssetCredibility,
    summary="Assess Asset Credibility",
    description="""
    Get current credibility assessment for deception asset.
    
    **Critical Success Factor:** Asset credibility determines intelligence quality.
    Low credibility = Attacker detection = Intelligence failure.
    """
)
async def assess_asset_credibility(
    asset_id: UUID,
    service: DeceptionAssetService = Depends(get_deception_service)
) -> AssetCredibility:
    """
    Assess current credibility of deception asset.
    
    Implements "Paradoxo do Realismo" monitoring: continuous assessment
    of asset convincingness to detect attacker awareness.
    
    Args:
        asset_id: Asset UUID
        service: Injected deception service
    
    Returns:
        AssetCredibility assessment with recommendations
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        credibility = await service.assess_credibility(asset_id)
        
        if not credibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        logger.info(
            "credibility_assessed",
            asset_id=str(asset_id),
            score=credibility.score,
            requires_maintenance=credibility.requires_maintenance
        )
        
        return credibility
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("credibility_assessment_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credibility assessment failed"
        )


# ============================================================================
# MAINTENANCE ENDPOINTS
# ============================================================================

@router.post(
    "/assets/{asset_id}/maintenance",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Schedule Asset Maintenance",
    description="""
    Schedule credibility maintenance for deception asset.
    
    **Continuous Operation:** Maintaining convincing deception requires
    regular curation - "jardinagem em campo minado" (gardening in minefield).
    """
)
async def schedule_asset_maintenance(
    asset_id: UUID,
    maintenance_type: str = Query(..., description="Type of maintenance required"),
    service: DeceptionAssetService = Depends(get_deception_service)
) -> dict:
    """
    Schedule maintenance for deception asset.
    
    Args:
        asset_id: Asset UUID
        maintenance_type: Type of maintenance
        service: Injected deception service
    
    Returns:
        Maintenance scheduling confirmation
    
    Raises:
        HTTPException: 404 if asset not found
    """
    try:
        logger.info("scheduling_maintenance", asset_id=str(asset_id), type=maintenance_type)
        
        scheduled = await service.schedule_maintenance(
            asset_id=asset_id,
            maintenance_type=maintenance_type
        )
        
        if not scheduled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        return {
            "asset_id": str(asset_id),
            "maintenance_type": maintenance_type,
            "status": "scheduled",
            "message": "Maintenance scheduled for human review"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("maintenance_scheduling_failed", asset_id=str(asset_id), error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Maintenance scheduling failed"
        )


# ============================================================================
# HEALTH & METRICS
# ============================================================================

@router.get(
    "/health",
    summary="Deception Module Health",
    description="Health check for deception module."
)
async def deception_health() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "module": "deception",
        "phase": "1",
        "constraints": "active"
    }
