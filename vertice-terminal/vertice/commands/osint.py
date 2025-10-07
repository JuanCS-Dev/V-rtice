"""
🔎 OSINT Command - Open Source Intelligence
===========================================

OSINT operations via Maximus AI orchestration.

Commands:
    username - Social media profiling
    breach - Breach database lookup
    vehicle - SINESP vehicle query (Brazil)
    multi - Multi-source OSINT search
    comprehensive - Full OSINT investigation

Examples:
    vcli osint username johndoe --platforms twitter,linkedin
    vcli osint breach user@email.com
    vcli osint vehicle ABC1234
    vcli osint multi "target query"
"""

import typer
import asyncio
from rich.console import Console
from rich.markdown import Markdown
from typing_extensions import Annotated

from ..connectors.osint import OSINTConnector
from ..utils.output import output_json, print_error, print_success, PrimordialPanel
from ..utils.auth import require_auth
from vertice.utils import primoroso

app = typer.Typer(
    name="osint",
    help="🔎 Open Source Intelligence operations",
    rich_markup_mode="rich",
)

console = Console()


@app.command()
def username(
    username: Annotated[str, typer.Argument(help="Username to investigate")],
    platforms: Annotated[
        str,
        typer.Option("--platforms", "-p", help="Comma-separated platforms (default: all)")
    ] = None,
    json: Annotated[bool, typer.Option("--json", "-j", help="Output JSON")] = False,
):
    """
    Investigate username across social media platforms.

    Examples:
        vcli osint username johndoe
        vcli osint username janedoe --platforms "twitter,linkedin,github"
    """
    require_auth()

    async def _execute():
        connector = OSINTConnector()
        try:
            if not await connector.health_check():
                print_error("OSINT services offline")
                raise typer.Exit(1)

            platform_list = [p.strip() for p in platforms.split(",")] if platforms else None

            primoroso.info(f"[bold]Investigating username:[/bold] {username}")
            result = await connector.social_media_profiling(username, platform_list)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Social Media Profile: {username}",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("OSINT complete")
            else:
                print_error("No results")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def breach(
    identifier: Annotated[str, typer.Argument(help="Email, username, or phone")],
    type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: email, username, phone, domain")
    ] = "email",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Search breach databases.

    Examples:
        vcli osint breach user@example.com
        vcli osint breach johndoe --type username
    """
    require_auth()

    async def _execute():
        connector = OSINTConnector()
        try:
            primoroso.info(f"[bold]Searching breaches:[/bold] {identifier}")
            result = await connector.breach_data_lookup(identifier, type)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Breach Data: {identifier}",
                        console=console
                    )
                    panel.with_status("error").render()
                print_success("Search complete")
            else:
                print_error("No breaches found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def vehicle(
    plate: Annotated[str, typer.Argument(help="Vehicle plate (Brazilian format)")],
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Query SINESP vehicle database (Brazil).

    Examples:
        vcli osint vehicle ABC1234
    """
    require_auth()

    async def _execute():
        connector = OSINTConnector()
        try:
            primoroso.info(f"[bold]Querying SINESP:[/bold] {plate}")
            result = await connector.sinesp_vehicle_query(plate)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"Vehicle: {plate}",
                        console=console
                    )
                    panel.with_status("info").render()
                print_success("Query complete")
            else:
                print_error("Vehicle not found")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def multi(
    query: Annotated[str, typer.Argument(help="Search query")],
    search_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: all, people, organizations, domains")
    ] = "all",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Multi-source OSINT search.

    Examples:
        vcli osint multi "John Doe New York"
        vcli osint multi "Example Corp" --type organizations
    """
    require_auth()

    async def _execute():
        connector = OSINTConnector()
        try:
            primoroso.info(f"[bold]Multi-source search:[/bold] {query}")
            result = await connector.multi_source_search(query, search_type)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(str(result.get("result", result))),
                        title=f"OSINT Results: {query}",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("Search complete")
            else:
                print_error("No results")
        finally:
            await connector.close()

    asyncio.run(_execute())


@app.command()
def comprehensive(
    target: Annotated[str, typer.Argument(help="Target to investigate")],
    target_type: Annotated[
        str,
        typer.Option("--type", "-t", help="Type: auto, person, organization, domain, email")
    ] = "auto",
    json: Annotated[bool, typer.Option("--json", "-j")] = False,
):
    """
    Comprehensive OSINT investigation (Maximus orchestrated).

    Examples:
        vcli osint comprehensive example.com --type domain
        vcli osint comprehensive "John Doe" --type person
    """
    require_auth()

    async def _execute():
        connector = OSINTConnector()
        try:
            primoroso.info(f"[bold]Comprehensive OSINT:[/bold] {target}")
            result = await connector.comprehensive_osint(target, target_type)

            if result:
                if json:
                    output_json(result)
                else:
                    panel = PrimordialPanel(
                        Markdown(result.get("response", str(result))),
                        title=f"OSINT Report: {target}",
                        console=console
                    )
                    panel.with_status("success").render()
                print_success("Investigation complete")
            else:
                print_error("Investigation failed")
        finally:
            await connector.close()

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
