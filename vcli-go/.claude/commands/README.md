# Agent Smith - Slash Commands

Quick reference for all available Agent Smith slash commands in Claude Code.

## 🤖 Available Commands

### `/full-cycle` - Complete Development Workflow
Execute all 4 agents sequentially with HITL checkpoints.

**Flow:** DIAGNOSTICADOR → ARQUITETO → DEV SENIOR → TESTER

**Use when:**
- Implementing complex features from scratch
- Need comprehensive analysis + planning + implementation + validation
- Want full quality control with human approvals

**Example:**
```
/full-cycle
"Implement user authentication with JWT tokens in ./internal/auth"
```

---

### `/agents-dev` - DEV SENIOR (Rapid Implementation)
Fast code generation with LLM (GPT-4) or template fallback.

**Use when:**
- Need quick implementation of a feature
- Have clear requirements, no planning needed
- Want autonomous code generation (--hitl=false)

**Features:**
- ✅ LLM-powered code generation (GPT-4)
- ✅ Retry + Exponential Backoff
- ✅ Circuit Breaker
- ✅ In-Memory Cache (-70% LLM costs)
- ✅ Self-healing compilation retry
- ✅ Reflection engine (quality analysis)

**Example:**
```
/agents-dev
"Add /health endpoint with database ping in ./cmd/api"
```

---

### `/agents-test` - TESTER (Validation)
Run tests with coverage analysis and quality gates.

**Use when:**
- Need to validate code changes
- Want coverage reports
- Check if quality thresholds are met

**Features:**
- Coverage measurement
- Quality gate validation
- HTML/text reports
- Integration + unit test support

**Example:**
```
/agents-test
"Validate ./internal/auth with minimum 80% coverage"
```

---

### `/agents-plan` - ARQUITETO (Architecture Planning)
Generate implementation plans with ADRs and risk assessment.

**Use when:**
- Starting a complex feature
- Unsure about best architecture approach
- Need to document design decisions
- Want step-by-step roadmap

**Output:**
- Architecture overview
- ADRs (Architecture Decision Records)
- Risk assessment
- Complexity estimates
- File impact analysis
- Implementation steps

**Example:**
```
/agents-plan
"Design microservices architecture for user service"
```

---

## 📊 Command Comparison

| Command | Agents Used | Speed | Autonomy | Best For |
|---------|-------------|-------|----------|----------|
| `/full-cycle` | All 4 | Slow | Medium (5 HITL checkpoints) | Complex features |
| `/agents-dev` | DEV SENIOR | Fast | High (--hitl=false) | Quick implementations |
| `/agents-test` | TESTER | Fast | High | Validation only |
| `/agents-plan` | ARQUITETO | Medium | High | Planning only |

---

## 🚀 Typical Workflows

### Workflow 1: Quick Feature Implementation
```
1. /agents-dev "Add feature X"
2. /agents-test "Validate feature X with coverage"
```

### Workflow 2: Complex Feature (Planned)
```
1. /agents-plan "Design architecture for feature Y"
2. [Review plan]
3. /agents-dev "Implement feature Y using plan from step 1"
4. /agents-test "Validate feature Y"
```

### Workflow 3: Full Quality Control
```
1. /full-cycle "Implement feature Z"
   [All agents run sequentially with approvals]
```

---

## 🔧 Configuration

All commands require:
```bash
# For LLM-powered code generation (optional)
export MAXIMUS_ORACULO_ENDPOINT="http://localhost:8026"
export OPENAI_API_KEY="sk-..."

# Start Oráculo service
cd backend/services/maximus_oraculo
ENABLE_KAFKA=false uvicorn api:app --port 8026
```

Without configuration, agents use **template-based generation** (TODOs).

---

## 📝 Command Syntax

All commands follow the same pattern:
```
/<command>
"<task description> in <target path>"
```

**Examples:**
- `/agents-dev "Add logging to main.go"`
- `/agents-test "Run tests in ./internal/auth"`
- `/agents-plan "Design API versioning strategy"`
- `/full-cycle "Implement rate limiting middleware"`

---

## 💡 Tips

1. **Use /agents-dev for speed** - Skip planning if requirements are clear
2. **Use /agents-plan first** - For complex features, plan before coding
3. **Use /full-cycle for critical features** - Get full quality control
4. **Enable Oráculo for real code** - Without it, you get templates only
5. **Check coverage with /agents-test** - Validate before committing

---

## 📚 More Documentation

- **Quick Start Guide:** `docs/agent-smith/QUICK-START-GUIDE.html` (web version)
- **Print Guide:** `docs/agent-smith/QUICK-START-GUIDE-PRINT.html` (paper version)
- **Architecture:** `docs/agents/ARCHITECTURE.md`
- **Usage:** `docs/agents/USAGE.md`

---

**Agent Smith v2.0** | FASE 4.7.3-5 Complete: Production Readiness Achieved
