#!/usr/bin/env python3
"""
VALIDAÇÃO COMPLETA DE TODAS AS CORREÇÕES DE PORTAS
Testa TODOS os 66 serviços corrigidos e gera relatório de completude
"""

import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def test_health_endpoint(port, container_name):
    """Testa health endpoint na porta externa"""
    url = f"http://localhost:{port}/health"
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return "HEALTHY", response.json() if response.headers.get('content-type', '').startswith('application/json') else "OK"
        else:
            return "UNHEALTHY", f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return "TIMEOUT", "Connection timeout"
    except requests.exceptions.ConnectionError:
        return "UNREACHABLE", "Connection refused"
    except Exception as e:
        return "ERROR", str(e)

def get_container_status(container_name):
    """Verifica se container está rodando"""
    try:
        result = subprocess.run(
            ['docker', 'inspect', '-f', '{{.State.Status}}', container_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return "unknown"

def main():
    print(f"{CYAN}╔══════════════════════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║  VALIDAÇÃO COMPLETA - Todas as Correções de Portas      ║{NC}")
    print(f"{CYAN}╚══════════════════════════════════════════════════════════╝{NC}")
    print()

    manifest_path = Path("/home/juan/vertice-dev/docs/port_manifest.json")

    with open(manifest_path, 'r') as f:
        services = json.load(f)

    # Filter only services that were corrected (had mismatches)
    corrected_services = [s for s in services if s.get('mismatch', False)]

    print(f"{BLUE}📊 Total de serviços corrigidos: {len(corrected_services)}{NC}")
    print()

    results = {
        'healthy': [],
        'unhealthy': [],
        'unreachable': [],
        'timeout': [],
        'container_down': []
    }

    for service in corrected_services:
        container = service['container']
        external = service['external_port']
        real_port = service['real_port']

        # Check container status first
        container_status = get_container_status(container)

        if container_status != 'running':
            results['container_down'].append({
                'container': container,
                'port': external,
                'status': container_status
            })
            print(f"{RED}❌ {container} (:{external}) - Container {container_status.upper()}{NC}")
            continue

        # Test health endpoint
        status, message = test_health_endpoint(external, container)

        if status == "HEALTHY":
            results['healthy'].append({
                'container': container,
                'port': external,
                'real_port': real_port
            })
            print(f"{GREEN}✅ {container} (:{external}) - HEALTHY{NC}")
        elif status == "UNHEALTHY":
            results['unhealthy'].append({
                'container': container,
                'port': external,
                'message': message
            })
            print(f"{YELLOW}⚠ {container} (:{external}) - {message}{NC}")
        elif status == "TIMEOUT":
            results['timeout'].append({
                'container': container,
                'port': external
            })
            print(f"{YELLOW}⏱ {container} (:{external}) - TIMEOUT{NC}")
        elif status == "UNREACHABLE":
            results['unreachable'].append({
                'container': container,
                'port': external
            })
            print(f"{RED}❌ {container} (:{external}) - UNREACHABLE{NC}")
        else:
            results['unreachable'].append({
                'container': container,
                'port': external,
                'error': message
            })
            print(f"{RED}❌ {container} (:{external}) - ERROR: {message}{NC}")

    print()
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print()
    print(f"{CYAN}📊 RELATÓRIO DE COMPLETUDE:{NC}")
    print()
    print(f"  {GREEN}✅ HEALTHY: {len(results['healthy'])}{NC}")
    print(f"  {YELLOW}⚠ UNHEALTHY: {len(results['unhealthy'])}{NC}")
    print(f"  {YELLOW}⏱ TIMEOUT: {len(results['timeout'])}{NC}")
    print(f"  {RED}❌ UNREACHABLE: {len(results['unreachable'])}{NC}")
    print(f"  {RED}🔴 CONTAINER DOWN: {len(results['container_down'])}{NC}")
    print()

    total = len(corrected_services)
    success_rate = (len(results['healthy']) / total * 100) if total > 0 else 0

    print(f"{CYAN}📈 TAXA DE SUCESSO: {success_rate:.1f}% ({len(results['healthy'])}/{total}){NC}")
    print()

    # Save detailed report
    report_path = Path("/home/juan/vertice-dev/docs/port_correction_validation.json")
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_corrected': total,
            'success_rate': success_rate,
            'results': results
        }, f, indent=2)

    print(f"{GREEN}✅ Relatório detalhado salvo em: {report_path}{NC}")
    print()

    # Show problematic services if any
    if results['unhealthy'] or results['unreachable'] or results['timeout'] or results['container_down']:
        print(f"{YELLOW}⚠ SERVIÇOS COM PROBLEMAS:{NC}")
        print()

        if results['container_down']:
            print(f"{RED}  Containers não rodando:{NC}")
            for item in results['container_down']:
                print(f"    - {item['container']} (status: {item['status']})")
            print()

        if results['unreachable']:
            print(f"{RED}  Portas não alcançáveis:{NC}")
            for item in results['unreachable']:
                print(f"    - {item['container']} (:{item['port']})")
            print()

        if results['timeout']:
            print(f"{YELLOW}  Timeouts:{NC}")
            for item in results['timeout']:
                print(f"    - {item['container']} (:{item['port']})")
            print()

    return 0 if success_rate == 100 else 1

if __name__ == '__main__':
    exit(main())
