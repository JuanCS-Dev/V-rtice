"""
Reactive Fabric - Intelligence Service.

Business logic for threat intelligence fusion, analysis and reporting.
Primary value delivery mechanism for Phase 1: actionable threat intelligence.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.repositories.intelligence_repository import (
    IntelligenceRepository, TTPPatternRepository, IntelligenceMetricsRepository
)
from ..database.repositories.threat_repository import ThreatEventRepository
from ..database.repositories.deception_repository import DeceptionAssetRepository
from ..models.intelligence import (
    IntelligenceReport, IntelligenceReportCreate, IntelligenceReportUpdate,
    IntelligenceType, IntelligenceConfidence, IntelligenceSource,
    TTPPattern, IntelligenceMetrics
)
from ..models.threat import ThreatEvent
from .threat_service import ThreatEventService


logger = logging.getLogger(__name__)


class IntelligenceService:
    """
    Intelligence fusion and analysis service.
    
    Orchestrates intelligence pipeline:
    1. Event correlation and pattern detection
    2. TTP identification and MITRE ATT&CK mapping
    3. APT attribution and campaign tracking
    4. Intelligence report generation
    5. Detection rule creation
    6. Success metrics tracking
    
    Phase 1 Value Proposition:
    - Proactive threat intelligence from attacker interactions
    - Novel TTP discovery
    - Actionable detection rules
    - APT behavior pattern recognition
    
    This service represents the ROI justification for reactive fabric.
    Quality and actionability of intelligence determines Phase 2 go/no-go.
    
    Phase 1 KPIs:
    - Novel TTPs discovered
    - Detection rules deployed
    - Hunt hypotheses validated
    - Average confidence score
    - Time to detection rule
    
    Consciousness Parallel:
    Like semantic binding in Global Workspace Theory, this service
    integrates distributed threat observations into coherent narratives
    with attributed meaning (APT campaigns, attack chains, strategic intent).
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize intelligence service.
        
        Args:
            session: Async database session
        """
        self.session = session
        self.report_repository = IntelligenceRepository(session)
        self.ttp_repository = TTPPatternRepository(session)
        self.metrics_repository = IntelligenceMetricsRepository(session)
        self.threat_repository = ThreatEventRepository(session)
        self.asset_repository = DeceptionAssetRepository(session)
        self.threat_service = ThreatEventService(session)
    
    async def analyze_events(
        self,
        event_ids: List[UUID],
        analyst: str,
        analysis_type: IntelligenceType = IntelligenceType.TACTICAL
    ) -> IntelligenceReport:
        """
        Analyze threat events and generate intelligence report.
        
        Core intelligence pipeline function.
        Correlates events, identifies patterns, generates recommendations.
        
        Args:
            event_ids: List of ThreatEvent IDs to analyze
            analyst: Analyst conducting analysis
            analysis_type: Type of intelligence report to generate
        
        Returns:
            Generated IntelligenceReport
        
        Raises:
            ValueError: If no events provided
            NotFoundError: If events not found
            DatabaseError: On database errors
        
        Example:
            >>> # Analyze high-severity events from last 24 hours
            >>> unanalyzed = await threat_service.get_unanalyzed_events(
            ...     priority_severity=[ThreatSeverity.CRITICAL, ThreatSeverity.HIGH]
            ... )
            >>> report = await intelligence_service.analyze_events(
            ...     event_ids=[e.id for e in unanalyzed[:10]],
            ...     analyst="security_analyst_1",
            ...     analysis_type=IntelligenceType.TACTICAL
            ... )
        """
        if not event_ids:
            raise ValueError("At least one event ID required for analysis")
        
        logger.info(
            f"Starting intelligence analysis of {len(event_ids)} events "
            f"by {analyst} (type={analysis_type})"
        )
        
        # Load events
        events = []
        for event_id in event_ids:
            event = await self.threat_repository.get_by_id_or_raise(event_id)
            events.append(self.threat_repository._to_pydantic(event))
        
        # Perform correlation and pattern analysis
        analysis_result = await self._correlate_and_analyze(events)
        
        # Generate report
        report = await self._generate_report(
            events=events,
            analysis_result=analysis_result,
            analyst=analyst,
            intelligence_type=analysis_type
        )
        
        # Mark events as analyzed
        for event_id in event_ids:
            await self.threat_service.mark_as_analyzed(
                event_id=event_id,
                related_events=[e for e in event_ids if e != event_id]
            )
        
        logger.info(f"Intelligence report generated: {report.report_number}")
        
        return report
    
    async def create_ttp_pattern(
        self,
        name: str,
        description: str,
        mitre_tactics: List[str],
        mitre_techniques: List[str],
        confidence: IntelligenceConfidence,
        behavioral_indicators: Optional[List[str]] = None,
        network_indicators: Optional[List[str]] = None,
        observed_apt_groups: Optional[List[str]] = None
    ) -> TTPPattern:
        """
        Create new TTP pattern from observed attacker behavior.
        
        Core intelligence artifact for Phase 1 success validation.
        Each novel TTP discovered demonstrates fabric value.
        
        Args:
            name: Pattern name
            description: Pattern description
            mitre_tactics: ATT&CK tactic IDs
            mitre_techniques: ATT&CK technique IDs
            confidence: Pattern confidence level
            behavioral_indicators: Optional behavioral IoCs
            network_indicators: Optional network IoCs
            observed_apt_groups: Optional APT group attributions
        
        Returns:
            Created TTPPattern
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> pattern = await intelligence_service.create_ttp_pattern(
            ...     name="SSH Brute Force with Credential Stuffing",
            ...     description="Rapid SSH login attempts using leaked credentials",
            ...     mitre_tactics=["TA0006"],
            ...     mitre_techniques=["T1110", "T1110.001"],
            ...     confidence=IntelligenceConfidence.HIGH,
            ...     behavioral_indicators=["multiple_failed_auth", "credential_list"],
            ...     network_indicators=["ssh_port_22"]
            ... )
        """
        logger.info(f"Creating TTP pattern: {name}")
        
        pattern = TTPPattern(
            name=name,
            description=description,
            mitre_tactics=mitre_tactics,
            mitre_techniques=mitre_techniques,
            confidence=confidence,
            behavioral_indicators=behavioral_indicators or [],
            network_indicators=network_indicators or [],
            observed_apt_groups=observed_apt_groups or []
        )
        
        created_pattern = await self.ttp_repository.create_from_model(pattern)
        
        logger.info(f"TTP pattern created: {created_pattern.id}")
        
        return created_pattern
    
    async def get_report(self, report_id: UUID) -> Optional[IntelligenceReport]:
        """
        Retrieve intelligence report by ID.
        
        Args:
            report_id: Report UUID
        
        Returns:
            IntelligenceReport if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        report = await self.report_repository.get_by_id(report_id)
        if report:
            # Load related entities
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
            
            return await self.report_repository._to_pydantic(report, related_events, related_assets)
        return None
    
    async def get_report_by_number(self, report_number: str) -> Optional[IntelligenceReport]:
        """
        Retrieve intelligence report by human-readable number.
        
        Args:
            report_number: Report identifier (e.g., "INT-2024-001")
        
        Returns:
            IntelligenceReport if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.report_repository.get_by_report_number(report_number)
    
    async def get_recent_reports(
        self,
        days: int = 30,
        intelligence_type: Optional[IntelligenceType] = None,
        min_confidence: Optional[IntelligenceConfidence] = None,
        peer_reviewed_only: bool = False
    ) -> List[IntelligenceReport]:
        """
        Get recent intelligence reports with filters.
        
        Args:
            days: Number of days back to retrieve
            intelligence_type: Optional type filter
            min_confidence: Optional minimum confidence filter
            peer_reviewed_only: Only peer-reviewed reports
        
        Returns:
            List of intelligence reports
        
        Raises:
            DatabaseError: On database errors
        """
        if intelligence_type:
            return await self.report_repository.get_reports_by_type(
                intelligence_type=intelligence_type,
                confidence=min_confidence,
                limit=1000  # Within time window
            )
        
        return await self.report_repository.get_recent_reports(
            days=days,
            peer_reviewed_only=peer_reviewed_only
        )
    
    async def peer_review_report(
        self,
        report_id: UUID,
        reviewer: str,
        approved: bool,
        notes: Optional[str] = None
    ) -> IntelligenceReport:
        """
        Peer review intelligence report.
        
        Quality assurance step for report validation.
        
        Args:
            report_id: Report UUID
            reviewer: Reviewer identifier
            approved: Review approval status
            notes: Optional review notes
        
        Returns:
            Updated IntelligenceReport
        
        Raises:
            NotFoundError: If report not found
            DatabaseError: On database errors
        """
        logger.info(f"Peer reviewing report {report_id} by {reviewer}: {'approved' if approved else 'rejected'}")
        
        update_data = IntelligenceReportUpdate(
            peer_reviewed=approved,
            reviewed_by=reviewer,
            review_date=datetime.utcnow()
        )
        
        if notes:
            # Add review notes to metadata
            report = await self.report_repository.get_by_id_or_raise(report_id)
            metadata = report.metadata or {}
            metadata['peer_review_notes'] = notes
            update_data.metadata = metadata
        
        return await self.report_repository.update_from_model(report_id, update_data)
    
    async def calculate_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> IntelligenceMetrics:
        """
        Calculate Phase 1 success metrics for time period.
        
        Primary mechanism for tracking fabric effectiveness and
        validating progression to Phase 2.
        
        Args:
            start_time: Metrics period start
            end_time: Metrics period end
        
        Returns:
            IntelligenceMetrics snapshot
        
        Raises:
            DatabaseError: On database errors
        
        Example:
            >>> # Calculate monthly metrics
            >>> end_time = datetime.utcnow()
            >>> start_time = end_time - timedelta(days=30)
            >>> metrics = await intelligence_service.calculate_metrics(start_time, end_time)
            >>> print(f"Novel TTPs discovered: {metrics.novel_ttps_discovered}")
            >>> print(f"Detection rules created: {metrics.detection_rules_created}")
        """
        logger.info(f"Calculating intelligence metrics for period: {start_time} to {end_time}")
        
        # Get threat event statistics
        event_stats = await self.threat_repository.get_event_statistics(
            start_time=start_time,
            end_time=end_time
        )
        
        # Get deception asset statistics
        asset_stats = await self.asset_repository.get_asset_statistics()
        
        # Get report statistics
        reports = await self.report_repository.get_recent_reports(
            days=(end_time - start_time).days,
            peer_reviewed_only=False
        )
        
        # Calculate intelligence-specific metrics
        tactical_reports = sum(1 for r in reports if r.intelligence_type == IntelligenceType.TACTICAL)
        operational_reports = sum(1 for r in reports if r.intelligence_type == IntelligenceType.OPERATIONAL)
        strategic_reports = sum(1 for r in reports if r.intelligence_type == IntelligenceType.STRATEGIC)
        
        total_detection_rules = sum(len(r.detection_rules) for r in reports)
        total_hunt_hypotheses = sum(len(r.hunt_hypotheses) for r in reports)
        
        # Confidence scoring
        if reports:
            confidence_scores = {
                IntelligenceConfidence.CONFIRMED: 1.0,
                IntelligenceConfidence.HIGH: 0.8,
                IntelligenceConfidence.MEDIUM: 0.6,
                IntelligenceConfidence.LOW: 0.4,
                IntelligenceConfidence.SPECULATIVE: 0.2
            }
            avg_confidence = sum(confidence_scores.get(r.confidence, 0.5) for r in reports) / len(reports)
        else:
            avg_confidence = 0.0
        
        peer_review_rate = sum(1 for r in reports if r.peer_reviewed) / len(reports) if reports else 0.0
        
        # Get TTP statistics
        # TTP patterns queried from threat_reports collection with time filter
        novel_ttps = 0  # Placeholder
        ttp_patterns = 0  # Placeholder
        
        # Create metrics snapshot
        metrics = IntelligenceMetrics(
            total_threat_events=event_stats.get('total_events', 0),
            unique_source_ips=event_stats.get('unique_source_ips', 0),
            unique_apt_groups_observed=len(set(r.get("apt_group") for r in reports if r.get("apt_group"))),
            novel_ttps_discovered=novel_ttps,
            ttp_patterns_identified=ttp_patterns,
            reports_generated=len(reports),
            tactical_reports=tactical_reports,
            operational_reports=operational_reports,
            strategic_reports=strategic_reports,
            detection_rules_created=total_detection_rules,
            hunt_hypotheses_validated=len([h for h in hypotheses if h.get("validated")]),
            defensive_measures_implemented=len([m for m in measures if m.get("implemented")]),
            average_confidence_score=avg_confidence,
            peer_review_rate=peer_review_rate,
            average_analysis_time_hours=sum((r["completed_at"] - r["created_at"]).total_seconds()/3600 for r in reports if "completed_at" in r)/(len(reports) or 1),
            time_to_detection_rule_hours=sum((r["rule_deployed_at"] - r["threat_detected_at"]).total_seconds()/3600 for r in reports if "rule_deployed_at" in r)/(len(reports) or 1),
            active_deception_assets=asset_stats.get('active_assets', 0),
            assets_with_interactions=asset_stats.get('assets_with_recent_interactions', 0),
            average_asset_credibility=asset_stats.get('average_credibility', 0.0),
            period_start=start_time,
            period_end=end_time
        )
        
        # Persist metrics snapshot
        saved_metrics = await self.metrics_repository.create_from_model(metrics)
        
        logger.info(
            f"Metrics calculated - Reports: {metrics.reports_generated}, "
            f"Detection Rules: {metrics.detection_rules_created}, "
            f"Avg Confidence: {metrics.average_confidence_score:.2f}"
        )
        
        return saved_metrics
    
    async def get_latest_metrics(self) -> Optional[IntelligenceMetrics]:
        """
        Get most recent metrics snapshot.
        
        Returns:
            Latest IntelligenceMetrics if available, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.metrics_repository.get_latest_metrics()
    
    async def get_metrics_trend(self, days: int = 30) -> List[IntelligenceMetrics]:
        """
        Get metrics trend over time period.
        
        Supports visualization of Phase 1 progress.
        
        Args:
            days: Number of days back to retrieve
        
        Returns:
            List of metrics snapshots ordered by time
        
        Raises:
            DatabaseError: On database errors
        """
        return await self.metrics_repository.get_metrics_trend(days=days)
    
    # Private analysis methods
    
    async def _correlate_and_analyze(self, events: List[ThreatEvent]) -> Dict[str, Any]:
        """
        Correlate events and perform pattern analysis.
        
        Identifies:
        - Common source IPs (attacker correlation)
        - Common TTPs (behavioral patterns)
        - Attack chains (multi-stage campaigns)
        - Target patterns (reconnaissance targets)
        
        Args:
            events: List of ThreatEvents to analyze
        
        Returns:
            Analysis result dictionary
        """
        # Group by source IP
        ip_groups: Dict[str, List[ThreatEvent]] = {}
        for event in events:
            if event.source_ip not in ip_groups:
                ip_groups[event.source_ip] = []
            ip_groups[event.source_ip].append(event)
        
        # Extract TTPs
        ttps_observed = set()
        for event in events:
            if event.mitre_mapping:
                technique_id = event.mitre_mapping.get('technique_id')
                if technique_id:
                    ttps_observed.add(technique_id)
        
        # Identify attack chains (events from same IP in sequence)
        attack_chains = []
        for source_ip, ip_events in ip_groups.items():
            if len(ip_events) > 1:
                sorted_events = sorted(ip_events, key=lambda e: e.timestamp)
                attack_chains.append({
                    'source_ip': source_ip,
                    'events': sorted_events,
                    'duration_hours': (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds() / 3600
                })
        
        # Calculate confidence based on evidence
        confidence = IntelligenceConfidence.MEDIUM
        if len(ip_groups) == 1 and len(events) > 5:
            confidence = IntelligenceConfidence.HIGH  # Consistent attacker behavior
        elif len(ttps_observed) >= 3:
            confidence = IntelligenceConfidence.HIGH  # Multiple TTPs identified
        
        return {
            'unique_attackers': len(ip_groups),
            'attacker_groups': ip_groups,
            'ttps_observed': list(ttps_observed),
            'attack_chains': attack_chains,
            'confidence': confidence
        }
    
    async def _generate_report(
        self,
        events: List[ThreatEvent],
        analysis_result: Dict[str, Any],
        analyst: str,
        intelligence_type: IntelligenceType
    ) -> IntelligenceReport:
        """
        Generate structured intelligence report from analysis.
        
        Args:
            events: Analyzed events
            analysis_result: Correlation analysis results
            analyst: Analyst identifier
            intelligence_type: Report type
        
        Returns:
            Generated IntelligenceReport
        """
        # Generate report number
        report_count = await self.report_repository.count()
        report_number = f"INT-{datetime.utcnow().year}-{report_count + 1:04d}"
        
        # Extract time period
        timestamps = [e.timestamp for e in events]
        period_start = min(timestamps)
        period_end = max(timestamps)
        
        # Generate executive summary
        unique_attackers = analysis_result['unique_attackers']
        ttps_count = len(analysis_result['ttps_observed'])
        executive_summary = (
            f"Analysis of {len(events)} threat events from {period_start.date()} to {period_end.date()} "
            f"identified {unique_attackers} unique attacker(s) utilizing {ttps_count} distinct TTP(s). "
        )
        
        if analysis_result['attack_chains']:
            executive_summary += (
                f"Detected {len(analysis_result['attack_chains'])} multi-stage attack chain(s) "
                f"indicating coordinated reconnaissance and exploitation attempts."
            )
        
        # Generate technical analysis
        technical_analysis = self._generate_technical_analysis(events, analysis_result)
        
        # Extract IoCs
        iocs = []
        for event in events:
            iocs.append(event.source_ip)
            iocs.extend([ind['value'] for ind in event.indicators if 'value' in ind])
        
        # Generate defensive recommendations
        defensive_recs = self._generate_recommendations(events, analysis_result)
        
        # Get involved assets
        asset_ids = []
        for event in events:
            if event.source == "honeypot" or event.source == "deception_asset":
                # Would need to correlate with asset by IP
                pass
        
        # Create report
        report_create = IntelligenceReportCreate(
            report_number=report_number,
            title=f"{intelligence_type.value.title()} Intelligence: {', '.join(analysis_result['ttps_observed'][:3])}",
            intelligence_type=intelligence_type,
            confidence=analysis_result['confidence'],
            executive_summary=executive_summary,
            technical_analysis=technical_analysis,
            indicators_of_compromise=list(set(iocs)),
            related_threat_events=[e.id for e in events],
            related_assets=asset_ids,
            sources=[IntelligenceSource.INTERNAL_TELEMETRY],
            defensive_recommendations=defensive_recs,
            detection_rules=[self._generate_detection_rule(ttp) for ttp in analysis.get("ttps", [])[:5]],
            hunt_hypotheses=[self._generate_hunt_hypothesis(ttp) for ttp in analysis.get("ttps", [])[:3]],
            analysis_period_start=period_start,
            analysis_period_end=period_end,
            generated_by=analyst,
            tags=list(analysis_result['ttps_observed'])
        )
        
        return await self.report_repository.create_from_model(report_create)
    
    def _generate_technical_analysis(
        self,
        events: List[ThreatEvent],
        analysis_result: Dict[str, Any]
    ) -> str:
        """Generate detailed technical analysis section."""
        analysis = f"## Threat Overview\n\n"
        analysis += f"Total Events Analyzed: {len(events)}\n"
        analysis += f"Unique Source IPs: {analysis_result['unique_attackers']}\n"
        analysis += f"TTPs Observed: {', '.join(analysis_result['ttps_observed'])}\n\n"
        
        analysis += f"## Attacker Behavior\n\n"
        for source_ip, ip_events in analysis_result['attacker_groups'].items():
            analysis += f"**Source IP: {source_ip}**\n"
            analysis += f"- Total Events: {len(ip_events)}\n"
            severities = [e.severity for e in ip_events]
            analysis += f"- Severity Distribution: {dict((s, severities.count(s)) for s in set(severities))}\n"
            analysis += f"- First Seen: {min(e.timestamp for e in ip_events)}\n"
            analysis += f"- Last Seen: {max(e.timestamp for e in ip_events)}\n\n"
        
        if analysis_result['attack_chains']:
            analysis += f"## Attack Chains\n\n"
            for chain in analysis_result['attack_chains']:
                analysis += f"**Chain from {chain['source_ip']}** (Duration: {chain['duration_hours']:.1f}h)\n"
                for event in chain['events']:
                    analysis += f"- {event.timestamp.strftime('%Y-%m-%d %H:%M')} | {event.category} | {event.title}\n"
                analysis += "\n"
        
        return analysis
    
    def _generate_recommendations(
        self,
        events: List[ThreatEvent],
        analysis_result: Dict[str, Any]
    ) -> List[str]:
        """Generate defensive recommendations."""
        recommendations = []
        
        # IP-based blocking
        if analysis_result['unique_attackers'] <= 10:
            recommendations.append(
                f"Block/monitor source IPs: {', '.join(list(analysis_result['attacker_groups'].keys())[:5])}"
            )
        
        # TTP-based defenses
        for ttp in analysis_result['ttps_observed']:
            if ttp.startswith('T1110'):  # Brute force
                recommendations.append("Implement rate limiting on authentication endpoints")
                recommendations.append("Enable MFA for all exposed services")
            elif ttp.startswith('T1190'):  # Exploit public-facing app
                recommendations.append("Patch and harden public-facing applications")
                recommendations.append("Deploy WAF with latest rule sets")
        
        # Network segmentation
        if len(events) > 10:
            recommendations.append("Review network segmentation for targeted services")
        
        return recommendations
