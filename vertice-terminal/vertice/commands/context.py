"""
Comando para gerenciamento de contextos de engajamento
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from vertice.config.context_manager import get_context_manager, ContextError
from vertice.utils.output import print_error, print_success, print_info, print_warning

app = typer.Typer(help="🎯 Gerenciamento de contextos de engajamento")
console = Console()


# Helper functions para formatação inline
def format_error(msg: str) -> str:
    return f"[red]{msg}[/red]"


def format_success(msg: str) -> str:
    return f"[green]{msg}[/green]"


def format_info(msg: str) -> str:
    return f"[blue]{msg}[/blue]"


def format_warning(msg: str) -> str:
    return f"[yellow]{msg}[/yellow]"


@app.command("create")
def create_context(
    name: str = typer.Argument(..., help="Nome do contexto (ex: pentest-acme)"),
    target: str = typer.Option(..., "--target", "-t", help="Alvo do engagement (IP, range, domain)"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Diretório de output personalizado"),
    proxy: Optional[str] = typer.Option(None, "--proxy", "-p", help="Proxy HTTP (ex: http://127.0.0.1:8080)"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notas sobre o engagement"),
    no_auto_use: bool = typer.Option(False, "--no-auto-use", help="Não ativar automaticamente após criar")
):
    """
    Cria um novo contexto de engajamento

    Exemplo:
        vertice context create pentest-acme --target 10.0.0.0/24 --proxy http://127.0.0.1:8080
    """
    try:
        ctx_manager = get_context_manager()
        context = ctx_manager.create(
            name=name,
            target=target,
            output_dir=output_dir,
            proxy=proxy,
            notes=notes,
            auto_use=not no_auto_use
        )

        console.print(format_success(f"✓ Contexto '{name}' criado com sucesso!"))
        console.print()

        # Mostrar detalhes do contexto criado
        table = Table(title=f"📋 Contexto: {name}", box=box.ROUNDED, show_header=False)
        table.add_column("Campo", style="cyan bold")
        table.add_column("Valor", style="white")

        table.add_row("🎯 Target", context.target)
        table.add_row("📁 Output Dir", context.output_dir)
        if context.proxy:
            table.add_row("🌐 Proxy", context.proxy)
        if context.notes:
            table.add_row("📝 Notes", context.notes)
        table.add_row("🕒 Created", context.created_at)

        console.print(table)
        console.print()

        if not no_auto_use:
            console.print(format_info(f"✓ Contexto '{name}' está ativo agora"))
        else:
            console.print(format_info(f"💡 Para ativar: vertice context use {name}"))

        console.print()
        console.print(format_info("📂 Estrutura criada:"))
        console.print(f"  {context.output_dir}/")
        console.print("    ├── scans/")
        console.print("    ├── recon/")
        console.print("    ├── exploits/")
        console.print("    ├── loot/")
        console.print("    └── reports/")

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("list")
def list_contexts():
    """
    Lista todos os contextos disponíveis

    Exemplo:
        vertice context list
    """
    try:
        ctx_manager = get_context_manager()
        contexts = ctx_manager.list()
        current_name = ctx_manager.get_current_name()

        if not contexts:
            console.print(format_warning("⚠ Nenhum contexto criado ainda"))
            console.print(format_info("💡 Crie um: vertice context create <name> --target <target>"))
            return

        table = Table(title="🎯 Contextos de Engajamento", box=box.ROUNDED)
        table.add_column("Status", justify="center", style="bold", width=6)
        table.add_column("Nome", style="cyan bold")
        table.add_column("Target", style="yellow")
        table.add_column("Output Dir", style="blue")
        table.add_column("Proxy", style="magenta")
        table.add_column("Created", style="green")

        for ctx in sorted(contexts, key=lambda c: c.created_at, reverse=True):
            is_current = ctx.name == current_name
            status = "✓" if is_current else ""
            status_style = "green bold" if is_current else ""

            table.add_row(
                f"[{status_style}]{status}[/{status_style}]",
                f"[bold]{ctx.name}[/bold]" if is_current else ctx.name,
                ctx.target,
                ctx.output_dir,
                ctx.proxy or "-",
                ctx.created_at.split('T')[0]
            )

        console.print(table)
        console.print()

        if current_name:
            console.print(format_success(f"✓ Contexto ativo: {current_name}"))
        else:
            console.print(format_warning("⚠ Nenhum contexto ativo"))
            console.print(format_info("💡 Ative um: vertice context use <name>"))

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("use")
def use_context(
    name: str = typer.Argument(..., help="Nome do contexto para ativar")
):
    """
    Ativa um contexto existente

    Exemplo:
        vertice context use pentest-acme
    """
    try:
        ctx_manager = get_context_manager()
        ctx_manager.use(name)

        context = ctx_manager.get(name)

        console.print(format_success(f"✓ Contexto '{name}' ativado!"))
        console.print()

        # Mostrar detalhes
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

        table.add_row("🎯 Target", context.target)
        table.add_row("📁 Output", context.output_dir)
        if context.proxy:
            table.add_row("🌐 Proxy", context.proxy)

        console.print(table)

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("current")
def show_current():
    """
    Mostra o contexto ativo atual

    Exemplo:
        vertice context current
    """
    try:
        ctx_manager = get_context_manager()
        current = ctx_manager.get_current()

        if current is None:
            console.print(format_warning("⚠ Nenhum contexto ativo"))
            console.print(format_info("💡 Crie um: vertice context create <name> --target <target>"))
            console.print(format_info("💡 Ou ative um existente: vertice context use <name>"))
            return

        # Panel com informações do contexto
        info_lines = [
            f"[cyan bold]Nome:[/cyan bold] {current.name}",
            f"[yellow bold]Target:[/yellow bold] {current.target}",
            f"[blue bold]Output Dir:[/blue bold] {current.output_dir}",
        ]

        if current.proxy:
            info_lines.append(f"[magenta bold]Proxy:[/magenta bold] {current.proxy}")

        if current.notes:
            info_lines.append(f"[white bold]Notes:[/white bold] {current.notes}")

        info_lines.extend([
            f"[green bold]Created:[/green bold] {current.created_at}",
            f"[green bold]Updated:[/green bold] {current.updated_at}",
        ])

        panel = Panel(
            "\n".join(info_lines),
            title=f"🎯 Contexto Ativo: {current.name}",
            border_style="green",
            box=box.ROUNDED
        )

        console.print(panel)

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("delete")
def delete_context(
    name: str = typer.Argument(..., help="Nome do contexto para deletar"),
    delete_files: bool = typer.Option(False, "--delete-files", "-f", help="Deletar também os arquivos do output_dir"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirmar sem perguntar")
):
    """
    Deleta um contexto

    Exemplo:
        vertice context delete old-project
        vertice context delete old-project --delete-files --yes
    """
    try:
        ctx_manager = get_context_manager()
        context = ctx_manager.get(name)

        if context is None:
            console.print(format_error(f"✗ Contexto '{name}' não existe"))
            raise typer.Exit(1)

        # Confirmação
        if not yes:
            console.print(format_warning(f"⚠ Você está prestes a deletar o contexto '{name}'"))
            if delete_files:
                console.print(format_error(f"⚠ ATENÇÃO: Os arquivos em {context.output_dir} serão PERMANENTEMENTE deletados!"))

            confirm = typer.confirm("Tem certeza?")
            if not confirm:
                console.print(format_info("✓ Operação cancelada"))
                return

        ctx_manager.delete(name, delete_files=delete_files)

        console.print(format_success(f"✓ Contexto '{name}' deletado com sucesso"))

        if delete_files:
            console.print(format_info(f"✓ Arquivos deletados: {context.output_dir}"))

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("update")
def update_context(
    name: str = typer.Argument(..., help="Nome do contexto para atualizar"),
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Novo target"),
    proxy: Optional[str] = typer.Option(None, "--proxy", "-p", help="Novo proxy"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Novas notas")
):
    """
    Atualiza informações de um contexto

    Exemplo:
        vertice context update pentest-acme --target 10.0.0.0/16
        vertice context update pentest-acme --notes "Fase 2: Post-exploitation"
    """
    try:
        if all(v is None for v in [target, proxy, notes]):
            console.print(format_error("✗ Nenhum campo para atualizar fornecido"))
            console.print(format_info("💡 Use --target, --proxy ou --notes"))
            raise typer.Exit(1)

        ctx_manager = get_context_manager()
        ctx_manager.update(
            name=name,
            target=target,
            proxy=proxy,
            notes=notes
        )

        console.print(format_success(f"✓ Contexto '{name}' atualizado com sucesso"))

        # Mostrar contexto atualizado
        context = ctx_manager.get(name)
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

        table.add_row("🎯 Target", context.target)
        if context.proxy:
            table.add_row("🌐 Proxy", context.proxy)
        if context.notes:
            table.add_row("📝 Notes", context.notes)
        table.add_row("🕒 Updated", context.updated_at)

        console.print(table)

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


@app.command("info")
def context_info(
    name: Optional[str] = typer.Argument(None, help="Nome do contexto (usa o atual se não fornecido)")
):
    """
    Mostra informações detalhadas de um contexto

    Exemplo:
        vertice context info
        vertice context info pentest-acme
    """
    try:
        ctx_manager = get_context_manager()

        if name is None:
            context = ctx_manager.get_current()
            if context is None:
                console.print(format_warning("⚠ Nenhum contexto ativo"))
                console.print(format_info("💡 Especifique um contexto: vertice context info <name>"))
                raise typer.Exit(1)
        else:
            context = ctx_manager.get(name)
            if context is None:
                console.print(format_error(f"✗ Contexto '{name}' não existe"))
                raise typer.Exit(1)

        # Panel com todas as informações
        info_lines = [
            f"[cyan bold]Nome:[/cyan bold] {context.name}",
            f"[yellow bold]Target:[/yellow bold] {context.target}",
            f"[blue bold]Output Dir:[/blue bold] {context.output_dir}",
        ]

        if context.proxy:
            info_lines.append(f"[magenta bold]Proxy:[/magenta bold] {context.proxy}")

        if context.notes:
            info_lines.append(f"[white bold]Notes:[/white bold] {context.notes}")

        info_lines.extend([
            "",
            f"[green bold]Created:[/green bold] {context.created_at}",
            f"[green bold]Updated:[/green bold] {context.updated_at}",
        ])

        if context.metadata:
            info_lines.append("")
            info_lines.append("[bold]Metadata:[/bold]")
            for key, value in context.metadata.items():
                info_lines.append(f"  {key}: {value}")

        panel = Panel(
            "\n".join(info_lines),
            title=f"📋 Informações do Contexto: {context.name}",
            border_style="blue",
            box=box.ROUNDED
        )

        console.print(panel)

        # Mostrar se é o contexto ativo
        current_name = ctx_manager.get_current_name()
        if current_name == context.name:
            console.print()
            console.print(format_success("✓ Este é o contexto ATIVO"))

    except ContextError as e:
        console.print(format_error(f"✗ Erro: {e}"))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
