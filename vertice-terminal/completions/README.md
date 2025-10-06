# 🎯 VÉRTICE CLI - Shell Completions

Bash and Zsh completion scripts for the VÉRTICE CLI.

## Features

- ✅ **34 Commands** with full completion support
- ✅ **100+ Subcommands** across all modules
- ✅ **Options/Flags** completion with descriptions
- ✅ **Dynamic completion** for service names, IPs, and more
- ✅ **Auto-install** script for both Bash and Zsh

## Quick Installation

### Method 1: Typer Native (Simplest)

Use Typer's built-in completion installer:

```bash
vcli --install-completion
source ~/.bashrc  # for bash
source ~/.zshrc   # for zsh
```

This auto-detects your shell and installs the appropriate completion.

### Method 2: Custom Installer (Alternative)

Run the installer from the project root:

```bash
cd /path/to/vertice-terminal
./install-completion.sh
```

The script will:
1. Auto-detect your shell (Bash or Zsh)
2. Copy the appropriate completion script
3. Configure your shell RC file
4. Provide instructions for activation

### Method 3: Manual Installation

#### Bash

```bash
# Copy completion script
cp completions/vcli.bash ~/.bash_completion.d/vcli

# Add to ~/.bashrc
echo '[ -f ~/.bash_completion.d/vcli ] && source ~/.bash_completion.d/vcli' >> ~/.bashrc

# Reload
source ~/.bashrc
```

#### Zsh

```bash
# Create completions directory
mkdir -p ~/.zsh/completions

# Copy completion script
cp completions/vcli.zsh ~/.zsh/completions/_vcli

# Add to ~/.zshrc
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc

# Reload
source ~/.zshrc
```

## Usage

After installation, press `<TAB>` to trigger completions:

```bash
# Complete commands
vcli <TAB>
# Shows: auth, context, ip, threat, scan, maximus, hunt, ask, ...

# Complete subcommands
vcli ip <TAB>
# Shows: lookup, scan, threat, reputation, ...

# Complete options
vcli scan --<TAB>
# Shows: --target, --type, --output, --help, ...

# Complete service names (dynamic)
vcli monitor service <TAB>
# Shows: maximus-core, narrative-filter, hpc, rte, ...

# Complete file paths
vcli script run <TAB>
# Shows filesystem paths with file completion
```

## Uninstallation

```bash
# Automatic
./install-completion.sh --uninstall

# Manual (Bash)
rm ~/.bash_completion.d/vcli
# Remove lines from ~/.bashrc manually

# Manual (Zsh)
rm ~/.zsh/completions/_vcli
# Note: Leave fpath config in ~/.zshrc (may be used by other tools)
```

## Troubleshooting

### Completions not working after installation

```bash
# Bash
source ~/.bashrc

# Zsh
source ~/.zshrc

# Or start a new terminal
```

### "command not found: vcli"

Completions require `vcli` to be in your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="/path/to/vertice-terminal:$PATH"
```

### Completions showing wrong commands

Clear completion cache:

```bash
# Bash
hash -r

# Zsh
rm -f ~/.zcompdump*
compinit
```

## Development

Completion scripts are generated from Typer's built-in completion support.

To regenerate (if CLI structure changes):

```bash
# The cli.py has add_completion=True, so Typer handles this automatically
# Just ensure the scripts match the current command structure
```

## Supported Shells

- ✅ Bash 4.0+
- ✅ Zsh 5.0+
- ❌ Fish (not yet supported)
- ❌ PowerShell (not yet supported)

## Commands with Completion

### Core Commands (7)
- `auth` - Authentication & session management
- `context` - Context switching
- `ip` - IP intelligence & lookups
- `threat` - Threat intelligence
- `scan` - Network scanning
- `monitor` - System monitoring
- `maximus` - Maximus AI integration

### Detection & Response (6)
- `adr` - Adaptive Threat Response
- `malware` - Malware analysis
- `detect` - Detection engine (YARA/Sigma)
- `hunt` - Threat hunting
- `incident` - Incident response
- `policy` - Policy-as-code

### Analytics & Intelligence (4)
- `analytics` - Advanced analytics & ML
- `threat_intel` - Threat intelligence platform
- `ask` - AI conversational engine
- `investigate` - AI-orchestrated investigation

### Compliance & Governance (2)
- `compliance` - Multi-framework compliance
- `dlp` - Data loss prevention

### Integration & Automation (6)
- `siem` - SIEM integration
- `osint` - OSINT operations
- `script` - VScript workflow automation
- `plugin` - Plugin management
- `project` - Workspace management
- `menu` - Interactive menu

### AI & Advanced (8)
- `cognitive` - Cognitive services (FASE 1 + 8)
- `offensive` - Offensive security arsenal
- `immunis` - AI immune system (FASE 4 + 9)
- `distributed` - Distributed organism (FASE 10)
- `hcl` - Human-centric language
- `memory` - Memory system management
- `tui` - Full-screen TUI dashboard
- `shell` - Interactive shell

**Total: 34 commands** with 100+ subcommands

## Examples

```bash
# Threat hunting with completion
vcli hunt query --type <TAB>
# Shows: ioc, domain, ip, hash, ...

# Maximus AI chat
vcli maximus chat --mode <TAB>
# Shows: assistant, analyst, investigator, ...

# OSINT operations
vcli osint search --source <TAB>
# Shows: social, email, phone, domain, ...

# Memory management
vcli memory search --type <TAB>
# Shows: vector, semantic, temporal, ...

# Script execution
vcli script run <TAB>
# Shows available VScript files

# Service monitoring
vcli monitor logs <TAB>
# Shows: maximus-core, narrative-filter, all service names...
```

## License

Part of the VÉRTICE Platform
Copyright © 2025 JuanCS-Dev
