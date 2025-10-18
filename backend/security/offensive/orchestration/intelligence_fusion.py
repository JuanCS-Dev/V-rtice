"""
Intelligence Fusion - AI-driven threat intelligence aggregation.

Fuses data from reconnaissance, exploitation, and external sources
to build comprehensive target profiles and attack strategies.
"""
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError


class IntelligenceSource(Enum):
    """Intelligence data sources."""
    RECONNAISSANCE = "reconnaissance"
    OSINT = "osint"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    EXTERNAL_API = "external_api"
    MANUAL = "manual"


class ThreatLevel(Enum):
    """Target threat assessment levels."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IntelligenceItem:
    """Single piece of intelligence."""
    source: IntelligenceSource
    category: str
    data: Any
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class TargetProfile:
    """Comprehensive target profile."""
    identifier: str
    creation_time: datetime
    last_updated: datetime
    
    # Network information
    ip_addresses: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)
    open_ports: Dict[int, str] = field(default_factory=dict)
    
    # System information
    os_fingerprint: Optional[str] = None
    services: Dict[str, str] = field(default_factory=dict)
    technologies: Set[str] = field(default_factory=set)
    
    # Vulnerabilities
    vulnerabilities: List[str] = field(default_factory=list)
    exploitable_services: List[str] = field(default_factory=list)
    
    # Assessment
    threat_level: ThreatLevel = ThreatLevel.MINIMAL
    attack_surface_score: float = 0.0
    recommended_strategies: List[str] = field(default_factory=list)
    
    # Intelligence items
    intelligence: List[IntelligenceItem] = field(default_factory=list)


@dataclass
class ThreatIntelligence:
    """Aggregated threat intelligence."""
    targets: Dict[str, TargetProfile]
    correlations: Dict[str, List[str]]
    timeline: List[IntelligenceItem]
    metadata: Dict = field(default_factory=dict)


class IntelligenceFusion(OffensiveTool):
    """
    AI-enhanced intelligence fusion engine.
    
    Aggregates, correlates, and analyzes intelligence from multiple sources
    to build comprehensive target profiles and recommend attack strategies.
    """
    
    def __init__(self) -> None:
        """Initialize intelligence fusion."""
        super().__init__(
            name="intelligence_fusion",
            category="orchestration"
        )
        
        self.profiles: Dict[str, TargetProfile] = {}
        self.correlation_rules: List[callable] = []
        self.intelligence_history: List[IntelligenceItem] = []
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        intelligence_data: Optional[Dict] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute intelligence operations.
        
        Args:
            operation: Operation type (ingest, analyze, query, export)
            target: Target identifier (for targeted operations)
            intelligence_data: Intelligence data to ingest
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with operation results
            
        Raises:
            OffensiveToolError: If operation fails
        """
        try:
            if operation == "ingest":
                result = await self._ingest_intelligence(
                    target=target,
                    data=intelligence_data,
                    **kwargs
                )
            
            elif operation == "analyze":
                result = await self._analyze_target(target, **kwargs)
            
            elif operation == "query":
                result = await self._query_intelligence(**kwargs)
            
            elif operation == "export":
                result = await self._export_intelligence(target)
            
            else:
                raise OffensiveToolError(
                    f"Unknown operation: {operation}",
                    tool_name=self.name
                )
            
            return ToolResult(
                success=True,
                data=result,
                message=f"Intelligence operation completed: {operation}",
                metadata=self._create_metadata()
            )
            
        except Exception as e:
            raise OffensiveToolError(
                f"Intelligence operation failed: {str(e)}",
                tool_name=self.name,
                details={"operation": operation, "target": target}
            )
    
    async def _ingest_intelligence(
        self,
        target: str,
        data: Dict,
        source: IntelligenceSource = IntelligenceSource.MANUAL,
        confidence: float = 0.8,
        **kwargs
    ) -> Dict:
        """
        Ingest intelligence data.
        
        Args:
            target: Target identifier
            data: Intelligence data
            source: Data source
            confidence: Confidence score
            **kwargs: Additional parameters
            
        Returns:
            Ingestion result
        """
        # Get or create profile
        if target not in self.profiles:
            self.profiles[target] = TargetProfile(
                identifier=target,
                creation_time=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
        
        profile = self.profiles[target]
        profile.last_updated = datetime.utcnow()
        
        # Process intelligence data
        items_added = 0
        
        # Network information
        if "ip_addresses" in data:
            for ip in data["ip_addresses"]:
                profile.ip_addresses.add(ip)
                items_added += 1
        
        if "domains" in data:
            for domain in data["domains"]:
                profile.domains.add(domain)
                items_added += 1
        
        if "open_ports" in data:
            for port, service in data["open_ports"].items():
                profile.open_ports[int(port)] = service
                items_added += 1
        
        # System information
        if "os_fingerprint" in data:
            profile.os_fingerprint = data["os_fingerprint"]
            items_added += 1
        
        if "services" in data:
            profile.services.update(data["services"])
            items_added += 1
        
        if "technologies" in data:
            for tech in data["technologies"]:
                profile.technologies.add(tech)
                items_added += 1
        
        # Vulnerabilities
        if "vulnerabilities" in data:
            profile.vulnerabilities.extend(data["vulnerabilities"])
            items_added += len(data["vulnerabilities"])
        
        # Create intelligence item
        intel_item = IntelligenceItem(
            source=source,
            category="ingestion",
            data=data,
            timestamp=datetime.utcnow(),
            confidence=confidence
        )
        
        profile.intelligence.append(intel_item)
        self.intelligence_history.append(intel_item)
        
        # Run correlation
        await self._correlate_intelligence(profile)
        
        return {
            "target": target,
            "items_added": items_added,
            "total_intelligence": len(profile.intelligence),
            "profile_updated": True
        }
    
    async def _analyze_target(self, target: str, **kwargs) -> TargetProfile:
        """
        Analyze target and update profile.
        
        Args:
            target: Target identifier
            **kwargs: Additional parameters
            
        Returns:
            Updated target profile
        """
        if target not in self.profiles:
            raise OffensiveToolError(
                f"Target profile not found: {target}",
                tool_name=self.name
            )
        
        profile = self.profiles[target]
        
        # Calculate attack surface score
        profile.attack_surface_score = self._calculate_attack_surface(profile)
        
        # Assess threat level
        profile.threat_level = self._assess_threat_level(profile)
        
        # Generate recommendations
        profile.recommended_strategies = self._generate_strategies(profile)
        
        profile.last_updated = datetime.utcnow()
        
        return profile
    
    async def _query_intelligence(
        self,
        query_type: str = "all",
        filters: Optional[Dict] = None,
        **kwargs
    ) -> ThreatIntelligence:
        """
        Query intelligence database.
        
        Args:
            query_type: Type of query
            filters: Query filters
            **kwargs: Additional parameters
            
        Returns:
            Aggregated threat intelligence
        """
        # Apply filters
        filtered_profiles = self.profiles
        
        if filters:
            if "threat_level" in filters:
                filtered_profiles = {
                    k: v for k, v in filtered_profiles.items()
                    if v.threat_level == ThreatLevel[filters["threat_level"].upper()]
                }
            
            if "has_vulnerabilities" in filters and filters["has_vulnerabilities"]:
                filtered_profiles = {
                    k: v for k, v in filtered_profiles.items()
                    if v.vulnerabilities
                }
        
        # Build correlations
        correlations = self._build_correlations(list(filtered_profiles.values()))
        
        return ThreatIntelligence(
            targets=filtered_profiles,
            correlations=correlations,
            timeline=self.intelligence_history[-100:],  # Last 100 items
            metadata={
                "total_profiles": len(self.profiles),
                "filtered_profiles": len(filtered_profiles),
                "total_intelligence_items": len(self.intelligence_history)
            }
        )
    
    async def _export_intelligence(self, target: Optional[str] = None) -> Dict:
        """
        Export intelligence data.
        
        Args:
            target: Optional target filter
            
        Returns:
            Exported data
        """
        if target:
            if target not in self.profiles:
                raise OffensiveToolError(
                    f"Target profile not found: {target}",
                    tool_name=self.name
                )
            
            return self._export_profile(self.profiles[target])
        
        # Export all profiles
        return {
            "profiles": {
                k: self._export_profile(v)
                for k, v in self.profiles.items()
            },
            "metadata": {
                "export_time": datetime.utcnow().isoformat(),
                "total_profiles": len(self.profiles),
                "total_intelligence": len(self.intelligence_history)
            }
        }
    
    def _export_profile(self, profile: TargetProfile) -> Dict:
        """Export single profile."""
        return {
            "identifier": profile.identifier,
            "creation_time": profile.creation_time.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
            "ip_addresses": list(profile.ip_addresses),
            "domains": list(profile.domains),
            "open_ports": profile.open_ports,
            "os_fingerprint": profile.os_fingerprint,
            "services": profile.services,
            "technologies": list(profile.technologies),
            "vulnerabilities": profile.vulnerabilities,
            "exploitable_services": profile.exploitable_services,
            "threat_level": profile.threat_level.value,
            "attack_surface_score": profile.attack_surface_score,
            "recommended_strategies": profile.recommended_strategies,
            "intelligence_count": len(profile.intelligence)
        }
    
    async def _correlate_intelligence(self, profile: TargetProfile) -> None:
        """
        Correlate intelligence to identify patterns.
        
        Args:
            profile: Target profile
        """
        # Identify exploitable services based on known vulnerabilities
        for port, service in profile.open_ports.items():
            # Check for known vulnerable service versions
            if any(vuln in service.lower() for vuln in ["outdated", "unpatched", "vulnerable"]):
                if f"{service}:{port}" not in profile.exploitable_services:
                    profile.exploitable_services.append(f"{service}:{port}")
        
        # Correlate technologies with known vulnerabilities
        vulnerable_techs = {
            "wordpress": ["CVE-2021-XXXX"],
            "apache": ["CVE-2021-YYYY"],
            "nginx": ["CVE-2020-ZZZZ"]
        }
        
        for tech in profile.technologies:
            tech_lower = tech.lower()
            for vuln_tech, cves in vulnerable_techs.items():
                if vuln_tech in tech_lower:
                    profile.vulnerabilities.extend(cves)
    
    def _calculate_attack_surface(self, profile: TargetProfile) -> float:
        """
        Calculate attack surface score.
        
        Args:
            profile: Target profile
            
        Returns:
            Attack surface score (0.0 to 1.0)
        """
        score = 0.0
        
        # Open ports contribute
        score += min(len(profile.open_ports) * 0.05, 0.3)
        
        # Services contribute
        score += min(len(profile.services) * 0.03, 0.2)
        
        # Vulnerabilities contribute significantly
        score += min(len(profile.vulnerabilities) * 0.1, 0.4)
        
        # Exploitable services contribute
        score += min(len(profile.exploitable_services) * 0.15, 0.3)
        
        return min(score, 1.0)
    
    def _assess_threat_level(self, profile: TargetProfile) -> ThreatLevel:
        """
        Assess target threat level.
        
        Args:
            profile: Target profile
            
        Returns:
            Threat level
        """
        score = profile.attack_surface_score
        
        if score >= 0.8:
            return ThreatLevel.CRITICAL
        elif score >= 0.6:
            return ThreatLevel.HIGH
        elif score >= 0.4:
            return ThreatLevel.MODERATE
        elif score >= 0.2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.MINIMAL
    
    def _generate_strategies(self, profile: TargetProfile) -> List[str]:
        """
        Generate recommended attack strategies.
        
        Args:
            profile: Target profile
            
        Returns:
            List of recommended strategies
        """
        strategies = []
        
        # Port-based strategies
        if 80 in profile.open_ports or 443 in profile.open_ports:
            strategies.append("web_application_testing")
        
        if 22 in profile.open_ports:
            strategies.append("ssh_authentication_attack")
        
        if 445 in profile.open_ports or 139 in profile.open_ports:
            strategies.append("smb_exploitation")
        
        if 3389 in profile.open_ports:
            strategies.append("rdp_exploitation")
        
        # Vulnerability-based strategies
        if profile.vulnerabilities:
            strategies.append("targeted_exploit_deployment")
        
        # Service-based strategies
        if "wordpress" in str(profile.technologies).lower():
            strategies.append("cms_exploitation")
        
        if not strategies:
            strategies.append("comprehensive_reconnaissance")
        
        return strategies
    
    def _build_correlations(
        self, profiles: List[TargetProfile]
    ) -> Dict[str, List[str]]:
        """
        Build correlations between targets.
        
        Args:
            profiles: List of target profiles
            
        Returns:
            Correlation mappings
        """
        correlations = {}
        
        # Find targets sharing IP addresses
        ip_map: Dict[str, List[str]] = {}
        for profile in profiles:
            for ip in profile.ip_addresses:
                if ip not in ip_map:
                    ip_map[ip] = []
                ip_map[ip].append(profile.identifier)
        
        # Build correlations
        for ip, targets in ip_map.items():
            if len(targets) > 1:
                for target in targets:
                    if target not in correlations:
                        correlations[target] = []
                    correlations[target].extend([t for t in targets if t != target])
        
        return correlations
    
    def _create_metadata(self) -> ToolMetadata:
        """
        Create tool metadata.
        
        Returns:
            Tool metadata
        """
        return ToolMetadata(
            tool_name=self.name,
            execution_time=0.0,
            success_rate=1.0,
            confidence_score=0.95,
            resource_usage={
                "total_profiles": len(self.profiles),
                "intelligence_items": len(self.intelligence_history)
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate intelligence fusion.
        
        Returns:
            True if validation passes
        """
        # Test basic operations
        try:
            await self._ingest_intelligence(
                target="test_target",
                data={"ip_addresses": ["192.168.1.1"]},
                source=IntelligenceSource.MANUAL
            )
            
            await self._analyze_target("test_target")
            
            # Cleanup test data
            del self.profiles["test_target"]
            
            return True
        except Exception:
            return False
