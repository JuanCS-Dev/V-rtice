#!/usr/bin/env python3
"""
Script focado: 100% absoluto APENAS em backend/ (excluindo consciousness).
Execução categórica por prioridade.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_coverage_focused() -> Dict:
    """Executa coverage APENAS em backend/ excluindo consciousness."""
    print("🔍 Coverage scan (backend only, sem consciousness)...")
    subprocess.run([
        "pytest",
        "--cov=backend",
        "--cov-report=json:coverage_backend_focused.json",
        "--cov-report=term-missing",
        "-v",
        "--ignore=backend/consciousness",
        "--ignore=tests/consciousness"
    ], cwd="/home/juan/vertice-dev")
    
    with open("/home/juan/vertice-dev/coverage_backend_focused.json") as f:
        return json.load(f)


def filter_backend_only(cov_data: Dict) -> List[Tuple[str, List[int], float, int]]:
    """Filtra APENAS backend/ (sem consciousness), retorna (path, missing, %, stmts)."""
    targets = []
    
    for filepath, data in cov_data.get("files", {}).items():
        # Apenas backend/, excluindo consciousness
        if not filepath.startswith("backend/"):
            continue
        if "consciousness" in filepath:
            continue
            
        summary = data.get("summary", {})
        coverage_pct = summary.get("percent_covered", 0)
        num_statements = summary.get("num_statements", 0)
        
        if coverage_pct < 100:
            missing_lines = data.get("missing_lines", [])
            if missing_lines:
                targets.append((filepath, missing_lines, coverage_pct, num_statements))
    
    # Ordena por: prioridade = gap% * num_statements (impacto)
    return sorted(targets, key=lambda x: (100 - x[2]) * x[3], reverse=True)


def categorize_targets(targets: List[Tuple]) -> Dict[str, List]:
    """Categoriza alvos por área."""
    categories = {
        "shared": [],
        "libs": [],
        "modules": [],
        "services": [],
        "outros": []
    }
    
    for target in targets:
        filepath = target[0]
        if "shared/" in filepath:
            categories["shared"].append(target)
        elif "libs/" in filepath:
            categories["libs"].append(target)
        elif "modules/" in filepath:
            categories["modules"].append(target)
        elif "services/" in filepath:
            categories["services"].append(target)
        else:
            categories["outros"].append(target)
    
    return categories


def generate_fix_script(target: Tuple, output_dir: Path) -> Path:
    """Gera script Python para cobrir 100% de UM arquivo específico."""
    filepath, missing_lines, current_cov, stmts = target
    
    # Lê código fonte
    source_path = Path(f"/home/juan/vertice-dev/{filepath}")
    if not source_path.exists():
        return None
        
    source_lines = source_path.read_text().splitlines()
    
    # Identifica contexto das linhas
    contexts = []
    for line_num in missing_lines[:50]:  # Max 50 linhas por vez
        if line_num <= len(source_lines):
            line = source_lines[line_num - 1]
            contexts.append(f"    # Line {line_num}: {line.strip()}")
    
    # Nome do módulo
    module_path = filepath.replace("backend/", "").replace(".py", "").replace("/", ".")
    test_name = source_path.stem
    
    script_content = f'''#!/usr/bin/env python3
"""
AUTO-GENERATED: Testes para {filepath}
TARGET: 100% coverage absoluto
MISSING: {len(missing_lines)} linhas
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from {module_path} import *

# LINHAS NÃO COBERTAS:
{chr(10).join(contexts)}

class Test{test_name.title().replace("_", "")}Absolute:
    """Cobertura 100% absoluta."""
    
    def test_all_branches(self):
        """Cobre TODOS os branches não testados."""
        # TODO: Implementar testes específicos
        pass
    
    def test_edge_cases(self):
        """Cobre TODOS os edge cases."""
        # TODO: Implementar edge cases
        pass
    
    def test_error_paths(self):
        """Cobre TODOS os caminhos de erro."""
        # TODO: Implementar error paths
        pass
'''
    
    # Salva script
    script_path = output_dir / f"fix_{test_name}.py"
    script_path.write_text(script_content)
    return script_path


def main():
    print("="*80)
    print("🎯 BACKEND 100% ABSOLUTO (FOCUSED - SEM CONSCIOUSNESS)")
    print("="*80)
    
    # 1. Coverage scan
    cov_data = run_coverage_focused()
    
    # 2. Filtra apenas backend
    targets = filter_backend_only(cov_data)
    
    if not targets:
        print("\n✅ 100% COVERAGE ABSOLUTO ALCANÇADO EM BACKEND!")
        return 0
    
    # 3. Categoriza
    categories = categorize_targets(targets)
    
    # 4. Relatório
    print(f"\n📊 GAPS POR CATEGORIA:")
    for cat_name, cat_targets in categories.items():
        if not cat_targets:
            continue
        total_lines = sum(len(t[1]) for t in cat_targets)
        avg_cov = sum(t[2] for t in cat_targets) / len(cat_targets) if cat_targets else 0
        print(f"   • {cat_name:12s}: {len(cat_targets):3d} arquivos, {total_lines:5d} linhas, avg {avg_cov:.1f}%")
    
    # 5. Top 20 alvos prioritários
    print(f"\n🎯 TOP 20 ALVOS (maior impacto):")
    for i, (filepath, missing, cov, stmts) in enumerate(targets[:20], 1):
        impact = (100 - cov) * stmts
        print(f"   {i:2d}. {filepath:60s} {cov:5.1f}% ({len(missing):3d} linhas, impact={impact:.0f})")
    
    # 6. Gera scripts de fix
    output_dir = Path("/home/juan/vertice-dev/scripts/fixes")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🔧 Gerando scripts de fix para top 20...")
    for target in targets[:20]:
        script_path = generate_fix_script(target, output_dir)
        if script_path:
            print(f"   → {script_path.name}")
    
    # 7. Salva plano executivo
    plan_path = Path("/home/juan/vertice-dev/docs/backend_100/EXECUTION_PLAN.md")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    
    plan_content = f"""# BACKEND 100% ABSOLUTE - PLANO EXECUTIVO

## SITUAÇÃO ATUAL
- **Total de arquivos com gaps:** {len(targets)}
- **Total de linhas faltando:** {sum(len(t[1]) for t in targets)}
- **Coverage médio:** {sum(t[2] for t in targets) / len(targets):.2f}%

## CATEGORIAS

"""
    
    for cat_name, cat_targets in categories.items():
        if not cat_targets:
            continue
        plan_content += f"\n### {cat_name.upper()}\n"
        for filepath, missing, cov, stmts in cat_targets[:10]:
            plan_content += f"- [ ] `{filepath}` - {cov:.1f}% ({len(missing)} linhas)\n"
    
    plan_content += f"""

## ESTRATÉGIA DE EXECUÇÃO

### FASE 1: SHARED (fundação)
Começar por shared/ pois é usado por todos os outros módulos.

### FASE 2: LIBS (dependências)
Libs são usadas por modules e services.

### FASE 3: MODULES
Módulos de negócio.

### FASE 4: SERVICES
Serviços de alto nível.

### FASE 5: VALIDAÇÃO FINAL
100% absoluto em tudo.

## PRÓXIMOS PASSOS

1. Executar fixes categoria por categoria
2. Validar após cada arquivo
3. Commit incremental
4. Iterar até 100%
"""
    
    plan_path.write_text(plan_content)
    
    print(f"\n📋 Plano salvo em: {plan_path}")
    print(f"🔧 Scripts de fix em: {output_dir}")
    print(f"\n{'='*80}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
