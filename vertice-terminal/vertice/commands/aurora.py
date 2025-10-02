import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from typing_extensions import Annotated

# Importa os componentes da nossa arquitetura
from ..connectors.ai_agent import AIAgentConnector
from ..utils.output import output_json, print_error, print_success

# Cria a aplicação Typer para este módulo de comando
app = typer.Typer(
    name="aurora",
    help="🌌 Interaja com a Aurora, a IA central do ecossistema VÉRTICE.",
    rich_markup_mode="rich"
)

# Instância do console Rich para uma saída bonita
console = Console()

async def _execute_aurora_command(
    connector_method, 
    prompt: str, 
    json_output: bool, 
    spinner_text: str = "Aurora AI processando..."
):
    """Função auxiliar para executar comandos da Aurora de forma assíncrona com UX robusta."""
    connector = AIAgentConnector()
    try:
        with Live(Spinner("dots", text=f"[bold bright_magenta]{spinner_text}[/bold bright_magenta]"), console=console, transient=True, refresh_per_second=20):
            # 1. Verifica a saúde do serviço primeiro
            if not await connector.health_check():
                print_error(f"O serviço '{connector.service_name}' está offline ou inacessível em {connector.base_url}")
                raise typer.Exit(code=1)
            
            # 2. Executa o método do conector (ex: connector.query)
            response_data = await connector_method(prompt)

        # 3. Processa e exibe a resposta
        if response_data:
            if json_output:
                output_json(response_data)
            else:
                # Extrai a resposta principal para uma exibição mais limpa
                response_text = response_data.get('response', 'A resposta da Aurora não continha um campo "response".')
                console.print(Panel(response_text, title="[bold cyan]Aurora[/bold cyan]", border_style="cyan"))
                print_success("Análise concluída.")
        else:
            print_error("Não foi possível obter uma resposta da Aurora AI. A resposta foi vazia.")
            raise typer.Exit(code=1)

    except Exception as e:
        print_error(f"Ocorreu um erro inesperado: {e}")
        raise typer.Exit(code=1)
    finally:
        await connector.close()

@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="A pergunta ou prompt em linguagem natural para a Aurora AI.")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Exibir a saída bruta em formato JSON.")] = False
):
    """
    Faz uma pergunta direta para a Aurora AI.
    """
    connector = AIAgentConnector()
    asyncio.run(_execute_aurora_command(connector.query, question, json_output, spinner_text="Aurora AI pensando..."))

@app.command()
def analyze(
    context: Annotated[str, typer.Argument(help="O contexto (ex: logs, código, relatório) para a Aurora AI analisar.")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Exibir a saída bruta em formato JSON.")] = False
):
    """
    Envia um bloco de contexto para a Aurora AI analisar.
    """
    connector = AIAgentConnector()
    asyncio.run(_execute_aurora_command(connector.analyze, context, json_output, spinner_text="Aurora AI analisando contexto..."))

@app.command()
def investigate(
    incident: Annotated[str, typer.Argument(help="Detalhes de um incidente para a Aurora AI investigar.")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Exibir a saída bruta em formato JSON.")] = False
):
    """
    Inicia uma investigação de incidente com a Aurora AI.
    """
    connector = AIAgentConnector()
    asyncio.run(_execute_aurora_command(connector.investigate, incident, json_output, spinner_text="Aurora AI iniciando investigação..."))

# --- Placeholders do Blueprint ---

@app.command()
def chat():
    """Inicia um modo de chat interativo com a Aurora AI."""
    console.print("[yellow]Funcionalidade 'chat' em desenvolvimento. Consulte o blueprint para detalhes.[/yellow]")

@app.command()
def oraculo():
    """Invoca o Oráculo para auto-melhoria."""
    console.print("[yellow]Funcionalidade 'oraculo' em desenvolvimento. Consulte o blueprint para detalhes.[/yellow]")

@app.command()
def eureka(code_path: Annotated[str, typer.Argument(help="Caminho para o código a ser analisado.")]):
    """Analisa código em busca de riscos e melhorias com o Eureka."""
    console.print(f"[yellow]Funcionalidade 'eureka' para analisar '{code_path}' em desenvolvimento. Consulte o blueprint para detalhes.[/yellow]")
