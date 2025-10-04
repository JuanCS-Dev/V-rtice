"""
Vértice Plugin Management - Extensible Integration System
=========================================================

Load, manage, and configure community plugins for extended functionality.
Plugins can enrich data, send notifications, integrate external APIs, etc.

Examples:
    vcli plugin list
    vcli plugin install shodan
    vcli plugin enable shodan
    vcli plugin info shodan
    vcli plugin disable shodan
"""

import typer
from typing import Optional, List
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
import json

from ..plugins import PluginRegistry, PluginLoader, PluginError, PluginLoadError
from ..utils import primoroso
from ..utils.output import print_json, print_error
from ..utils.config import config as vertice_config

console = Console()

app = typer.Typer(
    name="plugin",
    help="🔌 Plugin management - extend Vértice with community integrations",
    rich_markup_mode="rich",
)

# Global plugin registry
_registry = None


def get_registry() -> PluginRegistry:
    """Get or create global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


@app.command()
def list(
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    enabled_only: Annotated[bool, typer.Option("--enabled", "-e", help="Show only enabled plugins")] = False,
):
    """List installed plugins with status and metadata.

    Examples:
        vcli plugin list
        vcli plugin list --enabled
        vcli plugin list --json
    """
    registry = get_registry()

    # Discover and load plugins
    registry.discover_plugins()

    plugins = registry.list_plugins(enabled_only=enabled_only)

    if not plugins:
        if enabled_only:
            primoroso.info("No enabled plugins. Enable with: vcli plugin enable <name>")
        else:
            primoroso.info("No plugins installed. Install with: vcli plugin install <name>")
        return

    if json_output:
        plugins_data = [
            {
                "name": p.name,
                "version": p.metadata.version,
                "author": p.metadata.author,
                "description": p.metadata.description,
                "enabled": p.enabled,
                "homepage": p.metadata.homepage,
                "license": p.metadata.license,
            }
            for p in plugins
        ]
        print_json({"plugins": plugins_data, "count": len(plugins_data)})
        return

    # Rich table
    table = Table(title="🔌 Installed Plugins", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Version", justify="center", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Description", no_wrap=False)
    table.add_column("Author", style="dim")

    for plugin in plugins:
        status_icon = "🟢 Enabled" if plugin.enabled else "⚪ Disabled"

        table.add_row(
            plugin.name,
            plugin.metadata.version,
            status_icon,
            plugin.metadata.description[:60] + "..." if len(plugin.metadata.description) > 60 else plugin.metadata.description,
            plugin.metadata.author,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(plugins)} plugins ({sum(1 for p in plugins if p.enabled)} enabled)[/dim]")


@app.command()
def info(
    name: Annotated[str, typer.Argument(help="Plugin name")],
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Show detailed plugin information.

    Examples:
        vcli plugin info shodan
        vcli plugin info slack --json
    """
    registry = get_registry()
    plugin = registry.get_plugin(name)

    if not plugin:
        print_error(f"Plugin not loaded: {name}")
        primoroso.info("Available plugins: vcli plugin list")
        raise typer.Exit(code=1)

    metadata = plugin.get_metadata()

    if json_output:
        print_json({
            "name": metadata.name,
            "version": metadata.version,
            "author": metadata.author,
            "description": metadata.description,
            "homepage": metadata.homepage,
            "license": metadata.license,
            "dependencies": metadata.dependencies,
            "vertice_min_version": metadata.vertice_min_version,
            "enabled": plugin._enabled,
        })
        return

    # Rich panel display
    content = f"""[bold]Name:[/bold] {metadata.name}
[bold]Version:[/bold] {metadata.version}
[bold]Author:[/bold] {metadata.author}
[bold]Description:[/bold] {metadata.description}

[bold cyan]Details:[/bold cyan]
  • Homepage: {metadata.homepage or '[dim]None[/dim]'}
  • License: {metadata.license}
  • Min Vértice Version: {metadata.vertice_min_version}
  • Status: {'🟢 Enabled' if plugin._enabled else '⚪ Disabled'}

[bold cyan]Dependencies:[/bold cyan]
  {', '.join(metadata.dependencies) if metadata.dependencies else '[dim]None[/dim]'}"""

    # Add hook information if available
    hooks = []
    for method_name in dir(plugin):
        method = getattr(plugin, method_name)
        if hasattr(method, '_hook_metadata'):
            for hook_meta in method._hook_metadata:
                hooks.append(f"  • {hook_meta['event_name']} (priority: {hook_meta['priority'].name})")

    if hooks:
        content += f"\n\n[bold cyan]Registered Hooks:[/bold cyan]\n" + "\n".join(hooks)

    panel = Panel(content, title=f"🔌 Plugin: {metadata.name}", border_style="cyan")
    console.print(panel)


@app.command()
def install(
    plugin_source: Annotated[str, typer.Argument(help="Plugin name, file path, or GitHub URL")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Force reinstall if already exists")] = False,
):
    """Install plugin from file, GitHub, or marketplace.

    Examples:
        vcli plugin install shodan
        vcli plugin install /path/to/custom_plugin.py
        vcli plugin install https://github.com/user/vertice-plugin-censys
        vcli plugin install examples/plugins/shodan_plugin.py
    """
    loader = PluginLoader()
    registry = get_registry()

    try:
        # Determine source type
        plugin_path = Path(plugin_source)

        if plugin_path.exists():
            # Local file installation
            primoroso.info(f"Installing plugin from: {plugin_source}")

            # Load plugin to validate
            config = vertice_config.get("plugins", {}).get(plugin_path.stem, {})
            plugin = loader.load_from_file(plugin_path, config)

            # Check compatibility
            metadata = plugin.get_metadata()
            loader.check_compatibility(metadata.vertice_min_version)

            # Install dependencies
            if metadata.dependencies:
                primoroso.info(f"Installing {len(metadata.dependencies)} dependencies...")
                loader.install_dependencies(metadata.dependencies)

            # Copy to user plugins directory
            user_plugins_dir = Path.home() / ".vertice" / "plugins"
            user_plugins_dir.mkdir(parents=True, exist_ok=True)

            dest_path = user_plugins_dir / plugin_path.name

            if dest_path.exists() and not force:
                print_error(f"Plugin already exists: {dest_path}")
                primoroso.info("Use --force to overwrite")
                raise typer.Exit(code=1)

            # Copy file
            import shutil
            shutil.copy2(plugin_path, dest_path)

            primoroso.success(f"Plugin installed: {metadata.name} v{metadata.version}")
            console.print(f"  [dim]Location:[/dim] {dest_path}")
            console.print(f"  [dim]Author:[/dim] {metadata.author}")

            if metadata.dependencies:
                console.print(f"  [dim]Dependencies:[/dim] {', '.join(metadata.dependencies)}")

            primoroso.info("Enable with: vcli plugin enable " + metadata.name)

        elif plugin_source.startswith("http://") or plugin_source.startswith("https://"):
            # GitHub/URL installation
            primoroso.warning("GitHub/URL installation not yet implemented")
            console.print("  [dim]Planned for Phase 2.2[/dim]")
            raise typer.Exit(code=1)

        else:
            # Marketplace installation (future)
            primoroso.warning("Marketplace installation not yet implemented")
            console.print("  [dim]Planned for Phase 2.3[/dim]")
            console.print(f"  [dim]Try installing from file: vcli plugin install /path/to/{plugin_source}.py[/dim]")
            raise typer.Exit(code=1)

    except PluginLoadError as e:
        print_error(f"Failed to install plugin: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Installation error: {e}")
        raise typer.Exit(code=1)


@app.command()
def enable(
    name: Annotated[str, typer.Argument(help="Plugin name to enable")],
):
    """Enable plugin to activate its hooks.

    Enabled plugins will receive events and can modify behavior.

    Examples:
        vcli plugin enable shodan
        vcli plugin enable slack
    """
    registry = get_registry()

    try:
        # Load plugin if not already loaded
        if not registry.get_plugin(name):
            config = vertice_config.get("plugins", {}).get(name, {})
            registry.load_plugin(name, config)

        registry.enable_plugin(name)
        primoroso.success(f"Plugin enabled: {name}")
        console.print("  [dim]Plugin hooks are now active[/dim]")

    except PluginLoadError as e:
        print_error(f"Failed to enable plugin: {e}")
        primoroso.info("Check configuration in ~/.vertice/config.yaml")
        raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Error enabling plugin: {e}")
        raise typer.Exit(code=1)


@app.command()
def disable(
    name: Annotated[str, typer.Argument(help="Plugin name to disable")],
):
    """Disable plugin to deactivate its hooks.

    Disabled plugins remain installed but won't receive events.

    Examples:
        vcli plugin disable shodan
        vcli plugin disable slack
    """
    registry = get_registry()

    try:
        registry.disable_plugin(name)
        primoroso.success(f"Plugin disabled: {name}")
        console.print("  [dim]Plugin hooks deactivated[/dim]")

    except PluginError as e:
        print_error(f"Failed to disable plugin: {e}")
        raise typer.Exit(code=1)


@app.command()
def uninstall(
    name: Annotated[str, typer.Argument(help="Plugin name to uninstall")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """Uninstall plugin completely.

    Removes plugin file from ~/.vertice/plugins/

    Examples:
        vcli plugin uninstall old-plugin
        vcli plugin uninstall old-plugin --yes
    """
    if not yes:
        confirm = typer.confirm(f"⚠️  Uninstall plugin '{name}'?")
        if not confirm:
            primoroso.info("Uninstallation cancelled")
            return

    registry = get_registry()

    try:
        # Unload from registry
        registry.unload_plugin(name)

        # Remove plugin file
        user_plugins_dir = Path.home() / ".vertice" / "plugins"
        plugin_file = user_plugins_dir / f"{name}.py"

        if plugin_file.exists():
            plugin_file.unlink()
            primoroso.success(f"Plugin uninstalled: {name}")
        else:
            primoroso.warning(f"Plugin file not found, but removed from registry: {name}")

    except Exception as e:
        print_error(f"Failed to uninstall plugin: {e}")
        raise typer.Exit(code=1)


@app.command()
def update(
    name: Annotated[str, typer.Argument(help="Plugin name to update")],
):
    """Update plugin to latest version.

    Fetches latest version from original source.

    Examples:
        vcli plugin update shodan
    """
    primoroso.warning("Plugin updates not yet implemented")
    console.print("  [dim]Planned for Phase 2.2[/dim]")
    console.print(f"  [dim]Manually update by: vcli plugin install {name} --force[/dim]")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
):
    """Search plugin marketplace.

    Examples:
        vcli plugin search osint
        vcli plugin search notification
    """
    primoroso.warning("Plugin marketplace not yet implemented")
    console.print("  [dim]Planned for Phase 2.3[/dim]")
    console.print("\n  Available example plugins:")
    console.print("    • examples/plugins/shodan_plugin.py - Shodan OSINT enrichment")
    console.print("    • examples/plugins/slack_notification_plugin.py - Slack alerts")


@app.command()
def config(
    name: Annotated[str, typer.Argument(help="Plugin name")],
    show: Annotated[bool, typer.Option("--show", "-s", help="Show current configuration")] = False,
):
    """Configure plugin settings.

    Plugin configuration is stored in ~/.vertice/config.yaml

    Examples:
        vcli plugin config shodan --show
    """
    plugin_config = vertice_config.get("plugins", {}).get(name, {})

    if show or not plugin_config:
        if not plugin_config:
            primoroso.info(f"No configuration found for plugin: {name}")
            console.print("\n  [bold]Configuration file:[/bold] ~/.vertice/config.yaml")
            console.print("\n  [bold]Example configuration:[/bold]")

            example = f"""plugins:
  {name}:
    api_key: YOUR_API_KEY
    enabled: true"""

            syntax = Syntax(example, "yaml", theme="monokai", line_numbers=False)
            console.print(syntax)
        else:
            primoroso.success(f"Configuration for plugin: {name}")

            config_yaml = json.dumps(plugin_config, indent=2)
            syntax = Syntax(config_yaml, "json", theme="monokai", line_numbers=False)
            console.print(syntax)
    else:
        primoroso.info("Plugin configuration editing via CLI not yet implemented")
        console.print("  [dim]Edit manually: ~/.vertice/config.yaml[/dim]")


@app.command()
def stats():
    """Show plugin system statistics.

    Examples:
        vcli plugin stats
    """
    registry = get_registry()
    stats = registry.get_stats()

    # Rich panel display
    content = f"""[bold cyan]Plugin Statistics:[/bold cyan]
  • Total Plugins: {stats['total_plugins']}
  • Enabled: {stats['enabled_plugins']}
  • Disabled: {stats['disabled_plugins']}

[bold cyan]Hook System:[/bold cyan]
  • Total Hooks: {stats['hook_stats']['total_hooks']}
  • Registered Handlers: {stats['hook_stats']['registered_handlers']}
  • Active Plugins: {stats['hook_stats']['active_plugins']}"""

    panel = Panel(content, title="📊 Plugin System Stats", border_style="cyan")
    console.print(panel)

    # Show plugin details
    if stats['plugins']:
        console.print("\n[bold]Plugin Details:[/bold]")
        for plugin_name, plugin_data in stats['plugins'].items():
            status = "🟢" if plugin_data['enabled'] else "⚪"
            console.print(f"  {status} {plugin_name} v{plugin_data['version']}")
