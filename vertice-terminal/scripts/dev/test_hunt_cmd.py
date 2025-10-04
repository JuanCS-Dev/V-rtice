"""
Threat Hunting Commands - PRODUCTION READY
Uses real threat_intel_service backend
"""

import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
from typing import Optional
from ..utils.output import print_json, spinner_task, print_error
from ..connectors.threat_intel import ThreatIntelConnector
from ..utils.decorators import with_connector

console = Console()

app = typer.Typer(
    name="hunt", help="🔎 Threat hunting operations", rich_markup_mode="rich"
)


@app.command()
@with_connector(ThreatIntelConnector)
async def search(
