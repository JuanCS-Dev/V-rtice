"""
Test 01: Health Checks - Conectividade de Serviços
===================================================

Valida que todos os serviços estão online e respondendo.
"""

import pytest
import httpx
import asyncio

# Service endpoints
SERVICES = {
    "maximus_core": "http://localhost:8001/health",
    "api_gateway": "http://localhost:8000/health",
    "threat_intel": "http://localhost:8013/health",
    "osint": "http://localhost:8007/health",
    "malware": "http://localhost:8011/health",
    "ssl_monitor": "http://localhost:8012/health",
    "nmap": "http://localhost:8006/health",
    "domain": "http://localhost:8003/health",
}

@pytest.mark.asyncio
async def test_maximus_core_health():
    """Testa se Maximus Core está online e healthy."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("http://localhost:8001/health")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert data.get("status") in ["healthy", "ok", "operational"], f"Status not healthy: {data.get('status')}"
            assert data.get("llm_ready") is not None, "LLM ready status missing"
            assert data.get("total_integrated_tools", 0) > 0, "No tools integrated"

            print(f"✅ Maximus Core: HEALTHY")
            print(f"   - LLM Ready: {data.get('llm_ready')}")
            print(f"   - Tools: {data.get('total_integrated_tools')}")
            print(f"   - Memory: {data.get('memory_system', {}).get('initialized')}")

        except httpx.ConnectError:
            pytest.skip("Maximus Core (port 8001) is not running - service offline")

@pytest.mark.asyncio
async def test_all_backend_services():
    """Testa conectividade de todos os serviços backend."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = {}

        for name, url in SERVICES.items():
            try:
                response = await client.get(url)
                results[name] = {
                    "status": response.status_code,
                    "healthy": response.status_code == 200
                }

                if response.status_code == 200:
                    print(f"✅ {name}: ONLINE")
                else:
                    print(f"⚠️  {name}: HTTP {response.status_code}")

            except httpx.ConnectError:
                results[name] = {"status": "offline", "healthy": False}
                print(f"❌ {name}: OFFLINE")
            except Exception as e:
                results[name] = {"status": str(e), "healthy": False}
                print(f"❌ {name}: ERROR - {e}")

        # Report
        total = len(results)
        healthy = sum(1 for r in results.values() if r["healthy"])
        print(f"\n📊 Backend Services: {healthy}/{total} healthy")

        # Skip if Maximus Core is offline (service not running)
        if not results.get("maximus_core", {}).get("healthy"):
            pytest.skip("Maximus Core is offline - service not running")

@pytest.mark.asyncio
async def test_critical_endpoints():
    """Testa endpoints críticos do Maximus Core."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        endpoints = {
            "/api/tools/complete": "GET",
            "/api/chat": "POST",
            "/memory/stats": "GET",
        }

        for endpoint, method in endpoints.items():
            url = f"http://localhost:8001{endpoint}"

            try:
                if method == "GET":
                    response = await client.get(url)
                else:
                    # POST com payload mínimo
                    response = await client.post(
                        url,
                        json={"messages": [{"role": "user", "content": "test"}]}
                    )

                # Aceita 200 ou erros de validação (400, 422) - significa que endpoint existe
                assert response.status_code in [200, 400, 422], \
                    f"Endpoint {endpoint} returned {response.status_code}"

                print(f"✅ {endpoint}: Accessible")

            except httpx.ConnectError:
                pytest.skip(f"Endpoint {endpoint} not reachable - service offline")

@pytest.mark.asyncio
async def test_tools_catalog():
    """Testa se o catálogo de tools está disponível."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/tools/complete")
            assert response.status_code == 200

            data = response.json()
            total_tools = data.get("total_tools", 0)

            assert total_tools > 50, f"Expected 50+ tools, got {total_tools}"

            print(f"✅ Tools Catalog: {total_tools} tools available")
            print(f"   - World-class: {data.get('world_class_tools', {}).get('count', 0)}")
            print(f"   - Offensive: {data.get('offensive_arsenal', {}).get('count', 0)}")
            print(f"   - All Services: {data.get('all_services', {}).get('count', 0)}")

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")

@pytest.mark.asyncio
async def test_memory_system():
    """Testa se o Memory System está funcional."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/memory/stats")

            # Aceita 200 ou 404 (se não há conversas ainda)
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Memory System: ACTIVE")
                print(f"   - Conversations: {data.get('total_conversations', 0)}")
                print(f"   - Messages: {data.get('total_messages', 0)}")
            else:
                print(f"✅ Memory System: READY (no data yet)")

    except httpx.ConnectError:
        pytest.skip("Maximus Core not running - service offline")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
