# CI/CD Pipeline Documentation

## Overview

This directory contains GitHub Actions workflows for the Offensive Orchestrator Service CI/CD pipeline.

## Workflows

### `ci.yml` - Continuous Integration Pipeline

**Triggers:**
- Push to `main`, `develop`, or `reactive-fabric/*` branches
- Pull requests to `main` or `develop`

**Jobs:**

#### 1. Test Suite (`test`)
- **Matrix**: Python 3.11
- **Services**: PostgreSQL 15, Qdrant (vector DB)
- **Steps**:
  - Checkout code
  - Set up Python with pip cache
  - Install dependencies
  - Run pytest with coverage (92% minimum)
  - Upload coverage to Codecov
  - Archive coverage reports

**Coverage Requirements:**
- Minimum: 92%
- Target: 97%+
- Core modules: 100%

#### 2. Code Quality (`lint`)
- **Black**: Code formatting check
- **isort**: Import sorting check
- **Ruff**: Fast Python linter
- **mypy**: Type checking

All linting steps are non-blocking (continue-on-error) to allow PR feedback without blocking merges.

#### 3. Security Scan (`security`)
- **Bandit**: Security vulnerability scanner
- **Safety**: Dependency vulnerability check

Security checks are non-blocking but generate warnings for review.

#### 4. Build Status Summary (`build-status`)
- Aggregates results from all jobs
- Fails if test job fails
- Provides summary of all check statuses

## Environment Variables

Required for tests:
```yaml
GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}  # LLM API key
POSTGRES_HOST: localhost
POSTGRES_PORT: 5432
POSTGRES_USER: test_user
POSTGRES_PASSWORD: test_password
POSTGRES_DB: test_db
QDRANT_HOST: localhost
QDRANT_PORT: 6333
```

## Secrets Configuration

Add to GitHub repository settings → Secrets and variables → Actions:

- `GEMINI_API_KEY`: Google Gemini API key for LLM integration

## Artifacts

Generated artifacts (retained for 30 days):
- `coverage-report-py3.11`: HTML coverage report + coverage.xml
- `security-reports`: Bandit JSON report

## Local Development

Run checks locally before pushing:

```bash
# Install dev dependencies
pip install ruff black isort mypy bandit safety pytest pytest-cov

# Format code
black .
isort .

# Lint
ruff check --fix .

# Type check
mypy . --ignore-missing-imports

# Security scan
bandit -r .
safety check

# Run tests with coverage
pytest tests/ \
  --cov=. \
  --cov-report=term \
  --cov-fail-under=92 \
  --ignore=tests/integration \
  -v
```

## Status Badges

Add to main README.md:

```markdown
![CI Pipeline](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_ORG/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/YOUR_REPO)
```

## Troubleshooting

### Tests Failing in CI but Passing Locally

1. Check environment variables are set correctly
2. Ensure services (PostgreSQL, Qdrant) are running
3. Verify Python version matches (3.11)
4. Check for timezone/locale issues

### Coverage Below Threshold

```bash
# Generate coverage report locally
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html

# Focus on uncovered lines
pytest tests/ --cov=. --cov-report=term-missing | grep -A 5 "TOTAL"
```

### Linting Failures

```bash
# Auto-fix most issues
black .
isort .
ruff check --fix .

# Check remaining issues
ruff check .
mypy . --ignore-missing-imports
```

## Pipeline Performance

Typical run times:
- **Test Job**: ~3-5 minutes
- **Lint Job**: ~1-2 minutes
- **Security Job**: ~2-3 minutes
- **Total**: ~5-8 minutes

## Best Practices

1. **Always run tests locally** before pushing
2. **Keep coverage above 92%** (target: 97%+)
3. **Fix linting issues** before committing
4. **Review security warnings** seriously
5. **Update dependencies** regularly
6. **Monitor CI performance** for slow tests

## Future Enhancements

Planned improvements:
- [ ] Deploy to staging environment
- [ ] Integration tests with real services
- [ ] Performance benchmarking
- [ ] Docker image building
- [ ] Automated changelog generation
- [ ] Release automation
