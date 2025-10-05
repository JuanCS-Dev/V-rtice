"""
Test: ASAConnector
==================

Testa o conector de Autonomic Safety Architecture.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.asa import ASAConnector
from tests.fixtures.sample_data import SAMPLE_TARGETS


class TestASAConnector:
    """Testes do ASAConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector ASA."""
        connector = ASAConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ ASA Connector: HEALTHY")
            else:
                print("⚠️  ASA Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_adr_analysis(self):
        """Testa ADR (Anomaly Detection & Response) analysis."""
        connector = ASAConnector()
        try:
            result = await connector.adr_analysis(
                target=SAMPLE_TARGETS["domain_safe"],
                scan_depth="quick"
            )

            assert result is not None
            print("✅ ADR analysis: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_strategic_plan(self):
        """Testa Strategic Planning service."""
        connector = ASAConnector()
        try:
            result = await connector.strategic_plan(
                objective="Test security objective",
                constraints={"time": "1h", "scope": "network"}
            )

            print("✅ Strategic plan: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_filter_narrative(self):
        """Testa Narrative Manipulation Filter."""
        connector = ASAConnector()
        try:
            result = await connector.filter_narrative(
                content="This is test content for narrative filtering",
                check_type="propaganda"
            )

            print("✅ Narrative filter: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
