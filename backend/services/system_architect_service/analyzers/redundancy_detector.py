"""Redundancy Detector - Identifies redundant or overlapping services."""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RedundancyDetector:
    """Detects redundant services and consolidation opportunities."""

    def __init__(self, scanner):
        self.scanner = scanner

    async def detect(self) -> Dict[str, Any]:
        """Detect redundancies in service architecture."""
        logger.info("🔄 Detecting redundancies...")

        architecture = await self.scanner.scan()
        services = architecture["services"]

        # Group services by functional similarity
        service_groups = self._group_similar_services(services)

        # Identify potential consolidations
        consolidation_opportunities = self._identify_consolidations(service_groups)

        # Estimate resource savings
        savings = self._estimate_savings(consolidation_opportunities)

        result = {
            "redundant_services": consolidation_opportunities,
            "total_opportunities": len(consolidation_opportunities),
            "estimated_savings": savings,
            "service_groups": {k: len(v) for k, v in service_groups.items()}
        }

        logger.info(f"✅ Found {len(consolidation_opportunities)} consolidation opportunities")
        return result

    def _group_similar_services(
        self,
        services: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Group services by functional similarity."""
        groups = {}

        # Group by common keywords
        keywords = ["osint", "intel", "threat", "immune", "narrative"]

        for keyword in keywords:
            matching = [
                name for name in services
                if keyword in name.lower()
            ]
            if len(matching) > 1:
                groups[keyword] = matching

        return groups

    def _identify_consolidations(
        self,
        service_groups: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """Identify consolidation opportunities."""
        opportunities = []

        for group_name, services in service_groups.items():
            if len(services) > 2:
                opportunities.append({
                    "group": group_name,
                    "services": services,
                    "count": len(services),
                    "recommendation": f"Consider consolidating {len(services)} {group_name} services",
                    "priority": "MEDIUM" if len(services) > 3 else "LOW"
                })

        return opportunities

    def _estimate_savings(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Estimate resource savings from consolidation."""
        total_services_to_consolidate = sum(
            opp["count"] - 1  # Keep 1, consolidate others
            for opp in opportunities
        )

        return {
            "services_reduced": total_services_to_consolidate,
            "estimated_memory_savings_gb": total_services_to_consolidate * 0.5,
            "estimated_cpu_savings_cores": total_services_to_consolidate * 0.25
        }
