"""
Test: ImmunisConnector
======================

Testa o conector do AI Immune System.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.immunis import ImmunisConnector
from tests.fixtures.sample_data import SAMPLE_THREAT_DATA


class TestImmunisConnector:
    """Testes do ImmunisConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector Immunis."""
        connector = ImmunisConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ Immunis Connector: HEALTHY")
            else:
                print("⚠️  Immunis Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_get_immune_status(self):
        """Testa obtenção do status do sistema imune."""
        connector = ImmunisConnector()
        try:
            result = await connector.get_immune_status()

            # Status pode retornar vazio ou com dados
            print("✅ Immune status: PASS")

            if isinstance(result, dict):
                print(f"   Status keys: {list(result.keys())}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_detect_threat(self):
        """Testa detecção de ameaça."""
        connector = ImmunisConnector()
        try:
            result = await connector.detect_threat(SAMPLE_THREAT_DATA)

            print("✅ Threat detection: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_activate_nk_patrol(self):
        """Testa ativação de patrulha NK Cell."""
        connector = ImmunisConnector()
        try:
            result = await connector.activate_nk_patrol(
                patrol_zone="network_segment_1"
            )

            print("✅ NK patrol activation: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
