Execute DEV SENIOR agent for rapid code implementation with LLM-powered code generation.

**What it does:**
- Detects language automatically (Go/Python)
- Generates implementation plan (unless --skip-planning)
- Calls Oráculo API for LLM code generation (GPT-4)
- Falls back to templates if Oráculo unavailable
- Applies Anthropic patterns: Planning, Reflection, Self-Healing
- Runs compilation and basic tests
- Creates git commit automatically

**Required environment:**
```bash
export MAXIMUS_ORACULO_ENDPOINT="http://localhost:8026"  # For LLM generation
export OPENAI_API_KEY="sk-..."                           # For real GPT-4 code
```

**Usage examples:**
- "Use agents-dev to add /health endpoint with DB ping in ./cmd/api"
- "Run DEV SENIOR to implement JWT authentication middleware in ./internal/auth"
- "agents-dev: create user CRUD operations in ./internal/users"

**Key flags:**
- `--hitl=false` - Skip human approval (autonomous mode)
- `--enable-reflection` - LLM reviews own generated code (default: true)
- `--enable-retry` - Auto-fix compilation errors (3 attempts)
- `--skip-planning` - Fast mode, skip planning phase
- `--targets <path>` - Target directory for implementation

**Production-ready features:**
- ✅ Retry + Exponential Backoff (95%+ success rate)
- ✅ Circuit Breaker (protects from cascading failures)
- ✅ In-Memory Cache (-70% LLM costs on repetitive tasks)
- ✅ Observability (metrics: requests, failures, cache hits)

Provide the task description and target path. The agent will handle the rest.
