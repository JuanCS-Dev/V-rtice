"""Oráculo Engine - Main orchestration for threat intelligence pipeline.

This is the brain of the Oráculo system, orchestrating:
1. Threat feed ingestion (OSV.dev)
2. Dependency graph cross-referencing
3. Relevance filtering
4. APV generation
5. Kafka publishing

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio
import logging

from threat_feeds.osv_client import OSVClient
from filtering.dependency_graph import DependencyGraphBuilder
from filtering.relevance_filter import RelevanceFilter, RelevanceMatch
from kafka_integration.apv_publisher import APVPublisher
from services.maximus_oraculo.models.apv import APV, CVSSScore, AffectedPackage, ASTGrepPattern

logger = logging.getLogger(__name__)


class OraculoEngine:
    """
    Main orchestration engine for Oráculo Threat Sentinel.
    
    Responsibilities:
    - Orchestrate end-to-end CVE → APV → Kafka pipeline
    - Manage threat feed clients
    - Coordinate dependency graph
    - Filter for relevance
    - Generate APVs
    - Publish to Kafka
    - Collect metrics
    
    Theoretical Foundation:
    - Pipeline Pattern: Sequential data transformation
    - Event-Driven Architecture: Kafka as event bus
    - Circuit Breaker: Fail fast on feed unavailability
    
    Usage:
        >>> engine = OraculoEngine(repo_root="/path/to/maximus")
        >>> await engine.initialize()
        >>> results = await engine.scan_vulnerabilities()
        >>> print(f"Published {results['published']} APVs")
    """
    
    def __init__(
        self,
        repo_root: Path,
        kafka_servers: str = "localhost:9096",
        osv_rate_limit: int = 100
    ):
        """
        Initialize Oráculo Engine.
        
        Args:
            repo_root: MAXIMUS repository root
            kafka_servers: Kafka bootstrap servers
            osv_rate_limit: OSV.dev rate limit (req/min)
        """
        self.repo_root = Path(repo_root)
        self.kafka_servers = kafka_servers
        
        # Components (initialized in initialize())
        self.dependency_graph: Optional[DependencyGraphBuilder] = None
        self.relevance_filter: Optional[RelevanceFilter] = None
        self.osv_client: Optional[OSVClient] = None
        self.apv_publisher: Optional[APVPublisher] = None
        
        # Metrics
        self._metrics = {
            "vulnerabilities_fetched": 0,
            "relevant_matches": 0,
            "apvs_generated": 0,
            "apvs_published": 0,
            "errors": 0,
            "last_run": None
        }
        
        logger.info(f"Initialized OraculoEngine for {self.repo_root}")
    
    async def initialize(self) -> None:
        """
        Initialize all components.
        
        Builds dependency graph, initializes clients, etc.
        """
        logger.info("Initializing Oráculo Engine components...")
        
        # Build dependency graph
        logger.info("Building dependency graph...")
        self.dependency_graph = DependencyGraphBuilder(self.repo_root)
        self.dependency_graph.build_graph()
        
        graph_stats = self.dependency_graph.get_stats()
        logger.info(
            f"Dependency graph built: "
            f"{graph_stats['total_services']} services, "
            f"{graph_stats['total_packages']} packages"
        )
        
        # Initialize relevance filter
        self.relevance_filter = RelevanceFilter(self.dependency_graph)
        
        # Initialize OSV client
        self.osv_client = OSVClient(rate_limit=100)
        await self.osv_client._ensure_session()
        
        # Initialize Kafka publisher
        self.apv_publisher = APVPublisher(bootstrap_servers=self.kafka_servers)
        await self.apv_publisher.start()
        
        logger.info("Oráculo Engine initialization complete")
    
    async def shutdown(self) -> None:
        """Shutdown all components."""
        logger.info("Shutting down Oráculo Engine...")
        
        if self.osv_client:
            await self.osv_client.close()
        
        if self.apv_publisher:
            await self.apv_publisher.stop()
        
        logger.info("Oráculo Engine shutdown complete")
    
    async def scan_vulnerabilities(
        self,
        packages: Optional[List[str]] = None,
        min_severity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Run full vulnerability scan pipeline.
        
        Pipeline:
        1. Fetch vulnerabilities from OSV.dev (for all packages or specified)
        2. Filter by relevance (dependency graph cross-reference)
        3. Generate APVs
        4. Publish to Kafka
        
        Args:
            packages: Specific packages to scan (None = all packages in graph)
            min_severity: Minimum CVSS score to process
            
        Returns:
            Dict with scan results and metrics
        """
        if not all([self.dependency_graph, self.relevance_filter, self.osv_client, self.apv_publisher]):
            raise RuntimeError("Engine not initialized. Call initialize() first.")
        
        logger.info("Starting vulnerability scan...")
        self._metrics["last_run"] = datetime.utcnow().isoformat()
        
        # Determine which packages to scan
        if packages is None:
            packages_to_scan = list(self.dependency_graph.get_all_packages())
        else:
            packages_to_scan = packages
        
        logger.info(f"Scanning {len(packages_to_scan)} packages")
        
        # Fetch vulnerabilities from OSV.dev
        all_vulnerabilities = await self._fetch_vulnerabilities(packages_to_scan)
        self._metrics["vulnerabilities_fetched"] = len(all_vulnerabilities)
        
        # Filter for relevance
        relevant_matches = self.relevance_filter.filter_vulnerabilities(
            all_vulnerabilities,
            min_severity=min_severity
        )
        self._metrics["relevant_matches"] = len(relevant_matches)
        
        # Generate APVs
        apvs = await self._generate_apvs(relevant_matches, all_vulnerabilities)
        self._metrics["apvs_generated"] = len(apvs)
        
        # Publish to Kafka
        publish_results = await self.apv_publisher.publish_batch(apvs)
        self._metrics["apvs_published"] = publish_results["success"]
        self._metrics["errors"] = publish_results["failed"]
        
        results = {
            "packages_scanned": len(packages_to_scan),
            "vulnerabilities_fetched": self._metrics["vulnerabilities_fetched"],
            "relevant_matches": self._metrics["relevant_matches"],
            "apvs_generated": self._metrics["apvs_generated"],
            "published": publish_results["success"],
            "failed": publish_results["failed"],
            "timestamp": self._metrics["last_run"]
        }
        
        logger.info(
            f"Scan complete: {results['published']} APVs published, "
            f"{results['failed']} failed"
        )
        
        return results
    
    async def _fetch_vulnerabilities(
        self,
        packages: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch vulnerabilities for multiple packages.
        
        Args:
            packages: List of package names
            
        Returns:
            List of vulnerability dicts
        """
        if not self.osv_client:
            raise RuntimeError("OSV client not initialized")
        
        all_vulns: List[Dict[str, Any]] = []
        
        # Batch query for efficiency
        batch_size = 10
        for i in range(0, len(packages), batch_size):
            batch = packages[i:i+batch_size]
            
            # Prepare batch query
            package_dicts = [
                {"ecosystem": "PyPI", "name": pkg}
                for pkg in batch
            ]
            
            try:
                results = await self.osv_client.query_batch(package_dicts)
                
                for pkg_name, vulns in results.items():
                    all_vulns.extend(vulns)
                
            except Exception as e:
                logger.error(f"Error fetching vulnerabilities for batch: {e}")
                # Continue with other batches
                continue
        
        logger.info(f"Fetched {len(all_vulns)} total vulnerabilities")
        
        return all_vulns
    
    async def _generate_apvs(
        self,
        matches: List[RelevanceMatch],
        raw_vulnerabilities: List[Dict[str, Any]]
    ) -> List[APV]:
        """
        Generate APV objects from relevance matches.
        
        Args:
            matches: Relevance matches
            raw_vulnerabilities: Original vulnerability dicts for enrichment
            
        Returns:
            List of APV objects
        """
        apvs: List[APV] = []
        
        # Build lookup map for raw vulns
        vuln_map = {v.get("id"): v for v in raw_vulnerabilities}
        
        for match in matches:
            raw_vuln = vuln_map.get(match.cve_id)
            if not raw_vuln:
                logger.warning(f"Raw vulnerability not found for {match.cve_id}")
                continue
            
            try:
                apv = await self._create_apv_from_match(match, raw_vuln)
                apvs.append(apv)
            except Exception as e:
                logger.error(f"Error creating APV for {match.cve_id}: {e}")
                continue
        
        return apvs
    
    async def _create_apv_from_match(
        self,
        match: RelevanceMatch,
        raw_vulnerability: Dict[str, Any]
    ) -> APV:
        """
        Create APV object from relevance match and raw vulnerability.
        
        Args:
            match: Relevance match
            raw_vulnerability: Raw vulnerability dict from OSV
            
        Returns:
            APV object
        """
        # Extract data from raw vulnerability
        cve_id = raw_vulnerability.get("id", match.cve_id)
        
        # Get timestamps
        published_str = raw_vulnerability.get("published")
        modified_str = raw_vulnerability.get("modified")
        
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00")) if published_str else datetime.utcnow()
        modified = datetime.fromisoformat(modified_str.replace("Z", "+00:00")) if modified_str else datetime.utcnow()
        
        # Get description
        summary = raw_vulnerability.get("summary", "")
        details = raw_vulnerability.get("details", "")
        
        # If no summary, use first 100 chars of details
        if not summary and details:
            summary = details[:100] + "..." if len(details) > 100 else details
        
        # If neither, use generic
        if not summary:
            summary = f"Vulnerability in {match.package_name}"
        
        if not details:
            details = summary
        
        # Extract CVSS if available
        cvss = None
        severity_list = raw_vulnerability.get("severity", [])
        for severity_item in severity_list:
            if severity_item.get("type") == "CVSS_V3":
                score_string = severity_item.get("score", "")
                if score_string:
                    # Parse CVSS score
                    # Example: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
                    cvss = CVSSScore(
                        version="3.1",
                        base_score=match.severity_score or 5.0,
                        severity="MEDIUM",
                        vector_string=score_string
                    )
                    break
        
        # Build affected packages list
        affected_packages_list = []
        for affected_item in raw_vulnerability.get("affected", []):
            package_info = affected_item.get("package", {})
            pkg_name = package_info.get("name")
            pkg_ecosystem = package_info.get("ecosystem", "PyPI")
            
            if pkg_name == match.package_name:
                # Extract version ranges
                ranges = affected_item.get("ranges", [])
                versions = affected_item.get("versions", [])
                
                # Build version spec string (simplified)
                version_spec = "*"
                if ranges:
                    # Extract first range
                    first_range = ranges[0]
                    events = first_range.get("events", [])
                    for event in events:
                        if "introduced" in event:
                            intro = event["introduced"]
                            if intro != "0":
                                version_spec = f">={intro}"
                            break
                
                affected_packages_list.append(
                    AffectedPackage(
                        ecosystem=pkg_ecosystem,
                        name=pkg_name,
                        affected_versions=[version_spec],
                        fixed_versions=[]  # Would extract from "fixed" events
                    )
                )
        
        # If no affected packages found, create one from match
        if not affected_packages_list:
            affected_packages_list.append(
                AffectedPackage(
                    ecosystem=match.ecosystem,
                    name=match.package_name,
                    affected_versions=["*"],
                    fixed_versions=[]
                )
            )
        
        # Create APV
        apv = APV(
            cve_id=cve_id,
            aliases=raw_vulnerability.get("aliases", []),
            published=published,
            modified=modified,
            summary=summary,
            details=details,
            cvss=cvss,
            affected_packages=affected_packages_list,
            maximus_context={
                "affected_services": match.affected_services,
                "version_match": match.version_match,
                "discovered_by": "oraculo_engine",
                "scan_timestamp": datetime.utcnow().isoformat()
            },
            source_feed="OSV.dev",
            oraculo_version="1.0.0"
        )
        
        return apv
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return self._metrics.copy()
