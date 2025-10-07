"""Maximus Threat Intelligence Service - Offline Engine.

This module implements an Offline Threat Intelligence Engine for the Maximus
AI's Threat Intelligence Service. It is responsible for managing and querying
a local, cached repository of threat intelligence data, reducing reliance on
real-time external API calls and improving response times.

Key functionalities include:
- Storing a curated set of known indicators of compromise (IoCs), TTPs, and threat actor profiles.
- Performing rapid lookups against the local threat intelligence database.
- Providing contextual information for security events even when external TIPs
  are unavailable or rate-limited.
- Supporting offline threat assessment and incident response capabilities.

This engine is crucial for ensuring that Maximus AI has immediate access to
critical threat intelligence, enhancing its ability to detect and respond to
known threats efficiently.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class OfflineThreatIntelEngine:
    """Manages and queries a local, cached repository of threat intelligence data,
    reducing reliance on real-time external API calls and improving response times.

    Stores a curated set of known indicators of compromise (IoCs), TTPs, and
    threat actor profiles, and performs rapid lookups against the local database.
    """

    def __init__(self):
        """Initializes the OfflineThreatIntelEngine with a mock threat intelligence database."""
        self.threat_intel_db: Dict[str, Dict[str, Any]] = {
            "ip:1.2.3.4": {
                "indicator": "1.2.3.4",
                "type": "ip",
                "threat_level": "high",
                "description": "Known C2 server",
                "last_updated": (datetime.now() - timedelta(days=7)).isoformat(),
            },
            "domain:malicious.com": {
                "indicator": "malicious.com",
                "type": "domain",
                "threat_level": "critical",
                "description": "Phishing domain",
                "last_updated": (datetime.now() - timedelta(days=1)).isoformat(),
            },
            "hash:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
                "indicator": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "type": "hash",
                "threat_level": "medium",
                "description": "Known malware sample",
                "last_updated": datetime.now().isoformat(),
            },
        }
        self.last_db_update: Optional[datetime] = datetime.now()
        self.query_count: int = 0

    async def get_threat_intel(
        self, indicator: str, indicator_type: str
    ) -> Dict[str, Any]:
        """Retrieves threat intelligence for a given indicator from the offline database.

        Args:
            indicator (str): The indicator to query.
            indicator_type (str): The type of indicator (e.g., 'ip', 'domain', 'hash').

        Returns:
            Dict[str, Any]: A dictionary containing the threat intelligence information.
        """
        print(
            f"[OfflineThreatIntelEngine] Querying offline DB for {indicator_type}: {indicator}"
        )
        await asyncio.sleep(0.05)  # Simulate fast lookup

        key = f"{indicator_type}:{indicator}"
        result = self.threat_intel_db.get(
            key,
            {
                "indicator": indicator,
                "type": indicator_type,
                "threat_level": "unknown",
                "description": "No offline intelligence found.",
                "last_updated": datetime.now().isoformat(),
            },
        )
        self.query_count += 1
        return result

    async def update_threat_intel_db(self, new_intel: List[Dict[str, Any]]):
        """Updates the offline threat intelligence database with new data.

        Args:
            new_intel (List[Dict[str, Any]]): A list of new threat intelligence entries.
        """
        print(
            f"[OfflineThreatIntelEngine] Updating offline DB with {len(new_intel)} new entries."
        )
        await asyncio.sleep(0.1)  # Simulate update time
        for entry in new_intel:
            key = f"{entry['type']}:{entry['indicator']}"
            self.threat_intel_db[key] = entry
        self.last_db_update = datetime.now()

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Offline Threat Intelligence Engine.

        Returns:
            Dict[str, Any]: A dictionary summarizing the engine's status.
        """
        return {
            "status": "active",
            "total_indicators_in_db": len(self.threat_intel_db),
            "last_db_update": (
                self.last_db_update.isoformat() if self.last_db_update else "N/A"
            ),
            "total_queries": self.query_count,
        }
