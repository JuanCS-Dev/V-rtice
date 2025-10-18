"""
Reactive Fabric - Deception Asset Service.

Business logic for deception asset lifecycle and interaction tracking.
Implements "Ilha de Sacrifício" (Sacrifice Island) management for Phase 1.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.repositories.deception_repository import (
    DeceptionAssetRepository, AssetInteractionRepository
)
from ..models.deception import (
    DeceptionAsset, DeceptionAssetCreate, DeceptionAssetUpdate,
    AssetType, AssetStatus, AssetInteractionLevel,
    AssetInteractionEvent, AssetCredibility
)


logger = logging.getLogger(__name__)


class DeceptionAssetService:
    """
    Deception asset service with credibility management.
    
    Orchestrates "Ilha de Sacrifício" lifecycle:
    1. Asset deployment and configuration
    2. Continuous credibility monitoring
    3. Interaction tracking and correlation
    4. Intelligence value measurement
    5. Maintenance scheduling
    
    Phase 1 Constraints:
    - LOW/MEDIUM interaction only (no HIGH)
    - Manual approval for asset modifications
    - Continuous credibility assessment
    - Zero response automation
    
    Critical Success Factor:
    Asset credibility determines intelligence quality.
    Low credibility = Attacker detection = Intelligence failure.
    
    "Paradoxo do Realismo":
    Maintaining convincing deception requires continuous curation.
    Not "configure and forget" - it's gardening in a minefield.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize deception asset service.
        
        Args:
            session: Async database session
        """
        self.session = session
        self.asset_repository = DeceptionAssetRepository(session)
        self.interaction_repository = AssetInteractionRepository(session)
        self._credibility_threshold = 0.5  # Minimum acceptable credibility
    
    async def deploy_asset(
        self,
        asset: DeceptionAssetCreate,
        validate_phase1_constraints: bool = True
    ) -> DeceptionAsset:
        """
        Deploy new deception asset.
        
        Critical operation requiring human approval in production.
        
        Args:
            asset: DeceptionAssetCreate DTO
            validate_phase1_constraints: Enforce Phase 1 safety constraints
        
        Returns:
            Deployed DeceptionAsset
        
        Raises:
            ValueError: If Phase 1 constraints violated
            DuplicateError: If IP address already in use
            DatabaseError: On database errors
        
        Example:
            >>> asset = DeceptionAssetCreate(
            ...     name="honeypot-ssh-01",
            ...     asset_type=AssetType.HONEYPOT_SSH,
            ...     interaction_level=AssetInteractionLevel.LOW,
            ...     ip_address="10.0.1.100",
            ...     port=22,
            ...     network_segment="dmz-vlan10",
            ...     credibility=AssetCredibility(
            ...         realism_score=0.85,
            ...         service_authenticity=0.9,
            ...         data_authenticity=0.8,
            ...         network_integration=0.85,
            ...         assessment_method="manual_review"
            ...     ),
            ...     telemetry=AssetTelemetry(...),
            ...     deployed_by="security_team"
            ... )
            >>> deployed = await service.deploy_asset(asset)
        """
        logger.info(
            f"Deploying deception asset: {asset.name} ({asset.asset_type}) "
            f"at {asset.ip_address}:{asset.port}"
        )
        
        # Phase 1 constraint validation
        if validate_phase1_constraints:
            if asset.interaction_level == AssetInteractionLevel.HIGH:
                raise ValueError(
                    "HIGH interaction assets prohibited in Phase 1. "
                    "Risk: Containment failure and attacker pivot to production. "
                    "Use LOW or MEDIUM interaction only."
                )
            
            if asset.credibility.realism_score < 0.6:
                logger.warning(
                    f"Asset {asset.name} has low initial credibility "
                    f"({asset.credibility.realism_score}). May be ineffective."
                )
        
        # Check IP uniqueness
        existing_asset = await self.asset_repository.get_asset_by_ip(asset.ip_address)
        if existing_asset:
            raise ValueError(f"IP address {asset.ip_address} already in use by {existing_asset.name}")
        
        # Deploy asset
        deployed_asset = await self.asset_repository.create_from_model(asset)
        
        logger.info(
            f"Deception asset deployed: {deployed_asset.id} ({deployed_asset.name}) "
            f"with credibility {deployed_asset.credibility.realism_score:.2f}"
        )
        
        return deployed_asset
    
    async def get_asset(self, asset_id: UUID) -> Optional[DeceptionAsset]:
        """
        Retrieve deception asset by ID.
        
        Args:
            asset_id: Asset UUID
        
        Returns:
            DeceptionAsset if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        asset = await self.asset_repository.get_by_id(asset_id)
        if asset:
            return self.asset_repository._to_pydantic(asset)
        return None
    
    async def get_active_assets(
        self,
        asset_type: Optional[AssetType] = None,
        min_credibility: Optional[float] = None
    ) -> List[DeceptionAsset]:
        """
        Get all active deception assets.
        
        Args:
            asset_type: Optional filter by asset type
            min_credibility: Optional minimum credibility threshold
        
        Returns:
            List of active assets ordered by credibility
        
        Raises:
            DatabaseError: On database errors
        """
        if min_credibility is None:
            min_credibility = self._credibility_threshold
        
        return await self.asset_repository.get_active_assets(
            asset_type=asset_type,
            min_credibility=min_credibility
        )
    
    async def record_interaction(
        self,
        asset_id: UUID,
        source_ip: str,
        interaction_type: str,
        command: Optional[str] = None,
        payload: Optional[str] = None,
        indicators_extracted: Optional[List[str]] = None,
        mitre_technique: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssetInteractionEvent:
        """
        Record attacker interaction with deception asset.
        
        Critical intelligence collection point.
        Every interaction is suspicious by definition (asset is decoy).
        
        Args:
            asset_id: Asset that was interacted with
            source_ip: Attacker IP
            interaction_type: Type of interaction (connection, command, file_access, etc.)
            command: Command executed if applicable
            payload: Request payload if applicable
            indicators_extracted: IoCs extracted from interaction
            mitre_technique: MITRE technique ID if identified
            metadata: Additional context
        
        Returns:
            Created AssetInteractionEvent
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        
        Example:
            >>> interaction = await service.record_interaction(
            ...     asset_id=honeypot_id,
            ...     source_ip="203.0.113.1",
            ...     interaction_type="ssh_login_attempt",
            ...     command="cat /etc/passwd",
            ...     indicators_extracted=["203.0.113.1"],
            ...     mitre_technique="T1087"
            ... )
        """
        logger.info(
            f"Recording interaction on asset {asset_id} from {source_ip}: "
            f"{interaction_type}"
        )
        
        # Create interaction event
        interaction = AssetInteractionEvent(
            asset_id=asset_id,
            source_ip=source_ip,
            interaction_type=interaction_type,
            command=command,
            payload=payload,
            indicators_extracted=indicators_extracted or [],
            mitre_technique=mitre_technique,
            metadata=metadata or {}
        )
        
        created_interaction = await self.interaction_repository.create_from_model(interaction)
        
        # Update asset statistics
        # Check if this is a new attacker
        existing_interactions = await self.interaction_repository.get_attacker_interactions(
            source_ip=source_ip
        )
        is_new_attacker = len(existing_interactions) == 1  # Only the one we just created
        
        await self.asset_repository.update_interaction_stats(
            asset_id=asset_id,
            new_interaction=True,
            new_attacker=is_new_attacker
        )
        
        # Increment intelligence value if TTP discovered
        if mitre_technique:
            await self.asset_repository.increment_intelligence_value(
                asset_id=asset_id,
                new_ttp=mitre_technique
            )
        
        logger.info(f"Interaction recorded: {created_interaction.id}")
        
        return created_interaction
    
    async def get_asset_interactions(
        self,
        asset_id: UUID,
        time_window_hours: Optional[int] = None,
        limit: int = 100
    ) -> List[AssetInteractionEvent]:
        """
        Get all interactions for specific asset.
        
        Args:
            asset_id: Asset UUID
            time_window_hours: Optional time window (hours back from now)
            limit: Maximum interactions to retrieve
        
        Returns:
            List of interaction events
        
        Raises:
            DatabaseError: On database errors
        """
        end_time = datetime.utcnow()
        start_time = None
        if time_window_hours:
            start_time = end_time - timedelta(hours=time_window_hours)
        
        return await self.interaction_repository.get_asset_interactions(
            asset_id=asset_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    
    async def get_attacker_behavior(
        self,
        source_ip: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze attacker behavior across all assets.
        
        Provides cross-asset correlation for TTP identification.
        
        Args:
            source_ip: Attacker IP address
            limit: Maximum interactions to analyze
        
        Returns:
            Dictionary with behavioral analysis:
                - total_interactions
                - assets_targeted
                - interaction_types
                - commands_executed
                - ttps_observed
                - first_seen
                - last_seen
        
        Raises:
            DatabaseError: On database errors
        """
        interactions = await self.interaction_repository.get_attacker_interactions(
            source_ip=source_ip,
            limit=limit
        )
        
        if not interactions:
            return {
                "total_interactions": 0,
                "assets_targeted": [],
                "interaction_types": [],
                "commands_executed": [],
                "ttps_observed": [],
                "first_seen": None,
                "last_seen": None
            }
        
        # Analyze behavior pattern
        assets_targeted = list(set(i.asset_id for i in interactions))
        interaction_types = list(set(i.interaction_type for i in interactions))
        commands = [i.command for i in interactions if i.command]
        ttps = list(set(i.mitre_technique for i in interactions if i.mitre_technique))
        
        return {
            "total_interactions": len(interactions),
            "assets_targeted": assets_targeted,
            "assets_targeted_count": len(assets_targeted),
            "interaction_types": interaction_types,
            "commands_executed": commands,
            "unique_commands": len(set(commands)),
            "ttps_observed": ttps,
            "first_seen": min(i.timestamp for i in interactions),
            "last_seen": max(i.timestamp for i in interactions),
            "duration_hours": (max(i.timestamp for i in interactions) - 
                             min(i.timestamp for i in interactions)).total_seconds() / 3600
        }
    
    async def update_credibility(
        self,
        asset_id: UUID,
        new_credibility: AssetCredibility
    ) -> DeceptionAsset:
        """
        Update asset credibility assessment.
        
        Critical for "Paradoxo do Realismo" management.
        Low credibility indicates attacker detection risk.
        
        Args:
            asset_id: Asset UUID
            new_credibility: Updated credibility assessment
        
        Returns:
            Updated DeceptionAsset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        logger.info(f"Updating credibility for asset {asset_id}: {new_credibility.realism_score:.2f}")
        
        updated_asset = await self.asset_repository.update_from_model(
            asset_id,
            DeceptionAssetUpdate(credibility=new_credibility)
        )
        
        # Alert if credibility dropped below threshold
        if new_credibility.realism_score < self._credibility_threshold:
            logger.warning(
                f"Asset {updated_asset.name} credibility dropped below threshold: "
                f"{new_credibility.realism_score:.2f} < {self._credibility_threshold}. "
                f"Recommendation: Review and update or decommission."
            )
        
        return updated_asset
    
    async def get_assets_needing_maintenance(self) -> List[DeceptionAsset]:
        """
        Get assets requiring maintenance attention.
        
        Identifies assets with:
        - Passed maintenance schedule
        - Low credibility scores
        - No recent interactions (possible attacker detection)
        
        Returns:
            List of assets needing attention
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.asset_repository.get_assets_needing_maintenance()
    
    async def schedule_maintenance(
        self,
        asset_id: UUID,
        next_maintenance: datetime,
        notes: Optional[str] = None
    ) -> DeceptionAsset:
        """
        Schedule maintenance for deception asset.
        
        Args:
            asset_id: Asset UUID
            next_maintenance: Next scheduled maintenance date
            notes: Optional maintenance notes
        
        Returns:
            Updated DeceptionAsset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        logger.info(f"Scheduling maintenance for asset {asset_id}: {next_maintenance}")
        
        return await self.asset_repository.update_from_model(
            asset_id,
            DeceptionAssetUpdate(
                last_maintenance=datetime.utcnow(),
                next_maintenance=next_maintenance,
                maintenance_notes=notes
            )
        )
    
    async def decommission_asset(
        self,
        asset_id: UUID,
        reason: str
    ) -> DeceptionAsset:
        """
        Decommission deception asset.
        
        Sets status to RETIRED and logs reason.
        Asset data retained for historical analysis.
        
        Args:
            asset_id: Asset UUID
            reason: Reason for decommissioning
        
        Returns:
            Updated DeceptionAsset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        logger.info(f"Decommissioning asset {asset_id}: {reason}")
        
        return await self.asset_repository.update_from_model(
            asset_id,
            DeceptionAssetUpdate(
                status=AssetStatus.RETIRED,
                metadata={"decommission_reason": reason, "decommission_date": datetime.utcnow().isoformat()}
            )
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate deception asset statistics.
        
        Supports dashboard metrics and Phase 1 effectiveness tracking.
        
        Returns:
            Statistics dictionary
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.asset_repository.get_asset_statistics()
