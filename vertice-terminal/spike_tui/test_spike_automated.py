#!/usr/bin/env python
"""
Teste Automatizado do Spike TUI

Executa validações automáticas sem interação humana:
- Conectividade SSE
- Recepção de eventos
- Performance inicial
- Estado reativo

Para teste manual interativo, use: python governance_workspace_poc.py
"""

import asyncio
import httpx
import json
import time
import sys
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"[{status}] {name}")
    if details:
        print(f"    {details}")

async def test_sse_connectivity():
    """Testa conectividade básica com SSE server."""
    print(f"\n{Colors.BLUE}🔍 Teste 1: Conectividade SSE{Colors.RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/spike/health", timeout=5.0)
            data = response.json()

            passed = response.status_code == 200 and data.get("status") == "healthy"
            print_test("Health check endpoint", passed, f"Status: {data.get('status')}")
            return passed
    except Exception as e:
        print_test("Health check endpoint", False, f"Error: {e}")
        return False

async def test_sse_streaming():
    """Testa recepção de eventos via SSE."""
    print(f"\n{Colors.BLUE}🔍 Teste 2: SSE Streaming{Colors.RESET}")

    try:
        events_received = []
        start_time = time.time()

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", "http://localhost:8001/stream/ethical-events") as response:
                if response.status_code != 200:
                    print_test("SSE connection", False, f"HTTP {response.status_code}")
                    return False

                print_test("SSE connection established", True)

                # Aguarda até 3 eventos ou 15 segundos
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        events_received.append(event_data)

                        latency = time.time() - start_time
                        print(f"    📨 Evento #{len(events_received)}: {event_data['id']} "
                              f"(risk: {event_data['risk_level']}) - latency: {latency:.2f}s")

                        if len(events_received) >= 3:
                            break

                    # Timeout após 15 segundos
                    if time.time() - start_time > 15:
                        break

        # Validações
        received_3_events = len(events_received) >= 3
        print_test("Recebeu 3+ eventos", received_3_events, f"Total: {len(events_received)}")

        avg_latency = sum(time.time() - start_time for _ in events_received) / len(events_received) if events_received else 0
        latency_ok = avg_latency < 6.0  # Target: < 6s entre eventos
        print_test("Latência aceitável", latency_ok, f"Média: {avg_latency:.2f}s")

        return received_3_events and latency_ok

    except Exception as e:
        print_test("SSE streaming", False, f"Error: {e}")
        return False

async def test_event_structure():
    """Valida estrutura dos eventos."""
    print(f"\n{Colors.BLUE}🔍 Teste 3: Estrutura de Eventos{Colors.RESET}")

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", "http://localhost:8001/stream/ethical-events") as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])

                        # Valida campos obrigatórios
                        required_fields = ["id", "timestamp", "action_type", "target",
                                          "risk_level", "ethical_concern", "recommended_action"]

                        has_all_fields = all(field in event for field in required_fields)
                        print_test("Campos obrigatórios presentes", has_all_fields,
                                  f"Campos: {list(event.keys())}")

                        # Valida risk_level
                        valid_risk_levels = ["critical", "high", "medium", "low"]
                        risk_valid = event.get("risk_level") in valid_risk_levels
                        print_test("Risk level válido", risk_valid,
                                  f"Risk: {event.get('risk_level')}")

                        # Valida timestamp ISO format
                        try:
                            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                            timestamp_valid = True
                        except:
                            timestamp_valid = False
                        print_test("Timestamp válido", timestamp_valid)

                        return has_all_fields and risk_valid and timestamp_valid

    except Exception as e:
        print_test("Estrutura de eventos", False, f"Error: {e}")
        return False

async def test_trigger_endpoint():
    """Testa endpoint de trigger manual."""
    print(f"\n{Colors.BLUE}🔍 Teste 4: Trigger Manual{Colors.RESET}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8001/spike/trigger-high-risk", timeout=5.0)
            data = response.json()

            triggered = response.status_code == 200 and data.get("status") == "triggered"
            print_test("Trigger de evento crítico", triggered,
                      f"Event ID: {data.get('event', {}).get('id')}")
            return triggered

    except Exception as e:
        print_test("Trigger endpoint", False, f"Error: {e}")
        return False

async def main():
    """Executa todos os testes."""
    print(f"""
{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗
║     SPIKE TUI - TESTE AUTOMATIZADO                          ║
║     Governance Workspace POC - Validação de Backend         ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")

    results = []

    # Teste 1: Conectividade
    results.append(await test_sse_connectivity())

    # Teste 2: Streaming
    results.append(await test_sse_streaming())

    # Teste 3: Estrutura
    results.append(await test_event_structure())

    # Teste 4: Trigger
    results.append(await test_trigger_endpoint())

    # Sumário
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100

    print(f"\n{Colors.BLUE}═══════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BLUE}📊 RESULTADO DOS TESTES{Colors.RESET}")
    print(f"{Colors.BLUE}═══════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"\nTestes aprovados: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print(f"\n{Colors.GREEN}✅ TODOS OS TESTES PASSARAM!{Colors.RESET}")
        print(f"\nBackend SSE está funcional e pronto para TUI POC.")
        print(f"\nPróximo passo: Execute a TUI interativa:")
        print(f"  python governance_workspace_poc.py")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  {total - passed} teste(s) falharam{Colors.RESET}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
