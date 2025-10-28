# 🎯 FASE 4: GIT INTEGRATION - Plano de Execução

**Data**: 2025-01-10  
**Status**: 🟢 **APROVADO - EXECUÇÃO INICIADA**  
**Baseado em**: Blueprint Phase 5 - HITL Interface  
**Glory to YHWH** 🙏

---

## 📋 VISÃO GERAL

### Objetivo
Implementar sistema completo de aplicação automatizada de patches via Git + criação de Pull Requests para review humano (HITL - Human-in-the-Loop).

### Conceito Biológico
> No sistema imune adaptativo, após células B produzirem anticorpos específicos (Fase 3), esses anticorpos devem ser **integrados permanentemente** no repertório imunológico via memória imunológica (células B de memória). Requer validação rigorosa antes de integração permanente.

**Mapeamento Digital**: Patches (anticorpos) devem ser aplicados ao codebase (organismo) via Git, com PR servindo como "checkpoint de validação" antes de integração permanente (merge).

---

## 🎯 ESCOPO FASE 4

### O Que Implementar
1. **Git Operations Engine** - Aplicar patches em branches isoladas
2. **PR Creation Service** - Criar PRs contextualmente ricos
3. **Git Safety Layer** - Validações pré-commit
4. **Rollback Mechanism** - Reverter patches com problemas
5. **Integration Tests** - Validar E2E Git workflow

### O Que NÃO Implementar (Out of Scope)
- ❌ Wargaming validation (Fase 4.5 - depois)
- ❌ Kubernetes staging (Fase 4.5)
- ❌ WebSocket real-time updates (Fase 5)
- ❌ Auto-merge logic (sempre HITL)

---

## 🏗️ ARQUITETURA PROPOSTA

```
┌─────────────────────────────────────────────────────────┐
│              ORCHESTRATOR (Existing)                    │
│  orchestration/eureka_orchestrator.py                   │
└───────────────┬─────────────────────────────────────────┘
                │
                ↓ Patch Object (validated)
┌─────────────────────────────────────────────────────────┐
│           GIT OPERATIONS ENGINE (NEW)                   │
│  git_integration/git_operations.py                      │
│                                                          │
│  • Branch creation (remediation/CVE-YYYY-NNNNN)        │
│  • Patch application (git apply + validation)          │
│  • Commit creation (templated message)                 │
│  • Push to remote                                       │
│  • Safety checks (pre-flight validations)              │
└───────────────┬─────────────────────────────────────────┘
                │
                ↓ Git Branch Reference
┌─────────────────────────────────────────────────────────┐
│           PR CREATION SERVICE (NEW)                     │
│  git_integration/pr_creator.py                          │
│                                                          │
│  • GitHub API integration (PyGithub)                    │
│  • PR body template (Markdown rich)                     │
│  • Metadata (labels, reviewers, assignees)             │
│  • Link to validation artifacts                         │
└───────────────┬─────────────────────────────────────────┘
                │
                ↓ PR URL + ID
┌─────────────────────────────────────────────────────────┐
│           RESPONSE PUBLISHER (EXISTING)                 │
│  kafka_integration/response_publisher.py                │
│                                                          │
│  • Publish RemediationResponse to Kafka                 │
│  • Include PR URL for tracking                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 COMPONENTES DETALHADOS

### 1. Git Operations Engine

**Arquivo**: `git_integration/git_operations.py`

**Responsabilidades**:
- Clonar/usar repositório local
- Criar branch isolada por CVE
- Aplicar patch com `git apply`
- Validar aplicação (syntax check, imports)
- Commit com mensagem estruturada
- Push para remote

**Dependências**:
- `GitPython` (lib Python para Git)
- `pathlib` (filesystem ops)
- `subprocess` (fallback para git commands)

**API Proposta**:
```python
class GitOperations:
    async def create_remediation_branch(
        self, 
        cve_id: str,
        base_branch: str = "main"
    ) -> str:
        """Create isolated branch for remediation."""
        
    async def apply_patch(
        self, 
        patch: Patch,
        branch: str
    ) -> GitApplyResult:
        """Apply patch to branch with validation."""
        
    async def commit_changes(
        self, 
        patch: Patch,
        branch: str
    ) -> str:
        """Commit with structured message. Returns commit SHA."""
        
    async def push_branch(
        self, 
        branch: str,
        remote: str = "origin"
    ) -> PushResult:
        """Push branch to remote."""
        
    async def rollback_branch(
        self, 
        branch: str
    ) -> None:
        """Delete branch (local + remote)."""
```

**Commit Message Template**:
```
fix(security): Auto-remediate {CVE_ID} - {TITLE}

{DESCRIPTION}

Vulnerability Details:
- Severity: {CVSS_SCORE} ({SEVERITY})
- CWE: {CWE_ID}
- Package: {AFFECTED_PACKAGE} {VERSION_RANGE}
- Services Affected: {SERVICE_LIST}

Remediation Strategy: {STRATEGY}
- Confidence Score: {CONFIDENCE}%
- Strategy Used: {STRATEGY_TYPE}
- Files Modified: {FILE_COUNT}

Auto-generated by MAXIMUS Eureka
Patch ID: {PATCH_ID}
Timestamp: {TIMESTAMP}

Co-authored-by: MAXIMUS AI <maximus@vertice.ai>
```

---

### 2. PR Creator Service

**Arquivo**: `git_integration/pr_creator.py`

**Responsabilidades**:
- Autenticar com GitHub (PAT)
- Criar PR via API
- Popular template Markdown
- Adicionar labels/reviewers
- Link artifacts (logs, reports)

**Dependências**:
- `PyGithub` (GitHub API wrapper)
- `jinja2` (template rendering)

**API Proposta**:
```python
class PRCreator:
    async def create_pull_request(
        self,
        patch: Patch,
        branch: str,
        base_branch: str = "main"
    ) -> PRResult:
        """Create GitHub PR with rich metadata."""
        
    def _render_pr_body(
        self, 
        patch: Patch
    ) -> str:
        """Render PR description from template."""
        
    def _assign_labels(
        self, 
        patch: Patch
    ) -> list[str]:
        """Determine PR labels based on severity/strategy."""
```

**PR Body Template**:
```markdown
# 🛡️ Auto-Remediation: {CVE_ID}

## 🚨 Vulnerability Summary

**Severity**: {SEVERITY_BADGE}  
**CVSS Score**: {CVSS_SCORE}  
**CWE**: [{CWE_ID}](https://cwe.mitre.org/data/definitions/{CWE_ID}.html)

{CVE_DESCRIPTION}

## 📦 Impact Analysis

**Affected Services**:
{SERVICE_LIST}

**Affected Package**: `{PACKAGE_NAME} {VERSION_RANGE}`

**Exploitation Difficulty**: {COMPLEXITY}

## 🔧 Remediation Applied

**Strategy**: `{STRATEGY_TYPE}`  
**Confidence Score**: **{CONFIDENCE}%**

**Files Modified**:
{FILE_LIST}

### Diff Preview
```diff
{DIFF_SNIPPET}
```

## ✅ Validation Status

- [x] Syntax validation passed
- [x] Import checks passed
- [ ] Regression tests (run CI/CD)
- [ ] Security validation (to be completed)

## 📊 Metadata

- **APV ID**: `{APV_ID}`
- **Patch ID**: `{PATCH_ID}`
- **Generated**: {TIMESTAMP}
- **Generator**: MAXIMUS Eureka v{VERSION}

## 🔍 References

- [CVE Details]({CVE_URL})
- [OSV Entry]({OSV_URL})
- [Validation Report]({REPORT_URL})

---

**⚠️ Human Review Required**: This is an auto-generated patch. Please review carefully before merging.

Generated with ❤️ by **MAXIMUS Adaptive Immunity System**  
Glory to YHWH 🙏
```

---

### 3. Git Safety Layer

**Arquivo**: `git_integration/safety_checks.py`

**Responsabilidades**:
- Pre-apply validations
- Post-apply syntax checks
- Import verification
- Conflict detection

**API Proposta**:
```python
class SafetyChecks:
    async def validate_patch_format(
        self, 
        patch: Patch
    ) -> ValidationResult:
        """Validate patch is well-formed."""
        
    async def check_syntax_post_apply(
        self, 
        files_modified: list[Path]
    ) -> ValidationResult:
        """Run syntax checks on modified files."""
        
    async def verify_imports(
        self, 
        files_modified: list[Path]
    ) -> ValidationResult:
        """Ensure imports are resolvable."""
        
    async def detect_conflicts(
        self, 
        patch: Patch,
        target_branch: str
    ) -> ConflictReport:
        """Check for merge conflicts."""
```

---

### 4. Models & Types

**Arquivo**: `git_integration/models.py`

```python
from pydantic import BaseModel, Field, HttpUrl
from pathlib import Path
from datetime import datetime

class GitApplyResult(BaseModel):
    """Result of git apply operation."""
    success: bool
    commit_sha: str | None = None
    files_changed: list[str]
    conflicts: list[str] = Field(default_factory=list)
    error_message: str | None = None

class PushResult(BaseModel):
    """Result of git push operation."""
    success: bool
    branch: str
    remote_ref: str | None = None
    error_message: str | None = None

class PRResult(BaseModel):
    """Result of PR creation."""
    success: bool
    pr_number: int | None = None
    pr_url: HttpUrl | None = None
    error_message: str | None = None

class ValidationResult(BaseModel):
    """Result of safety validation."""
    passed: bool
    checks_run: list[str]
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ConflictReport(BaseModel):
    """Merge conflict detection report."""
    has_conflicts: bool
    conflicting_files: list[str] = Field(default_factory=list)
    resolution_suggestions: list[str] = Field(default_factory=list)

class GitConfig(BaseModel):
    """Git integration configuration."""
    repo_path: Path
    remote_url: HttpUrl
    default_branch: str = "main"
    branch_prefix: str = "remediation"
    github_token: str = Field(exclude=True)  # Sensitive
    commit_author: str = "MAXIMUS Eureka"
    commit_email: str = "eureka@maximus.ai"
```

---

## 🧪 TESTING STRATEGY

### Unit Tests

**Arquivo**: `tests/unit/git_integration/test_git_operations.py`

Tests:
1. `test_create_remediation_branch` - Branch creation
2. `test_apply_patch_success` - Successful patch application
3. `test_apply_patch_conflicts` - Handle merge conflicts
4. `test_commit_message_template` - Commit message formatting
5. `test_push_branch_success` - Push to remote
6. `test_rollback_branch` - Branch deletion

**Arquivo**: `tests/unit/git_integration/test_pr_creator.py`

Tests:
1. `test_create_pr_success` - PR creation via API
2. `test_pr_body_rendering` - Template rendering
3. `test_pr_labels_assignment` - Label logic
4. `test_pr_creation_failure` - Error handling

**Arquivo**: `tests/unit/git_integration/test_safety_checks.py`

Tests:
1. `test_validate_patch_format` - Patch format validation
2. `test_syntax_check_python` - Python syntax validation
3. `test_import_verification` - Import checks
4. `test_conflict_detection` - Conflict detection

### Integration Tests (Optional - Fase 4.5)

**Arquivo**: `tests/integration/test_git_e2e.py`

Tests:
1. `test_full_remediation_workflow` - E2E: patch → commit → PR
2. `test_rollback_on_failure` - Cleanup on errors

---

## 📊 IMPLEMENTATION PLAN

### Task Breakdown

```
┌────────────────────────────────────────────────────┐
│  PHASE 4: GIT INTEGRATION                          │
├────────────────────────────────────────────────────┤
│  ⏳ Task 4.1: Git Operations Engine        [0%]   │
│     - GitOperations class                          │
│     - Branch management                            │
│     - Patch application logic                      │
│     - Commit creation                              │
│     Estimate: 3-4h                                 │
│                                                    │
│  ⏳ Task 4.2: Safety Layer                [0%]   │
│     - SafetyChecks class                           │
│     - Syntax validation                            │
│     - Import verification                          │
│     - Conflict detection                           │
│     Estimate: 2-3h                                 │
│                                                    │
│  ⏳ Task 4.3: PR Creator Service          [0%]   │
│     - PRCreator class                              │
│     - GitHub API integration                       │
│     - Template rendering                           │
│     - Label/reviewer assignment                    │
│     Estimate: 2-3h                                 │
│                                                    │
│  ⏳ Task 4.4: Models & Types              [0%]   │
│     - Pydantic models                              │
│     - GitConfig                                    │
│     - Result types                                 │
│     Estimate: 1h                                   │
│                                                    │
│  ⏳ Task 4.5: Orchestrator Integration    [0%]   │
│     - Update EurekaOrchestrator                    │
│     - Git workflow orchestration                   │
│     - Error handling                               │
│     Estimate: 2h                                   │
│                                                    │
│  ⏳ Task 4.6: Unit Tests                  [0%]   │
│     - Git operations tests                         │
│     - PR creator tests                             │
│     - Safety checks tests                          │
│     - Mock GitHub API                              │
│     Estimate: 3-4h                                 │
│                                                    │
│  ⏳ Task 4.7: Documentation               [0%]   │
│     - Update README                                │
│     - Git workflow guide                           │
│     - Configuration docs                           │
│     Estimate: 1h                                   │
├────────────────────────────────────────────────────┤
│  Total Estimate: 14-18 hours                       │
│  Target: 2-3 days (sustainable pace)               │
└────────────────────────────────────────────────────┘
```

### Execution Order (Metodologia)

1. **Task 4.4** (Models) - Foundation
2. **Task 4.2** (Safety Layer) - Critical path
3. **Task 4.1** (Git Operations) - Core logic
4. **Task 4.3** (PR Creator) - Integration point
5. **Task 4.5** (Orchestrator) - Wiring
6. **Task 4.6** (Tests) - Validation
7. **Task 4.7** (Docs) - Completion

---

## 🎯 SUCCESS CRITERIA

### Definition of Done

- ✅ All classes implemented with type hints
- ✅ 100% docstring coverage (Google style)
- ✅ Unit tests ≥90% coverage
- ✅ All tests passing (100%)
- ✅ mypy --strict clean
- ✅ black + pylint clean
- ✅ Documentation complete
- ✅ E2E manual test successful (patch → PR)
- ✅ NO TODO/PLACEHOLDER/MOCK in production code

### Quality Gates

1. **Code Quality**: mypy + black + pylint ✅
2. **Test Coverage**: ≥90% ✅
3. **Test Pass Rate**: 100% ✅
4. **Documentation**: Complete ✅
5. **Security**: No secrets in code ✅

---

## 🚀 NEXT STEPS (Immediate)

### Task 4.4: Models & Types (START HERE)

1. Create `git_integration/` directory
2. Create `git_integration/__init__.py`
3. Create `git_integration/models.py`
4. Implement all Pydantic models
5. Add type exports to `__init__.py`

**Estimated Time**: 1 hour  
**Command to Start**:
```bash
cd backend/services/maximus_eureka
mkdir -p git_integration
touch git_integration/__init__.py
# Then implement models.py
```

---

## 📚 DEPENDENCIES

### Python Packages (pyproject.toml)
```toml
[tool.poetry.dependencies]
GitPython = "^3.1.40"  # Git operations
PyGithub = "^2.1.1"    # GitHub API
jinja2 = "^3.1.2"      # Template rendering
```

### Environment Variables
```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxx  # GitHub PAT with repo scope
GITHUB_REPO_OWNER=vertice-dev
GITHUB_REPO_NAME=vertice-dev

# Git Configuration
GIT_AUTHOR_NAME="MAXIMUS Eureka"
GIT_AUTHOR_EMAIL="eureka@maximus.ai"
GIT_DEFAULT_BRANCH=main
```

---

## 🙏 SPIRITUAL FOUNDATION

> **"O Senhor é a minha rocha, a minha fortaleza e o meu libertador; o meu Deus, a minha rocha em quem me refugio."**  
> — Salmos 18:2

Esta fase representa:
- **Integração**: Unir componentes isolados em sistema coeso
- **Permanência**: Git como registro imutável (glory eternal)
- **Humildade**: HITL reconhece limitações da automação
- **Excelência**: Cada PR é testemunho de qualidade

**Glory to YHWH - The Rock, the Foundation of all systems!** 🙏✨

---

## 📝 CHANGELOG

- **2025-01-10**: Plano inicial criado
- Status: **APROVADO PARA EXECUÇÃO**

---

**MAXIMUS Session | Phase 4 | Focus: Git Integration**  
**Doutrina ✓ | Métricas: 81/81 tests ✓**  
**Ready to integrate phenomenology into Git history.**
