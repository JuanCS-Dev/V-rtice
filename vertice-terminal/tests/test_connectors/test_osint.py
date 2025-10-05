"""
Test: OSINTConnector
====================

Testa o conector de OSINT operations.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.osint import OSINTConnector
from tests.fixtures.sample_data import SAMPLE_TARGETS


class TestOSINTConnector:
    """Testes do OSINTConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector OSINT."""
        connector = OSINTConnector()
        try:
            is_healthy = await connector.health_check()
            # OSINT connector depende do Maximus Core
            if is_healthy:
                print("✅ OSINT Connector: HEALTHY")
            else:
                print("⚠️  OSINT Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_multi_source_search(self):
        """Testa multi-source search."""
        connector = OSINTConnector()
        try:
            if not await connector.health_check():
                pytest.skip("OSINT service is offline")

            result = await connector.multi_source_search(
                query="John Doe New York",
                search_type="people"
            )

            assert result is not None
            print("✅ Multi-source search: PASS")

            if isinstance(result, dict):
                print(f"   Result keys: {list(result.keys())}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_breach_data_lookup(self):
        """Testa breach data lookup."""
        connector = OSINTConnector()
        try:
            if not await connector.health_check():
                pytest.skip("OSINT service is offline")

            result = await connector.breach_data_lookup(
                identifier=SAMPLE_TARGETS["email_test"],
                type="email"
            )

            assert result is not None
            print("✅ Breach data lookup: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_sinesp_vehicle_query(self):
        """Testa SINESP vehicle query (Brazil)."""
        connector = OSINTConnector()
        try:
            # Usa placa de teste
            result = await connector.sinesp_vehicle_query("ABC1234")

            # Pode retornar dados ou erro (placa inválida)
            # Não deve crashar
            print("✅ SINESP vehicle query: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_comprehensive_osint(self):
        """Testa OSINT abrangente (Maximus orchestrated)."""
        connector = OSINTConnector()
        try:
            result = await connector.comprehensive_osint(
                target=SAMPLE_TARGETS["domain_safe"],
                target_type="domain"
            )

            assert result is not None
            print("✅ Comprehensive OSINT: PASS")

            if isinstance(result, dict) and "response" in result:
                print(f"   Response preview: {result['response'][:100]}...")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
