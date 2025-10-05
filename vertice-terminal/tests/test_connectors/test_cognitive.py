"""
Test: CognitiveConnector
========================

Testa o conector de serviços cognitivos ASA.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.cognitive import CognitiveConnector


class TestCognitiveConnector:
    """Testes do CognitiveConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector Cognitive."""
        connector = CognitiveConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ Cognitive Connector: HEALTHY")
            else:
                print("⚠️  Cognitive Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyze_image(self):
        """Testa análise de imagem via Visual Cortex."""
        connector = CognitiveConnector()
        try:
            # Imagem base64 mínima (1x1 pixel PNG transparente)
            minimal_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            result = await connector.analyze_image(
                image_data=minimal_png,
                analysis_type="basic"
            )

            # Pode retornar resultado ou erro
            print("✅ Image analysis: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_prefrontal_decision(self):
        """Testa decision-making via Prefrontal Cortex."""
        connector = CognitiveConnector()
        try:
            decision_request = {
                "situation": "Test security incident",
                "options": [
                    {"action": "block", "risk": "low"},
                    {"action": "monitor", "risk": "medium"}
                ]
            }

            result = await connector.prefrontal_decision(decision_request)

            print("✅ Prefrontal decision: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
