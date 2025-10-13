# VCLI Natural Language Processing - User Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-13
**Authors:** Juan Carlos & Claude (MAXIMUS AI)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Supported Languages](#supported-languages)
4. [Command Examples](#command-examples)
5. [Interactive Shell](#interactive-shell)
6. [API Usage](#api-usage)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

VCLI's Natural Language Processing (NLP) engine allows you to interact with Kubernetes and other systems using natural language in Portuguese (PT-BR) or English. Instead of remembering complex command syntax, simply describe what you want to do in your own words.

### Features

- ✅ **Multi-language Support** - Portuguese (PT-BR) and English
- ✅ **Smart Suggestions** - "Did you mean?" functionality
- ✅ **Typo Correction** - Automatic typo detection and correction
- ✅ **Context Awareness** - Remembers your recent commands
- ✅ **Adaptive Learning** - Gets smarter with use
- ✅ **Safety Features** - Confirms dangerous operations
- ✅ **Fast Performance** - ~0.2ms response time

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/verticedev/vcli-go.git
cd vcli-go

# Build
go build -o bin/vcli ./cmd/

# Run interactive shell
./examples/nlp-shell/main.go
```

### Your First Query

Try these simple commands:

**Portuguese:**
```bash
vcli nlp "mostra os pods"
# → vcli k8s get pods

vcli nlp "lista pods no namespace production"
# → vcli k8s get pods -n production
```

**English:**
```bash
vcli nlp "show me the pods"
# → vcli k8s get pods

vcli nlp "list pods in production namespace"
# → vcli k8s get pods -n production
```

---

## Supported Languages

### Portuguese (PT-BR)

**Verbs Recognized:**
- `mostra`, `lista`, `exibe` → get/list
- `escala` → scale
- `deleta`, `remove` → delete
- `cria`, `aplica` → create/apply
- `atualiza` → update

**Example Queries:**
```bash
# Simple query
mostra os pods

# With namespace
lista deployments no namespace prod

# With filter
pods com problema no production

# Scale operation
escala nginx para 5 replicas
```

### English

**Verbs Recognized:**
- `show`, `list`, `display` → get/list
- `scale` → scale
- `delete`, `remove` → delete
- `create`, `apply` → create/apply
- `update` → update

**Example Queries:**
```bash
# Simple query
show the pods

# With namespace
list deployments in prod namespace

# With filter
show failed pods in production

# Scale operation
scale nginx to 5 replicas
```

---

## Command Examples

### Kubernetes Queries

#### List Resources

**Portuguese:**
```bash
mostra todos os pods
lista deployments
exibe services no namespace default
```

**English:**
```bash
show all pods
list deployments
display services in default namespace
```

#### Filtered Queries

**Portuguese:**
```bash
pods com problema no prod
deployments rodando no staging
services do tipo LoadBalancer
```

**English:**
```bash
failed pods in prod
running deployments in staging
LoadBalancer type services
```

#### Scale Operations

**Portuguese:**
```bash
escala nginx para 3 replicas
aumenta frontend para 5 instancias
```

**English:**
```bash
scale nginx to 3 replicas
scale frontend to 5 instances
```

#### Dangerous Operations

**Portuguese:**
```bash
deleta pod nginx-123
remove todos os pods no namespace test
```

**English:**
```bash
delete pod nginx-123
remove all pods in test namespace
```

⚠️ **Note:** Dangerous operations require confirmation!

---

## Interactive Shell

### Starting the Shell

```bash
go run ./examples/nlp-shell/main.go
```

### Shell Commands

| Command | Description |
|---------|-------------|
| `help` or `?` | Show help |
| `stats` | Show processing statistics |
| `popular` | Show popular commands |
| `suggest` | Get suggestions for partial input |
| `clear` | Clear screen |
| `exit` or `quit` or `q` | Exit shell |

### Example Session

```bash
╔════════════════════════════════════════════════════════════════╗
║          VCLI Natural Language Processing Shell                ║
║              Powered by MAXIMUS AI Engine                      ║
╚════════════════════════════════════════════════════════════════╝

Initializing NLP engine... ✓

vcli> mostra os pods

⚙  Processing...

┌─ Analysis
│ Input: "mostra os pods"
│ Intent: show (QUERY, 80.0% confidence)
│ Entities: K8S_RESOURCE=pods
│ Latency: 0.18ms
└─────────

┌─ Generated Command
│ vcli k8s get pods
└──────────────────

💾 Pattern learned (ID: 6d6f7374...)
✓ Ready to execute

vcli> stats

📊 Statistics:
  Total Requests:    1
  Successful:        1
  Failed:            0
  Validation Errors: 0
  Avg Latency:       0.18ms

📚 Learning Engine:
  Total Patterns:  1
  Cache Hit Rate:  0.0%
  Avg Success:     100.0%

vcli> exit
Goodbye! 👋
```

---

## API Usage

### Basic Usage

```go
package main

import (
    "fmt"
    "github.com/verticedev/vcli-go/internal/nlp"
)

func main() {
    // Create orchestrator
    orch, err := nlp.NewOrchestrator("/path/to/learning.db")
    if err != nil {
        panic(err)
    }
    defer orch.Close()

    // Process natural language input
    result, err := orch.Process("show the pods", "session-123")
    if err != nil {
        panic(err)
    }

    // Check if successful
    if result.Success {
        fmt.Printf("Command: %s\n", result.Command)
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
    orch, _ := nlp.NewOrchestrator("/path/to/db")
    defer orch.Close()

    // Process with feedback
    feedback := &learning.Feedback{
        Success:  true,
        Accepted: true,
    }

    result, err := orch.ProcessWithFeedback(
        "scale nginx to 5",
        "session-123",
        feedback,
    )

    if result.Success {
        // Execute command
        executeCommand(result.Command)
    }
}
```

### Getting Suggestions

```go
func main() {
    orch, _ := nlp.NewOrchestrator("/path/to/db")
    defer orch.Close()

    // Get suggestions for partial input
    suggestions := orch.GetSuggestions("sho")

    for _, sug := range suggestions {
        fmt.Println("Suggestion:", sug)
    }
}
```

### Popular Commands

```go
func main() {
    orch, _ := nlp.NewOrchestrator("/path/to/db")
    defer orch.Close()

    // Get top 10 popular commands
    popular, err := orch.GetPopularCommands(10)
    if err != nil {
        panic(err)
    }

    for i, pattern := range popular {
        fmt.Printf("%d. %s (used %d times)\n",
            i+1, pattern.Input, pattern.Frequency)
    }
}
```

---

## Advanced Features

### Context Awareness

The NLP engine remembers your recent commands and context:

```bash
# First command sets context
vcli> show pods in production
✓ Command: vcli k8s get pods -n production

# Second command uses previous namespace
vcli> show deployments
✓ Command: vcli k8s get deployments -n production  # Uses "production" from context
```

### Adaptive Learning

The engine learns from your usage patterns:

```bash
# First time using a phrase
vcli> mostra os pods ativos
→ Pattern learned

# Second time is faster and smarter
vcli> mostra os pods ativos
→ Using learned pattern (0.05ms)
```

### Safety Features

Dangerous operations require confirmation:

```bash
vcli> delete all pods in production

⚠️  WARNING: 'delete' is a destructive operation
Proceed? (yes/no): _
```

### Typo Correction

Automatic typo detection and correction:

```bash
vcli> lst deploiments
→ Did you mean: "list deployments"?
```

---

## Troubleshooting

### Common Issues

#### 1. "Database Error"

**Problem:** Cannot create learning database

**Solution:**
```bash
# Ensure directory exists
mkdir -p ~/.vcli

# Check permissions
chmod 755 ~/.vcli
```

#### 2. "Intent Not Recognized"

**Problem:** Your query isn't understood

**Solution:**
- Try using simpler language
- Use recognized verbs (show, list, scale, delete)
- Check examples in this guide

#### 3. "Validation Failed"

**Problem:** Generated command is invalid

**Solution:**
- Check the suggestions provided
- Verify resource names and namespaces
- Try rephrasing your query

### Getting Help

1. **In Shell:** Type `help` or `?`
2. **Documentation:** See `/docs` directory
3. **Examples:** Check `/examples` directory
4. **Issues:** Report at GitHub issues

---

## Performance Tips

### 1. Use Learning Database

The learning database makes repeated queries faster:

```go
// Store in home directory for persistence
dbPath := filepath.Join(os.UserHomeDir(), ".vcli", "nlp.db")
orch, _ := nlp.NewOrchestrator(dbPath)
```

### 2. Reuse Sessions

Reuse session IDs for better context:

```go
sessionID := "my-session"
result1, _ := orch.Process("show pods", sessionID)
result2, _ := orch.Process("show deployments", sessionID)
```

### 3. Cache Popular Commands

Frequently used commands are cached automatically:

```go
// First call: ~0.2ms
result, _ := orch.Process("show pods", session)

// Subsequent calls: ~0.05ms (cached)
result, _ := orch.Process("show pods", session)
```

---

## API Reference

### Orchestrator

#### NewOrchestrator

```go
func NewOrchestrator(learningDBPath string) (*Orchestrator, error)
```

Creates a new NLP orchestrator with learning database.

**Parameters:**
- `learningDBPath` - Path to BadgerDB database

**Returns:**
- `*Orchestrator` - Orchestrator instance
- `error` - Error if creation fails

#### Process

```go
func (o *Orchestrator) Process(input string, sessionID string) (*ProcessingResult, error)
```

Processes natural language input through complete pipeline.

**Parameters:**
- `input` - Natural language query
- `sessionID` - Session identifier

**Returns:**
- `*ProcessingResult` - Processing result
- `error` - Error if processing fails

#### ProcessWithFeedback

```go
func (o *Orchestrator) ProcessWithFeedback(
    input string,
    sessionID string,
    feedback *learning.Feedback,
) (*ProcessingResult, error)
```

Processes input and records feedback for learning.

#### GetSuggestions

```go
func (o *Orchestrator) GetSuggestions(input string) []validator.Suggestion
```

Returns suggestions for incomplete input.

#### GetPopularCommands

```go
func (o *Orchestrator) GetPopularCommands(limit int) ([]*learning.Pattern, error)
```

Returns most frequently used patterns.

#### GetStats

```go
func (o *Orchestrator) GetStats() *OrchestratorStats
```

Returns orchestrator statistics.

#### Close

```go
func (o *Orchestrator) Close() error
```

Closes orchestrator and releases resources.

---

## Examples Directory

The `/examples` directory contains:

### nlp-simple
Basic API usage with 6 examples:
```bash
go run ./examples/nlp-simple/main.go
```

### nlp-shell
Interactive shell with full features:
```bash
go run ./examples/nlp-shell/main.go
```

---

## Best Practices

### 1. Always Close Resources

```go
orch, err := nlp.NewOrchestrator(dbPath)
if err != nil {
    return err
}
defer orch.Close()  // Always close!
```

### 2. Handle Dangerous Operations

```go
if result.Validation != nil && result.Validation.RequiresConfirmation {
    if !getUserConfirmation() {
        return fmt.Errorf("operation cancelled")
    }
}
```

### 3. Record Feedback

```go
// Record execution result for learning
feedback := &learning.Feedback{
    PatternID: result.PatternID,
    Success:   executionSucceeded,
    Accepted:  true,
}
orch.ProcessWithFeedback(input, sessionID, feedback)
```

### 4. Use Statistics

```go
// Monitor performance
stats := orch.GetStats()
if stats.AverageLatencyMs > 50 {
    log.Warn("NLP performance degraded")
}
```

---

## Conclusion

VCLI's NLP engine makes Kubernetes management natural and intuitive. With support for Portuguese and English, smart learning, and safety features, it's designed for real-world production use.

**Quick Links:**
- [Architecture Documentation](./architecture/vcli-go/natural-language-parser-blueprint.md)
- [API Reference](./API_REFERENCE.md)
- [Examples](../examples/)
- [GitHub Issues](https://github.com/verticedev/vcli-go/issues)

**Questions?** Check `/docs` or file an issue on GitHub.

---

*Generated: 2025-10-13*
*MAXIMUS Quality Standard - Production Ready*
