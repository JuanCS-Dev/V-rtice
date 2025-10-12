"""
Reactive Fabric - Threat Event Repository.

Specialized repository for threat event database operations.
Supports high-volume ingestion and complex intelligence queries.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import ThreatEventDB
from . import BaseRepository, DatabaseError
from ...models.threat import (
    ThreatSeverity, ThreatCategory, DetectionSource,
    ThreatEvent, ThreatEventCreate, ThreatEventUpdate, ThreatEventQuery
)


class ThreatEventRepository(BaseRepository[ThreatEventDB]):
    """
    Threat event repository with intelligence-optimized queries.
    
    Core data access layer for threat detection pipeline.
    Optimized for:
    - High-volume event ingestion
    - Time-series analysis
    - Attacker correlation queries
    - Intelligence enrichment workflows
    
    Phase 1 Focus:
    All events are passive observations. No response automation.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize threat event repository."""
        super().__init__(ThreatEventDB, session)
    
    async def create_from_model(self, event: ThreatEventCreate) -> ThreatEvent:
        """
        Create threat event from Pydantic model.
        
        Args:
            event: ThreatEventCreate DTO
        
        Returns:
            Complete ThreatEvent with generated ID
        
        Raises:
            DatabaseError: On database errors
        """
        # Convert Pydantic model to dict for database insertion
        event_data = event.dict()
        
        # Convert nested Pydantic models to dicts
        if event_data.get('indicators'):
            event_data['indicators'] = [ind.dict() if hasattr(ind, 'dict') else ind 
                                       for ind in event_data['indicators']]
        
        if event_data.get('mitre_mapping'):
            event_data['mitre_mapping'] = (event_data['mitre_mapping'].dict() 
                                          if hasattr(event_data['mitre_mapping'], 'dict') 
                                          else event_data['mitre_mapping'])
        
        db_event = await self.create(**event_data)
        
        # Convert back to Pydantic model
        return self._to_pydantic(db_event)
    
    async def update_from_model(self, event_id: UUID, update: ThreatEventUpdate) -> ThreatEvent:
        """
        Update threat event from Pydantic model.
        
        Args:
            event_id: Event UUID
            update: ThreatEventUpdate DTO with fields to update
        
        Returns:
            Updated ThreatEvent
        
        Raises:
            NotFoundError: If event not found
            DatabaseError: On database errors
        """
        # Only include fields that were explicitly set
        update_data = update.dict(exclude_unset=True)
        
        # Convert nested Pydantic models
        if 'indicators' in update_data and update_data['indicators']:
            update_data['indicators'] = [ind.dict() if hasattr(ind, 'dict') else ind 
                                        for ind in update_data['indicators']]
        
        if 'mitre_mapping' in update_data and update_data['mitre_mapping']:
            update_data['mitre_mapping'] = (update_data['mitre_mapping'].dict() 
                                           if hasattr(update_data['mitre_mapping'], 'dict') 
                                           else update_data['mitre_mapping'])
        
        db_event = await self.update(event_id, **update_data)
        return self._to_pydantic(db_event)
    
    async def query_events(self, query: ThreatEventQuery) -> List[ThreatEvent]:
        """
        Query threat events with complex filters.
        
        Supports intelligence analyst investigation workflows.
        
        Args:
            query: ThreatEventQuery with filter parameters
        
        Returns:
            List of matching ThreatEvents
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(ThreatEventDB)
            
            # Apply filters
            conditions = []
            
            if query.severity:
                conditions.append(ThreatEventDB.severity.in_(query.severity))
            
            if query.category:
                conditions.append(ThreatEventDB.category.in_(query.category))
            
            if query.source:
                conditions.append(ThreatEventDB.source.in_(query.source))
            
            if query.source_ip:
                conditions.append(ThreatEventDB.source_ip == query.source_ip)
            
            if query.destination_ip:
                conditions.append(ThreatEventDB.destination_ip == query.destination_ip)
            
            if query.start_time:
                conditions.append(ThreatEventDB.timestamp >= query.start_time)
            
            if query.end_time:
                conditions.append(ThreatEventDB.timestamp <= query.end_time)
            
            if query.is_analyzed is not None:
                conditions.append(ThreatEventDB.is_analyzed == query.is_analyzed)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Order by timestamp descending (most recent first)
            stmt = stmt.order_by(desc(ThreatEventDB.timestamp))
            
            # Pagination
            stmt = stmt.limit(query.limit).offset(query.offset)
            
            result = await self.session.execute(stmt)
            db_events = result.scalars().all()
            
            return [self._to_pydantic(event) for event in db_events]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_unanalyzed_events(
        self,
        severity: Optional[List[ThreatSeverity]] = None,
        limit: int = 100
    ) -> List[ThreatEvent]:
        """
        Retrieve unanalyzed threat events for intelligence processing.
        
        Critical for intelligence pipeline workflow.
        
        Args:
            severity: Optional severity filter (prioritize CRITICAL/HIGH)
            limit: Maximum events to retrieve
        
        Returns:
            List of unanalyzed ThreatEvents ordered by severity then time
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(ThreatEventDB).where(
                ThreatEventDB.is_analyzed == False
            )
            
            if severity:
                stmt = stmt.where(ThreatEventDB.severity.in_(severity))
            
            # Order by severity (CRITICAL first) then timestamp
            severity_order = {
                ThreatSeverity.CRITICAL: 1,
                ThreatSeverity.HIGH: 2,
                ThreatSeverity.MEDIUM: 3,
                ThreatSeverity.LOW: 4,
                ThreatSeverity.INFO: 5
            }
            
            # For now, use timestamp ordering (proper severity ordering requires CASE expression)
            stmt = stmt.order_by(
                desc(ThreatEventDB.timestamp)
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            db_events = result.scalars().all()
            
            # Sort in Python by severity then timestamp
            sorted_events = sorted(
                db_events,
                key=lambda e: (severity_order.get(e.severity, 99), -e.timestamp.timestamp())
            )
            
            return [self._to_pydantic(event) for event in sorted_events]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_events_by_source_ip(
        self,
        source_ip: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ThreatEvent]:
        """
        Retrieve all events from specific source IP.
        
        Enables attacker behavior correlation and campaign tracking.
        
        Args:
            source_ip: Source IP address
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum events to retrieve
        
        Returns:
            List of ThreatEvents from that IP
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(ThreatEventDB).where(
                ThreatEventDB.source_ip == source_ip
            )
            
            if start_time:
                stmt = stmt.where(ThreatEventDB.timestamp >= start_time)
            
            if end_time:
                stmt = stmt.where(ThreatEventDB.timestamp <= end_time)
            
            stmt = stmt.order_by(desc(ThreatEventDB.timestamp)).limit(limit)
            
            result = await self.session.execute(stmt)
            db_events = result.scalars().all()
            
            return [self._to_pydantic(event) for event in db_events]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_event_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics for threat events.
        
        Supports dashboard metrics and Phase 1 success tracking.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
        
        Returns:
            Dictionary with statistics:
                - total_events
                - events_by_severity
                - events_by_category
                - events_by_source
                - unique_source_ips
                - analyzed_percentage
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            conditions = []
            if start_time:
                conditions.append(ThreatEventDB.timestamp >= start_time)
            if end_time:
                conditions.append(ThreatEventDB.timestamp <= end_time)
            
            base_query = select(ThreatEventDB)
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Total events
            total_result = await self.session.execute(
                select(func.count()).select_from(ThreatEventDB).where(and_(*conditions) if conditions else True)
            )
            total_events = total_result.scalar_one()
            
            # Get all events for grouping (could be optimized with group_by queries)
            result = await self.session.execute(base_query)
            events = result.scalars().all()
            
            # Calculate statistics
            stats = {
                "total_events": total_events,
                "events_by_severity": {},
                "events_by_category": {},
                "events_by_source": {},
                "unique_source_ips": len(set(e.source_ip for e in events)),
                "analyzed_count": sum(1 for e in events if e.is_analyzed),
                "analyzed_percentage": (sum(1 for e in events if e.is_analyzed) / total_events * 100) if total_events > 0 else 0
            }
            
            # Group by severity
            for event in events:
                severity = str(event.severity)
                stats["events_by_severity"][severity] = stats["events_by_severity"].get(severity, 0) + 1
            
            # Group by category
            for event in events:
                category = str(event.category)
                stats["events_by_category"][category] = stats["events_by_category"].get(category, 0) + 1
            
            # Group by source
            for event in events:
                source = str(event.source)
                stats["events_by_source"][source] = stats["events_by_source"].get(source, 0) + 1
            
            return stats
        
        except Exception as e:
            raise DatabaseError(f"Statistics query error: {str(e)}") from e
    
    async def mark_as_analyzed(self, event_id: UUID) -> ThreatEvent:
        """
        Mark threat event as analyzed.
        
        Critical state transition in intelligence pipeline.
        
        Args:
            event_id: Event UUID
        
        Returns:
            Updated ThreatEvent
        
        Raises:
            NotFoundError: If event not found
            DatabaseError: On database errors
        """
        return await self.update_from_model(
            event_id,
            ThreatEventUpdate(
                is_analyzed=True,
                analysis_timestamp=datetime.utcnow()
            )
        )
    
    def _to_pydantic(self, db_event: ThreatEventDB) -> ThreatEvent:
        """
        Convert database model to Pydantic model.
        
        Args:
            db_event: SQLAlchemy model instance
        
        Returns:
            Pydantic ThreatEvent model
        """
        return ThreatEvent(
            id=db_event.id,
            timestamp=db_event.timestamp,
            source=db_event.source,
            severity=db_event.severity,
            category=db_event.category,
            title=db_event.title,
            description=db_event.description,
            source_ip=db_event.source_ip,
            source_port=db_event.source_port,
            destination_ip=db_event.destination_ip,
            destination_port=db_event.destination_port,
            protocol=db_event.protocol,
            indicators=db_event.indicators or [],
            mitre_mapping=db_event.mitre_mapping,
            geolocation=db_event.geolocation,
            threat_intel_match=db_event.threat_intel_match,
            raw_payload=db_event.raw_payload,
            parsed_payload=db_event.parsed_payload,
            is_analyzed=db_event.is_analyzed,
            analysis_timestamp=db_event.analysis_timestamp,
            related_events=db_event.related_events or [],
            metadata=db_event.metadata or {}
        )
