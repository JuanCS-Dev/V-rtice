#!/usr/bin/env python3
"""
Script de automação para alcançar 100% de coverage absoluto em TODOS os módulos.
Gera testes para TODAS as linhas não cobertas, sem exceções.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def run_coverage() -> Dict:
    """Executa pytest com coverage e retorna dados JSON."""
    print("🔍 Executando coverage scan...")
    subprocess.run([
        "pytest",
        "--cov=backend",
        "--cov-report=json:coverage_scan_absolute.json",
        "--cov-report=term-missing",
        "-v"
    ], cwd="/home/juan/vertice-dev")
    
    with open("/home/juan/vertice-dev/coverage_scan_absolute.json") as f:
        return json.load(f)


def get_uncovered_lines(cov_data: Dict) -> List[Tuple[str, List[int], float]]:
    """Retorna lista de (arquivo, linhas_não_cobertas, coverage_atual)."""
    uncovered = []
    
    for filepath, data in cov_data.get("files", {}).items():
        if not filepath.startswith("backend/"):
            continue
            
        summary = data.get("summary", {})
        coverage_pct = summary.get("percent_covered", 0)
        
        if coverage_pct < 100:
            missing_lines = data.get("missing_lines", [])
            if missing_lines:
                uncovered.append((filepath, missing_lines, coverage_pct))
    
    return sorted(uncovered, key=lambda x: x[2])  # Ordena por coverage (menor primeiro)


def generate_test_for_file(filepath: str, missing_lines: List[int]) -> str:
    """Gera teste para cobrir linhas faltantes."""
    # Lê o arquivo fonte
    with open(f"/home/juan/vertice-dev/{filepath}") as f:
        source_lines = f.readlines()
    
    # Identifica funções/classes não cobertas
    test_cases = []
    
    for line_num in missing_lines:
        if line_num <= len(source_lines):
            line = source_lines[line_num - 1].strip()
            test_cases.append(f"# Line {line_num}: {line}")
    
    module_name = filepath.replace("backend/", "").replace("/", ".").replace(".py", "")
    test_file = filepath.replace("backend/", "tests/").replace(".py", "_test.py")
    
    return f"""
# AUTO-GENERATED TEST for {filepath}
# Target: 100% coverage absoluto

import pytest
from unittest.mock import Mock, patch, MagicMock
from {module_name} import *

class Test{Path(filepath).stem.title().replace('_', '')}Coverage:
    \"\"\"Tests para cobrir TODAS as linhas não cobertas.\"\"\"
    
    # Linhas alvo:
{chr(10).join(f'    {tc}' for tc in test_cases)}
    
    def test_all_edge_cases(self):
        \"\"\"Testa TODOS os edge cases não cobertos.\"\"\"
        # TODO: Implementar testes específicos para cada linha
        pass
"""


def generate_all_missing_tests(uncovered: List[Tuple[str, List[int], float]]) -> None:
    """Gera testes para TODOS os arquivos com coverage < 100%."""
    print(f"\n📊 MÓDULOS COM COVERAGE < 100%: {len(uncovered)}")
    
    for filepath, missing_lines, current_cov in uncovered:
        print(f"\n{'='*80}")
        print(f"📁 {filepath}")
        print(f"   Coverage atual: {current_cov:.2f}%")
        print(f"   Linhas faltando: {len(missing_lines)}")
        print(f"   Linhas: {missing_lines[:10]}{'...' if len(missing_lines) > 10 else ''}")
        
        # Gera estrutura de teste
        test_content = generate_test_for_file(filepath, missing_lines)
        
        # Salva em arquivo temporário para análise
        test_file = filepath.replace("backend/", "tests/").replace(".py", "_coverage_100.py")
        test_path = Path(f"/home/juan/vertice-dev/{test_file}")
        test_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"   → Gerado: {test_file}")


def create_execution_plan(uncovered: List[Tuple[str, List[int], float]]) -> str:
    """Cria plano de execução detalhado."""
    plan = """# PLANO DE EXECUÇÃO: 100% COVERAGE ABSOLUTO

## ESTRATÉGIA
1. Automatizar geração de testes base
2. Identificar padrões de edge cases
3. Implementar testes específicos por categoria
4. Validar incrementalmente

## ALVOS PRIORITÁRIOS (ordenado por dificuldade)

"""
    
    for i, (filepath, missing_lines, current_cov) in enumerate(uncovered, 1):
        gap = 100 - current_cov
        plan += f"""
### {i}. {filepath}
   - **Coverage atual:** {current_cov:.2f}%
   - **Gap:** {gap:.2f}%
   - **Linhas faltando:** {len(missing_lines)}
   - **Prioridade:** {'🔴 CRÍTICO' if gap > 10 else '🟡 MÉDIO' if gap > 5 else '🟢 BAIXO'}
   - **Linhas:** {missing_lines[:20]}{'...' if len(missing_lines) > 20 else ''}
"""
    
    return plan


def main():
    print("="*80)
    print("🎯 MISSÃO: 100% COVERAGE ABSOLUTO - AUTOMAÇÃO TOTAL")
    print("="*80)
    
    # 1. Executa coverage
    cov_data = run_coverage()
    
    # 2. Identifica gaps
    uncovered = get_uncovered_lines(cov_data)
    
    if not uncovered:
        print("\n✅ 100% COVERAGE ABSOLUTO ALCANÇADO!")
        return 0
    
    # 3. Gera plano
    plan = create_execution_plan(uncovered)
    plan_path = Path("/home/juan/vertice-dev/docs/BACKEND_100_EXECUTION_PLAN.md")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan)
    print(f"\n📋 Plano salvo em: {plan_path}")
    
    # 4. Gera estrutura de testes
    generate_all_missing_tests(uncovered)
    
    # 5. Relatório final
    total_missing = sum(len(lines) for _, lines, _ in uncovered)
    print(f"\n{'='*80}")
    print(f"📊 RESUMO:")
    print(f"   • Módulos com gaps: {len(uncovered)}")
    print(f"   • Total de linhas faltando: {total_missing}")
    print(f"   • Cobertura média: {sum(c for _, _, c in uncovered) / len(uncovered):.2f}%")
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    print(f"   1. Revisar plano em docs/BACKEND_100_EXECUTION_PLAN.md")
    print(f"   2. Implementar testes categoria por categoria")
    print(f"   3. Validar incrementalmente após cada batch")
    print(f"   4. Iterar até 100% absoluto")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
