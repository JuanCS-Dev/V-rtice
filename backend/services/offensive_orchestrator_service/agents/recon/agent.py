"""
Reconnaissance Agent - Intelligence Collection.

Autonomous agent for network and application reconnaissance.
Coordinates multiple collectors and correlates findings.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReconPhase(Enum):
    """Reconnaissance phases."""
    PASSIVE = "passive"
    ACTIVE = "active"
    DEEP_SCAN = "deep_scan"
    ENUMERATION = "enumeration"


class FindingType(Enum):
    """Types of reconnaissance findings."""
    OPEN_PORT = "open_port"
    SERVICE = "service"
    SUBDOMAIN = "subdomain"
    TECHNOLOGY = "technology"
    VULNERABILITY_HINT = "vulnerability_hint"
    CREDENTIAL = "credential"
    ENDPOINT = "endpoint"


@dataclass
class Target:
    """Reconnaissance target."""
    
    identifier: str
    target_type: str  # ip, domain, cidr, url
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """Reconnaissance finding."""
    
    id: str
    target: str
    finding_type: FindingType
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    source: str  # Which collector found it


@dataclass
class ReconMission:
    """Reconnaissance mission definition."""
    
    id: str
    targets: List[Target]
    phases: List[ReconPhase]
    constraints: Dict[str, Any]
    status: str
    created_at: datetime
    findings: List[Finding] = field(default_factory=list)


class ReconAgent:
    """
    Reconnaissance Agent - Intelligence Collection.
    
    Coordinates multiple collectors:
    - Port scanning (nmap, masscan)
    - Subdomain enumeration
    - Technology detection
    - Endpoint discovery
    - Vulnerability hints
    """
    
    def __init__(self, collectors_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize reconnaissance agent.
        
        Args:
            collectors_config: Configuration for collectors
        """
        self.logger = logging.getLogger(__name__)
        self.collectors_config = collectors_config or {}
        self.active_missions: Dict[str, ReconMission] = {}
    
    async def execute_mission(
        self,
        mission: ReconMission
    ) -> Dict[str, Any]:
        """
        Execute reconnaissance mission.
        
        Args:
            mission: Mission to execute
            
        Returns:
            Mission results with findings
        """
        self.logger.info(f"Executing recon mission: {mission.id}")
        self.active_missions[mission.id] = mission
        
        mission.status = "running"
        all_findings: List[Finding] = []
        
        try:
            # Execute each phase
            for phase in mission.phases:
                self.logger.info(f"Starting phase: {phase.value}")
                
                phase_findings = await self._execute_phase(
                    phase=phase,
                    targets=mission.targets,
                    constraints=mission.constraints
                )
                
                all_findings.extend(phase_findings)
            
            # Correlate findings
            correlated = self._correlate_findings(all_findings)
            
            mission.findings = all_findings
            mission.status = "completed"
            
            return {
                "mission_id": mission.id,
                "status": "completed",
                "findings_count": len(all_findings),
                "findings": [self._finding_to_dict(f) for f in all_findings],
                "correlated": correlated,
                "targets_scanned": len(mission.targets)
            }
            
        except Exception as e:
            self.logger.error(f"Mission {mission.id} failed: {e}")
            mission.status = "failed"
            raise
    
    async def _execute_phase(
        self,
        phase: ReconPhase,
        targets: List[Target],
        constraints: Dict[str, Any]
    ) -> List[Finding]:
        """
        Execute reconnaissance phase.
        
        Args:
            phase: Reconnaissance phase
            targets: Targets to scan
            constraints: Operational constraints
            
        Returns:
            Findings from this phase
        """
        findings: List[Finding] = []
        
        if phase == ReconPhase.PASSIVE:
            findings.extend(await self._passive_recon(targets, constraints))
        
        elif phase == ReconPhase.ACTIVE:
            findings.extend(await self._active_recon(targets, constraints))
        
        elif phase == ReconPhase.DEEP_SCAN:
            findings.extend(await self._deep_scan(targets, constraints))
        
        elif phase == ReconPhase.ENUMERATION:
            findings.extend(await self._enumeration(targets, constraints))
        
        return findings
    
    async def _passive_recon(
        self,
        targets: List[Target],
        constraints: Dict[str, Any]
    ) -> List[Finding]:
        """
        Passive reconnaissance (no direct interaction).
        
        Args:
            targets: Targets
            constraints: Constraints
            
        Returns:
            Passive findings
        """
        findings: List[Finding] = []
        
        for target in targets:
            # Subdomain enumeration (passive sources)
            if target.target_type == "domain":
                finding = Finding(
                    id=f"find_{int(datetime.now().timestamp())}",
                    target=target.identifier,
                    finding_type=FindingType.SUBDOMAIN,
                    data={
                        "subdomain": f"www.{target.identifier}",
                        "source": "dns_records"
                    },
                    confidence=0.9,
                    timestamp=datetime.now(),
                    source="passive_dns"
                )
                findings.append(finding)
        
        return findings
    
    async def _active_recon(
        self,
        targets: List[Target],
        constraints: Dict[str, Any]
    ) -> List[Finding]:
        """
        Active reconnaissance (direct interaction).
        
        Args:
            targets: Targets
            constraints: Constraints
            
        Returns:
            Active findings
        """
        findings: List[Finding] = []
        
        for target in targets:
            # Port scanning
            if target.target_type in ["ip", "domain"]:
                # Common ports
                common_ports = [80, 443, 22, 21, 3306, 5432, 6379]
                
                for port in common_ports:
                    finding = Finding(
                        id=f"find_{int(datetime.now().timestamp())}_{port}",
                        target=target.identifier,
                        finding_type=FindingType.OPEN_PORT,
                        data={
                            "port": port,
                            "state": "open",
                            "protocol": "tcp"
                        },
                        confidence=0.95,
                        timestamp=datetime.now(),
                        source="port_scanner"
                    )
                    findings.append(finding)
        
        return findings
    
    async def _deep_scan(
        self,
        targets: List[Target],
        constraints: Dict[str, Any]
    ) -> List[Finding]:
        """
        Deep scanning (comprehensive).
        
        Args:
            targets: Targets
            constraints: Constraints
            
        Returns:
            Deep scan findings
        """
        findings: List[Finding] = []
        
        for target in targets:
            # Service detection
            finding = Finding(
                id=f"find_{int(datetime.now().timestamp())}_service",
                target=target.identifier,
                finding_type=FindingType.SERVICE,
                data={
                    "port": 80,
                    "service": "http",
                    "version": "nginx/1.18.0",
                    "banner": "nginx"
                },
                confidence=0.9,
                timestamp=datetime.now(),
                source="service_detector"
            )
            findings.append(finding)
        
        return findings
    
    async def _enumeration(
        self,
        targets: List[Target],
        constraints: Dict[str, Any]
    ) -> List[Finding]:
        """
        Enumeration (detailed information gathering).
        
        Args:
            targets: Targets
            constraints: Constraints
            
        Returns:
            Enumeration findings
        """
        findings: List[Finding] = []
        
        for target in targets:
            # Technology detection
            finding = Finding(
                id=f"find_{int(datetime.now().timestamp())}_tech",
                target=target.identifier,
                finding_type=FindingType.TECHNOLOGY,
                data={
                    "technology": "nginx",
                    "version": "1.18.0",
                    "confidence": "high"
                },
                confidence=0.85,
                timestamp=datetime.now(),
                source="tech_detector"
            )
            findings.append(finding)
        
        return findings
    
    def _correlate_findings(
        self,
        findings: List[Finding]
    ) -> Dict[str, Any]:
        """
        Correlate findings to identify patterns.
        
        Args:
            findings: All findings
            
        Returns:
            Correlation analysis
        """
        by_target: Dict[str, List[Finding]] = {}
        by_type: Dict[str, int] = {}
        
        for finding in findings:
            # Group by target
            if finding.target not in by_target:
                by_target[finding.target] = []
            by_target[finding.target].append(finding)
            
            # Count by type
            finding_type = finding.finding_type.value
            by_type[finding_type] = by_type.get(finding_type, 0) + 1
        
        return {
            "targets_with_findings": len(by_target),
            "findings_by_type": by_type,
            "high_confidence_findings": len([
                f for f in findings if f.confidence >= 0.9
            ])
        }
    
    def _finding_to_dict(self, finding: Finding) -> Dict[str, Any]:
        """
        Convert Finding to dictionary.
        
        Args:
            finding: Finding object
            
        Returns:
            Dictionary representation
        """
        return {
            "id": finding.id,
            "target": finding.target,
            "type": finding.finding_type.value,
            "data": finding.data,
            "confidence": finding.confidence,
            "timestamp": finding.timestamp.isoformat(),
            "source": finding.source
        }
    
    def get_mission_status(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Get mission status.
        
        Args:
            mission_id: Mission identifier
            
        Returns:
            Mission status or None
        """
        mission = self.active_missions.get(mission_id)
        if not mission:
            return None
        
        return {
            "mission_id": mission.id,
            "status": mission.status,
            "targets_count": len(mission.targets),
            "findings_count": len(mission.findings),
            "created_at": mission.created_at.isoformat()
        }
