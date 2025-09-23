# vertice_cli/cli.py

import os
import time
import typer
import google.generativeai as genai
import questionary
import patch
import re
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from utils import (
    console, print_panel, thinking_stream, collect_files, exibir_banner,
    print_success, print_warning, print_error, print_info, create_status_table,
    git_safe_execute
)

load_dotenv()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    print_error(f"Erro ao configurar a API Gemini: {e}")
    raise typer.Exit()

app = typer.Typer(
    help="🚀 CLI para automação de desenvolvimento do Projeto VÉRTICE, com a IA Gemini.",
    rich_markup_mode="rich"
)

def carregar_prompt_oraculo(codigo_base: str) -> str:
    """Carrega o prompt base do Oráculo."""
    return f"""
Você é um engenheiro de software sênior especialista em projetos CLI e refatoração.
Analise o seguinte projeto (amostra de arquivos abaixo) e gere uma lista de ideias técnicas para:
- Refatoração e robustez, Novas funcionalidades úteis, Melhorias de UX e CLI
- Estruturação de logs, backups e rollback, Sugestões criativas
Para cada ideia, explique: O que é, Por que é relevante, Impacto esperado, Dificuldade.
Código base do projeto:
---
{codigo_base}
---
""".strip()

def carregar_prompt_eureka(codigo_base: str) -> str:
    """Carrega o prompt base do Eureka."""
    return f"""
Você é um engenheiro de segurança e migração de sistemas sênior.
Analise os arquivos abaixo, identifique oportunidades de melhoria, riscos de segurança e pontos frágeis.
Sugira melhorias com base nas melhores práticas para projetos CLI robustos e seguros.
Para cada ponto, seja claro e direto.
Arquivos para análise:
---
{codigo_base}
---
""".strip()

@app.command()
def eureka(root_path: str = typer.Argument(".", help="🔬 O caminho do projeto a ser analisado pelo Eureka.")):
    """🔬 Executa uma análise profunda de código em busca de riscos e melhorias."""
    exibir_banner()
    try:
        resolved_path = Path(root_path).resolve()
        thinking_stream(["🔬 Inicializando...", "🧬 Ajustando heurísticos...", "🕵️ Carregando perfil de segurança..."], delay=0.6)
        print_info(f"Coletando arquivos em '{resolved_path.name}' para análise profunda...")
        arquivos = collect_files(str(resolved_path))
        if not arquivos:
            print_warning("Nenhum arquivo de código relevante encontrado para análise.")
            raise typer.Exit()
        print_success(f"{len(arquivos)} arquivos encontrados para análise.\n")
        status_data = {
            "📁 Arquivos Python": {"status": "✅ Detectado", "details": f"{len([f for f in arquivos if f.suffix == '.py'])}"},
            "📄 Arquivos Config": {"status": "✅ Detectado", "details": f"{len([f for f in arquivos if f.suffix in ['.toml', '.yaml', '.json']])}"},
            "📝 Documentação": {"status": "✅ Detectado", "details": f"{len([f for f in arquivos if f.suffix == '.md'])}"}
        }
        console.print(create_status_table(status_data))
        console.print()
        codigo_base = []
        for file in arquivos:
            try:
                content = file.read_text(encoding='utf-8')
                codigo_base.append(f"# Arquivo: {file.relative_to(resolved_path)}\n\n{content[:2000]}...")
            except Exception:
                continue
        prompt_final = carregar_prompt_eureka("\n\n---\n\n".join(codigo_base))
        resposta = ""
        with Progress(SpinnerColumn("earth", style="bright_green"), TextColumn("[bold bright_cyan]🔬 Eureka Engine processando..."), TimeElapsedColumn()) as progress:
            progress.add_task("Analisando...", total=None)
            response = model.generate_content(prompt_final)
            resposta = response.text
        print_panel(resposta, title="Análise do Eureka Engine", color="green")
        log_path = Path(os.path.expanduser("~")) / f"vertice_eureka_log_{int(time.time())}.md"
        log_path.write_text(resposta, encoding='utf-8')
        print_info(f"Log completo salvo em: {log_path}")
        console.print()
        deseja_oraculo = questionary.confirm("🔮 Deseja invocar o Oráculo para ideias criativas a partir desta análise?", ...).ask()
        if deseja_oraculo:
            oraculo(root_path)
    except Exception as e:
        print_error(f"Erro inesperado no Eureka Engine: {e}")
        raise typer.Exit()

@app.command()
def oraculo(root_path: str = typer.Argument(".", help="🔮 O caminho do projeto a ser analisado pelo Oráculo.")):
    """🔮 Invoca o Oráculo para gerar ideias e melhorias para o projeto."""
    exibir_banner()
    try:
        resolved_path = Path(root_path).resolve()
        thinking_stream(["🔮 Conectando...", "🧠 Invocando insights...", "💡 Canalizando inspiração..."], delay=0.7)
        print_info(f"Coletando arquivos em '{resolved_path.name}' para contexto...")
        arquivos = collect_files(str(resolved_path))
        if not arquivos:
            print_warning("Nenhum arquivo de código relevante encontrado para análise.")
            raise typer.Exit()
        print_success(f"{len(arquivos)} arquivos encontrados.\n")
        codigo_base = []
        for file in arquivos:
            try:
                content = file.read_text(encoding='utf-8')
                codigo_base.append(f"# Arquivo: {file.relative_to(resolved_path)}\n\n{content[:1000]}...")
            except Exception:
                continue
        prompt_final = carregar_prompt_oraculo("\n\n---\n\n".join(codigo_base))
        resposta = ""
        with Progress(SpinnerColumn("moon", style="bright_magenta"), TextColumn("[bold bright_magenta]🔮 Oráculo consultando as estrelas..."), TimeElapsedColumn()) as progress:
            progress.add_task("Consultando...", total=None)
            response = model.generate_content(prompt_final)
            resposta = response.text
        print_panel(resposta, title="Ideias e Sugestões do Oráculo", color="magenta")
        log_path = Path(os.path.expanduser("~")) / f"vertice_oraculo_log_{int(time.time())}.md"
        log_path.write_text(resposta, encoding='utf-8')
        print_info(f"Log completo salvo em: {log_path}")
        console.print()
        exportar = questionary.confirm("📤 Deseja exportar as ideias para um arquivo no projeto?", ...).ask()
        if exportar:
            export_path_str = questionary.text("📁 Informe o caminho do arquivo:", ...).ask()
            if export_path_str:
                Path(export_path_str).write_text(resposta, encoding='utf-8')
                print_success(f"Ideias exportadas para: {export_path_str}")
    except Exception as e:
        print_error(f"Erro inesperado no Oráculo: {e}")
        raise typer.Exit()

@app.command()
def review(file_path: Path = typer.Argument(..., help="📝 O caminho para o arquivo a ser analisado.")):
    """📝 Faz um code review de um arquivo e oferece para aplicar as sugestões de forma controlada."""
    exibir_banner()
    print_info(f"Analisando o arquivo: {file_path}")
    if not file_path.is_file():
        print_error(f"O arquivo '{file_path}' não foi encontrado.")
        raise typer.Exit()
    try:
        content = file_path.read_text(encoding='utf-8')
        prompt = f"""
        Como um engenheiro de software sênior...
        (O resto do prompt do review continua aqui)
        """.strip()
        resposta_completa = ""
        with Progress(SpinnerColumn("clock", style="bright_cyan"), TextColumn("[bold bright_cyan]📝 Enviando para análise..."), TimeElapsedColumn()) as progress:
            progress.add_task("Analisando...", total=None)
            response = model.generate_content(prompt)
            resposta_completa = response.text
        print_panel(resposta_completa, title=f"Análise de {file_path.name}", color="cyan")
        diff_pattern = r"```diff\n(.*?)\n```"
        match = re.search(diff_pattern, resposta_completa, re.DOTALL)
        if match:
            diff_content = match.group(1).strip()
            console.print("\n[bold yellow]✨ Proposta de Refatoração Encontrada:[/bold yellow]")
            console.print(Syntax(diff_content, "diff", theme="monokai", line_numbers=True))
            console.print()
            aplicar = questionary.confirm("⚡ Aplicar as alterações acima?", ...).ask()
            if aplicar:
                def apply_review_patch():
                    try:
                        patch_set = patch.from_string(diff_content.encode('utf-8'))
                        with open(file_path, 'rb+') as f:
                            patch_set.apply(f)
                        print_success(f"Patch aplicado temporariamente em {file_path}")
                        return True
                    except Exception as e:
                        print_error(f"Erro ao aplicar o patch: {e}")
                        return False
                git_safe_execute(apply_review_patch, file_path.parent.resolve(), "review --apply")
        else:
            print_info("Nenhuma sugestão de refatoração automática foi encontrada.")
    except Exception as e:
        print_error(f"Ocorreu um erro durante o processo: {e}")
        raise typer.Exit()

@app.command()
def lint(
    path: str = typer.Argument(".", help="🔍 O caminho para analisar."),
    fix: bool = typer.Option(False, "--fix", "-f", help="🔧 Tenta corrigir os problemas automaticamente.")
):
    """🔍 Executa a análise de código estática com o Ruff."""
    exibir_banner()
    print_info(f"Executando Ruff em '[bright_cyan]{path}[/bright_cyan]'...")
    check_command = ["python3", "-m", "ruff", "check", path]
    result = subprocess.run(check_command, capture_output=True, text=True, check=False)
    has_problems = result.returncode != 0 and result.stdout
    if has_problems:
        print_panel(result.stdout, title="Problemas Encontrados", color="yellow")
    elif result.stderr:
        print_panel(result.stderr, title="Erro ao Executar o Ruff", color="red")
        return
    else:
        print_success("Nenhum problema encontrado. O código está limpo!")
        return
    if fix and has_problems:
        def apply_lint_fix():
            fix_command = ["python3", "-m", "ruff", "check", path, "--fix", "--exit-zero"]
            fix_result = subprocess.run(fix_command, capture_output=True, text=True)
            if fix_result.stderr:
                print_panel(fix_result.stderr, title="Erro ao Aplicar Correções", color="red")
                return False
            print_info("Ruff --fix aplicado temporariamente.")
            return True
        git_safe_execute(apply_lint_fix, Path(path).resolve(), "lint --fix")
    elif not has_problems and fix:
        print_info("Nenhum problema encontrado para corrigir.")
    else:
        print_info("Dica: Rode o comando com a flag `--fix` para tentar corrigir automaticamente.")

if __name__ == "__main__":
    app()
