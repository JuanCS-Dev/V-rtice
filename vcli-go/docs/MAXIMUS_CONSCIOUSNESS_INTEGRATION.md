# MAXIMUS CONSCIOUS AI - CLI Integration

**Date**: 2025-10-07
**Status**: ✅ **SPRINT 1 COMPLETE - PRODUCTION-READY**
**Integration**: vCLI-Go ↔ MAXIMUS Consciousness API

---

## 🎯 OVERVIEW

Complete integration of the MAXIMUS Consciousness System into vCLI-Go, providing real-time monitoring and control of:
- **TIG** (Topological Information Graph) - Information fabric
- **ESGT** (Event-Salience Global Triggers) - Attention mechanism
- **Arousal Controller** - System activation level

---

## 📊 INTEGRATION SUMMARY

```
╔═══════════════════════════════════════════════════════════╗
║  MAXIMUS CONSCIOUSNESS CLI INTEGRATION                    ║
╠═══════════════════════════════════════════════════════════╣
║  HTTP Client:           ✅ Complete (300 LOC)              ║
║  CLI Commands:          ✅ 6 commands + 3 subcommands      ║
║  Formatters:            ✅ Visual output (200 LOC)         ║
║  Autocomplete:          ✅ Integrated                      ║
║  Icons:                 ✅ All commands have icons         ║
║  Documentation:         ✅ Complete                        ║
║                                                           ║
║  Total Code:            ~930 lines                        ║
║  Build Status:          ✅ SUCCESS                         ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🛠️ DELIVERABLES

### Code Created (3 files, ~930 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `internal/maximus/consciousness_client.go` | 300 | HTTP client for consciousness API |
| `internal/maximus/formatters.go` | 200 | Pretty-print formatters |
| `cmd/maximus.go` (modified) | 430 | CLI commands implementation |
| `internal/shell/completer.go` (modified) | 6 | Autocomplete entries |
| `internal/palette/icons.go` (modified) | 8 | Command icons |

---

## 📋 CLI COMMANDS

### Command Structure

```
vcli maximus consciousness
├── state                           # Get complete consciousness state
├── metrics                         # Get system metrics
├── esgt
│   ├── events [--limit N]          # Get recent ESGT events
│   └── trigger [--novelty] [--relevance] [--urgency]  # Manual trigger
└── arousal
    ├── (no args)                   # Get arousal state
    └── adjust [--delta] [--duration]  # Adjust arousal level
```

### 1. Get Consciousness State

```bash
vcli maximus consciousness state

# Output:
# MAXIMUS CONSCIOUS AI - Consciousness State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# System Health:    ✅ HEALTHY
# ESGT Status:      ⚡ ACTIVE
# Arousal Level:    0.72 ████████████████░░░░ (HIGH)
# Recent Events:    15 events
#
# TIG Metrics:
#   node_count: 100
#   edge_density: 0.25
#   ...
```

### 2. Get ESGT Events

```bash
vcli maximus consciousness esgt events --limit 20

# Output:
# ESGT Events - Timeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# [15:04:05] ✅ ESGT - evt_12345
#   Salience: N:0.89 R:0.85 U:0.92 | Coherence: 0.87 ●●●●●●●●○○
#   Nodes: 42 | Duration: 12.3ms
#
# [15:03:58] ❌ ESGT - evt_12344
#   Salience: N:0.45 R:0.62 U:0.38
#   Nodes: 18
#   Reason: Salience below threshold
```

### 3. Trigger ESGT Manually

```bash
vcli maximus consciousness esgt trigger \
  --novelty 0.9 \
  --relevance 0.8 \
  --urgency 0.7

# Output:
# ✅ ESGT ignition successful!
# Event ID: evt_67890
# Coherence: 0.823
# Duration: 15.2ms
# Nodes: 38
```

### 4. Get Arousal State

```bash
vcli maximus consciousness arousal

# Output:
# Arousal State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Current Arousal:  0.720 ████████████████░░░░
# Classification:   HIGH
# Baseline:         0.600
#
# Contributions:
#   Need:    +0.080
#   Stress:  +0.040
```

### 5. Adjust Arousal Level

```bash
vcli maximus consciousness arousal adjust \
  --delta 0.2 \
  --duration 5

# Output:
# ✅ Arousal adjusted successfully
# New arousal: 0.920 (VERY_HIGH)
# Delta: +0.200 for 5.0s
```

### 6. Get System Metrics

```bash
vcli maximus consciousness metrics

# Output:
# Consciousness Metrics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# TIG Fabric Metrics:
#   node_count:           100
#   edge_count:           250
#   density:              0.25
#   avg_degree:           5.0
#
# ESGT Statistics:
#   total_ignitions:      42
#   success_rate:         0.85
#   avg_coherence:        0.78
#   avg_duration_ms:      14.5
```

---

## 🎨 VISUAL FEATURES

### Icons

All consciousness commands have distinctive icons for easy recognition:

- 🌟 `maximus consciousness state`
- ⚡ `maximus consciousness esgt events`
- ⚡ `maximus consciousness esgt trigger`
- 📊 `maximus consciousness arousal`
- 📈 `maximus consciousness metrics`

### Color-Coded Output

- **Green** (✅): Success states, healthy status
- **Red** (❌): Failures, errors
- **Cyan**: Primary information, active states
- **Yellow/Amber**: High arousal, warnings
- **Muted gray**: Secondary information

### Progress Bars

```
Arousal Level: 0.720 ████████████████░░░░ (HIGH)
                     ^^^^^^^^^^^^^^^^^^^
                     20-char visual bar

Coherence: 0.87 ●●●●●●●●○○
               ^^^^^^^^^^
               10-char dots
```

---

## 🔧 TECHNICAL DETAILS

### HTTP Client

**Endpoint**: `http://localhost:8022/api/consciousness`

**Methods**:
- `GET /state` - Complete consciousness state
- `GET /esgt/events?limit=N` - Recent ESGT events
- `GET /arousal` - Current arousal state
- `GET /metrics` - System metrics
- `POST /esgt/trigger` - Manual ESGT ignition
- `POST /arousal/adjust` - Adjust arousal level

**Timeout**: 10 seconds
**Content-Type**: `application/json`

### Error Handling

```go
// Client validates all inputs
if salience.Novelty < 0 || salience.Novelty > 1 {
    return nil, fmt.Errorf("novelty must be between 0 and 1")
}

// Clear error messages to user
if err != nil {
    return fmt.Errorf("failed to connect to consciousness API: %w", err)
}
```

### Data Types

**Request Models**:
```go
type SalienceInput struct {
    Novelty   float64                `json:"novelty"`    // 0-1
    Relevance float64                `json:"relevance"`  // 0-1
    Urgency   float64                `json:"urgency"`    // 0-1
    Context   map[string]interface{} `json:"context,omitempty"`
}

type ArousalAdjustment struct {
    Delta           float64 `json:"delta"`             // -0.5 to 0.5
    DurationSeconds float64 `json:"duration_seconds"`   // 0.1-60
    Source          string  `json:"source"`
}
```

**Response Models**:
```go
type ConsciousnessState struct {
    Timestamp             string
    ESGTActive            bool
    ArousalLevel          float64
    ArousalClassification string
    TIGMetrics            map[string]interface{}
    RecentEventsCount     int
    SystemHealth          string
}

type ESGTEvent struct {
    EventID            string
    Timestamp          string
    Success            bool
    Salience           map[string]float64
    Coherence          *float64  // Optional
    DurationMs         *float64  // Optional
    NodesParticipating int
    Reason             *string   // Optional
}
```

---

## 🎯 USAGE EXAMPLES

### Monitor System State

```bash
# Quick health check
vcli maximus consciousness state

# Get detailed metrics
vcli maximus consciousness metrics

# Watch arousal changes (manual loop)
watch -n 1 'vcli maximus consciousness arousal'
```

### Manual Control

```bash
# Trigger attention event (high priority)
vcli maximus consciousness esgt trigger \
  --novelty 0.95 \
  --relevance 0.90 \
  --urgency 0.85

# Increase arousal temporarily (alert mode)
vcli maximus consciousness arousal adjust \
  --delta 0.3 \
  --duration 10

# Decrease arousal (calm down)
vcli maximus consciousness arousal adjust \
  --delta -0.2 \
  --duration 5
```

### Investigation

```bash
# Review recent ignitions
vcli maximus consciousness esgt events --limit 50

# Check if system is conscious
vcli maximus consciousness state | grep "ESGT Status"

# JSON output for scripting
vcli maximus consciousness state --output json | jq '.arousal_level'
```

---

## 🧪 TESTING

### Prerequisites

Backend must be running:
```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service
python main.py  # Port 8022
```

### Test All Commands

```bash
# 1. State
./bin/vcli maximus consciousness state
# Expected: Complete state snapshot

# 2. Events
./bin/vcli maximus consciousness esgt events --limit 10
# Expected: Timeline of events

# 3. Trigger
./bin/vcli maximus consciousness esgt trigger \
  --novelty 0.9 --relevance 0.8 --urgency 0.7
# Expected: Ignition confirmation

# 4. Arousal
./bin/vcli maximus consciousness arousal
# Expected: Arousal state with bar

# 5. Adjust
./bin/vcli maximus consciousness arousal adjust \
  --delta 0.2 --duration 5
# Expected: Adjustment confirmation

# 6. Metrics
./bin/vcli maximus consciousness metrics
# Expected: TIG + ESGT metrics
```

### Expected Behavior

**When backend is running**:
- ✅ All commands return data
- ✅ Visual output is formatted correctly
- ✅ JSON output is valid
- ✅ Errors are handled gracefully

**When backend is offline**:
- ❌ Clear error: "failed to connect to consciousness API"
- ❌ Suggestion to check backend status
- ❌ Exit code: 1

---

## 📈 NEXT STEPS (Sprint 2)

### WebSocket Integration (Planned)

```bash
# Real-time event streaming
vcli maximus consciousness watch

# Output:
# 👁️  Watching consciousness system...
# Press Ctrl+C to stop
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# [15:04:05] ESGT_EVENT - Ignition success (coherence: 0.87)
# [15:04:10] AROUSAL_CHANGE - Level: HIGH (0.78 → 0.82)
# [15:04:15] HEARTBEAT - System healthy
```

### TUI Dashboard (Optional)

```bash
# Interactive dashboard
vcli tui consciousness

# Features:
# - Real-time state panel
# - Event timeline
# - Arousal graph over time
# - Interactive controls
```

---

## 📝 NOTES

1. **Backend Dependency**: Consciousness API must be running on port 8022
2. **No Authentication**: Currently localhost-only, no auth required
3. **Graceful Degradation**: CLI continues working if backend is offline (with errors)
4. **DOUTRINA Compliant**: NO MOCK, NO PLACEHOLDER, PRODUCTION-READY
5. **Backwards Compatible**: Doesn't break existing maximus commands (governance, eureka, oraculo)

---

## ✅ COMPLETION CHECKLIST

- [x] HTTP client implemented (`consciousness_client.go`)
- [x] All 6 CLI commands working
- [x] Visual formatters with bars and colors
- [x] Autocomplete integrated
- [x] Icons added to all commands
- [x] Build successful
- [x] Help text complete
- [x] Error handling robust
- [x] Documentation complete

**Status**: ✅ **SPRINT 1 COMPLETE** - Ready for production use!

---

**Created**: 2025-10-07
**Authors**: Juan Carlos & Anthropic Claude
**Version**: 1.0.0 - Sprint 1
