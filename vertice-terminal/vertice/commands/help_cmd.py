#!/usr/bin/env python3
"""
Enhanced help system for vCLI.
UI/UX Blueprint v1.2 - Fuzzy search integrado

Provides interactive help, examples, fuzzy search, and man-page style documentation.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from typing import Optional, List, Tuple
import re
from ..utils.fuzzy import FuzzyMatcher, fuzzy_find
from ..utils.output import GeminiStyleTable, PrimordialPanel

app = typer.Typer(
    name="help",
    help="📚 Enhanced help system with examples and search",
    rich_markup_mode="rich"
)

console = Console()

# Command examples database
COMMAND_EXAMPLES = {
    "investigate": {
        "description": "🔍 AI-orchestrated investigation with autonomous tool selection",
        "examples": [
            {
                "desc": "Deep investigation of a suspicious domain",
                "cmd": "vcli investigate target suspicious-domain.com --type defensive --depth deep"
            },
            {
                "desc": "Multi-target investigation (parallel execution)",
                "cmd": "vcli investigate multi --targets domain1.com,domain2.com,192.168.1.1"
            },
            {
                "desc": "Find similar past investigations (semantic search)",
                "cmd": "vcli investigate similar \"ransomware attack on financial sector\""
            }
        ],
        "flags": {
            "--type": "Investigation type: defensive, offensive, forensics",
            "--depth": "Analysis depth: quick, normal, deep, comprehensive",
            "--output": "Output format: json, yaml, table, report"
        }
    },
    "osint": {
        "description": "🔎 Open Source Intelligence operations",
        "examples": [
            {
                "desc": "Social media profiling across multiple platforms",
                "cmd": "vcli osint username johndoe --platforms twitter,linkedin,github"
            },
            {
                "desc": "Breach data lookup for email addresses",
                "cmd": "vcli osint breach leaked-emails.txt"
            },
            {
                "desc": "SINESP vehicle query (Brazil)",
                "cmd": "vcli osint vehicle ABC1234"
            },
            {
                "desc": "Comprehensive OSINT investigation",
                "cmd": "vcli osint comprehensive johndoe@example.com --depth deep"
            }
        ],
        "flags": {
            "--platforms": "Social media platforms to search (comma-separated)",
            "--depth": "Investigation depth: quick, normal, deep",
            "--output": "Output format: json, table, report"
        }
    },
    "maximus": {
        "description": "🤖 Direct interface to Maximus AI reasoning engine",
        "examples": [
            {
                "desc": "Interactive chat with Maximus",
                "cmd": "vcli maximus chat \"How do I detect lateral movement?\""
            },
            {
                "desc": "List all available tools (57 total)",
                "cmd": "vcli maximus tools list"
            },
            {
                "desc": "Check Maximus status and health",
                "cmd": "vcli maximus status"
            }
        ],
        "flags": {
            "--tools": "Specify tools to use (comma-separated)",
            "--confidence": "Minimum confidence threshold (0.0-1.0)"
        }
    },
    "memory": {
        "description": "🧠 Memory system management (working, episodic, semantic)",
        "examples": [
            {
                "desc": "View memory system status",
                "cmd": "vcli memory status"
            },
            {
                "desc": "Recall information about a topic (semantic search)",
                "cmd": "vcli memory recall \"SQL injection attacks\""
            },
            {
                "desc": "Find similar past investigations",
                "cmd": "vcli memory similar --query \"phishing campaign\" --top 5"
            },
            {
                "desc": "View memory statistics",
                "cmd": "vcli memory stats"
            }
        ]
    },
    "offensive": {
        "description": "⚔️ Offensive security arsenal (AUTHORIZED USE ONLY)",
        "examples": [
            {
                "desc": "Network reconnaissance (stealth mode)",
                "cmd": "vcli offensive recon 192.168.1.0/24 --type stealth"
            },
            {
                "desc": "Vulnerability intelligence lookup",
                "cmd": "vcli offensive vuln CVE-2021-44228 --format detailed"
            },
            {
                "desc": "Web attack simulation (authorized pentest)",
                "cmd": "vcli offensive web https://test.example.com --attacks sqli,xss"
            }
        ],
        "warning": "⚠️  AUTHORIZED USE ONLY - Requires explicit written permission"
    },
    "immunis": {
        "description": "🛡️ AI Immune System with 7 specialized cells",
        "examples": [
            {
                "desc": "Check immune system status (all cells)",
                "cmd": "vcli immunis status"
            },
            {
                "desc": "Activate NK patrol (proactive defense)",
                "cmd": "vcli immunis patrol network --targets 192.168.1.0/24"
            },
            {
                "desc": "Trigger threat response (specific cell)",
                "cmd": "vcli immunis respond --threat-id TH-2025-001 --cell cytotoxic-t"
            }
        ],
        "cells": [
            "🔬 Macrophage - First responder, pathogen detection",
            "⚡ Neutrophil - Rapid response, neutralization",
            "📊 Dendritic - Threat analysis, pattern learning",
            "🧬 B-Cell - Antibody generation, signature creation",
            "🤝 Helper T - Coordination, immune response orchestration",
            "⚔️ Cytotoxic T - Targeted elimination, precision strikes",
            "👁️ NK Cell - Surveillance, anomaly detection"
        ]
    },
    "hunt": {
        "description": "🔎 Threat hunting with VeQL queries",
        "examples": [
            {
                "desc": "Hunt for specific IOCs across fleet",
                "cmd": "vcli hunt search --ioc 192.168.1.100 --type ip"
            },
            {
                "desc": "Execute pre-built artifact query",
                "cmd": "vcli hunt artifact suspicious-powershell"
            },
            {
                "desc": "VeQL query across all endpoints",
                "cmd": "vcli hunt query \"SELECT * FROM processes WHERE name LIKE '%cmd.exe'\""
            }
        ]
    },
    "scan": {
        "description": "🌐 Network scanning and enumeration",
        "examples": [
            {
                "desc": "Nmap scan with vulnerability scripts",
                "cmd": "vcli scan nmap 192.168.1.0/24 --script vuln"
            },
            {
                "desc": "Service detection and version fingerprinting",
                "cmd": "vcli scan service 192.168.1.100 --verbose"
            }
        ]
    },
    "malware": {
        "description": "🦠 Malware analysis and sandboxing",
        "examples": [
            {
                "desc": "Analyze suspicious file in sandbox",
                "cmd": "vcli malware analyze suspicious.exe --sandbox"
            },
            {
                "desc": "Bulk scan directory for malware",
                "cmd": "vcli malware scan /path/to/files --recursive"
            }
        ]
    },
    "hcl": {
        "description": "📝 Human-Centric Language for security workflows",
        "examples": [
            {
                "desc": "Generate execution plan from objective",
                "cmd": "vcli hcl plan \"Perform comprehensive security assessment of web app\""
            },
            {
                "desc": "Execute HCL workflow file",
                "cmd": "vcli hcl execute security_audit.hcl"
            },
            {
                "desc": "Analyze and validate HCL syntax",
                "cmd": "vcli hcl analyze workflow.hcl"
            }
        ]
    }
}

# All vCLI commands (for search)
ALL_COMMANDS = {
    "investigate": "AI-orchestrated investigation",
    "osint": "Open Source Intelligence",
    "maximus": "Maximus AI interface",
    "memory": "Memory system management",
    "offensive": "Offensive security arsenal",
    "immunis": "AI Immune System",
    "hunt": "Threat hunting",
    "scan": "Network scanning",
    "malware": "Malware analysis",
    "hcl": "Human-Centric Language",
    "cognitive": "Cognitive services (vision, audio, decision)",
    "distributed": "Distributed organism management",
    "adr": "Anomaly Detection & Response",
    "analytics": "Advanced analytics & ML",
    "incident": "Incident response & orchestration",
    "compliance": "Multi-framework compliance",
    "threat_intel": "Threat intelligence platform",
    "dlp": "Data Loss Prevention",
    "siem": "SIEM integration",
    "ip": "IP intelligence",
    "threat": "Threat intelligence",
    "monitor": "Network monitoring",
    "ask": "AI conversational engine",
    "policy": "Policy-as-Code",
    "detect": "Detection engine (YARA/Sigma)",
    "context": "Context management",
    "auth": "Authentication",
    "menu": "Interactive menu",
    "project": "Workspace & state management",
    "plugin": "Plugin management",
    "script": "VScript workflow automation",
    "tui": "Text UI Dashboard",
    "shell": "Interactive shell",
    "help": "Enhanced help system with examples and search"
}


@app.command(name="show")
def show_help(
    command: Optional[str] = typer.Argument(None, help="Command to show help for"),
    examples: bool = typer.Option(False, "--examples", "-e", help="Show only examples"),
):
    """
    📖 Show detailed help for a command with examples.

    Examples:
        vcli help show investigate
        vcli help show osint --examples
    """
    if not command:
        console.print("[yellow]Please specify a command. Try: vcli help list[/yellow]")
        raise typer.Exit(1)

    if command not in COMMAND_EXAMPLES:
        console.print(f"[yellow]No detailed help found for '{command}'[/yellow]")
        console.print(f"\nTry: [cyan]vcli {command} --help[/cyan] for basic help")
        raise typer.Exit(1)

    cmd_data = COMMAND_EXAMPLES[command]

    # Header
    console.print(Panel(
        f"[bold cyan]{command}[/bold cyan] - {cmd_data['description']}",
        title="📚 Command Help",
        border_style="cyan"
    ))

    # Warning if applicable
    if "warning" in cmd_data:
        console.print(f"\n[bold red]{cmd_data['warning']}[/bold red]\n")

    # Examples
    if cmd_data.get("examples"):
        console.print("\n[bold]📝 Examples:[/bold]\n")
        for i, example in enumerate(cmd_data["examples"], 1):
            console.print(f"[dim]{i}. {example['desc']}[/dim]")
            syntax = Syntax(example["cmd"], "bash", theme="monokai", line_numbers=False)
            console.print(syntax)
            console.print()

    if examples:
        return

    # Flags
    if cmd_data.get("flags"):
        console.print("\n[bold]🚩 Common Flags:[/bold]\n")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Flag", style="cyan")
        table.add_column("Description")

        for flag, desc in cmd_data["flags"].items():
            table.add_row(flag, desc)

        console.print(table)

    # Special sections
    if cmd_data.get("cells"):
        console.print("\n[bold]🦠 Immune Cells:[/bold]\n")
        for cell in cmd_data["cells"]:
            console.print(f"  {cell}")
        console.print()


@app.command(name="search")
def search_help(
    keyword: str = typer.Argument(..., help="Keyword to search for"),
    show_examples: bool = typer.Option(False, "--examples", "-e", help="Show examples in results"),
    fuzzy: bool = typer.Option(True, "--fuzzy/--exact", help="Use fuzzy matching (default)"),
):
    """
    🔍 Search help across all commands with fuzzy matching.

    Examples:
        vcli help search malware
        vcli help search "threat hunting"
        vcli help search investigation --examples
        vcli help search mlwr --fuzzy  # Fuzzy matches "malware"
    """
    keyword_lower = keyword.lower()
    results = []

    if fuzzy:
        # Fuzzy search usando Levenshtein
        matcher = FuzzyMatcher(threshold=0.5)

        # Busca fuzzy em command names
        command_names = list(ALL_COMMANDS.keys())
        fuzzy_matches = matcher.find_matches(keyword_lower, command_names, limit=10)

        for score, cmd in fuzzy_matches:
            desc = ALL_COMMANDS[cmd]
            results.append((cmd, desc, "command", score))

        # Busca fuzzy em descriptions
        for cmd, desc in ALL_COMMANDS.items():
            desc_words = desc.lower().split()
            for word in desc_words:
                score = matcher.similarity_score(keyword_lower, word)
                if score >= matcher.threshold and cmd not in [r[0] for r in results]:
                    results.append((cmd, desc, "description", score))
                    break

        # Ordena por score descendente
        results.sort(key=lambda x: x[3], reverse=True)

    else:
        # Busca exata (comportamento original)
        for cmd, desc in ALL_COMMANDS.items():
            if keyword_lower in cmd.lower() or keyword_lower in desc.lower():
                results.append((cmd, desc, "command", 1.0))

    # Search in examples (only for exact match or as fallback)
    if not fuzzy or len(results) < 3:
        for cmd, data in COMMAND_EXAMPLES.items():
            for example in data.get("examples", []):
                if keyword_lower in example["desc"].lower() or keyword_lower in example["cmd"].lower():
                    if cmd not in [r[0] for r in results]:
                        results.append((cmd, data["description"], "example", 0.3))

    if not results:
        # Sugere correções usando fuzzy matching
        matcher = FuzzyMatcher(threshold=0.3)
        suggestions = matcher.suggest_correction(keyword, list(ALL_COMMANDS.keys()), top_n=5)

        PrimordialPanel.warning(
            suggestions,
            title="🔍 No Results Found",
            console=console
        )
        console.print("\n[cyan]Tip: Try 'vcli help list' to see all commands[/cyan]")
        raise typer.Exit(1)

    # Display results usando GeminiStyleTable
    table = GeminiStyleTable(
        title=f"Search Results: '{keyword}'",
        console=console
    )
    table.add_column("Command", width=20)
    table.add_column("Description", width=50)
    table.add_column("Match", alignment="center", width=15)

    if fuzzy:
        table.add_column("Score", alignment="center", width=10)

    for result in results[:10]:  # Limita a 10 resultados
        if fuzzy:
            cmd, desc, match_type, score = result
            # Formata score como percentual
            score_percent = f"{int(score * 100)}%"
            table.add_row(cmd, desc, match_type, score_percent)
        else:
            cmd, desc, match_type, _ = result
            table.add_row(cmd, desc, match_type)

    table.render()

    console.print(f"\n[grey70]Found {len(results)} match(es)[/grey70]")
    console.print(f"\n[deep_sky_blue1]💡 Tip: Use 'vcli help show <command>' for detailed help[/deep_sky_blue1]")

    # Show examples if requested
    if show_examples and results:
        console.print("\n[bold]📝 Examples from matched commands:[/bold]\n")
        for cmd, _, _ in results[:3]:  # Show top 3
            if cmd in COMMAND_EXAMPLES and COMMAND_EXAMPLES[cmd].get("examples"):
                console.print(f"[bold cyan]{cmd}:[/bold cyan]")
                example = COMMAND_EXAMPLES[cmd]["examples"][0]  # First example
                console.print(f"  [dim]{example['desc']}[/dim]")
                console.print(f"  [green]{example['cmd']}[/green]\n")


@app.command(name="list")
def list_commands(
    category: Optional[str] = typer.Argument(None, help="Filter by category"),
):
    """
    📋 List all available commands by category.

    Examples:
        vcli help list
        vcli help list ai
    """
    categories = {
        "ai": {
            "title": "🤖 AI & Intelligence",
            "commands": ["investigate", "ask", "maximus", "memory", "analytics", "hunt", "detect"]
        },
        "osint": {
            "title": "🔎 OSINT & Reconnaissance",
            "commands": ["osint", "ip", "threat", "threat_intel"]
        },
        "offensive": {
            "title": "⚔️ Offensive Security",
            "commands": ["offensive", "scan", "monitor"]
        },
        "defense": {
            "title": "🛡️ Defense & Response",
            "commands": ["immunis", "adr", "incident", "policy", "malware", "dlp"]
        },
        "management": {
            "title": "📊 Management & Compliance",
            "commands": ["compliance", "siem", "context", "auth", "menu"]
        },
        "advanced": {
            "title": "🧠 Advanced Features",
            "commands": ["hcl", "cognitive", "distributed", "project", "plugin", "script"]
        },
        "ui": {
            "title": "🎨 UI & Shell",
            "commands": ["tui", "shell"]
        }
    }

    if category:
        if category not in categories:
            console.print(f"[yellow]Category '{category}' not found[/yellow]")
            console.print(f"\nAvailable categories: {', '.join(categories.keys())}")
            raise typer.Exit(1)

        cat_data = categories[category]
        console.print(f"\n[bold]{cat_data['title']}[/bold]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", width=20)
        table.add_column("Description", width=70)

        for cmd in cat_data["commands"]:
            table.add_row(cmd, ALL_COMMANDS.get(cmd, ""))

        console.print(table)
        return

    # Show all categories
    console.print("\n[bold]📚 vCLI Command Reference[/bold]\n")

    for cat_key, cat_data in categories.items():
        console.print(f"[bold]{cat_data['title']}[/bold]")
        console.print(f"[dim]{len(cat_data['commands'])} commands[/dim]\n")

    console.print(f"\n[cyan]Total: {len(ALL_COMMANDS)} commands available[/cyan]")
    console.print(f"\n[dim]Tips:[/dim]")
    console.print("  • [cyan]vcli help list <category>[/cyan] - Show commands in category")
    console.print("  • [cyan]vcli help show <command>[/cyan] - Detailed help with examples")
    console.print("  • [cyan]vcli help search <keyword>[/cyan] - Search across all commands")


@app.command(name="quick")
def quick_reference():
    """
    ⚡ Show quick reference card for common commands.

    Examples:
        vcli help quick
    """
    console.print(Panel(
        "[bold]vCLI Quick Reference[/bold]",
        title="⚡ Most Used Commands",
        border_style="green"
    ))

    quick_ref = [
        ("investigate target <IOC>", "AI-orchestrated investigation"),
        ("osint username <name>", "Social media profiling"),
        ("maximus chat <query>", "Ask Maximus AI"),
        ("memory recall <topic>", "Semantic memory search"),
        ("hunt search --ioc <IOC>", "Threat hunting"),
        ("immunis status", "Check immune system"),
        ("malware analyze <file>", "Malware analysis"),
        ("hcl plan <objective>", "Generate HCL plan"),
        ("vcli shell", "Interactive shell"),
        ("vcli tui", "Launch dashboard"),
    ]

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Command", style="cyan", width=35)
    table.add_column("Description", width=45)

    for cmd, desc in quick_ref:
        table.add_row(cmd, desc)

    console.print(table)
    console.print("\n[dim]Tip: Use 'vcli help show <command>' for detailed examples[/dim]")


@app.callback(invoke_without_command=True)
def help_main(ctx: typer.Context):
    """Enhanced help system for vCLI."""
    if ctx.invoked_subcommand is None:
        console.print("\n[bold]📚 vCLI Enhanced Help System[/bold]\n")
        console.print("Available help commands:\n")
        console.print("  [cyan]vcli help list[/cyan]           - List all commands by category")
        console.print("  [cyan]vcli help show <cmd>[/cyan]     - Show detailed help with examples")
        console.print("  [cyan]vcli help search <keyword>[/cyan] - Search across all commands")
        console.print("  [cyan]vcli help quick[/cyan]          - Quick reference card")
        console.print("\n[dim]Examples:[/dim]")
        console.print("  vcli help show investigate")
        console.print("  vcli help search malware")
        console.print("  vcli help list ai\n")


if __name__ == "__main__":
    app()
