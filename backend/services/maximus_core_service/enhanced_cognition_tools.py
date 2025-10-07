"""Enhanced Cognition Tools - FASE 8 Integration

Tools for advanced narrative analysis, predictive threat hunting,
and autonomous investigation capabilities.

NO MOCKS - Production-ready cognitive enhancement.
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class EnhancedCognitionTools:
    """Enhanced Cognition Tools for MAXIMUS AI.

    Integrates FASE 8 services:
    - Narrative Analysis Service (port 8015)
    - Predictive Threat Hunting Service (port 8016)
    - Autonomous Investigation Service (port 8017)
    """

    def __init__(self, gemini_client: Any):
        """Initialize Enhanced Cognition Tools.

        Args:
            gemini_client: Gemini client instance
        """
        self.gemini_client = gemini_client
        self.narrative_url = "http://localhost:8015"
        self.predictive_url = "http://localhost:8016"
        self.investigation_url = "http://localhost:8017"

    async def analyze_narrative(
        self,
        text: str,
        analysis_type: str = "comprehensive",
        detect_bots: bool = True,
        track_memes: bool = True,
    ) -> Dict[str, Any]:
        """Analyze narrative for social engineering, propaganda, bots.

        Args:
            text: Text or social media content to analyze
            analysis_type: Type of analysis (comprehensive, bots_only, propaganda_only, meme_tracking)
            detect_bots: Enable bot network detection
            track_memes: Enable meme tracking

        Returns:
            Analysis results with social graph, bot detection, propaganda attribution
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.narrative_url}/analyze/narrative",
                    json={
                        "text": text,
                        "analysis_type": analysis_type,
                        "detect_bots": detect_bots,
                        "track_memes": track_memes,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Narrative analysis failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in analyze_narrative: {e}")
            return {"error": str(e)}

    async def predict_threats(
        self,
        context: Dict[str, Any],
        time_horizon_hours: int = 24,
        min_confidence: float = 0.6,
        include_vuln_forecast: bool = True,
    ) -> Dict[str, Any]:
        """Predict future threats using time-series analysis and Bayesian inference.

        Args:
            context: Context including historical events, current alerts
            time_horizon_hours: Prediction time horizon (default 24h)
            min_confidence: Minimum prediction confidence (0-1)
            include_vuln_forecast: Include vulnerability exploitation forecasting

        Returns:
            Predicted attacks, vulnerabilities, hunting recommendations
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.predictive_url}/predict/attacks",
                    json={
                        "context": context,
                        "time_horizon_hours": time_horizon_hours,
                        "min_confidence": min_confidence,
                        "include_vulnerability_forecast": include_vuln_forecast,
                    },
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Threat prediction failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in predict_threats: {e}")
            return {"error": str(e)}

    async def hunt_proactively(
        self,
        asset_inventory: Optional[List[str]] = None,
        threat_intel: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate proactive hunting recommendations.

        Args:
            asset_inventory: List of assets to focus hunting on
            threat_intel: Current threat intelligence context

        Returns:
            Hunting recommendations (asset scans, log reviews, network monitoring)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.predictive_url}/hunt/recommendations",
                    json={
                        "asset_inventory": asset_inventory or [],
                        "threat_intel": threat_intel or {},
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Proactive hunting failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in hunt_proactively: {e}")
            return {"error": str(e)}

    async def investigate_incident(
        self,
        incident_id: str,
        playbook: str = "standard",
        enable_actor_profiling: bool = True,
        enable_campaign_correlation: bool = True,
    ) -> Dict[str, Any]:
        """Launch autonomous investigation for incident.

        Args:
            incident_id: Incident identifier
            playbook: Investigation playbook (standard, apt, ransomware, insider)
            enable_actor_profiling: Enable threat actor profiling
            enable_campaign_correlation: Enable campaign correlation

        Returns:
            Investigation results with evidence, attribution, recommendations
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.investigation_url}/investigate/start",
                    json={
                        "incident_id": incident_id,
                        "playbook": playbook,
                        "enable_actor_profiling": enable_actor_profiling,
                        "enable_campaign_correlation": enable_campaign_correlation,
                    },
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Investigation failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in investigate_incident: {e}")
            return {"error": str(e)}

    async def correlate_campaigns(
        self,
        incidents: List[str],
        time_window_days: int = 30,
        correlation_threshold: float = 0.6,
    ) -> Dict[str, Any]:
        """Correlate incidents into attack campaigns.

        Args:
            incidents: List of incident IDs to correlate
            time_window_days: Temporal correlation window
            correlation_threshold: Minimum similarity for correlation (0-1)

        Returns:
            Identified campaigns with correlated incidents
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.investigation_url}/correlate/campaigns",
                    json={
                        "incidents": incidents,
                        "time_window_days": time_window_days,
                        "correlation_threshold": correlation_threshold,
                    },
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Campaign correlation failed: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            logger.error(f"Error in correlate_campaigns: {e}")
            return {"error": str(e)}

    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available Enhanced Cognition tools.

        Returns:
            List of tool metadata
        """
        return [
            {
                "name": "analyze_narrative",
                "method_name": "analyze_narrative",
                "description": "Analyze narrative for social engineering, propaganda, bot networks, and meme tracking",
                "parameters": {
                    "text": "Text or social media content to analyze",
                    "analysis_type": "Type of analysis (comprehensive, bots_only, propaganda_only, meme_tracking)",
                    "detect_bots": "Enable bot network detection (bool)",
                    "track_memes": "Enable meme tracking (bool)",
                },
            },
            {
                "name": "predict_threats",
                "method_name": "predict_threats",
                "description": "Predict future threats using time-series analysis and Bayesian inference",
                "parameters": {
                    "context": "Context with historical events and current alerts",
                    "time_horizon_hours": "Prediction time horizon (default 24h)",
                    "min_confidence": "Minimum prediction confidence 0-1",
                    "include_vuln_forecast": "Include vulnerability exploitation forecasting (bool)",
                },
            },
            {
                "name": "hunt_proactively",
                "method_name": "hunt_proactively",
                "description": "Generate proactive threat hunting recommendations based on asset inventory and threat intel",
                "parameters": {
                    "asset_inventory": "List of assets to focus hunting on",
                    "threat_intel": "Current threat intelligence context",
                },
            },
            {
                "name": "investigate_incident",
                "method_name": "investigate_incident",
                "description": "Launch autonomous investigation for incident with actor profiling and campaign correlation",
                "parameters": {
                    "incident_id": "Incident identifier",
                    "playbook": "Investigation playbook (standard, apt, ransomware, insider)",
                    "enable_actor_profiling": "Enable threat actor profiling (bool)",
                    "enable_campaign_correlation": "Enable campaign correlation (bool)",
                },
            },
            {
                "name": "correlate_campaigns",
                "method_name": "correlate_campaigns",
                "description": "Correlate multiple incidents into attack campaigns using similarity analysis",
                "parameters": {
                    "incidents": "List of incident IDs to correlate",
                    "time_window_days": "Temporal correlation window",
                    "correlation_threshold": "Minimum similarity for correlation 0-1",
                },
            },
        ]
