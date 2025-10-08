# vCLI Shell Commands Reference

Complete reference for vCLI Interactive Shell commands.

---

## Slash Commands

Slash commands provide quick access to shell features.

### `/help` (aliases: `/h`, `/?`)

**Description**: Display shell help and keyboard shortcuts

**Usage**:
```bash
┃ /help
┃ /?
```

**Output**:
- List of slash commands
- Keyboard shortcuts
- Autocomplete features
- Usage examples

---

### `/palette` (alias: `/p`)

**Description**: Open interactive command palette with fuzzy search

**Usage**:
```bash
┃ /palette
┃ /p
```

**Features**:
- Fuzzy search across all commands
- Real-time filtering
- Keyboard navigation (↑↓)
- Execute with Enter

**Example**:
```
╭─ Command Palette ─────────────────────────────────╮
│ Search: kube                                       │
├────────────────────────────────────────────────────┤
│ → k8s get pods              List all pods          │
│   k8s get nodes             List cluster nodes     │
╰────────────────────────────────────────────────────╯
```

---

### `/exit` (aliases: `/quit`, `/q`)

**Description**: Exit the interactive shell

**Usage**:
```bash
┃ /exit
┃ /quit
┃ /q
```

**Note**: You can also use `Ctrl+D` to exit.

---

### `/clear` (alias: `/cls`)

**Description**: Clear the terminal screen

**Usage**:
```bash
┃ /clear
┃ /cls
```

**Effect**: Clears screen and redraws banner + statusline

---

### `/history`

**Description**: Show command history

**Usage**:
```bash
┃ /history
```

**Output**: Last 20 commands executed in the current session

**Example**:
```
Command History:
──────────────────────────────────────────────────
  1. k8s get pods
  2. k8s get nodes
  3. orchestrate offensive apt-simulation
```

---

## vCLI Commands

All standard vCLI commands work without the `vcli` prefix.

### Kubernetes Commands

```bash
# List resources
┃ k8s get pods
┃ k8s get pods --all-namespaces
┃ k8s get pods --namespace kube-system
┃ k8s get deployments
┃ k8s get nodes
┃ k8s get services

# Describe resources
┃ k8s describe pod nginx-7848d4b86f-9xvzk
┃ k8s describe deployment my-app

# Logs
┃ k8s logs nginx-7848d4b86f-9xvzk
┃ k8s logs my-pod --follow
┃ k8s logs my-pod --tail 100

# Scale
┃ k8s scale deployment nginx --replicas=3

# Delete
┃ k8s delete pod my-pod
┃ k8s delete deployment my-app

# Apply
┃ k8s apply -f deployment.yaml

# Top (metrics)
┃ k8s top nodes
┃ k8s top pods
┃ k8s top pod my-pod --containers
```

---

### Orchestration Commands

```bash
# Offensive workflows
┃ orchestrate offensive apt-simulation
┃ orchestrate offensive target-assessment

# Defensive workflows
┃ orchestrate defensive threat-hunting
┃ orchestrate defensive threat-response

# OSINT workflows
┃ orchestrate osint deep-investigation
┃ orchestrate osint actor-profiling

# Monitoring workflows
┃ orchestrate monitoring security-posture
┃ orchestrate monitoring anomaly-response
```

---

### Data Commands

```bash
# Query Seriema graph
┃ data query "MATCH (n) RETURN n LIMIT 10"
┃ data query "MATCH (n:Entity) WHERE n.name = 'test' RETURN n"

# Ingest data
┃ data ingest --file data.json
┃ data ingest --source /path/to/data
```

---

### Investigation Commands

```bash
# Launch investigation workspace
┃ investigate

# Query specific entity
┃ investigate entity "192.168.1.1"
┃ investigate entity "malware.exe"
```

---

### Immune System Commands

```bash
# Check immune system status
┃ immune status

# Run security scan
┃ immunis scan

# View threat intelligence
┃ threat analyze
```

---

### MAXIMUS AI Commands

```bash
# Ask MAXIMUS AI
┃ maximus ask "What are the current threats?"
┃ maximus ask "Analyze this behavior pattern"

# Consciousness metrics
┃ maximus consciousness
```

---

### Metrics Commands

```bash
# Show system metrics
┃ metrics

# Show specific service metrics
┃ metrics --service immune
┃ metrics --service maximus
```

---

## Command Flags

### Global Flags

Available for most commands:

| Flag | Short | Description |
|------|-------|-------------|
| `--help` | `-h` | Show help for command |
| `--output` | `-o` | Output format (json, yaml, table) |
| `--namespace` | `-n` | Kubernetes namespace |
| `--all-namespaces` | | List resources from all namespaces |
| `--kubeconfig` | | Path to kubeconfig file |

---

## Output Formats

### Table Format (default)

```bash
┃ k8s get pods

NAME                     STATUS    AGE
nginx-7848d4b86f-9xvzk  Running   2d
postgres-5b9c8d7f-x7k2n  Running   5m
```

### JSON Format

```bash
┃ k8s get pods --output json

{
  "items": [
    {
      "metadata": {"name": "nginx-7848d4b86f-9xvzk"},
      "status": {"phase": "Running"}
    }
  ]
}
```

### YAML Format

```bash
┃ k8s get pods --output yaml

items:
- metadata:
    name: nginx-7848d4b86f-9xvzk
  status:
    phase: Running
```

---

## Autocomplete

### Context-Aware Suggestions

The shell provides intelligent autocomplete based on context:

```bash
# After typing "k8s"
k8s → get, describe, logs, delete, scale, apply, etc.

# After typing "k8s get"
k8s get → pods, nodes, deployments, services, namespaces, etc.

# After typing "k8s get pods"
k8s get pods → --namespace, --all-namespaces, --output, etc.
```

### Fuzzy Matching

Type abbreviations for faster command entry:

```bash
kgp → k8s get pods
kgd → k8s get deployments
kgn → k8s get nodes
orch off → orchestrate offensive
```

---

## History Navigation

### Arrow Keys

- `↑` (Up): Previous command in history
- `↓` (Down): Next command in history

### Search History

Type a prefix and press `↑` to search backwards through matching commands:

```bash
# Type "k8s" and press ↑ to find last k8s command
┃ k8s ↑ → k8s get pods --all-namespaces
```

---

## Special Features

### Statusline

When connected to a Kubernetes cluster, the shell displays context:

```
⎈ Context: production-cluster │ Namespace: default │ Cluster: my-cluster
```

### Spinner

Long-running operations show a spinner:

```
⠋ Fetching pods from namespace default...
✓ Found 23 pods
```

### Error Suggestions

When you mistype a command, the shell suggests corrections:

```bash
┃ k8s get pod

✗ Command not found: "k8s get pod"

Did you mean?
  → k8s get pods
  → k8s get pod [name]
```

---

## Tips & Tricks

### 1. Use Tab Completion

Press `Tab` after typing partial commands:

```bash
┃ k8s g[Tab] → k8s get
┃ k8s get p[Tab] → k8s get pods
```

### 2. Quick Palette Access

`/p` is faster than typing full commands:

```bash
┃ /p → [type filter] → [Enter]
```

### 3. Explore Unknown Commands

Not sure what's available? Press `Tab` on empty input to see common commands.

### 4. Clear Screen Quickly

`/cls` is faster than typing `/clear`.

### 5. Chain Commands

Some operations can be chained:

```bash
┃ k8s scale deployment nginx --replicas=3 && k8s get pods
```

---

## Environment Variables

vCLI respects these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` |
| `VCLI_LOG_LEVEL` | Logging verbosity | `debug`, `info`, `warn` |
| `VCLI_OUTPUT` | Default output format | `table`, `json`, `yaml` |

---

## Related Documentation

- [Keyboard Shortcuts](./KEYBOARD_SHORTCUTS.md) - Complete keyboard reference
- [Configuration](./CONFIGURATION.md) - vCLI configuration options
- [Autocomplete Guide](./AUTOCOMPLETE.md) - Detailed autocomplete behavior

---

**Last Updated**: 2025-10-07
**vCLI Version**: 2.0+
