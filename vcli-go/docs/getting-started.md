# 🚀 Getting Started with vCLI 2.0

**Version:** 1.0
**Last Updated:** 2025-01-06

Welcome to vCLI 2.0 - the high-performance Go implementation of the Vértice CLI!

---

## 📋 Prerequisites

### System Requirements

- **Operating System:** Linux, macOS, or Windows
- **Go Version:** 1.21 or higher (for building from source)
- **Memory:** 100MB available RAM
- **Disk:** 50MB free space

### Optional Tools

- `make` - For build automation
- `golangci-lint` - For linting (development)
- `air` - For live reload (development)

---

## 📦 Installation

### Option 1: Download Pre-built Binary (Recommended)

```bash
# Download latest release (Linux AMD64)
curl -L https://github.com/verticedev/vcli-go/releases/latest/download/vcli-linux-amd64 -o vcli
chmod +x vcli
sudo mv vcli /usr/local/bin/

# Verify installation
vcli version
```

**Available Platforms:**
- `vcli-linux-amd64` - Linux x86_64
- `vcli-linux-arm64` - Linux ARM64
- `vcli-darwin-amd64` - macOS Intel
- `vcli-darwin-arm64` - macOS Apple Silicon
- `vcli-windows-amd64.exe` - Windows x86_64

### Option 2: Install via Go

```bash
go install github.com/verticedev/vcli-go@latest
```

### Option 3: Build from Source

```bash
# Clone repository
git clone https://github.com/verticedev/vcli-go.git
cd vcli-go

# Install dependencies
go mod download

# Build
make build

# Binary will be at: bin/vcli
./bin/vcli version

# Optional: Install to $GOPATH/bin
make install
```

---

## 🎯 Quick Start

### 1. Initialize Configuration

```bash
# Initialize default configuration
vcli config init

# This creates ~/.vcli/config.yaml with defaults
```

**Output:**
```
✅ Configuration initialized at ~/.vcli/config.yaml
📝 Edit the file to customize settings
```

### 2. Explore Available Commands

```bash
# List all commands
vcli --help

# Get help for specific command
vcli config --help
vcli plugin --help
```

### 3. Install Your First Plugin

```bash
# List available plugins
vcli plugin list

# Install kubernetes plugin
vcli plugin install kubernetes

# Verify installation
vcli plugin list --installed
```

### 4. Launch TUI Mode

```bash
# Launch interactive TUI
vcli tui

# Launch specific workspace
vcli workspace launch governance
```

**TUI Keyboard Shortcuts:**
- `Ctrl+P` - Open command palette
- `Ctrl+W` - Switch workspace
- `Tab` - Next panel
- `Shift+Tab` - Previous panel
- `q` or `Ctrl+C` - Quit

---

## 🔧 Configuration

### Configuration Files

vCLI uses a hierarchical configuration system:

```
~/.vcli/
├── config.yaml          # User-level configuration
├── cache/               # Local cache directory
├── plugins/             # Installed plugins
└── offline/             # Offline mode database
```

### Basic Configuration

**~/.vcli/config.yaml:**

```yaml
# Global settings
global:
  logLevel: info           # debug, info, warn, error
  cacheDir: ~/.vcli/cache
  defaultWorkspace: governance

# UI settings
ui:
  theme: dark              # dark, light
  refreshRate: 5s
  showHelp: true

# Offline mode
offline:
  enabled: true
  cacheSize: 1GB
  cacheTTL: 24h
  syncInterval: 5m

# Telemetry
telemetry:
  enabled: true
  endpoint: https://telemetry.vertice.dev

# Plugins
plugins:
  kubernetes:
    enabled: true
  prometheus:
    enabled: true
  git:
    enabled: false
```

### Environment Variables

Override configuration via environment variables:

```bash
# Set log level
export VCLI_LOG_LEVEL=debug

# Disable telemetry
export VCLI_TELEMETRY_ENABLED=false

# Set cache directory
export VCLI_CACHE_DIR=/tmp/vcli-cache

# Run command
vcli --help
```

**Variable Format:** `VCLI_<SECTION>_<KEY>=value`

---

## 🔌 Working with Plugins

### List Available Plugins

```bash
# List all available plugins in registry
vcli plugin list

# List installed plugins
vcli plugin list --installed

# Search for plugins
vcli plugin search kubernetes
```

### Install/Uninstall Plugins

```bash
# Install from registry
vcli plugin install kubernetes

# Install from local file
vcli plugin install ./my-plugin.so

# Install from Git repository
vcli plugin install github.com/user/plugin

# Uninstall plugin
vcli plugin uninstall kubernetes
```

### Plugin Information

```bash
# Show plugin details
vcli plugin info kubernetes

# Check plugin health
vcli plugin health kubernetes

# View plugin logs
vcli plugin logs kubernetes
```

---

## 🏛️ Workspaces

Workspaces are pre-configured TUI layouts for specific tasks.

### Available Workspaces

1. **Governance Workspace** - HITL ethical decision making
2. **Investigation Workspace** - Deep dive analysis
3. **Situational Awareness** - Real-time dashboard

### Launch Workspace

```bash
# Launch specific workspace
vcli workspace launch governance

# List available workspaces
vcli workspace list

# Get workspace info
vcli workspace info governance
```

### Workspace Shortcuts

**Inside TUI:**
- `Ctrl+1` - Governance workspace
- `Ctrl+2` - Investigation workspace
- `Ctrl+3` - Situational Awareness workspace

---

## 💾 Offline Mode

vCLI works seamlessly offline with local caching.

### Enable Offline Mode

```yaml
# ~/.vcli/config.yaml
offline:
  enabled: true
  cacheSize: 1GB
  cacheTTL: 24h
  syncInterval: 5m
```

### Check Offline Status

```bash
# View sync status
vcli offline status

# Manually trigger sync
vcli offline sync

# View queued operations
vcli offline queue

# Clear local cache
vcli offline clear-cache
```

### How It Works

1. **Online:** Operations execute immediately and cache results
2. **Offline:** Operations queue locally, use cached data
3. **Reconnect:** Queued operations sync automatically
4. **Conflicts:** Resolved via last-write-wins or manual resolution

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "command not found: vcli"

**Solution:** Add to PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH=$PATH:/path/to/vcli
```

#### 2. "permission denied"

**Solution:** Make binary executable

```bash
chmod +x vcli
```

#### 3. "plugin failed to load"

**Solution:** Check compatibility

```bash
# View plugin requirements
vcli plugin info <plugin-name>

# Check system compatibility
vcli system info
```

#### 4. "offline database corrupted"

**Solution:** Reset offline cache

```bash
vcli offline clear-cache --force
vcli offline sync
```

### Enable Debug Logging

```bash
# Via environment variable
export VCLI_LOG_LEVEL=debug
vcli <command>

# Via flag
vcli --log-level=debug <command>

# View logs
tail -f ~/.vcli/logs/vcli.log
```

### Get Help

```bash
# Built-in help
vcli --help
vcli <command> --help

# Report issue
vcli bug-report

# Check system info
vcli system info
```

---

## 📚 Next Steps

### Learn More

- [Architecture Guide](architecture.md) - Understanding vCLI internals
- [Plugin Development](plugins.md) - Create your own plugins
- [Migration Guide](migration.md) - Migrate from Python vCLI
- [Contributing](contributing.md) - Contribute to vCLI

### Example Workflows

#### 1. Kubernetes Management

```bash
# Install k8s plugin
vcli plugin install kubernetes

# List pods
vcli k8s get pods

# Describe pod
vcli k8s describe pod nginx-123

# View logs
vcli k8s logs nginx-123 -f
```

#### 2. Ethical Governance

```bash
# Launch governance workspace
vcli workspace launch governance

# Inside TUI:
# - View pending decisions
# - Review AI reasoning
# - Approve/Reject/Escalate
# - View audit trail
```

#### 3. Multi-Cluster Operations

```bash
# Add clusters
vcli cluster add production --context prod-k8s
vcli cluster add staging --context stage-k8s

# Switch cluster
vcli cluster use production

# Execute across all clusters
vcli cluster exec-all "kubectl get nodes"
```

---

## 🎓 Resources

### Documentation

- **Official Docs:** https://docs.vertice.dev
- **API Reference:** https://godoc.org/github.com/verticedev/vcli-go
- **Examples:** [examples/](../examples/)

### Community

- **GitHub:** https://github.com/verticedev/vcli-go
- **Discord:** https://discord.gg/vertice
- **Twitter:** @verticedev

### Support

- **Issues:** https://github.com/verticedev/vcli-go/issues
- **Discussions:** https://github.com/verticedev/vcli-go/discussions
- **Email:** support@vertice.dev

---

## ✅ Checklist

Getting started checklist:

- [ ] Install vCLI
- [ ] Verify installation (`vcli version`)
- [ ] Initialize configuration (`vcli config init`)
- [ ] Install first plugin (`vcli plugin install kubernetes`)
- [ ] Launch TUI (`vcli tui`)
- [ ] Explore workspaces
- [ ] Read architecture guide
- [ ] Join community

---

**Ready to dive deeper?**

Continue to:
- [Architecture Guide](architecture.md) for technical details
- [Plugin Development](plugins.md) to create plugins
- [Contributing](contributing.md) to contribute code

---

**Version:** 1.0 | **Last Updated:** 2025-01-06
