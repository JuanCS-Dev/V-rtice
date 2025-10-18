"""
Reactive Fabric - Deception Asset Repository.

Specialized repository for deception asset and interaction management.
Critical for "Ilha de Sacrifício" operational effectiveness tracking.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import DeceptionAssetDB, AssetInteractionEventDB
from . import BaseRepository, DatabaseError
from ...models.deception import (
    AssetType, AssetStatus,
    DeceptionAsset, DeceptionAssetCreate, DeceptionAssetUpdate,
    AssetInteractionEvent
)


class DeceptionAssetRepository(BaseRepository[DeceptionAssetDB]):
    """
    Deception asset repository with credibility tracking.
    
    Manages honeypots, decoys and canary tokens forming the
    "Ilha de Sacrifício" (Sacrifice Island) infrastructure.
    
    Phase 1 Constraints:
    - Only LOW/MEDIUM interaction assets
    - Continuous credibility monitoring
    - Intelligence value tracking
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize deception asset repository."""
        super().__init__(DeceptionAssetDB, session)
    
    async def create_from_model(self, asset: DeceptionAssetCreate) -> DeceptionAsset:
        """
        Create deception asset from Pydantic model.
        
        Args:
            asset: DeceptionAssetCreate DTO
        
        Returns:
            Complete DeceptionAsset with generated ID
        
        Raises:
            DuplicateError: If IP address already in use
            DatabaseError: On database errors
        """
        asset_data = asset.dict()
        
        # Extract credibility for storage
        credibility = asset_data.pop('credibility')
        credibility_dict = credibility.dict() if hasattr(credibility, 'dict') else credibility
        asset_data['credibility_score'] = credibility_dict['realism_score']
        asset_data['credibility_data'] = credibility_dict
        
        # Extract telemetry
        telemetry = asset_data.pop('telemetry')
        asset_data['telemetry_config'] = telemetry.dict() if hasattr(telemetry, 'dict') else telemetry
        
        db_asset = await self.create(**asset_data)
        return self._to_pydantic(db_asset)
    
    async def update_from_model(self, asset_id: UUID, update: DeceptionAssetUpdate) -> DeceptionAsset:
        """
        Update deception asset from Pydantic model.
        
        Args:
            asset_id: Asset UUID
            update: DeceptionAssetUpdate DTO
        
        Returns:
            Updated DeceptionAsset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        update_data = update.dict(exclude_unset=True)
        
        # Handle credibility update
        if 'credibility' in update_data and update_data['credibility']:
            credibility = update_data.pop('credibility')
            credibility_dict = credibility.dict() if hasattr(credibility, 'dict') else credibility
            update_data['credibility_score'] = credibility_dict['realism_score']
            update_data['credibility_data'] = credibility_dict
            update_data['last_credibility_update'] = datetime.utcnow()
        
        # Handle telemetry update
        if 'telemetry' in update_data and update_data['telemetry']:
            telemetry = update_data.pop('telemetry')
            update_data['telemetry_config'] = telemetry.dict() if hasattr(telemetry, 'dict') else telemetry
        
        db_asset = await self.update(asset_id, **update_data)
        return self._to_pydantic(db_asset)
    
    async def get_active_assets(
        self,
        asset_type: Optional[AssetType] = None,
        min_credibility: float = 0.0
    ) -> List[DeceptionAsset]:
        """
        Get all active deception assets.
        
        Args:
            asset_type: Optional filter by asset type
            min_credibility: Minimum credibility score threshold
        
        Returns:
            List of active assets
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(DeceptionAssetDB).where(
                and_(
                    DeceptionAssetDB.status == AssetStatus.ACTIVE,
                    DeceptionAssetDB.credibility_score >= min_credibility
                )
            )
            
            if asset_type:
                stmt = stmt.where(DeceptionAssetDB.asset_type == asset_type)
            
            stmt = stmt.order_by(desc(DeceptionAssetDB.credibility_score))
            
            result = await self.session.execute(stmt)
            db_assets = result.scalars().all()
            
            return [self._to_pydantic(asset) for asset in db_assets]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_assets_needing_maintenance(self) -> List[DeceptionAsset]:
        """
        Get assets that need maintenance.
        
        Identifies assets with:
        - next_maintenance date passed
        - Low credibility scores
        - No recent interactions (potential detection by attackers)
        
        Returns:
            List of assets needing attention
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            now = datetime.utcnow()
            
            stmt = select(DeceptionAssetDB).where(
                and_(
                    DeceptionAssetDB.status == AssetStatus.ACTIVE,
                    or_(
                        DeceptionAssetDB.next_maintenance <= now,
                        DeceptionAssetDB.credibility_score < 0.5
                    )
                )
            ).order_by(asc(DeceptionAssetDB.next_maintenance))
            
            result = await self.session.execute(stmt)
            db_assets = result.scalars().all()
            
            return [self._to_pydantic(asset) for asset in db_assets]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def update_interaction_stats(
        self,
        asset_id: UUID,
        new_interaction: bool = True,
        new_attacker: bool = False
    ) -> DeceptionAsset:
        """
        Update asset interaction statistics.
        
        Called when attacker interacts with asset.
        
        Args:
            asset_id: Asset UUID
            new_interaction: Increment interaction count
            new_attacker: Increment unique attacker count
        
        Returns:
            Updated asset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        asset = await self.get_by_id_or_raise(asset_id)
        
        update_data = {
            'last_interaction': datetime.utcnow()
        }
        
        if new_interaction:
            update_data['total_interactions'] = asset.total_interactions + 1
        
        if new_attacker:
            update_data['unique_attackers'] = asset.unique_attackers + 1
        
        return await self.update_from_model(
            asset_id,
            DeceptionAssetUpdate(**update_data)
        )
    
    async def increment_intelligence_value(
        self,
        asset_id: UUID,
        new_ttp: Optional[str] = None
    ) -> DeceptionAsset:
        """
        Increment asset intelligence value metrics.
        
        Tracks contribution to threat intelligence.
        
        Args:
            asset_id: Asset UUID
            new_ttp: Optional new TTP discovered
        
        Returns:
            Updated asset
        
        Raises:
            NotFoundError: If asset not found
            DatabaseError: On database errors
        """
        asset = await self.get_by_id_or_raise(asset_id)
        
        ttps = list(asset.ttps_discovered)
        if new_ttp and new_ttp not in ttps:
            ttps.append(new_ttp)
        
        db_asset = await self.update(
            asset_id,
            intelligence_events_generated=asset.intelligence_events_generated + 1,
            ttps_discovered=ttps
        )
        
        return self._to_pydantic(db_asset)
    
    async def get_asset_by_ip(self, ip_address: str) -> Optional[DeceptionAsset]:
        """
        Get asset by IP address.
        
        Args:
            ip_address: Asset IP
        
        Returns:
            Asset if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            result = await self.session.execute(
                select(DeceptionAssetDB).where(DeceptionAssetDB.ip_address == ip_address)
            )
            db_asset = result.scalar_one_or_none()
            
            if db_asset:
                return self._to_pydantic(db_asset)
            return None
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_asset_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for deception assets.
        
        Returns:
            Dictionary with statistics:
                - total_assets
                - active_assets
                - assets_by_type
                - average_credibility
                - total_interactions
                - assets_with_recent_interactions
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            # Get all assets
            result = await self.session.execute(select(DeceptionAssetDB))
            assets = result.scalars().all()
            
            total_assets = len(assets)
            active_assets = sum(1 for a in assets if a.status == AssetStatus.ACTIVE)
            
            # Calculate statistics
            stats = {
                "total_assets": total_assets,
                "active_assets": active_assets,
                "assets_by_type": {},
                "assets_by_status": {},
                "average_credibility": sum(a.credibility_score for a in assets) / total_assets if total_assets > 0 else 0,
                "total_interactions": sum(a.total_interactions for a in assets),
                "total_unique_attackers": sum(a.unique_attackers for a in assets),
                "assets_with_recent_interactions": sum(1 for a in assets if a.last_interaction and 
                                                      (datetime.utcnow() - a.last_interaction).days <= 7)
            }
            
            # Group by type
            for asset in assets:
                asset_type = str(asset.asset_type)
                stats["assets_by_type"][asset_type] = stats["assets_by_type"].get(asset_type, 0) + 1
            
            # Group by status
            for asset in assets:
                status = str(asset.status)
                stats["assets_by_status"][status] = stats["assets_by_status"].get(status, 0) + 1
            
            return stats
        
        except Exception as e:
            raise DatabaseError(f"Statistics query error: {str(e)}") from e
    
    def _to_pydantic(self, db_asset: DeceptionAssetDB) -> DeceptionAsset:
        """Convert database model to Pydantic model."""
        from ...models.deception import AssetCredibility, AssetTelemetry
        
        return DeceptionAsset(
            id=db_asset.id,
            name=db_asset.name,
            asset_type=db_asset.asset_type,
            interaction_level=db_asset.interaction_level,
            status=db_asset.status,
            ip_address=db_asset.ip_address,
            port=db_asset.port,
            hostname=db_asset.hostname,
            network_segment=db_asset.network_segment,
            service_banner=db_asset.service_banner,
            emulated_os=db_asset.emulated_os,
            emulated_software=db_asset.emulated_software or [],
            decoy_data_profile=db_asset.decoy_data_profile,
            credibility=AssetCredibility(**db_asset.credibility_data),
            last_credibility_update=db_asset.last_credibility_update,
            telemetry=AssetTelemetry(**db_asset.telemetry_config),
            deployed_at=db_asset.deployed_at,
            deployed_by=db_asset.deployed_by,
            last_interaction=db_asset.last_interaction,
            total_interactions=db_asset.total_interactions,
            unique_attackers=db_asset.unique_attackers,
            intelligence_events_generated=db_asset.intelligence_events_generated,
            ttps_discovered=db_asset.ttps_discovered or [],
            last_maintenance=db_asset.last_maintenance,
            next_maintenance=db_asset.next_maintenance,
            maintenance_notes=db_asset.maintenance_notes,
            metadata=db_asset.metadata or {}
        )


class AssetInteractionRepository(BaseRepository[AssetInteractionEventDB]):
    """
    Asset interaction event repository.
    
    Tracks every attacker interaction with deception assets.
    Primary intelligence collection stream for Phase 1.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize interaction repository."""
        super().__init__(AssetInteractionEventDB, session)
    
    async def create_from_model(self, interaction: AssetInteractionEvent) -> AssetInteractionEvent:
        """
        Create interaction event from Pydantic model.
        
        Args:
            interaction: AssetInteractionEvent DTO
        
        Returns:
            Created interaction with generated ID
        
        Raises:
            DatabaseError: On database errors
        """
        interaction_data = interaction.dict()
        db_interaction = await self.create(**interaction_data)
        return self._to_pydantic(db_interaction)
    
    async def get_asset_interactions(
        self,
        asset_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AssetInteractionEvent]:
        """
        Get all interactions for specific asset.
        
        Args:
            asset_id: Asset UUID
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum interactions to retrieve
        
        Returns:
            List of interaction events
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(AssetInteractionEventDB).where(
                AssetInteractionEventDB.asset_id == asset_id
            )
            
            if start_time:
                stmt = stmt.where(AssetInteractionEventDB.timestamp >= start_time)
            
            if end_time:
                stmt = stmt.where(AssetInteractionEventDB.timestamp <= end_time)
            
            stmt = stmt.order_by(desc(AssetInteractionEventDB.timestamp)).limit(limit)
            
            result = await self.session.execute(stmt)
            db_interactions = result.scalars().all()
            
            return [self._to_pydantic(interaction) for interaction in db_interactions]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_attacker_interactions(
        self,
        source_ip: str,
        limit: int = 100
    ) -> List[AssetInteractionEvent]:
        """
        Get all interactions from specific attacker IP.
        
        Enables attacker behavior tracking across multiple assets.
        
        Args:
            source_ip: Attacker IP address
            limit: Maximum interactions to retrieve
        
        Returns:
            List of interaction events
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(AssetInteractionEventDB).where(
                AssetInteractionEventDB.source_ip == source_ip
            ).order_by(desc(AssetInteractionEventDB.timestamp)).limit(limit)
            
            result = await self.session.execute(stmt)
            db_interactions = result.scalars().all()
            
            return [self._to_pydantic(interaction) for interaction in db_interactions]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    def _to_pydantic(self, db_interaction: AssetInteractionEventDB) -> AssetInteractionEvent:
        """Convert database model to Pydantic model."""
        return AssetInteractionEvent(
            id=db_interaction.id,
            asset_id=db_interaction.asset_id,
            timestamp=db_interaction.timestamp,
            source_ip=db_interaction.source_ip,
            source_port=db_interaction.source_port,
            session_id=db_interaction.session_id,
            interaction_type=db_interaction.interaction_type,
            command=db_interaction.command,
            payload=db_interaction.payload,
            response=db_interaction.response,
            indicators_extracted=db_interaction.indicators_extracted or [],
            mitre_technique=db_interaction.mitre_technique,
            threat_event_id=db_interaction.threat_event_id,
            raw_log=db_interaction.raw_log,
            metadata=db_interaction.metadata or {}
        )
