#!/usr/bin/env python3
"""
Script para atualizar comandos com primoroso helpers - AUTOMÁTICO
"""
import re
from pathlib import Path

def upgrade_command_file(file_path: Path) -> bool:
    """Upgrade um arquivo de comando para usar primoroso helpers"""

    # Ler arquivo
    content = file_path.read_text()
    original = content

    # 1. Adicionar import (se não existir)
    if "from vertice.utils import primoroso" not in content:
        # Encontrar a última linha de import
        lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i

        # Inserir após último import
        if last_import_idx > 0:
            lines.insert(last_import_idx + 1, "from vertice.utils import primoroso")
            content = '\n'.join(lines)

    # 2. Substituir console.print com cores por helpers

    # Errors: [red]❌ ou [bold red]❌
    content = re.sub(
        r'console\.print\(f?["\'](\[(?:bold )?red\])?❌?\s*([^"\']+)["\'](?:,\s*style=["\'][^"\']+["\'])?\)',
        r'primoroso.error("\2")',
        content
    )

    # Success: [green]✅ ou [bold green]✅
    content = re.sub(
        r'console\.print\(f?["\'](\[(?:bold )?green\])?✅?\s*([^"\']+)["\'](?:,\s*style=["\'][^"\']+["\'])?\)',
        r'primoroso.success("\2")',
        content
    )

    # Warning: [yellow]⚠ ou [dim yellow]⚠
    content = re.sub(
        r'console\.print\(f?["\'](\[(?:dim )?yellow\])?⚠️?\s*([^"\']+)["\'](?:,\s*style=["\'][^"\']+["\'])?\)',
        r'primoroso.warning("\2")',
        content
    )

    # Info: [cyan]ℹ ou mensagens com [cyan]
    content = re.sub(
        r'console\.print\(f?["\'](\[cyan\])\s*([^"\']+?)\[/cyan\]["\'](?:,\s*style=["\'][^"\']+["\'])?\)',
        r'primoroso.info("\2")',
        content
    )

    # 3. Substituir padrões comuns de Panel de erro/sucesso
    content = re.sub(
        r'console\.print\(Panel\(\s*f?["\'](\[bold red\])?❌([^"\']+)["\'],\s*border_style=["\']red["\']',
        r'primoroso.error("\2"',
        content
    )

    content = re.sub(
        r'console\.print\(Panel\(\s*f?["\'](\[bold green\])?✅([^"\']+)["\'],\s*border_style=["\']green["\']',
        r'primoroso.success("\2"',
        content
    )

    # Se houve mudanças, salvar
    if content != original:
        file_path.write_text(content)
        return True

    return False


def main():
    commands_dir = Path("vertice/commands")

    # Arquivos para processar
    command_files = [
        "analytics.py", "ask.py", "compliance.py", "context.py",
        "detect.py", "dlp.py", "hunt.py", "incident.py",
        "malware.py", "monitor.py", "policy.py", "scan.py",
        "threat.py", "threat_intel.py", "ip.py", "maximus.py"
    ]

    upgraded = []
    skipped = []

    for file_name in command_files:
        file_path = commands_dir / file_name

        if not file_path.exists():
            print(f"⚠️  Não encontrado: {file_name}")
            skipped.append(file_name)
            continue

        try:
            if upgrade_command_file(file_path):
                print(f"✅ Upgraded: {file_name}")
                upgraded.append(file_name)
            else:
                print(f"⏭️  Sem mudanças: {file_name}")
                skipped.append(file_name)
        except Exception as e:
            print(f"❌ Erro em {file_name}: {e}")
            skipped.append(file_name)

    print(f"\n📊 Resumo:")
    print(f"  ✅ Upgraded: {len(upgraded)}")
    print(f"  ⏭️  Skipped: {len(skipped)}")
    print(f"\nUpgraded files: {', '.join(upgraded)}")


if __name__ == "__main__":
    main()
