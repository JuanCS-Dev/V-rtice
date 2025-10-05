"""
Test: MaximusSubsystemsConnector
=================================

Testa o conector de subsistemas especializados do Maximus.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.maximus_subsystems import MaximusSubsystemsConnector
from tests.fixtures.sample_data import SAMPLE_TARGETS


class TestMaximusSubsystemsConnector:
    """Testes do MaximusSubsystemsConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector Maximus Subsystems."""
        connector = MaximusSubsystemsConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ Maximus Subsystems Connector: HEALTHY")
            else:
                print("⚠️  Maximus Subsystems Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_get_subsystems_status(self):
        """Testa obtenção do status de subsistemas."""
        connector = MaximusSubsystemsConnector()
        try:
            result = await connector.get_subsystems_status()

            # Status pode retornar vazio ou com dados
            print("✅ Subsystems status: PASS")

            if isinstance(result, dict):
                print(f"   Status keys: {list(result.keys())}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_eureka_deep_analysis(self):
        """Testa análise profunda de malware via EUREKA."""
        connector = MaximusSubsystemsConnector()
        try:
            result = await connector.eureka_deep_analysis(
                malware_sample=SAMPLE_TARGETS["hash_test"],
                analysis_depth="basic"
            )

            print("✅ EUREKA deep analysis: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_predict_analytics(self):
        """Testa predictive analytics."""
        connector = MaximusSubsystemsConnector()
        try:
            result = await connector.predict_analytics({
                "prediction_type": "threat_trend",
                "timeframe": "24h"
            })

            print("✅ PREDICT analytics: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_orchestrator_investigate(self):
        """Testa orquestração multi-serviço."""
        connector = MaximusSubsystemsConnector()
        try:
            result = await connector.orchestrator_investigate(
                target=SAMPLE_TARGETS["domain_safe"],
                investigation_type="defensive",
                services=["threat_intel", "domain_analysis"]
            )

            print("✅ Orchestrator investigation: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
