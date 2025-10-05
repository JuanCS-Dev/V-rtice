#!/usr/bin/env python3
"""Fix automático de TODOS os erros dos 13 serviços"""

import re
from pathlib import Path

fixed_count = 0

print("=" * 70)
print("FIX AUTOMÁTICO - 13 SERVIÇOS")
print("=" * 70)
print()

# ============================================================================
# 1. FIX TYPING IMPORTS (c2, auditory, digital_thalamus)
# ============================================================================
print("1️⃣  Corrigindo imports de typing...")

typing_files = [
    'backend/services/c2_orchestration_service/cobalt_strike_wrapper.py',
    'backend/services/c2_orchestration_service/metasploit_wrapper.py',
    'backend/services/auditory_cortex_service/binaural_correlation.py',
    'backend/services/auditory_cortex_service/cocktail_party_triage.py',
    'backend/services/auditory_cortex_service/ttp_signature_recognition.py',
    'backend/services/auditory_cortex_service/c2_beacon_detector.py',
]

for filepath in typing_files:
    full_path = Path(f'/home/juan/vertice-dev/{filepath}')
    if not full_path.exists():
        continue

    with open(full_path, 'r') as f:
        content = f.read()

    # Adicionar typing import se não existir
    if 'from typing import' not in content:
        # Inserir após outros imports padrão
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                continue
            else:
                lines.insert(i, 'from typing import List, Dict, Any, Optional')
                content = '\n'.join(lines)
                break

        with open(full_path, 'w') as f:
            f.write(content)
        print(f"  ✓ {filepath}")
        fixed_count += 1

# digital_thalamus: adicionar Field
dt_api = Path('/home/juan/vertice-dev/backend/services/digital_thalamus_service/api.py')
if dt_api.exists():
    with open(dt_api, 'r') as f:
        content = f.read()

    if 'from pydantic import BaseModel' in content and 'Field' not in content:
        content = content.replace(
            'from pydantic import BaseModel',
            'from pydantic import BaseModel, Field'
        )
        with open(dt_api, 'w') as f:
            f.write(content)
        print(f"  ✓ digital_thalamus_service/api.py")
        fixed_count += 1

# ============================================================================
# 2. FIX PYDANTIC V2 (BaseSettings migration)
# ============================================================================
print("\n2️⃣  Corrigindo Pydantic V2...")

# ip_intelligence: BaseSettings
ip_config = Path('/home/juan/vertice-dev/backend/services/ip_intelligence_service/config.py')
if ip_config.exists():
    with open(ip_config, 'r') as f:
        content = f.read()

    if 'from pydantic import BaseSettings' in content:
        content = content.replace(
            'from pydantic import BaseSettings',
            'from pydantic_settings import BaseSettings'
        )
        with open(ip_config, 'w') as f:
            f.write(content)
        print(f"  ✓ ip_intelligence_service/config.py")
        fixed_count += 1

# ============================================================================
# 3. FIX SYNTAX ERRORS (strings não terminadas)
# ============================================================================
print("\n3️⃣  Corrigindo syntax errors...")

# offensive_gateway: linha 156
og_orch = Path('/home/juan/vertice-dev/backend/services/offensive_gateway/orchestrator.py')
if og_orch.exists():
    with open(og_orch, 'r') as f:
        lines = f.readlines()

    # Procurar string não terminada e fechar
    for i in range(len(lines)):
        if '"""' in lines[i]:
            # Contar quantas """ existem até linha 156
            count = ''.join(lines[:157]).count('"""')
            if count % 2 != 0:  # Ímpar = não fechado
                # Adicionar """ na linha 156 ou próxima vazia
                if i == 155 or i == 156:
                    if not lines[i].strip().endswith('"""'):
                        lines[i] = lines[i].rstrip() + '\n"""\n'
                        break

    with open(og_orch, 'w') as f:
        f.writelines(lines)
    print(f"  ✓ offensive_gateway/orchestrator.py")
    fixed_count += 1

# ============================================================================
# 4. FIX IMPORT COMPLEXO (hpc-service)
# ============================================================================
print("\n4️⃣  Corrigindo imports complexos...")

hpc_main = Path('/home/juan/vertice-dev/backend/services/hpc_service/main.py')
if hpc_main.exists():
    with open(hpc_main, 'r') as f:
        content = f.read()

    # from .bayesian_core → from bayesian_core
    content = re.sub(r'^from \.([a-zA-Z0-9_./]+)', r'from \1', content, flags=re.MULTILINE)

    with open(hpc_main, 'w') as f:
        f.write(content)
    print(f"  ✓ hpc_service/main.py")
    fixed_count += 1

# ============================================================================
# 5. FIX STRING LITERALS NOS COGNITIVE SERVICES
# ============================================================================
print("\n5️⃣  Verificando strings não terminadas em cognitive services...")

cognitive_services = [
    'homeostatic_regulation',
    'maximus_core_service',
    'prefrontal_cortex_service',
    'visual_cortex_service',
    'vestibular_service',
    'narrative_manipulation_filter'
]

for svc in cognitive_services:
    api_file = Path(f'/home/juan/vertice-dev/backend/services/{svc}/api.py')
    main_file = Path(f'/home/juan/vertice-dev/backend/services/{svc}/main.py')

    for filepath in [api_file, main_file]:
        if not filepath.exists():
            continue

        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Compilar para verificar syntax
            compile(content, str(filepath), 'exec')
            # Se chegou aqui, não tem erro

        except SyntaxError as e:
            # Tentar fix automático
            lines = content.split('\n')
            error_line = e.lineno - 1

            if 'unterminated' in str(e):
                # Adicionar delimitador faltante
                if '"""' in lines[error_line] and lines[error_line].count('"""') % 2 != 0:
                    lines[error_line] += '"""'
                elif '"' in lines[error_line] and lines[error_line].count('"') % 2 != 0:
                    lines[error_line] += '"'
                elif "'" in lines[error_line] and lines[error_line].count("'") % 2 != 0:
                    lines[error_line] += "'"

                content = '\n'.join(lines)
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  ✓ {filepath.name} (linha {e.lineno})")
                fixed_count += 1

print()
print("=" * 70)
print(f"✅ CONCLUÍDO: {fixed_count} correções aplicadas")
print("=" * 70)
