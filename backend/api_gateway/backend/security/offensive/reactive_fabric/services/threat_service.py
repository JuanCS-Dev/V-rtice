"""
Reactive Fabric - Threat Event Service.

Business logic for threat event processing, enrichment and analysis.
Implements Phase 1 passive threat intelligence collection pipeline.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.repositories.threat_repository import ThreatEventRepository
from ..models.threat import (
    ThreatEvent, ThreatEventCreate, ThreatEventUpdate, ThreatEventQuery,
    ThreatSeverity, ThreatCategory, ThreatIndicator
)


logger = logging.getLogger(__name__)


class ThreatEventService:
    """
    Threat event service with enrichment pipeline.
    
    Orchestrates threat event lifecycle:
    1. Ingestion from detection sources
    2. Automatic enrichment (geolocation, threat intel)
    3. MITRE ATT&CK mapping
    4. Correlation with existing events
    5. Intelligence analysis preparation
    
    Phase 1 Philosophy:
    Every event is passive observation. Zero automated responses.
    All events flow to intelligence analysis for human review.
    
    Consciousness Parallel:
    Like perceptual binding in biological consciousness, this service
    integrates distributed threat signals into coherent event representations.
    No phenomenological experience, but systematic pattern recognition.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize threat event service.
        
        Args:
            session: Async database session (managed by FastAPI dependency)
        """
        self.session = session
        self.repository = ThreatEventRepository(session)
        self._enrichment_enabled = True  # Feature flag for enrichment pipeline
    
    async def create_event(
        self,
        event: ThreatEventCreate,
        auto_enrich: bool = True
    ) -> ThreatEvent:
        """
        Create new threat event with optional enrichment.
        
        Primary ingestion point for all detection sources.
        
        Args:
            event: ThreatEventCreate DTO
            auto_enrich: Run enrichment pipeline automatically
        
        Returns:
            Created and optionally enriched ThreatEvent
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> event = ThreatEventCreate(
            ...     source=DetectionSource.HONEYPOT,
            ...     severity=ThreatSeverity.HIGH,
            ...     category=ThreatCategory.INITIAL_ACCESS,
            ...     title="SSH brute force attempt",
            ...     description="Multiple failed login attempts from 203.0.113.1",
            ...     source_ip="203.0.113.1",
            ...     destination_ip="10.0.1.50",
            ...     destination_port=22
            ... )
            >>> created_event = await service.create_event(event)
        """
        logger.info(
            f"Creating threat event: {event.title} from {event.source_ip} "
            f"(severity={event.severity}, category={event.category})"
        )
        
        # Persist to database
        created_event = await self.repository.create_from_model(event)
        
        # Run enrichment pipeline if enabled
        if auto_enrich and self._enrichment_enabled:
            created_event = await self._enrich_event(created_event)
        
        logger.info(f"Threat event created: {created_event.id}")
        
        return created_event
    
    async def get_event(self, event_id: UUID) -> Optional[ThreatEvent]:
        """
        Retrieve threat event by ID.
        
        Args:
            event_id: Event UUID
        
        Returns:
            ThreatEvent if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        event = await self.repository.get_by_id(event_id)
        if event:
            return self.repository._to_pydantic(event)
        return None
    
    async def query_events(self, query: ThreatEventQuery) -> List[ThreatEvent]:
        """
        Query threat events with filters.
        
        Supports analyst investigation workflows.
        
        Args:
            query: ThreatEventQuery with filter parameters
        
        Returns:
            List of matching threat events
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> query = ThreatEventQuery(
            ...     severity=[ThreatSeverity.CRITICAL, ThreatSeverity.HIGH],
            ...     is_analyzed=False,
            ...     limit=50
            ... )
            >>> events = await service.query_events(query)
        """
        return await self.repository.query_events(query)
    
    async def get_unanalyzed_events(
        self,
        priority_severity: Optional[List[ThreatSeverity]] = None,
        limit: int = 100
    ) -> List[ThreatEvent]:
        """
        Get unanalyzed threat events for intelligence processing.
        
        Critical for intelligence pipeline workflow.
        Prioritizes by severity: CRITICAL > HIGH > MEDIUM > LOW > INFO.
        
        Args:
            priority_severity: Optional severity filter
            limit: Maximum events to retrieve
        
        Returns:
            List of unanalyzed events ordered by priority
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> # Get high-priority unanalyzed events
            >>> events = await service.get_unanalyzed_events(
            ...     priority_severity=[ThreatSeverity.CRITICAL, ThreatSeverity.HIGH]
            ... )
        """
        return await self.repository.get_unanalyzed_events(
            severity=priority_severity,
            limit=limit
        )
    
    async def correlate_events_by_ip(
        self,
        source_ip: str,
        time_window_hours: int = 24
    ) -> List[ThreatEvent]:
        """
        Correlate all events from specific source IP within time window.
        
        Enables attacker behavior pattern analysis and campaign tracking.
        Critical for TTP identification.
        
        Args:
            source_ip: Attacker source IP
            time_window_hours: Time window for correlation
        
        Returns:
            List of correlated threat events
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> # Find all activity from attacker in last 24 hours
            >>> events = await service.correlate_events_by_ip("203.0.113.1")
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        return await self.repository.get_events_by_source_ip(
            source_ip=source_ip,
            start_time=start_time,
            end_time=end_time
        )
    
    async def enrich_event(self, event_id: UUID) -> ThreatEvent:
        """
        Manually trigger enrichment for existing event.
        
        Useful for re-enrichment with updated threat intelligence.
        
        Args:
            event_id: Event UUID
        
        Returns:
            Enriched threat event
        
        Raises:
            NotFoundError: If event not found
            DatabaseError: On database errors
        """
        event = await self.repository.get_by_id_or_raise(event_id)
        pydantic_event = self.repository._to_pydantic(event)
        return await self._enrich_event(pydantic_event)
    
    async def mark_as_analyzed(
        self,
        event_id: UUID,
        related_events: Optional[List[UUID]] = None
    ) -> ThreatEvent:
        """
        Mark threat event as analyzed and link related events.
        
        Critical state transition in intelligence pipeline.
        Called by intelligence service after analysis completion.
        
        Args:
            event_id: Event UUID
            related_events: Optional list of correlated event IDs
        
        Returns:
            Updated threat event
        
        Raises:
            NotFoundError: If event not found
            DatabaseError: On database errors
        """
        logger.info(f"Marking event {event_id} as analyzed")
        
        update_data = ThreatEventUpdate(
            is_analyzed=True,
            analysis_timestamp=datetime.utcnow()
        )
        
        if related_events:
            update_data.related_events = related_events
        
        return await self.repository.update_from_model(event_id, update_data)
    
    async def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate threat event statistics.
        
        Supports dashboard metrics and Phase 1 progress tracking.
        
        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
        
        Returns:
            Statistics dictionary with counts and breakdowns
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.repository.get_event_statistics(
            start_time=start_time,
            end_time=end_time
        )
    
    # Private enrichment methods
    
    async def _enrich_event(self, event: ThreatEvent) -> ThreatEvent:
        """
        Run enrichment pipeline on threat event.
        
        Enrichment stages:
        1. Geolocation lookup (IP -> Country/City/ASN)
        2. Threat intelligence correlation (check known malicious IPs)
        3. MITRE ATT&CK technique suggestion
        4. Indicator extraction refinement
        
        Args:
            event: ThreatEvent to enrich
        
        Returns:
            Enriched ThreatEvent
        
        Note:
            Each enrichment stage is non-blocking. Failures are logged
            but don't prevent event creation.
        """
        enrichment_updates = ThreatEventUpdate()
        
        # Stage 1: Geolocation
        try:
            geolocation = await self._enrich_geolocation(event.source_ip)
            if geolocation:
                enrichment_updates.geolocation = geolocation
                logger.debug(f"Geolocation enriched for {event.source_ip}: {geolocation}")
        except Exception as e:
            logger.warning(f"Geolocation enrichment failed for {event.source_ip}: {e}")
        
        # Stage 2: Threat Intel
        try:
            threat_intel = await self._enrich_threat_intel(event.source_ip, event.indicators)
            if threat_intel:
                enrichment_updates.threat_intel_match = threat_intel
                logger.debug(f"Threat intel match for {event.source_ip}: {threat_intel}")
        except Exception as e:
            logger.warning(f"Threat intel enrichment failed for {event.source_ip}: {e}")
        
        # Stage 3: MITRE ATT&CK refinement
        try:
            if not event.mitre_mapping or event.mitre_mapping.get('confidence', 0) < 0.7:
                suggested_mapping = await self._suggest_mitre_mapping(event)
                if suggested_mapping:
                    enrichment_updates.mitre_mapping = suggested_mapping
                    logger.debug(f"MITRE mapping suggested for event {event.id}")
        except Exception as e:
            logger.warning(f"MITRE mapping enrichment failed for event {event.id}: {e}")
        
        # Apply enrichments if any
        if enrichment_updates.dict(exclude_unset=True):
            return await self.repository.update_from_model(event.id, enrichment_updates)
        
        return event
    
    async def _enrich_geolocation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Enrich IP address with geolocation data.
        
        Phase 1: Placeholder for integration with MaxMind GeoIP or similar.
        
        Args:
            ip_address: IP to geolocate
        
        Returns:
            Geolocation data dict or None
        """
        # Geolocation via MaxMind GeoIP2 or ipapi.co API
        # For now, return placeholder
        logger.debug(f"Geolocation lookup for {ip_address} - integration pending")
        return None
    
    async def _enrich_threat_intel(
        self,
        ip_address: str,
        indicators: List[ThreatIndicator]
    ) -> Optional[Dict[str, Any]]:
        """
        Correlate with external threat intelligence feeds.
        
        Phase 1: Placeholder for integration with threat intel platforms.
        
        Args:
            ip_address: Source IP
            indicators: Extracted IoCs
        
        Returns:
            Threat intel correlation data or None
        """
        # Threat intel via MISP API, AlienVault OTX, VirusTotal
        logger.debug(f"Threat intel lookup for {ip_address} - integration pending")
        return None
    
    async def _suggest_mitre_mapping(self, event: ThreatEvent) -> Optional[Dict[str, Any]]:
        """
        Suggest MITRE ATT&CK technique mapping based on event characteristics.
        
        Phase 1: Rule-based heuristics.
        Phase 2+: ML-based technique prediction.
        
        Args:
            event: ThreatEvent to analyze
        
        Returns:
            Suggested MITRE mapping dict or None
        """
        # Simple heuristics for common patterns
        # ML enhancement via ThreatClassifier model (sklearn/transformers)
        
        # Example: SSH brute force -> T1110.001 (Brute Force: Password Guessing)
        if event.destination_port == 22 and "brute" in event.title.lower():
            return {
                "tactic_id": "TA0006",
                "tactic_name": "Credential Access",
                "technique_id": "T1110",
                "technique_name": "Brute Force",
                "sub_technique_id": "T1110.001",
                "confidence": 0.8
            }
        
        # Example: Web exploitation -> T1190 (Exploit Public-Facing Application)
        if event.destination_port in [80, 443, 8080] and event.category == ThreatCategory.INITIAL_ACCESS:
            return {
                "tactic_id": "TA0001",
                "tactic_name": "Initial Access",
                "technique_id": "T1190",
                "technique_name": "Exploit Public-Facing Application",
                "sub_technique_id": None,
                "confidence": 0.75
            }
        
        return None
