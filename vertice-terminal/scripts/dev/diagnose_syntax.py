#!/usr/bin/env python3
"""
🔍 Diagnóstico de Erros de Sintaxe - METODICO
"""
import py_compile
from pathlib import Path
from collections import defaultdict

def diagnose_file(file_path: Path) -> dict:
    """Diagnostica um arquivo e retorna info do erro"""
    try:
        py_compile.compile(str(file_path), doraise=True)
        return {"status": "ok", "file": file_path.name}
    except SyntaxError as e:
        return {
            "status": "error",
            "file": file_path.name,
            "line": e.lineno,
            "msg": e.msg,
            "text": e.text.strip() if e.text else ""
        }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path.name,
            "msg": str(e)
        }

def categorize_error(error: dict) -> str:
    """Categoriza tipo de erro baseado na mensagem"""
    msg = error.get("msg", "").lower()
    text = error.get("text", "").lower()

    if "'(' was never closed" in msg or "unmatched '('" in msg:
        if "panel(" in text:
            return "PANEL_NOT_CLOSED"
        return "PAREN_NOT_CLOSED"

    if "unmatched ')'" in msg:
        return "EXTRA_PAREN"

    if "invalid syntax" in msg and "[/" in text:
        return "RICH_TAG_IN_STRING"

    if "invalid syntax" in msg:
        return "GENERIC_SYNTAX"

    return "UNKNOWN"

def main():
    commands_dir = Path("vertice/commands")

    # Files to check
    files = sorted(commands_dir.glob("*.py"))
    files = [f for f in files if f.name not in ["__init__.py", "hunt_test.py"]]

    print("🔍 DIAGNÓSTICO DE SINTAXE\n")
    print(f"Analisando {len(files)} arquivos...\n")

    errors = []
    ok_count = 0

    for file_path in files:
        result = diagnose_file(file_path)

        if result["status"] == "ok":
            print(f"✅ {result['file']}")
            ok_count += 1
        else:
            print(f"❌ {result['file']}")
            errors.append(result)

    print(f"\n{'='*60}")
    print(f"📊 RESUMO: {ok_count} OK | {len(errors)} ERROS")
    print(f"{'='*60}\n")

    if errors:
        # Categorizar erros
        by_category = defaultdict(list)
        for err in errors:
            category = categorize_error(err)
            by_category[category].append(err)

        print("🏷️  ERROS POR CATEGORIA:\n")
        for category, errs in sorted(by_category.items()):
            print(f"  {category}: {len(errs)} arquivo(s)")
            for err in errs:
                line_info = f"(linha {err.get('line', '?')})" if err.get('line') else ""
                print(f"    • {err['file']} {line_info}")
                if err.get('text'):
                    print(f"      → {err['text'][:80]}")
            print()

        print(f"\n📋 DETALHES COMPLETOS:\n")
        for i, err in enumerate(errors, 1):
            print(f"{i}. {err['file']}")
            print(f"   Linha: {err.get('line', 'N/A')}")
            print(f"   Erro: {err.get('msg', 'N/A')}")
            if err.get('text'):
                print(f"   Código: {err['text'][:100]}")
            print()

if __name__ == "__main__":
    main()
