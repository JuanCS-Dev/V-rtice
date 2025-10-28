#!/usr/bin/env python3
"""Compare duplicated services and recommend merge strategy."""
import os
import sys
from pathlib import Path

pairs = [
    ("bas_service", "bas-service"),
    ("c2_orchestration_service", "c2-orchestration-service"),
    ("network_recon_service", "network-recon-service"),
    ("vuln_intel_service", "vuln-intel-service"),
    ("web_attack_service", "web-attack-service"),
]

print("=" * 80)
print("ANÁLISE COMPARATIVA DE SERVIÇOS DUPLICADOS")
print("=" * 80)

recommendations = []

for old_name, new_name in pairs:
    old_path = Path(f"backend/services/{old_name}")
    new_path = Path(f"backend/services/{new_name}")

    print(f"\n{'─' * 80}")
    print(f"📦 Par: {old_name} vs {new_name}")
    print(f"{'─' * 80}")

    # Check if both exist
    if not old_path.exists():
        print(f"❌ {old_name} não existe")
        continue
    if not new_path.exists():
        print(f"❌ {new_name} não existe")
        continue

    # Count files
    old_py_files = list(old_path.rglob("*.py"))
    new_py_files = list(new_path.rglob("*.py"))

    old_dockerfile = old_path / "Dockerfile"
    new_dockerfile = new_path / "Dockerfile"

    old_requirements = old_path / "requirements.txt"
    new_requirements = new_path / "requirements.txt"

    old_deployment = old_path / "deployment.yaml"
    new_deployment = new_path / "deployment.yaml"

    old_readme = old_path / "README.md"
    new_readme = new_path / "README.md"

    print(f"\n📊 Estatísticas:")
    print(f"  {old_name}:")
    print(f"    - Arquivos Python: {len(old_py_files)}")
    print(f"    - Dockerfile: {'✅' if old_dockerfile.exists() else '❌'}")
    print(f"    - requirements.txt: {'✅' if old_requirements.exists() else '❌'}")
    print(f"    - deployment.yaml: {'✅' if old_deployment.exists() else '❌'}")
    print(f"    - README.md: {'✅' if old_readme.exists() else '❌'}")

    print(f"  {new_name}:")
    print(f"    - Arquivos Python: {len(new_py_files)}")
    print(f"    - Dockerfile: {'✅' if new_dockerfile.exists() else '❌'}")
    print(f"    - requirements.txt: {'✅' if new_requirements.exists() else '❌'}")
    print(f"    - deployment.yaml: {'✅' if new_deployment.exists() else '❌'}")
    print(f"    - README.md: {'✅' if new_readme.exists() else '❌'}")

    # Analyze what's unique in new version
    needs_merge = False
    merge_items = []

    if new_dockerfile.exists() and not old_dockerfile.exists():
        needs_merge = True
        merge_items.append("Dockerfile")

    if new_deployment.exists() and not old_deployment.exists():
        needs_merge = True
        merge_items.append("deployment.yaml")

    if new_readme.exists() and not old_readme.exists():
        needs_merge = True
        merge_items.append("README.md")

    # Compare Python files by name
    old_py_names = {f.name for f in old_py_files}
    new_py_names = {f.name for f in new_py_files}
    unique_in_new = new_py_names - old_py_names

    if unique_in_new:
        needs_merge = True
        merge_items.extend([f"Python: {name}" for name in unique_in_new])

    print(f"\n🔍 Análise:")
    if len(old_py_files) > len(new_py_files):
        print(f"  ✅ {old_name} é mais completo ({len(old_py_files)} vs {len(new_py_files)} arquivos Python)")
    elif len(new_py_files) > len(old_py_files):
        print(f"  ⚠️  {new_name} tem mais arquivos Python ({len(new_py_files)} vs {len(old_py_files)})")
    else:
        print(f"  ⚖️  Ambos têm {len(old_py_files)} arquivos Python")

    if needs_merge:
        print(f"  🔀 MERGE NECESSÁRIO")
        print(f"     Itens únicos em {new_name}:")
        for item in merge_items:
            print(f"       - {item}")
        recommendations.append({
            "pair": (old_name, new_name),
            "action": "merge",
            "items": merge_items
        })
    else:
        print(f"  ✂️  PODE REMOVER {new_name} (nada único)")
        recommendations.append({
            "pair": (old_name, new_name),
            "action": "delete",
            "items": []
        })

print(f"\n{'═' * 80}")
print("📋 RECOMENDAÇÕES FINAIS")
print(f"{'═' * 80}\n")

for rec in recommendations:
    old_name, new_name = rec["pair"]
    if rec["action"] == "merge":
        print(f"🔀 {new_name} → {old_name}")
        print(f"   Copiar para {old_name}:")
        for item in rec["items"]:
            print(f"     - {item}")
        print()
    else:
        print(f"✂️  Remover {new_name} (sem valor único)")
        print()

print(f"{'═' * 80}\n")
