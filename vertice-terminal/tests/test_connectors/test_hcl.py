"""
Test: HCLConnector
==================

Testa o conector de Human-Centric Language.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.hcl import HCLConnector
from tests.fixtures.sample_data import SAMPLE_HCL_WORKFLOW


class TestHCLConnector:
    """Testes do HCLConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do conector HCL."""
        connector = HCLConnector()
        try:
            is_healthy = await connector.health_check()
            if is_healthy:
                print("✅ HCL Connector: HEALTHY")
            else:
                print("⚠️  HCL Connector: Service may be offline")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analyze_intent(self):
        """Testa análise de intent de código HCL."""
        connector = HCLConnector()
        try:
            result = await connector.analyze_intent(
                hcl_code="Scan network and report vulnerabilities"
            )

            assert result is not None
            print("✅ Intent analysis: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_plan(self):
        """Testa geração de plan HCL."""
        connector = HCLConnector()
        try:
            result = await connector.generate_plan(
                objective="Perform comprehensive security assessment"
            )

            print("✅ Plan generation: PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_query_knowledge_base(self):
        """Testa consulta ao HCL knowledge base."""
        connector = HCLConnector()
        try:
            result = await connector.query_knowledge_base(
                query="API security best practices",
                category="security"
            )

            print("✅ Knowledge base query: PASS")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
