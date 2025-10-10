#!/usr/bin/env python3
"""Diagnóstico automático dos 13 serviços falhando"""

import subprocess
import json
import re

FAILING_SERVICES = [
    'offensive_gateway',
    'vertice-homeostatic-regulation',
    'c2_orchestration_service',
    'maximus-core',
    'vertice-prefrontal-cortex',
    'vertice-digital-thalamus',
    'vertice-visual-cortex',
    'vertice-auditory-cortex',
    'vertice-vestibular',
    'vertice-ip-intel',
    'rte-service',
    'hpc-service',
    'vertice-narrative-filter'
]

def get_logs(container):
    """Pega últimas 100 linhas de log"""
    try:
        result = subprocess.run(['docker', 'logs', container],
                              capture_output=True, text=True, timeout=5)
        return result.stdout + result.stderr
    except:
        return ""

def analyze_error(service, logs):
    """Categoriza o erro"""

    # ImportError com path complexo
    import_match = re.search(r'from \.([a-zA-Z0-9_./]+) import', logs)
    if import_match:
        return {
            'category': 'import_complex',
            'pattern': import_match.group(0),
            'module': import_match.group(1)
        }

    # ImportError simples
    if 'ImportError: attempted relative import' in logs:
        return {'category': 'import_simple'}

    # SyntaxError
    syntax_match = re.search(r'SyntaxError: (.+)', logs)
    if syntax_match:
        file_match = re.search(r'File "(.+)", line (\d+)', logs)
        return {
            'category': 'syntax',
            'error': syntax_match.group(1),
            'file': file_match.group(1) if file_match else None,
            'line': file_match.group(2) if file_match else None
        }

    # TypeError (Pydantic)
    if "TypeError: 'mode' is an invalid keyword" in logs:
        return {'category': 'pydantic_v2'}

    # ModuleNotFoundError
    if 'ModuleNotFoundError' in logs:
        mod_match = re.search(r"No module named '([^']+)'", logs)
        return {
            'category': 'missing_module',
            'module': mod_match.group(1) if mod_match else 'unknown'
        }

    return {'category': 'unknown'}

# Diagnóstico
results = {'import_complex': [], 'import_simple': [], 'syntax': [],
           'pydantic_v2': [], 'missing_module': [], 'unknown': []}

print("=" * 70)
print("DIAGNÓSTICO AUTOMÁTICO - 13 SERVIÇOS")
print("=" * 70)
print()

for service in FAILING_SERVICES:
    logs = get_logs(service)
    analysis = analyze_error(service, logs)
    category = analysis['category']
    results[category].append({'service': service, **analysis})
    print(f"{'✓' if category != 'unknown' else '?'} {service:40} -> {category}")

print()
print("=" * 70)
print("RESUMO POR CATEGORIA")
print("=" * 70)

for cat, items in results.items():
    if items:
        print(f"\n{cat.upper()}: {len(items)} serviços")
        for item in items:
            print(f"  - {item['service']}")

# Salvar JSON
with open('/tmp/diagnosis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n📁 Detalhes salvos em: /tmp/diagnosis.json")
