#!/usr/bin/env python3
"""Generate release notes merging SBOM/vulnerability info."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

TEMPLATE_DEFAULT = Path(__file__).resolve().parent.parent / "docs" / "cGPT" / "session-03" / "thread-a" / "RELEASE_NOTES_TEMPLATE.md"


def load_template(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return TEMPLATE_DEFAULT.read_text()


def summarize_vulns(vuln_file: Path) -> str:
    if not vuln_file.exists():
        return "Nenhum relatório de vulnerabilidade encontrado."
    data = json.loads(vuln_file.read_text())
    counts = {}
    if isinstance(data, dict):
        matches = data.get("matches", [])
        for match in matches:
            severity = match.get("vulnerability", {}).get("severity", "UNKNOWN")
            counts[severity] = counts.get(severity, 0) + 1
    if not counts:
        return "Sem vulnerabilidades identificadas."
    items = [f"{severity}: {count}" for severity, count in sorted(counts.items())]
    return "; ".join(items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate release notes markdown.")
    parser.add_argument("--component", required=True)
    parser.add_argument("--version", default="0.0.0")
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--vuln", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=TEMPLATE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--owner", default="Release Team")
    args = parser.parse_args()

    template = load_template(args.template)
    content = template.replace("{{component}}", args.component)
    content = content.replace("{{version}}", args.version)
    content = content.replace("{{date}}", dt.datetime.utcnow().strftime("%Y-%m-%d"))
    content = content.replace("{{owner}}", args.owner)
    content = content.replace("{{sbom_path}}", str(args.sbom))
    content = content.replace("{{vuln_path}}", str(args.vuln))
    content = content.replace("{{signature_ref}}", "cosign://TODO")

    summary = summarize_vulns(args.vuln)
    content += f"\n## Resumo de Vulnerabilidades\n- {summary}\n"

    args.output.write_text(content)
    print(f"✅ Release notes geradas em {args.output}")


if __name__ == "__main__":
    main()
