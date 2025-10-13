# VCLI NLP Examples

This directory contains working examples demonstrating the VCLI Natural Language Processing engine.

---

## Available Examples

### 1. nlp-simple - Basic API Usage

Simple demonstration of NLP API with 6 examples.

**Run:**
```bash
go run ./examples/nlp-simple/main.go
```

**Features Demonstrated:**
- Simple Portuguese query
- Query with namespace
- English scale command
- Query with filters
- Typo handling
- Dangerous operation detection

**Sample Output:**
```
=== Example 1: Simple Query (Portuguese) ===
Input: "mostra os pods"
Success: true
Intent: show (QUERY, confidence: 80.0%)
Command: vcli k8s get pods
Latency: 0.15ms
```

---

### 2. nlp-shell - Interactive Shell

Full-featured interactive shell with NLP support.

**Run:**
```bash
go run ./examples/nlp-shell/main.go
```

**Features:**
- ✅ Interactive REPL
- ✅ Color-coded output
- ✅ Statistics tracking
- ✅ Popular commands
- ✅ Smart suggestions
- ✅ Pattern learning
- ✅ Multi-language support

**Available Commands:**
- `help` or `?` - Show help
- `stats` - Show statistics
- `popular` - Show popular commands
- `suggest` - Get suggestions
- `clear` - Clear screen
- `exit` or `quit` - Exit shell

**Sample Session:**
```bash
╔════════════════════════════════════════════════════════════════╗
║          VCLI Natural Language Processing Shell                ║
║              Powered by MAXIMUS AI Engine                      ║
╚════════════════════════════════════════════════════════════════╝

vcli> mostra os pods no namespace production

⚙  Processing...

┌─ Analysis
│ Input: "mostra os pods no namespace production"
│ Intent: show (QUERY, 80.0% confidence)
│ Entities: K8S_RESOURCE=pods, NAMESPACE=production
│ Latency: 0.18ms
└─────────

┌─ Generated Command
│ vcli k8s get pods -n production
└──────────────────

💾 Pattern learned
✓ Ready to execute

vcli> stats

📊 Statistics:
  Total Requests:    1
  Successful:        1
  Avg Latency:       0.18ms

vcli> exit
Goodbye! 👋
```

---

## Example Queries

### Portuguese (PT-BR)

```bash
# Simple queries
mostra os pods
lista deployments
exibe services

# With namespace
lista pods no namespace production
mostra deployments no prod

# With filters
pods com problema no prod
deployments rodando no staging

# Scale operations
escala nginx para 5 replicas
aumenta frontend para 3 instancias

# Dangerous operations (requires confirmation)
deleta pod nginx-123
remove todos os pods no test
```

### English

```bash
# Simple queries
show the pods
list deployments
display services

# With namespace
list pods in production namespace
show deployments in prod

# With filters
show failed pods in prod
running deployments in staging

# Scale operations
scale nginx to 5 replicas
scale frontend to 3 instances

# Dangerous operations (requires confirmation)
delete pod nginx-123
remove all pods in test namespace
```

---

## Building Examples

### Build Individual Examples

```bash
# Build simple example
go build -o bin/nlp-simple ./examples/nlp-simple/

# Build interactive shell
go build -o bin/nlp-shell ./examples/nlp-shell/

# Run built binaries
./bin/nlp-simple
./bin/nlp-shell
```

### Build All Examples

```bash
# From project root
go build -o bin/ ./examples/...

# Run
./bin/nlp-simple
./bin/nlp-shell
```

---

## Integration in Your Code

### Basic Integration

```go
package main

import (
    "fmt"
    "os"
    "path/filepath"

    "github.com/verticedev/vcli-go/internal/nlp"
)

func main() {
    // Create learning database path
    homeDir, _ := os.UserHomeDir()
    dbPath := filepath.Join(homeDir, ".vcli", "nlp.db")

    // Create orchestrator
    orch, err := nlp.NewOrchestrator(dbPath)
    if err != nil {
        panic(err)
    }
    defer orch.Close()

    // Process natural language
    result, err := orch.Process("show the pods", "my-session")
    if err != nil {
        panic(err)
    }

    // Check result
    if result.Success {
        fmt.Printf("Command: %s\n", result.Command)
        // Execute command here
    } else {
        fmt.Printf("Error: %s\n", result.Error)
    }
}
```

### With Feedback

```go
import (
    "github.com/verticedev/vcli-go/internal/nlp"
    "github.com/verticedev/vcli-go/internal/nlp/learning"
)

func main() {
    orch, _ := nlp.NewOrchestrator(dbPath)
    defer orch.Close()

    // Process with feedback
    feedback := &learning.Feedback{
        Success:  true,
        Accepted: true,
    }

    result, _ := orch.ProcessWithFeedback(
        "scale nginx to 5",
        "session-123",
        feedback,
    )

    if result.Success {
        executeCommand(result.Command)
    }
}
```

---

## Performance

Expected performance on modern hardware:

| Operation | Latency | Notes |
|-----------|---------|-------|
| Simple Query | ~0.15-0.20ms | First time |
| Cached Query | ~0.05ms | Pattern cached |
| With Namespace | ~0.18ms | Additional entity |
| Scale Command | ~0.21ms | Multiple entities |

**Capacity:** ~4,700 requests/second

---

## Requirements

- Go 1.21+
- BadgerDB (included in go.mod)
- No external dependencies

---

## Troubleshooting

### Database Permission Issues

```bash
mkdir -p ~/.vcli
chmod 755 ~/.vcli
```

### Import Errors

Ensure you're running from the project root:
```bash
cd /path/to/vcli-go
go run ./examples/nlp-simple/main.go
```

### Build Errors

Clean and rebuild:
```bash
go clean -cache
go mod tidy
go build ./examples/...
```

---

## Documentation

For complete documentation, see:
- [NLP User Guide](../docs/NLP_USER_GUIDE.md)
- [NLP Complete Report](../docs/NLP_COMPLETE.md)
- [NLP Status](../docs/NLP_STATUS.md)

---

## Support

Questions or issues? Check:
1. Documentation in `/docs`
2. Source code comments (godoc)
3. GitHub issues

---

*VCLI NLP Examples - Production Ready*
*MAXIMUS Quality Standard*
