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

# Importa TODAS as nossas ferramentas do canivete suíço
from utils import console, print_panel, thinking_stream, collect_files, exibir_banner

# Carrega as variáveis de ambiente
load_dotenv()

# Configura a API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    console.print(f"🚨 [bold red]Erro ao configurar a API Gemini:[/bold red] {e}")
    raise typer.Exit()

app = typer.Typer(help="CLI para automação de desenvolvimento do Projeto VÉRTICE, com a IA Gemini.")


def carregar_prompt_oraculo(codigo_base: str) -> str:
    """Carrega o prompt base do Oráculo."""
    return f"""
Você é um engenheiro de software sênior especialista em projetos CLI e refatoração.
Analise o seguinte projeto (amostra de arquivos abaixo) e gere uma lista de ideias técnicas para:
- Refatoração e robustez
- Novas funcionalidades úteis
- Melhorias de UX e CLI
- Estruturação de logs, backups e rollback
- Sugestões criativas

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
def eureka(root_path: str = typer.Argument(".", help="O caminho do projeto a ser analisado pelo Eureka.")):
    """Executa uma análise profunda de código em busca de riscos e melhorias."""
    console.clear()
    exibir_banner()
    
    try:
        resolved_path = Path(root_path).resolve()
        thinking_stream([
            "🔄 Inicializando subsistemas de análise...",
            "🧬 Ajustando sensibilidade dos heurísticos...",
            "🕵️ Carregando perfil de engenharia de segurança..."
        ])

        console.print(f"[cyan]🔍 Coletando arquivos em '{resolved_path.name}' para análise profunda...[/cyan]")
        arquivos = collect_files(str(resolved_path))
        
        if not arquivos:
            console.print("⚠️ [yellow]Nenhum arquivo de código relevante encontrado para análise.[/yellow]")
            raise typer.Exit()
        
        console.print(f"[green]✅ {len(arquivos)} arquivos encontrados.[/green]\n")

        codigo_base = []
        for file in arquivos:
            try:
                content = file.read_text(encoding='utf-8')
                codigo_base.append(f"# Arquivo: {file.relative_to(resolved_path)}\n\n{content[:2000]}...")
            except Exception:
                continue
        
        prompt_final = carregar_prompt_eureka("\n\n---\n\n".join(codigo_base))

        resposta = ""
        with console.status("[bold blue]Eureka analisando o código-fonte...[/bold blue]", spinner="dots"):
            response = model.generate_content(prompt_final)
            resposta = response.text

        print_panel(resposta, title="[green]📊 Análise do Eureka Engine[/green]", color="green")
        
        log_path = Path(os.path.expanduser("~")) / f"vertice_eureka_log_{int(time.time())}.md"
        log_path.write_text(resposta, encoding='utf-8')
        console.print(f"💾 [dim]Log completo salvo em: {log_path}[/dim]\n")

        deseja_oraculo = questionary.confirm("Deseja invocar o Oráculo para gerar ideias criativas a partir desta análise?").ask()
        if deseja_oraculo:
            # Chama a função oraculo diretamente
            oraculo(root_path)

    except Exception as e:
        console.print(f"\n🚨 [bold red]Erro inesperado no Eureka Engine:[/bold red]\n→ {e}\n")
        raise typer.Exit()


@app.command()
def oraculo(root_path: str = typer.Argument(".", help="O caminho do projeto a ser analisado pelo Oráculo.")):
    """Invoca o Oráculo para gerar ideias e melhorias para o projeto."""
    console.clear()
    exibir_banner()

    try:
        resolved_path = Path(root_path).resolve()
        if not resolved_path.is_dir():
            console.print(f"🚨 [bold red]Erro: O caminho '{resolved_path}' não é um diretório válido.[/bold red]")
            raise typer.Exit()

        thinking_stream([
            "🧠 Invocando insights técnicos...",
            "💡 Gerando ideias criativas para o projeto...",
            "⏳ Aguardando inspiração da IA..."
        ])

        console.print(f"[cyan]🔍 Coletando arquivos em '{resolved_path.name}' para contexto...[/cyan]")
        arquivos = collect_files(str(resolved_path))
        
        if not arquivos:
            console.print("⚠️ [yellow]Nenhum arquivo de código relevante encontrado para análise.[/yellow]")
            raise typer.Exit()
            
        console.print(f"[green]✅ {len(arquivos)} arquivos encontrados.[/green]\n")

        codigo_base = []
        for file in arquivos:
            try:
                content = file.read_text(encoding='utf-8')
                codigo_base.append(f"# Arquivo: {file.relative_to(resolved_path)}\n\n{content[:1000]}...")
            except Exception:
                continue
        
        prompt_final = carregar_prompt_oraculo("\n\n---\n\n".join(codigo_base))

        resposta = ""
        with console.status("[bold blue]Oráculo consultando as estrelas... (Isso pode levar um momento)[/bold blue]", spinner="dots"):
            response = model.generate_content(prompt_final)
            resposta = response.text

        print_panel(resposta, title="[magenta]💡 Ideias e Sugestões do Oráculo[/magenta]", color="magenta")
        
        log_path = Path(os.path.expanduser("~")) / f"vertice_oraculo_log_{int(time.time())}.md"
        log_path.write_text(resposta, encoding='utf-8')
        console.print(f"💾 [dim]Log completo salvo em: {log_path}[/dim]\n")

        exportar = questionary.confirm("Deseja exportar as ideias para um arquivo no projeto?").ask()
        if exportar:
            export_path_str = questionary.text(
                "Informe o caminho do arquivo:",
                default=f"./oraculo_ideias_{int(time.time())}.md"
            ).ask()
            if export_path_str:
                Path(export_path_str).write_text(resposta, encoding='utf-8')
                console.print(f"✅ [bold green]Ideias exportadas para: {export_path_str}[/bold green]")

    except Exception as e:
        console.print(f"\n🚨 [bold red]Erro inesperado no Oráculo:[/bold red]\n→ {e}\n")
        raise typer.Exit()


@app.command()
def review(file_path: Path = typer.Argument(..., help="O caminho para o arquivo a ser analisado.")):
    """Faz um code review de um arquivo e oferece para aplicar as sugestões de forma controlada."""
    console.clear()
    exibir_banner()
    console.print(f"🔎 Analisando o arquivo: {file_path}")

    if not file_path.is_file():
        console.print(f"🚨 [bold red]Erro: O arquivo '{file_path}' não foi encontrado.[/bold red]")
        raise typer.Exit()

    try:
        content = file_path.read_text(encoding='utf-8')
        prompt = f"""
        Como um engenheiro de software sênior, revise o código abaixo.
        Primeiro, forneça uma análise geral em texto.
        Depois, se houver sugestões de refatoração, forneça um bloco de código único
        no formato diff unificado (`diff -u`).
        O bloco de código do diff DEVE ser formatado exatamente assim:
        ```diff
        --- a/{file_path.name}
        +++ b/{file_path.name}
        @@ ... @@
        ... (conteúdo do diff) ...
        ```
        Arquivo: `{file_path.name}`
        ---
        ```python
        {content}
        ```
        ---
        Análise e Bloco de Diff:
        """
        resposta_completa = ""
        with console.status("[bold blue]Enviando para análise do Gemini Pro...[/bold blue]", spinner="dots"):
            response = model.generate_content(prompt)
            resposta_completa = response.text
        
        print_panel(resposta_completa, title=f"[cyan]Análise de {file_path.name}[/cyan]", color="cyan")

        diff_pattern = r"```diff\n(.*?)\n```"
        match = re.search(diff_pattern, resposta_completa, re.DOTALL)

        if match:
            diff_content = match.group(1).strip()
            console.print("\n[bold yellow]✨ Proposta de Refatoração Automática Encontrada:[/bold yellow]")
            
            diff_syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=True)
            console.print(diff_syntax)
            
            aplicar = questionary.confirm("Aplicar as alterações acima?").ask()

            if aplicar:
                patch_set = patch.from_string(diff_content.encode('utf-8'))
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                file_path.rename(backup_path)
                console.print(f"💾 [dim]Backup do arquivo original salvo em: {backup_path}[/dim]")
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f_in, open(file_path, 'w', encoding='utf-8') as f_out:
                         patch_set.apply(f_in, f_out)
                    console.print(f"✅ [bold green]Refatoração aplicada com sucesso em {file_path}![/bold green]")
                except Exception:
                    console.print("🚨 [bold red]Erro ao aplicar o patch. O arquivo original foi restaurado do backup.[/bold red]")
                    backup_path.rename(file_path)
        else:
            console.print("\n[bold blue]Nenhuma sugestão de refatoração automática foi encontrada na análise.[/bold blue]")

    except Exception as e:
        console.print(f"🚨 [bold red]Ocorreu um erro durante o processo:[/bold red] {e}")
        raise typer.Exit()


@app.command()
def lint(
    path: str = typer.Argument(".", help="O caminho do arquivo ou diretório para analisar."),
    fix: bool = typer.Option(False, "--fix", "-f", help="Tenta corrigir os problemas automaticamente.")
):
    """
    Executa a análise de código estática com o Ruff para encontrar e corrigir problemas.
    """
    console.clear()
    exibir_banner()
    console.print(f"🔎 Executando análise de código estática com Ruff em '[cyan]{path}[/cyan]'...")

    command = ["python3", "-m", "ruff", "check", path]
    if fix:
        command.append("--fix")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode != 0 and result.stdout:
            print_panel(result.stdout, title="[yellow]Problemas Encontrados[/yellow]", color="yellow")
            if not fix:
                console.print("\n💡 [bold]Dica:[/bold] Rode o comando com a flag `--fix` para tentar corrigir automaticamente.")
        elif result.stderr:
            print_panel(result.stderr, title="[red]Erro ao Executar o Ruff[/red]", color="red")
        else:
            print_panel("✅ Nenhum problema encontrado. O código está limpo!", title="[green]Resultado da Análise[/green]", color="green")
            
    except Exception as e:
        console.print(f"🚨 [bold red]Ocorreu um erro inesperado:[/bold red] {e}")


if __name__ == "__main__":
    app()
