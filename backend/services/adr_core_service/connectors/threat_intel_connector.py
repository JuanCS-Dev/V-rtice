"""Threat Intelligence Connector for enriching threat data.

This module provides a connector to the Threat Intelligence Service. It is used
to check indicators (IPs, domains, hashes) against a database of known
threats, providing reputation, threat scores, and associated malware families.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# As with the previous file, BaseConnector is assumed to exist.
class BaseConnector:
    def __init__(self, config):
        pass
    async def enrich(self, data):
        return data

logger = logging.getLogger(__name__)


class ThreatIntelConnector(BaseConnector):
    """Connects to the Threat Intelligence Service for threat enrichment.

    This connector queries the Threat Intel Service to get detailed information
    about indicators like IPs, domains, and file hashes. It provides threat
    scores, reputation, and MITRE ATT&CK TTPs to enrich raw detections.

    Attributes:
        base_url (str): The base URL of the Threat Intelligence Service.
        client (httpx.AsyncClient): The client for making asynchronous HTTP requests.
        cache (Dict[str, Any]): An in-memory cache for threat intelligence results.
    """

    def __init__(self, base_url: str = "http://localhost:8013"):
        """Initializes the ThreatIntelConnector.

        Args:
            base_url (str, optional): The base URL of the Threat Intelligence Service.
                Defaults to "http://localhost:8013".
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=15.0)
        self.cache = {}
        logger.info(f"Initialized ThreatIntelConnector for URL: {base_url}")

    async def check_threat(
        self,
        target: str,
        target_type: str = "auto"
    ) -> Optional[Dict[str, Any]]:
        """Checks a single target (IP, domain, hash) for threat information.

        Queries the Threat Intel Service for a given target. It uses an in-memory
        cache to avoid redundant queries.

        Args:
            target (str): The indicator to check (e.g., '8.8.8.8', 'evil.com').
            target_type (str, optional): The type of target ('ip', 'domain', 'hash').
                Defaults to "auto".

        Returns:
            Optional[Dict[str, Any]]: A dictionary with threat intelligence data,
                or None if the check fails.
        """
        cache_key = f"{target}:{target_type}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for threat: {target}")
            return self.cache[cache_key]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/threat-intel/check",
                json={"target": target, "target_type": target_type}
            )
            response.raise_for_status()
            data = response.json()

            enriched_data = self._format_response(data)
            self.cache[cache_key] = enriched_data

            logger.info(
                f"Threat intel for {target}: Score={enriched_data['threat_score']}, "
                f"Malicious={enriched_data['is_malicious']}"
            )
            return enriched_data

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Threat Intel Service returned status {e.response.status_code} for {target}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Threat Intel Service: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while checking threat {target}: {e}")
            return None

    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formats the raw service response into a structured dictionary."""
        return {
            'target': data.get('target'),
            'target_type': data.get('target_type'),
            'threat_score': data.get('threat_score', 0),
            'is_malicious': data.get('is_malicious', False),
            'confidence': data.get('confidence', 'low'),
            'reputation': data.get('reputation', 'unknown'),
            'categories': data.get('categories', []),
            'mitre_tactics': self._extract_mitre_tactics(data),
            'sources': data.get('sources', {}),
            'recommendations': data.get('recommendations', []),
            'first_seen': data.get('first_seen'),
            'last_seen': data.get('last_seen'),
            'enriched_at': datetime.utcnow().isoformat(),
            'enriched_by': 'threat_intel_service'
        }

    async def enrich_threat_with_intel(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches a threat detection object with threat intelligence.

        Extracts all relevant indicators from a threat object, queries the
        Threat Intel Service for each, and aggregates the results into the
        threat's `enriched_context`. It also adjusts the threat score.

        Args:
            threat (Dict[str, Any]): The threat detection object to enrich.

        Returns:
            Dict[str, Any]: The enriched threat detection object.
        """
        targets_to_check = self._extract_targets_from_threat(threat)
        intel_results = {}

        for item in targets_to_check:
            intel = await self.check_threat(item['target'], item['type'])
            if intel:
                intel_results[item['target']] = intel

        if 'enriched_context' not in threat:
            threat['enriched_context'] = {}
        threat['enriched_context']['threat_intelligence'] = intel_results

        if intel_results:
            self._adjust_threat_score(threat, intel_results)

        return threat

    def _extract_targets_from_threat(self, threat: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extracts unique indicators (targets) from a threat object."""
        targets = []
        seen_targets = set()

        # Helper to add a target if it hasn't been seen before
        def add_target(target, target_type):
            if target not in seen_targets:
                targets.append({'target': target, 'type': target_type})
                seen_targets.add(target)

        # Extract from source
        source = threat.get('source', '')
        if source:
            add_target(source, self._detect_target_type(source))

        # Extract from indicators
        for indicator in threat.get('indicators', []):
            extracted = self._extract_target_from_indicator(str(indicator))
            if extracted:
                add_target(extracted['target'], extracted['type'])

        # Extract from raw data (e.g., file hash)
        raw_data = threat.get('raw_data', {})
        if raw_data.get('file_hash'):
            add_target(raw_data['file_hash'], 'hash')

        return targets

    def _adjust_threat_score(self, threat: Dict[str, Any], intel_results: Dict[str, Any]):
        """Adjusts threat score based on the highest score from intelligence results."""
        threat_scores = [
            intel_data['threat_score']
            for intel_data in intel_results.values()
        ]
        if not threat_scores:
            return

        worst_intel_score = max(threat_scores)
        original_score = threat.get('threat_score', 0)
        # Weighted average: 60% threat intel, 40% original detection
        adjusted_score = int(worst_intel_score * 0.6 + original_score * 0.4)

        threat['threat_score_original'] = original_score
        threat['threat_score'] = adjusted_score
        threat['threat_score_adjusted_by'] = 'threat_intelligence'
        threat['severity'] = self._calculate_severity(adjusted_score)

        logger.info(
            f"Threat score adjusted: {original_score} -> {adjusted_score} based on threat intelligence."
        )

        # Aggregate recommendations
        all_recommendations = set(threat.get('recommendations', []))
        for intel_data in intel_results.values():
            for rec in intel_data.get('recommendations', []):
                all_recommendations.add(rec)
        threat['recommendations'] = list(all_recommendations)

    def _detect_target_type(self, target: str) -> str:
        """Automatically detects the type of an indicator (IP, domain, hash, etc.)."""
        import re
        if re.match(r'^(?:\d{1,3}\.){3}\d{1,3}$', target):
            return 'ip'
        if len(target) in [32, 40, 64] and re.match(r'^[a-fA-F0-9]+$', target):
            return 'hash'
        if '://' in target:
            return 'url'
        if '.' in target:
            return 'domain'
        return 'auto'

    def _extract_target_from_indicator(self, indicator: str) -> Optional[Dict[str, str]]:
        """Extracts the most likely indicator from a generic string."""
        import re
        # Regex patterns ordered by specificity
        patterns = {
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'hash': r'\b[a-fA-F0-9]{32,64}\b',
            'domain': r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        }
        for target_type, pattern in patterns.items():
            match = re.search(pattern, indicator)
            if match:
                return {'target': match.group(0), 'type': target_type}
        return None

    def _extract_mitre_tactics(self, data: Dict[str, Any]) -> List[str]:
        """Extracts MITRE ATT&CK tactic IDs from threat categories."""
        category_to_mitre = {
            'malware': ['TA0002'],       # Execution
            'botnet': ['TA0011'],        # Command and Control
            'phishing': ['TA0001'],      # Initial Access
            'ransomware': ['TA0040'],    # Impact
            'trojan': ['TA0002', 'TA0011'],
            'backdoor': ['TA0003', 'TA0011'] # Persistence, C2
        }
        tactics = set()
        for cat in data.get('categories', []):
            for key, mitre_ids in category_to_mitre.items():
                if key in cat.lower():
                    tactics.update(mitre_ids)
        return list(tactics)

    def _calculate_severity(self, threat_score: int) -> str:
        """Calculates a severity string from a numerical threat score."""
        if threat_score >= 80:
            return 'critical'
        elif threat_score >= 60:
            return 'high'
        elif threat_score >= 40:
            return 'medium'
        else:
            return 'low'

    async def close(self):
        """Closes the asynchronous HTTP client session."""
        await self.client.aclose()
        logger.info("ThreatIntelConnector client closed.")

    async def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches threat data. Implementation of the abstract method."""
        return await self.enrich_threat_with_intel(data)