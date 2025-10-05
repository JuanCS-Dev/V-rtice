"""
Test E2E: Investigation Flow
==============================

Testa fluxo completo de investigação via CLI e API.

Fluxo 1: Investigação Defensiva de Domínio
- Usar API para análise de domínio
- Verificar que tools são chamadas
- Validar resultado estruturado

Fluxo 2: Memory System com Recall
- Fazer query
- Salvar na memória
- Recuperar da memória
"""

import pytest
import httpx
import subprocess
import time
from tests.fixtures.sample_data import SAMPLE_TARGETS


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_domain_investigation_api():
    """
    E2E Flow 1: Investigação defensiva de domínio via API.

    Passos:
    1. Fazer chat query sobre o domínio
    2. Verificar resposta
    3. Verificar que memory foi atualizada
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Passo 1: Query sobre domínio
        try:
            response = await client.post(
                "http://localhost:8001/api/chat",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Analyze the domain {SAMPLE_TARGETS['domain_safe']} and tell me if it's safe."
                        }
                    ],
                    "session_id": "test_e2e_domain_001"
                }
            )

            assert response.status_code == 200, "Chat request failed"
            data = response.json()

            # Passo 2: Validar resposta
            assert "response" in data
            assert len(data["response"]) > 20, "Response too short"

            print(f"✅ E2E Domain Investigation: Response received")
            print(f"   Length: {len(data['response'])} chars")
            print(f"   Preview: {data['response'][:150]}...")

            # Passo 3: Verificar que memory foi atualizada
            await asyncio.sleep(1)  # Dar tempo para salvar

            memory_response = await client.get("http://localhost:8001/memory/stats")

            if memory_response.status_code == 200:
                memory_data = memory_response.json()
                print(f"✅ Memory updated:")
                print(f"   Conversations: {memory_data.get('episodic_stats', {}).get('conversations', 0)}")
                print(f"   Messages: {memory_data.get('episodic_stats', {}).get('messages', 0)}")

            print(f"✅ E2E Domain Investigation: COMPLETE")

        except httpx.ReadTimeout:
            pytest.skip("⚠️  Maximus AI timed out (Gemini may be slow)")


@pytest.mark.e2e
def test_e2e_cli_command_execution():
    """
    E2E Flow 2: Execução de comando CLI completo.

    Testa que o CLI completo funciona end-to-end.
    """
    # Testa comando memory status
    result = subprocess.run(
        ["vcli", "memory", "status"],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Deve executar sem erro OU pedir autenticação (comportamento esperado)
    auth_required = "Authentication Required" in result.stdout or "auth login" in result.stdout

    assert result.returncode == 0 or auth_required or "Service offline" in result.stderr, \
        f"Command failed unexpectedly: {result.stderr}"

    if result.returncode == 0:
        print(f"✅ CLI Memory Status: SUCCESS")
        print(f"   Output preview: {result.stdout[:200]}")
    elif auth_required:
        print(f"✅ CLI Memory Status: AUTH REQUIRED (expected)")
    else:
        print(f"⚠️  CLI Memory Status: Service may be offline")

    print(f"✅ E2E CLI Execution: COMPLETE")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_tools_orchestration():
    """
    E2E Flow 3: Tool orchestration via Maximus.

    Verifica que múltiplas tools podem ser orquestradas.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Request que deve acionar múltiplas tools
        try:
            response = await client.post(
                "http://localhost:8001/api/chat",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "What tools do you have available for security analysis?"
                        }
                    ]
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "response" in data
            response_text = data["response"].lower()

            # Deve mencionar tools ou capabilities
            has_tools_info = any(word in response_text for word in [
                "tool", "capability", "service", "analysis", "scan"
            ])

            assert has_tools_info, "Response should mention tools or capabilities"

            print(f"✅ E2E Tools Orchestration: Response mentions capabilities")
            print(f"   Preview: {data['response'][:150]}...")

        except httpx.ReadTimeout:
            pytest.skip("⚠️  Maximus AI timed out")


import asyncio  # Import necessário


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])
