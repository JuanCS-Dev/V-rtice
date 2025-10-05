"""
⚔️ OFFENSIVE Command - Offensive Security Arsenal
==================================================

Offensive security operations (authorized pentesting only).

Commands:
    recon - Network reconnaissance
    vuln - Vulnerability intelligence
    exploit - Exploit search
    web - Web attack simulation
    c2 - C2 infrastructure setup
    bas - Breach attack simulation

ATTENTION: For authorized pentesting and red team operations only.

Examples:
    vcli offensive recon 192.168.1.0/24 --type stealth
    vcli offensive vuln CVE-2021-44228
    vcli offensive web https://target.com/app
"""

import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.offensive import OffensiveConnector
from ..utils.output import output_json, print_error, print_success
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="offensive",
    help="⚔️ Offensive Security Arsenal (authorized use only)",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def recon(
    target: Annotated[str, typer.Argument(help="Target (IP, CIDR, hostname)")],
    scan_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: quick, full, stealth, aggressive")
    ] = "quick",
    ports: Annotated[
        str,
        typer.Option("--ports", "-p", help="Port range (e.g., 1-1000, 80,443)")
    ] = "1-1000",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Network reconnaissance (Masscan + Nmap).

    Examples:
        vcli offensive recon 192.168.1.0/24 --type stealth
        vcli offensive recon target.com --ports "1-65535"
    """
    require_auth()

    async def _execute():
        connector = OffensiveConnector()
        try:
            primoroso.warning("[bold red]⚔️  OFFENSIVE RECON[/bold red]")
            primoroso.info(f"[bold]Target:[/bold] {target}")
            result = await connector.network_recon(target, scan_type, ports)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[red]Recon: {target}[/red]",
                        border_style="red"
                    ))
                print_success("Recon complete")
            else:
                print_error("Recon failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def vuln(
    identifier: Annotated[str, typer.Argument(help="CVE ID, product, or vendor")],
    search_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: cve, product, vendor")
    ] = "cve",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Vulnerability intelligence search.

    Examples:
        vcli offensive vuln CVE-2021-44228
        vcli offensive vuln "Apache Log4j" --type product
    """
    require_auth()

    async def _execute():
        connector = OffensiveConnector()
        try:
            primoroso.info(f"[bold]Searching vulnerabilities:[/bold] {identifier}")
            result = await connector.vuln_intel_search(identifier, search_type)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[yellow]Vuln Intel: {identifier}[/yellow]",
                        border_style="yellow"
                    ))
                print_success("Search complete")
            else:
                print_error("Not found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def exploit(
    cve_id: Annotated[str, typer.Argument(help="CVE ID")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Search available exploits for CVE.

    Examples:
        vcli offensive exploit CVE-2021-44228
    """
    require_auth()

    async def _execute():
        connector = OffensiveConnector()
        try:
            primoroso.info(f"[bold]Searching exploits:[/bold] {cve_id}")
            result = await connector.exploit_search(cve_id)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[red]Exploits: {cve_id}[/red]",
                        border_style="red"
                    ))
                print_success("Search complete")
            else:
                print_error("No exploits found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def web(
    target_url: Annotated[str, typer.Argument(help="Target URL")],
    attacks: Annotated[
        str,
        typer.Option("--attacks", "-a", help="Comma-separated: xss,sqli,csrf,xxe,ssrf,lfi,rfi")
    ] = None,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Web attack simulation.

    Examples:
        vcli offensive web https://target.com/login --attacks "sqli,xss"
    """
    require_auth()

    async def _execute():
        connector = OffensiveConnector()
        try:
            primoroso.warning("[bold red]⚔️  WEB ATTACK SIMULATION[/bold red]")
            primoroso.info(f"[bold]Target:[/bold] {target_url}")

            attack_list = [a.strip() for a in attacks.split(",")] if attacks else None
            result = await connector.web_attack_simulate(target_url, attack_list)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[red]Web Attack: {target_url}[/red]",
                        border_style="red"
                    ))
                print_success("Simulation complete")
            else:
                print_error("Simulation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def bas(
    scenario: Annotated[str, typer.Argument(help="Scenario: ransomware, apt, insider")],
    target: Annotated[str, typer.Argument(help="Target host/network")],
    intensity: Annotated[
        str,
        typer.Option("--intensity", "-i", help="Intensity: low, medium, high")
    ] = "medium",
    duration: Annotated[
        int,
        typer.Option("--duration", "-d", help="Duration in minutes")
    ] = 30,
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Breach Attack Simulation (BAS).

    Examples:
        vcli offensive bas ransomware 192.168.1.100 --intensity high
        vcli offensive bas apt "example.com" --duration 60
    """
    require_auth()

    async def _execute():
        connector = OffensiveConnector()
        try:
            primoroso.warning("[bold red]⚔️  BREACH ATTACK SIMULATION[/bold red]")
            primoroso.info(f"[bold]Scenario:[/bold] {scenario}")
            primoroso.info(f"[bold]Target:[/bold] {target}")

            config = {"intensity": intensity, "duration_minutes": duration}
            result = await connector.bas_execute(scenario, target, config)

            if result:
                if json:
                    output_json(result)
                else:
                    console.print(Panel(
                        Markdown(str(result.get("result", result))),
                        title=f"[red]BAS: {scenario}[/red]",
                        border_style="red"
                    ))
                print_success("BAS complete")
            else:
                print_error("BAS failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
