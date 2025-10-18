"""
Reactive Fabric - Intelligence Report Repository.

Specialized repository for intelligence reports and metrics.
Primary output artifact of reactive fabric intelligence pipeline.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import (
    IntelligenceReportDB, TTPPatternDB, IntelligenceMetricsDB,
    IntelligenceReportEventLink, IntelligenceReportAssetLink
)
from . import BaseRepository, DatabaseError
from ...models.intelligence import (
    IntelligenceType, IntelligenceConfidence, IntelligenceReport, IntelligenceReportCreate, IntelligenceReportUpdate,
    TTPPattern, IntelligenceMetrics
)


class IntelligenceRepository(BaseRepository[IntelligenceReportDB]):
    """
    Intelligence report repository with correlation tracking.
    
    Manages structured threat intelligence reports representing
    analyzed and contextualized threat information.
    
    Phase 1 KPI:
    Report quality and actionability determines fabric success.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize intelligence repository."""
        super().__init__(IntelligenceReportDB, session)
    
    async def create_from_model(self, report: IntelligenceReportCreate) -> IntelligenceReport:
        """
        Create intelligence report from Pydantic model.
        
        Args:
            report: IntelligenceReportCreate DTO
        
        Returns:
            Complete IntelligenceReport with generated ID
        
        Raises:
            DuplicateError: If report_number already exists
            DatabaseError: On database errors
        """
        report_data = report.dict()
        
        # Extract related events and assets for link tables
        related_events = report_data.pop('related_threat_events', [])
        related_assets = report_data.pop('related_assets', [])
        
        # Convert threat_actor to dict
        if report_data.get('threat_actor'):
            threat_actor = report_data['threat_actor']
            report_data['threat_actor'] = threat_actor.dict() if hasattr(threat_actor, 'dict') else threat_actor
        
        # Convert TTP patterns to UUIDs
        if report_data.get('ttp_patterns'):
            ttp_patterns = report_data['ttp_patterns']
            report_data['ttp_patterns'] = [
                ttp.id if hasattr(ttp, 'id') else ttp for ttp in ttp_patterns
            ]
        
        # Create report
        db_report = await self.create(**report_data)
        
        # Create event links
        for event_id in related_events:
            link = IntelligenceReportEventLink(
                report_id=db_report.id,
                event_id=event_id
            )
            self.session.add(link)
        
        # Create asset links
        for asset_id in related_assets:
            link = IntelligenceReportAssetLink(
                report_id=db_report.id,
                asset_id=asset_id
            )
            self.session.add(link)
        
        await self.session.flush()
        await self.session.refresh(db_report)
        
        return await self._to_pydantic(db_report, related_events, related_assets)
    
    async def update_from_model(
        self,
        report_id: UUID,
        update: IntelligenceReportUpdate
    ) -> IntelligenceReport:
        """
        Update intelligence report from Pydantic model.
        
        Args:
            report_id: Report UUID
            update: IntelligenceReportUpdate DTO
        
        Returns:
            Updated IntelligenceReport
        
        Raises:
            NotFoundError: If report not found
            DatabaseError: On database errors
        """
        update_data = update.dict(exclude_unset=True)
        
        # Convert threat_actor
        if 'threat_actor' in update_data and update_data['threat_actor']:
            threat_actor = update_data['threat_actor']
            update_data['threat_actor'] = threat_actor.dict() if hasattr(threat_actor, 'dict') else threat_actor
        
        # Convert TTP patterns
        if 'ttp_patterns' in update_data and update_data['ttp_patterns']:
            ttp_patterns = update_data['ttp_patterns']
            update_data['ttp_patterns'] = [
                ttp.id if hasattr(ttp, 'id') else ttp for ttp in ttp_patterns
            ]
        
        db_report = await self.update(report_id, **update_data)
        
        # Get related entities
        event_links = await self.session.execute(
            select(IntelligenceReportEventLink).where(
                IntelligenceReportEventLink.report_id == report_id
            )
        )
        related_events = [link.event_id for link in event_links.scalars().all()]
        
        asset_links = await self.session.execute(
            select(IntelligenceReportAssetLink).where(
                IntelligenceReportAssetLink.report_id == report_id
            )
        )
        related_assets = [link.asset_id for link in asset_links.scalars().all()]
        
        return await self._to_pydantic(db_report, related_events, related_assets)
    
    async def get_reports_by_type(
        self,
        intelligence_type: IntelligenceType,
        confidence: Optional[IntelligenceConfidence] = None,
        limit: int = 100
    ) -> List[IntelligenceReport]:
        """
        Get reports by intelligence type.
        
        Args:
            intelligence_type: Type of intelligence
            confidence: Optional minimum confidence filter
            limit: Maximum reports to retrieve
        
        Returns:
            List of intelligence reports
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            stmt = select(IntelligenceReportDB).where(
                IntelligenceReportDB.intelligence_type == intelligence_type
            )
            
            if confidence:
                confidence_order = {
                    IntelligenceConfidence.CONFIRMED: 5,
                    IntelligenceConfidence.HIGH: 4,
                    IntelligenceConfidence.MEDIUM: 3,
                    IntelligenceConfidence.LOW: 2,
                    IntelligenceConfidence.SPECULATIVE: 1
                }
                # Get all with confidence >= specified
                target_level = confidence_order[confidence]
                valid_confidences = [c for c, level in confidence_order.items() if level >= target_level]
                stmt = stmt.where(IntelligenceReportDB.confidence.in_(valid_confidences))
            
            stmt = stmt.order_by(desc(IntelligenceReportDB.generated_at)).limit(limit)
            
            result = await self.session.execute(stmt)
            db_reports = result.scalars().all()
            
            # Load related entities for each report
            reports = []
            for db_report in db_reports:
                event_links = await self.session.execute(
                    select(IntelligenceReportEventLink).where(
                        IntelligenceReportEventLink.report_id == db_report.id
                    )
                )
                related_events = [link.event_id for link in event_links.scalars().all()]
                
                asset_links = await self.session.execute(
                    select(IntelligenceReportAssetLink).where(
                        IntelligenceReportAssetLink.report_id == db_report.id
                    )
                )
                related_assets = [link.asset_id for link in asset_links.scalars().all()]
                
                reports.append(await self._to_pydantic(db_report, related_events, related_assets))
            
            return reports
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_recent_reports(
        self,
        days: int = 30,
        peer_reviewed_only: bool = False,
        limit: int = 100
    ) -> List[IntelligenceReport]:
        """
        Get recent intelligence reports.
        
        Args:
            days: Number of days back to retrieve
            peer_reviewed_only: Only return peer-reviewed reports
            limit: Maximum reports to retrieve
        
        Returns:
            List of recent intelligence reports
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(IntelligenceReportDB).where(
                IntelligenceReportDB.generated_at >= cutoff_date
            )
            
            if peer_reviewed_only:
                stmt = stmt.where(IntelligenceReportDB.peer_reviewed == True)
            
            stmt = stmt.order_by(desc(IntelligenceReportDB.generated_at)).limit(limit)
            
            result = await self.session.execute(stmt)
            db_reports = result.scalars().all()
            
            # Load related entities
            reports = []
            for db_report in db_reports:
                event_links = await self.session.execute(
                    select(IntelligenceReportEventLink).where(
                        IntelligenceReportEventLink.report_id == db_report.id
                    )
                )
                related_events = [link.event_id for link in event_links.scalars().all()]
                
                asset_links = await self.session.execute(
                    select(IntelligenceReportAssetLink).where(
                        IntelligenceReportAssetLink.report_id == db_report.id
                    )
                )
                related_assets = [link.asset_id for link in asset_links.scalars().all()]
                
                reports.append(await self._to_pydantic(db_report, related_events, related_assets))
            
            return reports
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_by_report_number(self, report_number: str) -> Optional[IntelligenceReport]:
        """
        Get report by human-readable report number.
        
        Args:
            report_number: Report identifier (e.g., "INT-2024-001")
        
        Returns:
            Intelligence report if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            result = await self.session.execute(
                select(IntelligenceReportDB).where(
                    IntelligenceReportDB.report_number == report_number
                )
            )
            db_report = result.scalar_one_or_none()
            
            if db_report is None:
                return None
            
            # Load related entities
            event_links = await self.session.execute(
                select(IntelligenceReportEventLink).where(
                    IntelligenceReportEventLink.report_id == db_report.id
                )
            )
            related_events = [link.event_id for link in event_links.scalars().all()]
            
            asset_links = await self.session.execute(
                select(IntelligenceReportAssetLink).where(
                    IntelligenceReportAssetLink.report_id == db_report.id
                )
            )
            related_assets = [link.asset_id for link in asset_links.scalars().all()]
            
            return await self._to_pydantic(db_report, related_events, related_assets)
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def _to_pydantic(
        self,
        db_report: IntelligenceReportDB,
        related_events: List[UUID],
        related_assets: List[UUID]
    ) -> IntelligenceReport:
        """Convert database model to Pydantic model."""
        from ...models.intelligence import APTGroup
        
        return IntelligenceReport(
            id=db_report.id,
            report_number=db_report.report_number,
            title=db_report.title,
            intelligence_type=db_report.intelligence_type,
            confidence=db_report.confidence,
            executive_summary=db_report.executive_summary,
            technical_analysis=db_report.technical_analysis,
            threat_actor=APTGroup(**db_report.threat_actor) if db_report.threat_actor else None,
            ttp_patterns=[],  # Would need to load TTPPattern objects
            indicators_of_compromise=db_report.indicators_of_compromise or [],
            behavioral_indicators=db_report.behavioral_indicators or [],
            related_threat_events=related_events,
            related_assets=related_assets,
            sources=db_report.sources,
            defensive_recommendations=db_report.defensive_recommendations or [],
            detection_rules=db_report.detection_rules or [],
            hunt_hypotheses=db_report.hunt_hypotheses or [],
            analysis_period_start=db_report.analysis_period_start,
            analysis_period_end=db_report.analysis_period_end,
            generated_at=db_report.generated_at,
            generated_by=db_report.generated_by,
            classification=db_report.classification,
            tags=db_report.tags or [],
            peer_reviewed=db_report.peer_reviewed,
            reviewed_by=db_report.reviewed_by,
            review_date=db_report.review_date,
            metadata=db_report.metadata or {}
        )


class TTPPatternRepository(BaseRepository[TTPPatternDB]):
    """
    TTP pattern repository.
    
    Tracks identified attacker behavior patterns aligned with MITRE ATT&CK.
    Core intelligence artifact for Phase 1 success validation.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize TTP pattern repository."""
        super().__init__(TTPPatternDB, session)
    
    async def create_from_model(self, pattern: TTPPattern) -> TTPPattern:
        """Create TTP pattern from Pydantic model."""
        pattern_data = pattern.dict()
        db_pattern = await self.create(**pattern_data)
        return self._to_pydantic(db_pattern)
    
    async def get_by_technique(self, technique_id: str) -> List[TTPPattern]:
        """
        Get patterns associated with MITRE technique.
        
        Args:
            technique_id: MITRE ATT&CK technique ID (e.g., "T1190")
        
        Returns:
            List of TTP patterns
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            # PostgreSQL array contains operator
            stmt = select(TTPPatternDB).where(
                TTPPatternDB.mitre_techniques.contains([technique_id])
            )
            
            result = await self.session.execute(stmt)
            db_patterns = result.scalars().all()
            
            return [self._to_pydantic(pattern) for pattern in db_patterns]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def increment_observation(self, pattern_id: UUID) -> TTPPattern:
        """
        Increment pattern observation count.
        
        Called when pattern is observed again.
        
        Args:
            pattern_id: Pattern UUID
        
        Returns:
            Updated pattern
        
        Raises:
            NotFoundError: If pattern not found
            DatabaseError: On database errors
        """
        pattern = await self.get_by_id_or_raise(pattern_id)
        
        db_pattern = await self.update(
            pattern_id,
            observation_count=pattern.observation_count + 1,
            last_observed=datetime.utcnow()
        )
        
        return self._to_pydantic(db_pattern)
    
    def _to_pydantic(self, db_pattern: TTPPatternDB) -> TTPPattern:
        """Convert database model to Pydantic model."""
        return TTPPattern(
            id=db_pattern.id,
            name=db_pattern.name,
            description=db_pattern.description,
            mitre_tactics=db_pattern.mitre_tactics or [],
            mitre_techniques=db_pattern.mitre_techniques or [],
            behavioral_indicators=db_pattern.behavioral_indicators or [],
            network_indicators=db_pattern.network_indicators or [],
            observed_apt_groups=db_pattern.observed_apt_groups or [],
            confidence=db_pattern.confidence,
            first_observed=db_pattern.first_observed,
            last_observed=db_pattern.last_observed,
            observation_count=db_pattern.observation_count,
            detection_rules=db_pattern.detection_rules or []
        )


class IntelligenceMetricsRepository(BaseRepository[IntelligenceMetricsDB]):
    """
    Intelligence metrics repository.
    
    Tracks Phase 1 success metrics for go/no-go decision.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize metrics repository."""
        super().__init__(IntelligenceMetricsDB, session)
    
    async def create_from_model(self, metrics: IntelligenceMetrics) -> IntelligenceMetrics:
        """Create metrics snapshot from Pydantic model."""
        metrics_data = metrics.dict()
        db_metrics = await self.create(**metrics_data)
        return self._to_pydantic(db_metrics)
    
    async def get_latest_metrics(self) -> Optional[IntelligenceMetrics]:
        """
        Get most recent metrics snapshot.
        
        Returns:
            Latest metrics if available, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            result = await self.session.execute(
                select(IntelligenceMetricsDB).order_by(
                    desc(IntelligenceMetricsDB.created_at)
                ).limit(1)
            )
            db_metrics = result.scalar_one_or_none()
            
            if db_metrics:
                return self._to_pydantic(db_metrics)
            return None
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    async def get_metrics_trend(self, days: int = 30) -> List[IntelligenceMetrics]:
        """
        Get metrics trend over time period.
        
        Args:
            days: Number of days back to retrieve
        
        Returns:
            List of metrics snapshots ordered by time
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.session.execute(
                select(IntelligenceMetricsDB).where(
                    IntelligenceMetricsDB.created_at >= cutoff_date
                ).order_by(asc(IntelligenceMetricsDB.created_at))
            )
            db_metrics_list = result.scalars().all()
            
            return [self._to_pydantic(metrics) for metrics in db_metrics_list]
        
        except Exception as e:
            raise DatabaseError(f"Query error: {str(e)}") from e
    
    def _to_pydantic(self, db_metrics: IntelligenceMetricsDB) -> IntelligenceMetrics:
        """Convert database model to Pydantic model."""
        return IntelligenceMetrics(
            total_threat_events=db_metrics.total_threat_events,
            unique_source_ips=db_metrics.unique_source_ips,
            unique_apt_groups_observed=db_metrics.unique_apt_groups_observed,
            novel_ttps_discovered=db_metrics.novel_ttps_discovered,
            ttp_patterns_identified=db_metrics.ttp_patterns_identified,
            reports_generated=db_metrics.reports_generated,
            tactical_reports=db_metrics.tactical_reports,
            operational_reports=db_metrics.operational_reports,
            strategic_reports=db_metrics.strategic_reports,
            detection_rules_created=db_metrics.detection_rules_created,
            hunt_hypotheses_validated=db_metrics.hunt_hypotheses_validated,
            defensive_measures_implemented=db_metrics.defensive_measures_implemented,
            average_confidence_score=db_metrics.average_confidence_score,
            peer_review_rate=db_metrics.peer_review_rate,
            average_analysis_time_hours=db_metrics.average_analysis_time_hours,
            time_to_detection_rule_hours=db_metrics.time_to_detection_rule_hours,
            active_deception_assets=db_metrics.active_deception_assets,
            assets_with_interactions=db_metrics.assets_with_interactions,
            average_asset_credibility=db_metrics.average_asset_credibility,
            period_start=db_metrics.period_start,
            period_end=db_metrics.period_end
        )
