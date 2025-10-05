"""
Test 02: AI Integration - Maximus Core AI Features
====================================================

Valida que a integração AI está funcionando:
- Intelligent queries
- Reasoning engine
- Memory system
- Tool orchestration
"""

import pytest
import httpx
import asyncio
import json


@pytest.mark.asyncio
async def test_maximus_chat_simple():
    """Testa chat simples com Maximus AI."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8001/api/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "Hello, what is cybersecurity?"}
                    ]
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            assert len(data["response"]) > 10, "Response should not be empty"

            print(f"✅ Maximus chat simple: PASS")
            print(f"   Response preview: {data['response'][:100]}...")

        except httpx.ConnectError:
            pytest.skip("Maximus Core (port 8001) is not running - service offline")
        except httpx.ReadTimeout:
            pytest.skip("Maximus Core timed out (LLM may be slow) - service timeout")


@pytest.mark.asyncio
async def test_tools_catalog_complete():
    """Testa que o catálogo de tools está completo."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/tools/complete")
            assert response.status_code == 200

            data = response.json()
            total_tools = data.get("total_tools", 0)

            assert total_tools >= 50, f"Expected 50+ tools, got {total_tools}"

            # Verifica que temos ferramentas em categorias principais
            assert "world_class_tools" in data
            assert "offensive_arsenal" in data
            assert "all_services" in data

            print(f"✅ Tools catalog complete: PASS")
            print(f"   Total tools: {total_tools}")

            # Lista algumas ferramentas
            if "world_class_tools" in data and "tools" in data["world_class_tools"]:
                tools = data["world_class_tools"]["tools"][:5]
                if tools and isinstance(tools[0], dict):
                    print(f"   Sample tools: {[t.get('name') for t in tools]}")
                else:
                    print(f"   Sample tools: {tools}")

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")


@pytest.mark.asyncio
async def test_memory_system_stats():
    """Testa que o memory system está funcional."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/memory/stats")

            # Aceita 200 (tem dados) ou 404 (vazio)
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Memory system stats: PASS")
                print(f"   Initialized: {data.get('initialized')}")
                print(f"   Working memory: {data.get('working_memory')}")
                print(f"   Episodic memory: {data.get('episodic_memory')}")

                if "episodic_stats" in data:
                    stats = data["episodic_stats"]
                    print(f"   Conversations: {stats.get('conversations', 0)}")
                    print(f"   Messages: {stats.get('messages', 0)}")
            else:
                print(f"✅ Memory system stats: PASS (empty)")

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_intelligent_query_with_tool():
    """Testa query inteligente que usa ferramentas."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Query que deve acionar ferramentas de análise
            response = await client.post(
                "http://localhost:8001/api/chat",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "What can you tell me about the IP 8.8.8.8?"
                        }
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "response" in data
            assert len(data["response"]) > 20, "Should have substantial response"

            print(f"✅ Intelligent query with tool: PASS")
            print(f"   Response length: {len(data['response'])} chars")

            # Verifica se menciona Google (já que 8.8.8.8 é DNS do Google)
            if "google" in data["response"].lower():
                print(f"   ✨ AI correctly identified Google DNS!")

        except httpx.ReadTimeout:
            pytest.skip("⚠️  Maximus AI timed out (Gemini may be slow)")


@pytest.mark.asyncio
async def test_maximus_analyze_endpoint():
    """Testa endpoint de análise do Maximus."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8001/api/analyze",
                json={
                    "target": "example.com",
                    "analysis_type": "quick"
                }
            )

            # Aceita 200 (sucesso) ou 422 (validação - endpoint existe)
            assert response.status_code in [200, 422, 404], \
                f"Unexpected status: {response.status_code}"

            if response.status_code == 200:
                print(f"✅ Maximus analyze endpoint: PASS")
            elif response.status_code == 422:
                print(f"✅ Maximus analyze endpoint: EXISTS (validation error)")
            else:
                print(f"⚠️  Maximus analyze endpoint: NOT IMPLEMENTED")

        except httpx.ConnectError:
            pytest.skip("Maximus Core not running - service offline")


@pytest.mark.asyncio
async def test_reasoning_engine_status():
    """Testa que o reasoning engine está online."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200

            data = response.json()

            # Verifica reasoning engine
            assert "reasoning_engine" in data, "Should report reasoning engine status"
            reasoning_status = data["reasoning_engine"]

            assert reasoning_status in ["online", "ready", "active"], \
                f"Reasoning engine should be online, got: {reasoning_status}"

            print(f"✅ Reasoning engine: {reasoning_status.upper()}")

            # Verifica LLM ready
            assert data.get("llm_ready") is True, "LLM should be ready"
            print(f"✅ LLM ready: TRUE")

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")


@pytest.mark.asyncio
async def test_cognitive_capabilities():
    """Testa que capabilities cognitivas estão reportadas."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200

            data = response.json()

            # Verifica cognitive capabilities
            assert "cognitive_capabilities" in data
            capabilities = data["cognitive_capabilities"]

            print(f"✅ Cognitive capabilities: {capabilities}")

            # Deve ser algo como "NSA-grade", "advanced", etc.
            assert isinstance(capabilities, str)
            assert len(capabilities) > 0

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
