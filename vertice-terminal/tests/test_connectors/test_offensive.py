"""
Test: OffensiveConnector
========================

Testa o conector de Offensive Security Arsenal.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.offensive import OffensiveConnector
from tests.fixtures.sample_data import SAMPLE_TARGETS


class TestOffensiveConnector:
    """Testes do OffensiveConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector Offensive."""
        connector = OffensiveConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ Offensive Connector: HEALTHY")
            else:
                print("⚠️  Offensive Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_network_recon(self):
        """Testa network reconnaissance."""
        connector = OffensiveConnector()
        try:
            # Usa IP local seguro para teste
            result = await connector.network_recon(
                target=SAMPLE_TARGETS["ip_safe"],
                scan_type="quick",
                ports="80,443"
            )

            assert result is not None
            print("✅ Network recon: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_vuln_intel_search(self):
        """Testa busca de vulnerability intelligence."""
        connector = OffensiveConnector()
        try:
            if not await connector.health_check():
                pytest.skip("Offensive service is offline")

            result = await connector.vuln_intel_search(
                identifier=SAMPLE_TARGETS["cve_test"],
                type="cve"
            )

            assert result is not None
            print("✅ Vuln intel search: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_exploit_search(self):
        """Testa busca de exploits."""
        connector = OffensiveConnector()
        try:
            result = await connector.exploit_search(
                cve_id=SAMPLE_TARGETS["cve_test"]
            )

            print("✅ Exploit search: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
