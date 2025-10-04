"""
Shodan Plugin Example
=====================

Enriches host discoveries with Shodan intelligence.

Installation:
    pip install shodan

Configuration:
    ~/.vertice/config.yaml:
        plugins:
          shodan:
            api_key: YOUR_SHODAN_API_KEY
            auto_enrich: true

Usage:
    vcli plugin enable shodan

    # Plugin automatically enriches discovered hosts
    vcli scan nmap 1.1.1.1
    # → Shodan data automatically fetched

Author: example@vertice.dev
License: MIT
"""

from typing import Dict, Any, Optional
import logging

from vertice.plugins import BasePlugin, hook, HookPriority

logger = logging.getLogger(__name__)


class ShodanPlugin(BasePlugin):
    """
    Shodan OSINT integration plugin.

    Hooks into:
    - on_host_discovered: Enrich with Shodan data
    - on_scan_complete: Summary of Shodan findings
    """

    # Required metadata
    name = "shodan"
    version = "1.0.0"
    author = "vertice-community"
    description = "Enrich hosts with Shodan intelligence"

    # Optional metadata
    homepage = "https://github.com/vertice-plugins/shodan"
    dependencies = ["shodan>=1.28.0"]
    vertice_min_version = "1.0.0"

    def __init__(self):
        """Initialize Shodan plugin."""
        super().__init__()
        self.shodan_client = None
        self.cache = {}

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize Shodan client.

        Args:
            config: Must contain 'api_key'
        """
        super().initialize(config)

        api_key = config.get("api_key")

        if not api_key:
            raise ValueError("Shodan plugin requires 'api_key' in config")

        # Import Shodan (lazy load)
        try:
            import shodan
            self.shodan_client = shodan.Shodan(api_key)
            logger.info("Shodan client initialized")

        except ImportError:
            raise ValueError("Shodan library not installed. Run: pip install shodan")

    @hook("on_host_discovered", priority=HookPriority.NORMAL)
    def enrich_host(self, context):
        """
        Enrich host with Shodan data.

        Args:
            context: HookContext with host data

        Returns:
            Enrichment data
        """
        host = context.data.get("host")

        if not host:
            logger.warning("No host in context")
            return None

        ip_address = getattr(host, "ip_address", None)

        if not ip_address:
            logger.warning("Host has no IP address")
            return None

        # Check cache
        if ip_address in self.cache:
            logger.debug(f"Shodan data cached for {ip_address}")
            return self.cache[ip_address]

        # Query Shodan
        try:
            logger.info(f"Querying Shodan for {ip_address}")

            shodan_data = self.shodan_client.host(ip_address)

            # Extract relevant fields
            enrichment = {
                "shodan_country": shodan_data.get("country_name"),
                "shodan_org": shodan_data.get("org"),
                "shodan_isp": shodan_data.get("isp"),
                "shodan_asn": shodan_data.get("asn"),
                "shodan_ports": shodan_data.get("ports", []),
                "shodan_vulns": shodan_data.get("vulns", []),
                "shodan_tags": shodan_data.get("tags", []),
                "shodan_last_update": shodan_data.get("last_update"),
            }

            # Cache result
            self.cache[ip_address] = enrichment

            logger.info(
                f"Shodan enrichment: {ip_address} → {enrichment['shodan_org']} "
                f"({len(enrichment['shodan_ports'])} ports)"
            )

            return enrichment

        except Exception as e:
            logger.error(f"Shodan query failed for {ip_address}: {e}")
            return None

    @hook("on_scan_complete", priority=HookPriority.LOW)
    def summarize_findings(self, context):
        """
        Summarize Shodan findings after scan.

        Args:
            context: HookContext with scan results
        """
        scan_result = context.data.get("scan_result")

        if not scan_result:
            return

        # Count enriched hosts
        enriched_count = len(self.cache)

        logger.info(f"Shodan: Enriched {enriched_count} hosts during scan")

        # Find interesting findings
        vulns_found = sum(
            len(data.get("shodan_vulns", []))
            for data in self.cache.values()
        )

        if vulns_found > 0:
            logger.warning(f"Shodan: Found {vulns_found} known vulnerabilities")

    def deactivate(self) -> None:
        """Cleanup on deactivation."""
        super().deactivate()
        self.cache.clear()
        logger.info("Shodan plugin deactivated, cache cleared")
