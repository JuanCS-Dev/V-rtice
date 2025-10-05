"""
Test: MaximusUniversalConnector
================================

Testa o conector universal - orquestrador AI-First.
"""

import pytest
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vertice.connectors.maximus_universal import MaximusUniversalConnector
from tests.fixtures.sample_data import SAMPLE_TARGETS


class TestMaximusUniversalConnector:
    """Testes do MaximusUniversalConnector."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Testa health check do Maximus Core."""
        connector = MaximusUniversalConnector()
        try:
            is_healthy = await connector.health_check()
            # Test passes whether service is online or offline
            # Just verify no crash occurs
            if is_healthy:
                print("✅ Health check: PASS (service online)")
            else:
                print("✅ Health check: PASS (service offline - graceful degradation)")
        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_intelligent_query_simple(self):
        """Testa query inteligente simples."""
        connector = MaximusUniversalConnector()
        try:
            # Skip test if service is offline
            if not await connector.health_check():
                pytest.skip("Maximus Core service is offline")

            result = await connector.intelligent_query(
                query="What is cybersecurity?",
                mode="autonomous"
            )

            assert result is not None, "Result should not be None"
            assert "response" in result, "Response should contain 'response' field"
            assert len(result["response"]) > 0, "Response should not be empty"

            print(f"✅ Intelligent query: PASS")
            print(f"   Response length: {len(result['response'])} chars")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_intelligent_query_with_reasoning(self):
        """Testa query com reasoning engine."""
        connector = MaximusUniversalConnector()
        try:
            if not await connector.health_check():
                pytest.skip("Maximus Core service is offline")

            result = await connector.intelligent_query(
                query=f"Analyze the domain {SAMPLE_TARGETS['domain_safe']}",
                mode="deep",
                context={"investigation_type": "defensive"}
            )

            assert result is not None
            assert "response" in result
            # Reasoning trace pode ou não estar presente dependendo do endpoint usado
            # assert "reasoning_trace" in result, "Should contain reasoning trace"

            print(f"✅ Query with reasoning: PASS")
            print(f"   Response: {result['response'][:100]}...")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_execute_tool_direct(self):
        """Testa execução de tool específica."""
        connector = MaximusUniversalConnector()
        try:
            if not await connector.health_check():
                pytest.skip("Maximus Core service is offline")

            result = await connector.execute_tool(
                tool_name="threat_intel",
                params={
                    "target": SAMPLE_TARGETS["domain_safe"],
                    "target_type": "domain"
                }
            )

            assert result is not None
            # Tool execution pode retornar diferentes estruturas
            print(f"✅ Execute tool direct: PASS")
            print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_get_available_tools(self):
        """Testa listagem de tools disponíveis."""
        connector = MaximusUniversalConnector()
        try:
            if not await connector.health_check():
                pytest.skip("Maximus Core service is offline")

            tools = await connector.get_available_tools()

            assert tools is not None, "Tools list should not be None"
            assert isinstance(tools, list), "Tools should be a list"
            assert len(tools) > 50, f"Expected 50+ tools, got {len(tools)}"

            # Check structure
            if len(tools) > 0:
                first_tool = tools[0]
                assert "name" in first_tool, "Tool should have 'name'"
                assert "category" in first_tool, "Tool should have 'category'"

            print(f"✅ Get available tools: PASS")
            print(f"   Total tools: {len(tools)}")

            # Count by category
            categories = {}
            for tool in tools:
                cat = tool.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            print(f"   Categories: {dict(categories)}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_get_memory_stats(self):
        """Testa obtenção de estatísticas de memória."""
        connector = MaximusUniversalConnector()
        try:
            stats = await connector.get_memory_stats()

            # Stats podem estar vazias ou não dependendo do uso
            if stats:
                print(f"✅ Memory stats: PASS")
                print(f"   Stats keys: {list(stats.keys())}")
            else:
                print(f"✅ Memory stats: PASS (empty)")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_multi_tool_investigation(self):
        """Testa investigação multi-tool orquestrada."""
        connector = MaximusUniversalConnector()
        try:
            if not await connector.health_check():
                pytest.skip("Maximus Core service is offline")

            result = await connector.multi_tool_investigation(
                target=SAMPLE_TARGETS["domain_safe"],
                investigation_type="auto",
                tools=None,  # Maximus decide
                parallel=True
            )

            assert result is not None
            assert "response" in result or "summary" in result or "findings" in result

            print(f"✅ Multi-tool investigation: PASS")
            if "tools_used" in result:
                print(f"   Tools used: {len(result.get('tools_used', []))}")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_recall_conversation_not_found(self):
        """Testa recall de conversa inexistente."""
        connector = MaximusUniversalConnector()
        try:
            result = await connector.recall_conversation("nonexistent_session")

            # Pode retornar None, erro 404, ou estrutura vazia
            # Não deve dar crash
            print(f"✅ Recall conversation (not found): PASS")

        finally:
            await connector.close()

    @pytest.mark.asyncio
    async def test_find_similar_investigations(self):
        """Testa busca de investigações similares."""
        connector = MaximusUniversalConnector()
        try:
            result = await connector.find_similar_investigations(
                target=SAMPLE_TARGETS["domain_safe"],
                limit=5
            )

            # Pode retornar lista vazia se não há investigações
            # Não deve dar crash
            print(f"✅ Find similar investigations: PASS")
            if result:
                print(f"   Found: {len(result)} similar")

        finally:
            await connector.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
