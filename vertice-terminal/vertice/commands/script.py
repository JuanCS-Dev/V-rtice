"""
🔧 VScript - Workflow Automation Commands

Commands for VScript (Vértice Scripting Language):
- vcli script run       - Execute VScript file
- vcli script validate  - Validate VScript file
- vcli script list      - List available scripts
- vcli script new       - Create new script from template

Example:
    vcli script run recon.vscript
    vcli script validate my-workflow.vscript
"""

import typer
from pathlib import Path
from typing import Optional
import sys

from vertice.scripting import (
    VScriptParser,
    VScriptRuntime,
    VScriptValidator,
    ValidationLevel,
    ValidationError,
)
from vertice.utils.primoroso import console


app = typer.Typer(
    name="script",
    help="🔧 VScript workflow automation - Execute, validate, and manage VScript automation workflows",
    rich_markup_mode="rich",
)


@app.command(name="run")
def run_script(
    script_path: str = typer.Argument(..., help="Path to VScript file"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate before execution"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation mode"),
):
    """
    Execute VScript file.

    Example:
        vcli script run recon.vscript
        vcli script run pentest-workflow.vscript --no-validate
    """
    script_file = Path(script_path)

    try:
        # Read script
        console.print(f"\n[bold]📜 Loading script:[/bold] {script_file.name}")
        source = script_file.read_text()

        # Validate
        if validate:
            console.print("[bold]🔍 Validating...[/bold]")
            validator = VScriptValidator(strict=strict)
            issues = validator.validate(source)

            if issues:
                console.print(f"\n[yellow]Found {len(issues)} validation issue(s):[/yellow]\n")
                for issue in issues:
                    if issue.level == ValidationLevel.ERROR:
                        console.print(f"  [red]❌ Line {issue.line}: {issue.message}[/red]")
                    elif issue.level == ValidationLevel.WARNING:
                        console.print(f"  [yellow]⚠️  Line {issue.line}: {issue.message}[/yellow]")
                    else:
                        console.print(f"  [blue]ℹ️  Line {issue.line}: {issue.message}[/blue]")

                if validator.has_errors():
                    console.print("\n[red]❌ Validation failed - cannot execute[/red]")
                    sys.exit(1)

                console.print()

        # Parse
        console.print("[bold]🔧 Parsing...[/bold]")
        parser = VScriptParser(source)
        program = parser.parse()

        console.print(f"[green]✓[/green] Parsed {len(program.statements)} statements\n")

        # Execute
        console.print("[bold cyan]🚀 Executing script...[/bold cyan]\n")
        console.print("─" * 60)

        runtime = VScriptRuntime()
        result = runtime.execute(program)

        console.print("─" * 60)
        console.print(f"\n[green]✅ Script completed successfully[/green]")

        if result is not None:
            console.print(f"[dim]Return value: {result}[/dim]")

    except SyntaxError as e:
        console.print(f"\n[red]❌ Syntax Error:[/red] {e}")
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[red]❌ Runtime Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@app.command(name="validate")
def validate_script(
    script_path: str = typer.Argument(..., help="Path to VScript file"),
    strict: bool = typer.Option(False, "--strict", help="Strict validation mode (warnings = errors)"),
):
    """
    Validate VScript file without executing.

    Checks for:
    - Syntax errors
    - Security issues
    - Best practices

    Example:
        vcli script validate my-workflow.vscript
        vcli script validate dangerous.vscript --strict
    """
    script_file = Path(script_path)

    try:
        console.print(f"\n[bold]🔍 Validating:[/bold] {script_file.name}\n")

        source = script_file.read_text()

        validator = VScriptValidator(strict=strict)
        issues = validator.validate(source)

        if not issues:
            console.print("[green]✅ No issues found - script is valid![/green]\n")
            sys.exit(0)

        # Print issues
        console.print(f"[yellow]Found {len(issues)} issue(s):[/yellow]\n")

        for issue in issues:
            if issue.level == ValidationLevel.ERROR:
                console.print(f"  [red]❌ ERROR[/red] Line {issue.line}: {issue.message}")
            elif issue.level == ValidationLevel.WARNING:
                console.print(f"  [yellow]⚠️  WARNING[/yellow] Line {issue.line}: {issue.message}")
            else:
                console.print(f"  [blue]ℹ️  INFO[/blue] Line {issue.line}: {issue.message}")

        # Summary
        errors = sum(1 for i in issues if i.level == ValidationLevel.ERROR)
        warnings = sum(1 for i in issues if i.level == ValidationLevel.WARNING)
        infos = sum(1 for i in issues if i.level == ValidationLevel.INFO)

        console.print(f"\n[bold]Summary:[/bold] {errors} error(s), {warnings} warning(s), {infos} info(s)\n")

        if validator.has_errors():
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        console.print(f"\n[red]❌ Error:[/red] {e}")
        sys.exit(1)


@app.command(name="list")
def list_scripts(
    path: str = typer.Option(".", "--path", help="Directory to search"),
):
    """
    List all VScript files in directory.

    Example:
        vcli script list
        vcli script list --path ~/scripts
    """
    search_path = Path(path)

    console.print(f"\n[bold]📋 VScript files in:[/bold] {search_path.absolute()}\n")

    # Find all .vscript files
    script_files = list(search_path.glob("**/*.vscript"))

    if not script_files:
        console.print("[yellow]No .vscript files found[/yellow]\n")
        return

    for script_file in sorted(script_files):
        # Get file size
        size_kb = script_file.stat().st_size / 1024

        # Count lines
        try:
            lines = len(script_file.read_text().splitlines())
            console.print(f"  📜 [cyan]{script_file.name}[/cyan] - {lines} lines ({size_kb:.1f} KB)")
        except:
            console.print(f"  📜 [cyan]{script_file.name}[/cyan] - ({size_kb:.1f} KB)")

    console.print(f"\n[green]Found {len(script_files)} script(s)[/green]\n")


@app.command(name="new")
def new_script(
    name: str = typer.Argument(..., help="Script name"),
    template: str = typer.Option("basic", "--template", help="Script template (basic/recon/pentest/defend)"),
):
    """
    Create new VScript file from template.

    Templates:
    - basic: Empty script with comments
    - recon: Reconnaissance workflow
    - pentest: Penetration testing workflow
    - defend: Defense/hardening workflow

    Example:
        vcli script new my-scan.vscript
        vcli script new recon.vscript --template recon
    """
    # Add .vscript extension if not present
    if not name.endswith(".vscript"):
        name += ".vscript"

    script_file = Path(name)

    if script_file.exists():
        console.print(f"[red]❌ File already exists:[/red] {name}")
        sys.exit(1)

    # Templates
    templates = {
        "basic": """# VScript Workflow
# Created with vcli script new

# Example: Create project and scan network
project = create_project("my-project")

# Your code here
console.log("Script started")

# Example scans
# hosts = scan_network("10.0.0.0/24", type="ping")
# for host in hosts:
#     services = scan_ports(host, type="quick")
#     workspace.store(services)

console.log("Script complete")
""",
        "recon": """# Reconnaissance Workflow
# Automated network discovery and enumeration

project = create_project("recon-scan")

# Phase 1: Network discovery
console.log("Phase 1: Discovering live hosts...")
hosts = scan_network("10.0.0.0/24", type="ping")
console.log(f"Found {len(hosts)} live hosts")

# Phase 2: Port scanning
console.log("\\nPhase 2: Scanning ports...")
for host in hosts:
    console.log(f"Scanning {host['ip']}...")
    services = scan_ports(host, type="full")
    workspace.store(services)

    # Check for web services
    if services.has_port(80) or services.has_port(443):
        console.log(f"  Web server detected on {host['ip']}")

# Phase 3: Report
console.log("\\nPhase 3: Generating report...")
generate_report(format="markdown", output="recon-report.md")

console.log("\\nReconnaissance complete!")
""",
        "pentest": """# Penetration Testing Workflow
# Recon → Scanning → Vulnerability Assessment

project = create_project("pentest-workflow")

# Configuration
target_network = "10.10.1.0/24"

# Phase 1: Discovery
console.log("=== Phase 1: Discovery ===")
hosts = scan_network(target_network, type="ping")
console.log(f"Discovered {len(hosts)} hosts\\n")

# Phase 2: Service Detection
console.log("=== Phase 2: Service Detection ===")
for host in hosts:
    services = scan_ports(host, type="full")
    workspace.store(services)

# Phase 3: Vulnerability Scanning
console.log("\\n=== Phase 3: Vulnerability Scanning ===")
web_hosts = [h for h in hosts if h.has_port(80) or h.has_port(443)]

for host in web_hosts:
    vulns = web_scan(host, tool="nikto")

    if len(vulns['vulns']) > 0:
        console.log(f"Found {len(vulns['vulns'])} vulnerabilities on {host['ip']}")
        notify_slack(f"Critical findings on {host['ip']}")

# Phase 4: Report
console.log("\\n=== Phase 4: Reporting ===")
generate_report(format="pdf", output="pentest-report.pdf")

console.log("\\nPentesting workflow complete!")
""",
        "defend": """# Defense & Hardening Workflow
# Baseline assessment → Vulnerability detection → Automated fixes

project = create_project("defense-hardening")

# Configuration
web_servers = ["10.0.1.10", "10.0.1.11", "10.0.1.12"]

# Phase 1: Baseline Assessment
console.log("=== Phase 1: Baseline Assessment ===")
for server in web_servers:
    console.log(f"Assessing {server}...")

    services = scan_ports(server, type="quick")
    workspace.store(services)

    # Check SSL/TLS
    if services.has_port(443):
        banner = grab_banner(server, 443)
        console.log(f"  HTTPS: {banner}")

# Phase 2: Vulnerability Detection
console.log("\\n=== Phase 2: Vulnerability Detection ===")
for server in web_servers:
    vulns = web_scan(server, tool="nuclei")

    critical = [v for v in vulns['vulns'] if v['severity'] == 'critical']
    if len(critical) > 0:
        console.warn(f"CRITICAL: {len(critical)} critical vulns on {server}")
        notify_slack(f"Critical vulnerabilities found on {server}")

# Phase 3: Reporting
console.log("\\n=== Phase 3: Reporting ===")
generate_report(format="html", output="security-assessment.html")

console.log("\\nDefense assessment complete!")
"""
    }

    content = templates.get(template, templates["basic"])

    script_file.write_text(content)

    console.print(f"\n[green]✅ Created script:[/green] {name}")
    console.print(f"[dim]Template:[/dim] {template}")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit: nano {name}")
    console.print(f"  2. Validate: vcli script validate {name}")
    console.print(f"  3. Run: vcli script run {name}\n")


# Export for CLI registration
__all__ = ["app"]
