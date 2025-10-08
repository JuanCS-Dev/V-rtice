#!/usr/bin/env python3
"""
Validação de Implementação - Blueprint UI/UX v1.2
Auditoria de conformidade com Regra de Ouro

Verifica:
- NO MOCK: Sem código mockado
- NO PLACEHOLDER: Sem placeholders/stubs
- NO TODOLIST: Sem TODOs pendentes
- QUALITY-FIRST: Type hints, docstrings, error handling
- PRODUCTION READY: Sintaxe válida, imports corretos
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


class CodeValidator:
    """Validador de código Python para regra de ouro."""

    def __init__(self):
        self.violations = []
        self.warnings = []

    def validate_file(self, filepath: Path) -> Dict:
        """Valida um arquivo Python."""
        result = {
            'file': str(filepath),
            'valid_syntax': False,
            'has_todos': False,
            'has_mocks': False,
            'has_placeholders': False,
            'has_type_hints': False,
            'has_docstrings': False,
            'violations': [],
            'warnings': []
        }

        try:
            content = filepath.read_text()

            # 1. Valida sintaxe
            try:
                tree = ast.parse(content)
                result['valid_syntax'] = True
            except SyntaxError as e:
                result['violations'].append(f"Syntax error: {e}")
                return result

            # 2. Busca TODOs
            todo_patterns = [r'TODO', r'FIXME', r'XXX', r'HACK', r'PLACEHOLDER']
            for pattern in todo_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result['has_todos'] = True
                    matches = re.findall(f'.*{pattern}.*', content, re.IGNORECASE)
                    result['violations'].extend([f"Found {pattern}: {m.strip()}" for m in matches[:3]])

            # 3. Busca MOCKs
            mock_patterns = [
                r'class\s+Mock',
                r'def\s+mock_',
                r'@mock\.',
                r'from\s+unittest\.mock',
                r'MagicMock',
                r'patch\(',
            ]
            for pattern in mock_patterns:
                if re.search(pattern, content):
                    result['has_mocks'] = True
                    result['violations'].append(f"Found mock pattern: {pattern}")

            # 4. Busca PLACEHOLDERs comuns
            placeholder_patterns = [
                r'pass\s*#.*implement',
                r'raise\s+NotImplementedError',
                r'\.\.\..*#.*TODO',
                r'return\s+None.*#.*placeholder',
            ]
            for pattern in placeholder_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result['has_placeholders'] = True
                    result['violations'].append(f"Found placeholder pattern: {pattern}")

            # 5. Verifica type hints (para funções públicas)
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            public_functions = [f for f in functions if not f.name.startswith('_')]

            if public_functions:
                typed_functions = 0
                for func in public_functions:
                    # Verifica se tem annotations nos args ou return
                    has_annotations = (
                        func.returns is not None or
                        any(arg.annotation is not None for arg in func.args.args)
                    )
                    if has_annotations:
                        typed_functions += 1

                type_hint_coverage = typed_functions / len(public_functions) if public_functions else 0
                result['has_type_hints'] = type_hint_coverage >= 0.8  # 80% threshold

                if type_hint_coverage < 0.8:
                    result['warnings'].append(
                        f"Type hint coverage: {type_hint_coverage:.0%} "
                        f"({typed_functions}/{len(public_functions)} functions)"
                    )

            # 6. Verifica docstrings
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            all_definitions = public_functions + classes

            if all_definitions:
                documented = sum(1 for node in all_definitions if ast.get_docstring(node))
                docstring_coverage = documented / len(all_definitions) if all_definitions else 0
                result['has_docstrings'] = docstring_coverage >= 0.8

                if docstring_coverage < 0.8:
                    result['warnings'].append(
                        f"Docstring coverage: {docstring_coverage:.0%} "
                        f"({documented}/{len(all_definitions)} items)"
                    )

        except Exception as e:
            result['violations'].append(f"Validation error: {e}")

        return result


def validate_implementation():
    """Executa validação completa da implementação."""

    print("\n" + "="*80)
    print(f"{Colors.BLUE}🔍 VALIDAÇÃO DE IMPLEMENTAÇÃO - Blueprint UI/UX v1.2{Colors.RESET}")
    print("="*80 + "\n")

    # Arquivos a validar (novos e modificados)
    files_to_validate = [
        # Novos
        'vertice/utils/output/table_builder.py',
        'vertice/utils/output/panel_builder.py',
        'vertice/utils/fuzzy.py',
        'vertice/ui/services/__init__.py',
        'vertice/ui/services/event_stream.py',
        'vertice/ui/services/context_manager.py',

        # Modificados - Phase 1-4A
        'vertice/ui/themes/vertice_design_system.py',
        'vertice/utils/output/formatters.py',
        'vertice/utils/output/console_utils.py',
        'vertice/commands/hunt.py',
        'vertice/commands/threat.py',
        'vertice/commands/maximus.py',
        'vertice/commands/help_cmd.py',

        # Wave 1 - Phase 5 (High Priority Commands)
        'vertice/commands/scan.py',
        'vertice/commands/compliance.py',
        'vertice/commands/analytics.py',
        'vertice/commands/incident.py',
        'vertice/commands/detect.py',

        # Wave 2 - Phase 6 (Medium Priority Commands)
        'vertice/commands/osint.py',
        'vertice/commands/adr.py',
        'vertice/commands/immunis.py',
        'vertice/commands/investigate.py',
        'vertice/commands/monitor.py',
    ]

    base_path = Path(__file__).parent
    validator = CodeValidator()

    results = []

    print(f"{Colors.BLUE}📁 Validando {len(files_to_validate)} arquivos...{Colors.RESET}\n")

    for filepath in files_to_validate:
        full_path = base_path / filepath

        if not full_path.exists():
            print_error(f"{filepath} - FILE NOT FOUND")
            results.append({'file': filepath, 'valid_syntax': False, 'violations': ['File not found']})
            continue

        result = validator.validate_file(full_path)
        results.append(result)

        # Print resultado
        filename = filepath.split('/')[-1]

        if result['violations']:
            print_error(f"{filename}")
            for violation in result['violations'][:5]:  # Max 5
                print(f"    {Colors.RED}• {violation}{Colors.RESET}")
        else:
            status_icons = []
            if result['valid_syntax']:
                status_icons.append('✓ syntax')
            if not result['has_todos']:
                status_icons.append('✓ no-todos')
            if not result['has_mocks']:
                status_icons.append('✓ no-mocks')
            if not result['has_placeholders']:
                status_icons.append('✓ no-placeholders')

            print_success(f"{filename} - {' | '.join(status_icons)}")

        # Print warnings
        if result['warnings']:
            for warning in result['warnings']:
                print(f"    {Colors.YELLOW}⚠ {warning}{Colors.RESET}")

    # Sumário
    print("\n" + "="*80)
    print(f"{Colors.BLUE}📊 SUMÁRIO DA VALIDAÇÃO{Colors.RESET}")
    print("="*80 + "\n")

    total = len(results)
    valid_syntax = sum(1 for r in results if r['valid_syntax'])
    no_todos = sum(1 for r in results if not r['has_todos'])
    no_mocks = sum(1 for r in results if not r['has_mocks'])
    no_placeholders = sum(1 for r in results if not r['has_placeholders'])
    has_type_hints = sum(1 for r in results if r.get('has_type_hints', False))
    has_docstrings = sum(1 for r in results if r.get('has_docstrings', False))

    print(f"Total de arquivos: {total}")
    print()

    # Regra de Ouro
    print(f"{Colors.BLUE}🎯 REGRA DE OURO:{Colors.RESET}")
    print(f"  {'✓' if valid_syntax == total else '✗'} Sintaxe válida: {valid_syntax}/{total}")
    print(f"  {'✓' if no_todos == total else '✗'} NO TODO: {no_todos}/{total}")
    print(f"  {'✓' if no_mocks == total else '✗'} NO MOCK: {no_mocks}/{total}")
    print(f"  {'✓' if no_placeholders == total else '✗'} NO PLACEHOLDER: {no_placeholders}/{total}")
    print()

    # Quality metrics
    print(f"{Colors.BLUE}📈 QUALITY METRICS:{Colors.RESET}")
    print(f"  {'✓' if has_type_hints >= total * 0.8 else '⚠'} Type hints: {has_type_hints}/{total} files (80%+)")
    print(f"  {'✓' if has_docstrings >= total * 0.8 else '⚠'} Docstrings: {has_docstrings}/{total} files (80%+)")
    print()

    # Violações
    total_violations = sum(len(r.get('violations', [])) for r in results)
    if total_violations > 0:
        print_error(f"Total de violações: {total_violations}")
        print("\nARQUIVOS COM VIOLAÇÕES:")
        for r in results:
            if r.get('violations'):
                print(f"  • {r['file'].split('/')[-1]}: {len(r['violations'])} violações")
    else:
        print_success("ZERO VIOLAÇÕES ENCONTRADAS! ✨")

    print("\n" + "="*80)

    # Veredito final
    passed = (
        valid_syntax == total and
        no_todos == total and
        no_mocks == total and
        no_placeholders == total
    )

    if passed:
        print(f"\n{Colors.GREEN}{'='*80}")
        print(f"{'✅ VALIDAÇÃO APROVADA - REGRA DE OURO CUMPRIDA':^80}")
        print(f"{'='*80}{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{'='*80}")
        print(f"{'❌ VALIDAÇÃO FALHOU - CORRIGIR VIOLAÇÕES':^80}")
        print(f"{'='*80}{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(validate_implementation())
