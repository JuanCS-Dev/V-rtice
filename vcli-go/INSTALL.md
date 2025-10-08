# vCLI-Go Installation Guide

**Quick installation guide for vCLI-Go (Go implementation)**

---

## 🚀 Quick Install

```bash
# 1. Build binary
go build -o bin/vcli ./cmd/

# 2. Run installer
./install.sh

# 3. Add aliases to your shell config
echo 'source ~/.local/bin/vcli-go-aliases.sh' >> ~/.bashrc
# OR for zsh:
echo 'source ~/.local/bin/vcli-go-aliases.sh' >> ~/.zshrc

# 4. Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

---

## 📦 What Gets Installed

1. **Binary**: `bin/vcli` (built from source)
2. **Symlink**: `~/.local/bin/vcli-go` → binary
3. **Aliases**: `~/.local/bin/vcli-go-aliases.sh`

### Aliases Available
```bash
vcli-go   # Full command
vgo       # Short alias
```

---

## ✅ Verify Installation

```bash
# Check version
vcli-go version

# Should show:
# vCLI version 2.0.0
# Build date: 2025-10-07
# Go implementation: High-performance TUI
```

---

## 🎮 Usage

### Interactive Shell (Requires TTY)

```bash
# Modern bubble-tea shell (default)
vcli-go shell

# Legacy go-prompt shell
vcli-go shell --legacy
```

**⚠️ Shell requires a real terminal (TTY)**
- ✅ Works: Local terminal, tmux, ssh -t
- ❌ Won't work: Pipes, Claude Code terminal, SSH without -t

### Direct Commands (No TTY needed)

```bash
# Kubernetes
vcli-go k8s get pods
vcli-go k8s get nodes --all-namespaces
vcli-go k8s describe pod nginx-xxx

# Orchestration
vcli-go orchestrate offensive apt-simulation
vcli-go orchestrate defensive threat-hunting

# Help
vcli-go --help
vcli-go k8s --help
```

---

## 🔧 Manual Installation (Alternative)

If `install.sh` doesn't work:

```bash
# 1. Build
go build -o bin/vcli ./cmd/

# 2. Copy to PATH
sudo cp bin/vcli /usr/local/bin/vcli-go

# 3. Make executable
sudo chmod +x /usr/local/bin/vcli-go

# 4. Test
vcli-go version
```

---

## 📁 Directory Structure

```
vcli-go/
├── bin/
│   └── vcli              # Built binary
├── cmd/                  # Main entry point
├── internal/             # Implementation
│   ├── shell/
│   │   ├── bubbletea/   # Modern shell (default)
│   │   ├── completer.go
│   │   ├── executor.go
│   │   └── shell.go      # Legacy shell
│   ├── k8s/             # Kubernetes integration
│   ├── palette/         # Command palette
│   └── visual/          # UI components
├── docs/                # Documentation
├── install.sh           # Installer script
└── go.mod              # Dependencies
```

---

## 🐛 Troubleshooting

### Error: "command not found: vcli-go"

**Solution 1**: Check PATH
```bash
echo $PATH | grep -q "$HOME/.local/bin" && echo "OK" || echo "NOT IN PATH"
```

If not in PATH, add to `~/.bashrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Solution 2**: Use full path
```bash
~/.local/bin/vcli-go version
```

### Error: "Interactive shell requires a terminal (TTY)"

**Cause**: Running without a real terminal

**Solutions**:
- Use local terminal (not Claude Code)
- SSH: add `-t` flag: `ssh -t user@host vcli-go shell`
- Use tmux/screen
- Or use direct commands: `vcli-go k8s get pods`

### Conflict with Python vcli

If you have Python vcli installed:
```bash
# Python version
vcli version

# Go version
vcli-go version
# or
vgo version
```

---

## 🔄 Update

```bash
# 1. Pull latest code
git pull

# 2. Rebuild
go build -o bin/vcli ./cmd/

# 3. Reinstall
./install.sh
```

---

## 🗑️ Uninstall

```bash
# Remove symlink
rm ~/.local/bin/vcli-go

# Remove aliases
rm ~/.local/bin/vcli-go-aliases.sh

# Remove from shell config (manual)
# Edit ~/.bashrc or ~/.zshrc and remove:
#   source ~/.local/bin/vcli-go-aliases.sh
```

---

## 📚 Documentation

- **UX Overview**: `docs/UX_OVERHAUL_COMPLETE.md`
- **Testing Guide**: `docs/SHELL_TESTING_GUIDE.md`
- **Keyboard Shortcuts**: `docs/KEYBOARD_SHORTCUTS.md`
- **Shell Commands**: `docs/SHELL_COMMANDS.md`

---

## ✨ Features

### Modern Shell (bubble-tea)
- ✨ Autocomplete appears as you type
- 📦 Icons for commands
- ⌨️  Full keyboard navigation
- 🎨 Visual feedback
- ⎈ K8s statusline (context, namespace)
- Bottom toolbar with keybindings

### Legacy Shell (go-prompt)
- Tab completion
- Command history
- Basic autocomplete

---

## 🎯 Quick Start

```bash
# Install
./install.sh
source ~/.bashrc

# Test
vcli-go version

# Interactive (in real terminal)
vcli-go shell

# Direct command
vcli-go k8s get pods --help
```

---

**Created**: 2025-10-07
**Version**: 2.0.0
**Go Version**: 1.24+
