import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.output import print_json, spinner_task, print_error, print_table
from ..utils.decorators import with_connector
from vertice.utils import primoroso

console = Console()

app = typer.Typer(
    name="threat", help="🛡️ Threat intelligence operations", rich_markup_mode="rich"
)


@app.command()
@with_connector(ThreatIntelConnector)
async def lookup(
    indicator: Annotated[
        str, typer.Argument(help="Threat indicator to lookup (IP, domain, hash)")
    ],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Lookup threat indicator.

    Example:
        vertice threat lookup malicious.com
    """
    if verbose:
        console.print(f"[dim]Looking up threat indicator: {indicator}...[/dim]")
    with spinner_task(f"Looking up threat indicator: {indicator}..."):
        result = await connector.lookup_threat(indicator)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.success(f"Threat Lookup Result for {indicator}:")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


@app.command()
@with_connector(ThreatIntelConnector)
async def check(
    target: Annotated[str, typer.Argument(help="Target to check for known threats")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Check a target for known threats.

    Example:
        vertice threat check malware.exe
    """
    if verbose:
        console.print(f"[dim]Checking target: {target}...[/dim]")
    with spinner_task(f"Checking target: {target}..."):
        result = await connector.lookup_threat(target)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.success(f"Threat Check Result for {target}:")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


@app.command()
@with_connector(ThreatIntelConnector)
async def scan(
    file_path: Annotated[str, typer.Argument(help="File path to scan for threats")],
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
    connector=None,
):
    """Scan a file for threats.

    Example:
        vertice threat scan /path/to/suspicious.zip
    """
    if verbose:
        console.print(f"[dim]Scanning file: {file_path}...[/dim]")
    with spinner_task(f"Scanning file: {file_path}..."):
        result = await connector.lookup_threat(file_path)

    if not result:
        return

    if json_output:
        print_json(result)
    else:
        primoroso.success(f"Threat Scan Result for {file_path}:")
        table_data = []
        for key, value in result.items():
            table_data.append({"Field": key, "Value": str(value)})
        print_table(table_data)


@app.command()
def feed(
    json_output: Annotated[
        bool, typer.Option("--json", "-j", help="Output as JSON")
    ] = False,
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Follow threat feed in real-time")
    ] = False,
):
    """Get threat intelligence feed.

    Example:
        vertice threat feed
        vertice threat feed --follow
    """
    # This command does not use a connector, so it is not refactored.
    primoroso.warning("Threat feed functionality coming soon...")
    if follow:
        console.print(
            "[dim]Real-time feed streaming will be available in next version.[/dim]"
        )
