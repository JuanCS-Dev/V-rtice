# Keyboard Shortcuts - vCLI Interactive Shell

**vCLI** provides a rich set of keyboard shortcuts for efficient navigation and command execution.

---

## Navigation

| Shortcut | Action |
|----------|--------|
| `Tab` | Trigger autocomplete / Move to next suggestion |
| `↓` (Down Arrow) | Move to next suggestion |
| `↑` (Up Arrow) | Move to previous suggestion |
| `Enter` | Execute current command / Select suggestion |
| `Ctrl+C` | Cancel current input (clear buffer) |
| `Ctrl+D` | Exit shell |

---

## Editing

| Shortcut | Action |
|----------|--------|
| `←` (Left Arrow) | Move cursor left |
| `→` (Right Arrow) | Move cursor right |
| `Ctrl+A` | Move to beginning of line |
| `Ctrl+E` | Move to end of line |
| `Ctrl+W` | Delete word before cursor |
| `Ctrl+K` | Delete from cursor to end of line |
| `Ctrl+U` | Delete from cursor to beginning of line |
| `Backspace` | Delete character before cursor |
| `Delete` | Delete character at cursor |

---

## History

| Shortcut | Action |
|----------|--------|
| `↑` (when input empty) | Navigate command history backwards |
| `↓` (when input empty) | Navigate command history forwards |
| `Ctrl+R` | Reverse search history *(planned)* |

---

## Slash Commands

Slash commands provide quick access to shell features:

| Command | Shortcut | Action |
|---------|----------|--------|
| `/help` | `/h`, `/?` | Show shell help |
| `/palette` | `/p` | Open command palette (fuzzy search) |
| `/exit` | `/quit`, `/q` | Exit shell |
| `/clear` | `/cls` | Clear screen |
| `/history` | - | Show command history |

---

## Autocomplete Behavior

### Smart Context Detection

**vCLI autocomplete** adapts based on what you're typing:

```bash
# Typing a slash
/ → Shows all slash commands (/help, /palette, etc.)

# K8s commands
k8s → Shows k8s subcommands (get, describe, logs, etc.)
k8s get → Shows resources (pods, nodes, deployments, etc.)
k8s get pods → Shows flags (--namespace, --all-namespaces, etc.)

# Orchestrate workflows
orchestrate → Shows categories (offensive, defensive, osint, etc.)
orchestrate offensive → Shows workflows (apt-simulation, target-assessment)

# Flags
--n → Shows --namespace, --name, etc.
-n → Shows -n (namespace shorthand)
```

### Fuzzy Matching

Autocomplete supports fuzzy matching for faster typing:

```bash
kgp → suggests "k8s get pods"
kgd → suggests "k8s get deployments"
orch off → suggests "orchestrate offensive"
```

### Trailing Space Behavior

**Important**: When you finish typing a word and press space, autocomplete hides to prevent visual clutter:

```bash
k8s ← Space pressed → No suggestions (waiting for next word)
k8s get ← Space pressed → No suggestions (waiting for resource)
```

This prevents the "sticky autocomplete" bug where suggestions stay on screen during cursor navigation.

---

## Command Palette

**Open with**: `/palette` or `/p`

The command palette provides fuzzy search across all available commands:

```
╭─ Command Palette ─────────────────────────────────────────────────╮
│ Search: kube                                                       │
├────────────────────────────────────────────────────────────────────┤
│ → k8s get pods                List all pods                        │
│   k8s get nodes               List cluster nodes                   │
│   k8s describe pod            Describe a specific pod              │
│   k8s logs                    View pod logs                        │
╰────────────────────────────────────────────────────────────────────╯
```

**Palette Shortcuts**:
- `↑↓` - Navigate suggestions
- `Enter` - Execute selected command
- `Esc` - Close palette
- Type to filter

---

## Terminal Size

vCLI adapts to your terminal size:

- **Minimum width**: 80 columns (recommended)
- **Responsive**: Banner, statusline, and tables adjust automatically
- **Small terminals**: Components gracefully degrade (no panic)

---

## Special Characters

### Unicode Support

vCLI fully supports Unicode input:

```bash
┃ echo "你好世界"  ← Unicode works
┃ k8s get pods --label="app=café"  ← Accents work
```

### Quoting

Use quotes for arguments with spaces:

```bash
k8s logs my-pod --tail "last 100 lines"
k8s annotate pod nginx description="Production web server"
```

---

## Tips & Tricks

### 1. Fast Navigation with Fuzzy Search

Instead of typing full commands:
```bash
# Instead of: k8s get pods --all-namespaces
# Type: kgp --all  → Tab → Select suggestion
```

### 2. Use Slash Commands for Quick Actions

```bash
/p  → Opens palette (faster than /palette)
/?  → Shows help (faster than /help)
/q  → Quick exit
```

### 3. Explore with Tab

Don't know what's available? Just press Tab:
```bash
k8s → Tab → See all k8s subcommands
k8s get → Tab → See all resources
```

### 4. Arrow Keys Navigate History

Press `↑` on empty input to recall previous commands.

### 5. Ctrl+C Clears Buffer

Made a typo? `Ctrl+C` clears current input without exiting.

---

## Compatibility

### Tested Terminals

- ✅ **iTerm2** (macOS)
- ✅ **Terminal.app** (macOS)
- ✅ **GNOME Terminal** (Linux)
- ✅ **Konsole** (Linux)
- ✅ **Windows Terminal** (Windows 10+)
- ✅ **Alacritty** (Cross-platform)

### Known Issues

- **Windows CMD**: Limited color support (use Windows Terminal instead)
- **tmux**: May require `TERM=xterm-256color` for proper colors

---

## Customization *(Future)*

**Planned features**:

- Custom key bindings (`.vcli/keybindings.yaml`)
- Vi mode vs Emacs mode
- Configurable autocomplete delay
- Custom slash commands

---

## Related Documentation

- [Shell Commands](./SHELL_COMMANDS.md) - Full command reference
- [Autocomplete Guide](./AUTOCOMPLETE.md) - Detailed autocomplete behavior
- [Configuration](./CONFIGURATION.md) - vCLI configuration options

---

**Last Updated**: 2025-10-07
**vCLI Version**: 2.0+
