"""MVP Narrative Engine - LLM-powered narrative generation for system observability.

This module provides the NarrativeEngine class that transforms raw system metrics
into human-readable narratives using Anthropic Claude. It analyzes metrics,
detects patterns, identifies anomalies, and generates contextual stories about
system behavior.

Key Features:
- Real-time narrative generation from Prometheus/InfluxDB metrics
- Anomaly detection and alerting
- Executive briefings and status reports
- Context-aware storytelling with historical analysis
- Integration with MAXIMUS consciousness

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from datetime import datetime
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import Message

logger = logging.getLogger(__name__)


class NarrativeEngine:
    """
    LLM-powered narrative generation engine.

    Transforms system metrics into coherent narratives using Claude's advanced
    language capabilities. Provides context-aware analysis and storytelling.

    Attributes:
        anthropic_api_key: Anthropic API key for Claude access
        model: Claude model to use (default: claude-sonnet-4.5-20250929)
        client: AsyncAnthropic client instance
        _initialized: Engine initialization state
    """

    def __init__(
        self, anthropic_api_key: str, model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize narrative engine.

        Args:
            anthropic_api_key: Anthropic API key
            model: Claude model identifier
        """
        if not anthropic_api_key or anthropic_api_key == "PLACEHOLDER":
            raise ValueError(
                "Valid ANTHROPIC_API_KEY required for narrative generation"
            )

        self.anthropic_api_key = anthropic_api_key
        self.model = model
        self.client: AsyncAnthropic | None = None
        self._initialized = False

        logger.info(f"🎭 NarrativeEngine configured with model: {model}")

    async def initialize(self) -> bool:
        """
        Initialize the narrative engine.

        Creates AsyncAnthropic client and validates API connectivity.

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            self.client = AsyncAnthropic(api_key=self.anthropic_api_key)

            # Validate API key with a minimal test call
            await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )

            self._initialized = True
            logger.info("✅ NarrativeEngine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize NarrativeEngine: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the narrative engine gracefully."""
        if self.client:
            await self.client.close()
            self.client = None
        self._initialized = False
        logger.info("👋 NarrativeEngine shut down")

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check on narrative engine.

        Returns:
            Dict with health status and details
        """
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
            "model": self.model,
            "client_connected": self.client is not None,
        }

    async def generate_narrative(
        self,
        narrative_type: str,
        metrics_data: dict[str, Any],
        time_range_minutes: int = 60,
        focus_areas: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate narrative from system metrics.

        Args:
            narrative_type: Type of narrative (realtime, summary, alert, briefing)
            metrics_data: Raw metrics data from SystemObserver
            time_range_minutes: Time range for analysis
            focus_areas: Specific areas to focus on (optional)

        Returns:
            Dict containing generated narrative and analysis metadata
        """
        if not self._initialized or not self.client:
            raise RuntimeError("NarrativeEngine not initialized")

        logger.info(
            f"📝 Generating {narrative_type} narrative "
            f"(time_range={time_range_minutes}m, focus={focus_areas})"
        )

        try:
            # Build context for Claude
            prompt = self._build_narrative_prompt(
                narrative_type, metrics_data, time_range_minutes, focus_areas
            )

            # Generate narrative with Claude
            message: Message = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )

            narrative_text = (
                message.content[0].text if message.content else "No narrative generated"
            )

            # Analyze metrics for anomalies
            anomalies = self._detect_anomalies_in_metrics(metrics_data)

            result = {
                "narrative": narrative_text,
                "metrics_analyzed": len(metrics_data.get("metrics", [])),
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "time_range_minutes": time_range_minutes,
                "focus_areas": focus_areas or [],
                "narrative_type": narrative_type,
                "timestamp": datetime.utcnow().isoformat(),
                "model": self.model,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            }

            logger.info(
                f"✅ Narrative generated successfully "
                f"({result['tokens_used']} tokens, {result['anomalies_detected']} anomalies)"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Failed to generate narrative: {e}", exc_info=True)
            raise

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for Claude narrative generation.

        Returns:
            System prompt string
        """
        return """You are the MAXIMUS Vision Protocol (MVP), an expert system observability analyst.

Your role is to transform raw system metrics into clear, insightful narratives that help
engineers and operators understand system behavior, identify issues, and make decisions.

Guidelines:
- Be concise but thorough - focus on actionable insights
- Identify patterns, trends, and anomalies in the data
- Use clear, professional language without unnecessary jargon
- Highlight critical issues with appropriate urgency
- Provide context by comparing current vs historical behavior
- Structure narratives logically: Overview → Key Findings → Recommendations
- Use specific numbers and percentages when relevant
- Avoid speculation - only report what the data shows

Narrative Types:
- realtime: Current system state snapshot (1-2 paragraphs)
- summary: Comprehensive analysis over time period (3-4 paragraphs)
- alert: Urgent issue requiring attention (focus on problem + action)
- briefing: Executive summary for stakeholders (high-level overview)

Always maintain objectivity and base conclusions on the provided metrics."""

    def _build_narrative_prompt(
        self,
        narrative_type: str,
        metrics_data: dict[str, Any],
        time_range_minutes: int,
        focus_areas: list[str] | None,
    ) -> str:
        """
        Build the prompt for narrative generation.

        Args:
            narrative_type: Type of narrative to generate
            metrics_data: Raw metrics data
            time_range_minutes: Time range for analysis
            focus_areas: Optional focus areas

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"Generate a {narrative_type} narrative for the Vértice platform.",
            f"\nTime Range: Last {time_range_minutes} minutes",
            f"Current Time: {datetime.utcnow().isoformat()}\n",
        ]

        if focus_areas:
            prompt_parts.append(f"Focus Areas: {', '.join(focus_areas)}\n")

        # Add metrics summary
        prompt_parts.append("\n## System Metrics\n")

        metrics_list = metrics_data.get("metrics", [])
        if metrics_list:
            for metric in metrics_list[:20]:  # Limit to top 20 metrics
                name = metric.get("name", "unknown")
                value = metric.get("value", 0)
                unit = metric.get("unit", "")
                prompt_parts.append(f"- {name}: {value} {unit}")
        else:
            prompt_parts.append("- No metrics available")

        # Add anomaly indicators
        anomalies = metrics_data.get("anomalies", [])
        if anomalies:
            prompt_parts.append("\n## Detected Anomalies\n")
            for anomaly in anomalies[:10]:  # Top 10 anomalies
                prompt_parts.append(
                    f"- {anomaly.get('description', 'Unknown anomaly')}"
                )

        # Add service status
        services = metrics_data.get("services", [])
        if services:
            prompt_parts.append("\n## Service Status\n")
            for service in services:
                name = service.get("name", "unknown")
                status = service.get("status", "unknown")
                prompt_parts.append(f"- {name}: {status}")

        prompt_parts.append(
            "\n## Task\n"
            f"Analyze the metrics above and generate a {narrative_type} narrative "
            "that provides clear insights into system health, performance, and any issues."
        )

        return "\n".join(prompt_parts)

    def _detect_anomalies_in_metrics(
        self, metrics_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in metrics data using simple heuristics.

        This is a basic anomaly detector. In production, this could use
        statistical methods, ML models, or integration with dedicated
        anomaly detection systems.

        Args:
            metrics_data: Metrics data to analyze

        Returns:
            List of detected anomalies
        """
        anomalies = []

        metrics_list = metrics_data.get("metrics", [])
        for metric in metrics_list:
            name = metric.get("name", "")
            value = metric.get("value", 0)

            # CPU usage anomalies
            if "cpu" in name.lower() and "usage" in name.lower():
                if value > 90:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "critical",
                            "description": f"Critical CPU usage: {value}%",
                        }
                    )
                elif value > 75:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "warning",
                            "description": f"High CPU usage: {value}%",
                        }
                    )

            # Memory usage anomalies
            if "memory" in name.lower() and "usage" in name.lower():
                if value > 90:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "critical",
                            "description": f"Critical memory usage: {value}%",
                        }
                    )
                elif value > 80:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "warning",
                            "description": f"High memory usage: {value}%",
                        }
                    )

            # Error rate anomalies
            if "error" in name.lower() and "rate" in name.lower():
                if value > 5:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "critical",
                            "description": f"High error rate: {value}%",
                        }
                    )
                elif value > 1:
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "warning",
                            "description": f"Elevated error rate: {value}%",
                        }
                    )

            # Latency anomalies
            if "latency" in name.lower() or "response_time" in name.lower():
                if value > 5000:  # 5 seconds
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "critical",
                            "description": f"Critical latency: {value}ms",
                        }
                    )
                elif value > 2000:  # 2 seconds
                    anomalies.append(
                        {
                            "metric": name,
                            "value": value,
                            "severity": "warning",
                            "description": f"High latency: {value}ms",
                        }
                    )

        return anomalies
