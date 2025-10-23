Execute a complete autonomous development cycle using Agent Smith's 4 agents in sequence:

1. **DIAGNOSTICADOR** - Analyze current code quality, security, and performance
2. **ARQUITETO** - Plan the implementation with ADRs and risk assessment
3. **DEV SENIOR** - Generate and apply code changes
4. **TESTER** - Validate with tests, coverage, and quality gates

The workflow will:
- Auto-detect language (Go/Python)
- Execute agents sequentially with context passing
- Request HITL approval at 5 critical checkpoints
- Generate comprehensive reports
- Prepare git commit (requires manual push approval)

Usage examples:
- "Execute full-cycle workflow to add authentication middleware"
- "Run full development cycle for adding rate limiting in ./internal/middleware/"
- "Full-cycle: implement user session management with Redis backend"

The workflow stops at these HITL checkpoints:
1. After DIAGNOSTICADOR (if critical issues found)
2. After ARQUITETO (plan approval required)
3. After DEV SENIOR (code review required)
4. After TESTER (if quality gates fail)
5. Before git push (final approval)
