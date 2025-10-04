# Vértice Plugin Examples

Example plugins demonstrating the Vértice Plugin SDK.

## Available Examples

### 1. Shodan Plugin (`shodan_plugin.py`)

**Purpose**: Enrich discovered hosts with Shodan OSINT intelligence.

**Features**:
- Automatic host enrichment on discovery
- Caching to avoid duplicate API calls
- Vulnerability correlation

**Configuration**:
```yaml
# ~/.vertice/config.yaml
plugins:
  shodan:
    api_key: YOUR_SHODAN_API_KEY
    auto_enrich: true
```

**Usage**:
```bash
vcli plugin install examples/plugins/shodan_plugin.py
vcli plugin enable shodan
vcli scan nmap 1.1.1.1  # Shodan data auto-fetched
```

---

### 2. Slack Notification Plugin (`slack_notification_plugin.py`)

**Purpose**: Send real-time notifications to Slack channels.

**Features**:
- Critical vulnerability alerts
- Scan completion notifications
- Project tracking

**Configuration**:
```yaml
# ~/.vertice/config.yaml
plugins:
  slack:
    webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
    notify_on_critical: true
    notify_on_scan_complete: true
```

**Usage**:
```bash
vcli plugin install examples/plugins/slack_notification_plugin.py
vcli plugin enable slack
# Notifications sent automatically
```

---

## Creating Your Own Plugin

### Minimal Example

```python
from vertice.plugins import BasePlugin, hook

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    author = "me@example.com"
    description = "My custom plugin"

    @hook("on_host_discovered")
    def my_hook(self, context):
        host = context.data["host"]
        print(f"Host discovered: {host.ip_address}")
```

### Plugin Structure

Required attributes:
- `name`: Unique plugin identifier
- `version`: Semantic version (e.g., "1.0.0")
- `author`: Plugin maintainer email

Optional attributes:
- `description`: Short description
- `homepage`: URL to plugin repo
- `license`: License identifier (default: "MIT")
- `dependencies`: List of pip packages
- `vertice_min_version`: Minimum Vértice version

### Available Hooks

Plugins can hook into these events:

| Hook | When Triggered | Data Available |
|------|----------------|----------------|
| `on_host_discovered` | New host found | `host` object |
| `on_vulnerability_found` | Vulnerability detected | `vulnerability` object |
| `on_scan_complete` | Scan finishes | `scan_result` object |
| `on_project_created` | Project created | `project` object |
| `on_port_discovered` | Open port found | `port`, `host` objects |

### Hook Priorities

Control execution order:

```python
from vertice.plugins import hook, HookPriority

@hook("on_host_discovered", priority=HookPriority.HIGH)
def urgent_handler(self, context):
    # Runs before NORMAL priority hooks
    pass

@hook("on_host_discovered", priority=HookPriority.LOW)
def cleanup_handler(self, context):
    # Runs after NORMAL priority hooks
    pass
```

Priorities: `HIGHEST → HIGH → NORMAL → LOW → LOWEST`

### Returning Enrichment Data

Hooks can return data to enrich objects:

```python
@hook("on_host_discovered")
def enrich_host(self, context):
    host = context.data["host"]

    # Query external API
    api_data = self.query_api(host.ip_address)

    # Return enrichment data
    return {
        "api_country": api_data["country"],
        "api_org": api_data["organization"],
        "api_risk_score": api_data["risk_score"],
    }
```

The returned dict is merged into the host object.

### Stop Propagation

Prevent subsequent hooks from executing:

```python
@hook("on_vulnerability_found")
def validate_vuln(self, context):
    vuln = context.data["vulnerability"]

    if self.is_false_positive(vuln):
        # Stop other plugins from processing this
        context.stop_propagation = True
        return None
```

### Configuration

Plugins receive configuration during initialization:

```python
def initialize(self, config):
    super().initialize(config)

    self.api_key = config.get("api_key")
    if not self.api_key:
        raise ValueError("api_key required")

    self.timeout = config.get("timeout", 30)
```

User configuration in `~/.vertice/config.yaml`:

```yaml
plugins:
  my-plugin:
    api_key: secret_key_123
    timeout: 60
```

### Dependencies

Specify Python packages:

```python
class MyPlugin(BasePlugin):
    dependencies = [
        "requests>=2.28.0",
        "shodan==1.28.0",
    ]
```

Vértice auto-installs dependencies when plugin is loaded.

### Lifecycle Methods

Override these methods for custom behavior:

```python
def initialize(self, config):
    # Called once after plugin loaded
    # Setup API clients, validate config
    pass

def activate(self):
    # Called when plugin enabled
    # Start background tasks, open connections
    pass

def deactivate(self):
    # Called when plugin disabled
    # Cleanup resources, close connections
    pass
```

## Installation

### From File

```bash
vcli plugin install /path/to/plugin.py
```

### From GitHub

```bash
vcli plugin install https://github.com/user/vertice-plugin-shodan
```

### From Marketplace

```bash
vcli plugin search shodan
vcli plugin install shodan
```

## Plugin Management

```bash
# List installed plugins
vcli plugin list

# Enable plugin
vcli plugin enable shodan

# Disable plugin
vcli plugin disable shodan

# Uninstall plugin
vcli plugin uninstall shodan

# Update plugin
vcli plugin update shodan

# Show plugin info
vcli plugin info shodan
```

## Testing Plugins

```python
import pytest
from vertice.plugins import HookContext

def test_my_plugin():
    plugin = MyPlugin()
    plugin.initialize({"api_key": "test_key"})
    plugin.activate()

    # Simulate hook
    context = HookContext(
        event_name="on_host_discovered",
        data={"host": mock_host}
    )

    result = plugin.my_hook(context)

    assert result is not None
    assert "enrichment_data" in result
```

## Publishing

### 1. Create GitHub Repo

```bash
mkdir vertice-plugin-myname
cd vertice-plugin-myname
git init
```

### 2. Add Topic

Add `vertice-plugin` topic to your GitHub repo.

### 3. Create setup.py

```python
from setuptools import setup

setup(
    name="vertice-plugin-myname",
    version="1.0.0",
    py_modules=["myname_plugin"],
    install_requires=["vertice>=1.0.0"],
)
```

### 4. Publish to PyPI

```bash
python setup.py sdist
twine upload dist/*
```

Your plugin is now installable via:

```bash
vcli plugin install myname
```

## Best Practices

✅ **Do**:
- Use semantic versioning
- Specify dependencies explicitly
- Add comprehensive docstrings
- Handle API errors gracefully
- Cache expensive operations
- Clean up resources in `deactivate()`

❌ **Don't**:
- Block event loop with long operations
- Modify core Vértice objects directly
- Hardcode API keys (use config)
- Ignore hook errors silently

## Support

- Documentation: https://docs.vertice.dev/plugins
- Examples: https://github.com/vertice/plugins
- Community: https://discord.gg/vertice

## License

All example plugins are MIT licensed.
