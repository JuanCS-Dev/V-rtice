#!/usr/bin/env python3
"""
🧪 Test HTTP Connectivity for Active Immune System Services

Testa conectividade via portas externas (host) para verificar
se o port mapping está funcionando corretamente.
"""

import urllib.request
import urllib.error
import json
from typing import Dict, Tuple

# Mapeamento de serviços e portas externas
SERVICES = {
    # Support Services
    "adaptive_immunity": ("http://localhost:8020/health", 8020),
    "memory_consolidation": ("http://localhost:8019/health", 8019),
    "immunis_treg": ("http://localhost:8018/health", 8018),

    # IMMUNIS Cell Agents
    "immunis_macrophage": ("http://localhost:8312/health", 8312),
    "immunis_neutrophil": ("http://localhost:8313/health", 8313),
    "immunis_bcell": ("http://localhost:8316/health", 8316),
    "immunis_dendritic": ("http://localhost:8314/health", 8314),
    "immunis_nk_cell": ("http://localhost:8319/health", 8319),
    "immunis_helper_t": ("http://localhost:8317/health", 8317),
    "immunis_cytotoxic_t": ("http://localhost:8318/health", 8318),

    # Core Service
    "active_immune_core": ("http://localhost:8200/health", 8200),
}

def test_endpoint(name: str, url: str, port: int) -> Tuple[bool, str, int]:
    """
    Testa um endpoint HTTP.

    Returns:
        (success, message, status_code)
    """
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            status_code = response.status
            if status_code == 200:
                return (True, f"✅ OK", status_code)
            else:
                return (False, f"❌ Unexpected status", status_code)
    except urllib.error.HTTPError as e:
        return (False, f"❌ HTTP {e.code}", e.code)
    except urllib.error.URLError as e:
        if "Connection refused" in str(e.reason):
            return (False, "❌ Connection refused", 0)
        elif "Connection reset" in str(e.reason):
            return (False, "❌ Connection reset", 0)
        else:
            return (False, f"❌ {e.reason}", 0)
    except TimeoutError:
        return (False, "❌ Timeout", 0)
    except Exception as e:
        return (False, f"❌ {type(e).__name__}: {e}", 0)

def main():
    print("🧪 Testando conectividade HTTP dos serviços do Active Immune System...")
    print()

    results = {}
    success_count = 0
    fail_count = 0

    for name, (url, port) in SERVICES.items():
        print(f"🔍 Testando: {name:25} (porta {port})... ", end="", flush=True)

        success, message, status_code = test_endpoint(name, url, port)
        results[name] = (success, message, status_code)

        print(message)

        if success:
            success_count += 1
        else:
            fail_count += 1

    print()
    print("=" * 80)
    print(f"📊 Resumo:")
    print(f"  Total: {len(SERVICES)} serviços")
    print(f"  ✅ Sucesso: {success_count}")
    print(f"  ❌ Falhas: {fail_count}")
    print("=" * 80)

    if fail_count > 0:
        print()
        print("🔥 Serviços com problemas:")
        for name, (success, message, status_code) in results.items():
            if not success:
                port = SERVICES[name][1]
                print(f"  - {name:25} (porta {port}): {message}")
        print()
        exit(1)
    else:
        print()
        print("✅ TODOS OS SERVIÇOS ESTÃO ACESSÍVEIS!")
        print()
        exit(0)

if __name__ == "__main__":
    main()
