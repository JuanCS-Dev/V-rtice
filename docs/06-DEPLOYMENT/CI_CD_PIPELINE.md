# CI/CD Pipeline Documentation

## Overview

Track 2 CI/CD pipeline provides automated validation, testing, and deployment for the Vértice MAXIMUS backend ecosystem.

## Workflows

### 1. `validate-backend.yml` - Port Registry Validation
**Trigger:** Changes to `backend/ports.yaml` or `backend/scripts/**`

**Jobs:**
- Validate port registry structure
- Check for port conflicts
- Verify service completeness

**Exit Criteria:**
- Zero port conflicts
- All 83 services mapped
- All ports within correct ranges

---

### 2. `ci-services.yml` - Service CI/CD
**Trigger:** Changes to `backend/services/**` or `backend/libs/**`

**Jobs:**

#### `detect-changes`
- Identifies modified services/libs
- Generates build matrix dynamically

#### `validate-libs` (if libs changed)
- Run ruff (linting)
- Run mypy (type checking)
- Run pytest with coverage
- Enforce 99% coverage threshold

#### `validate-service` (matrix per changed service)
- Install dependencies
- Run ruff
- Run mypy
- Check for mocks/TODOs (Padrão Pagani enforcement)
- Run tests
- Check 95% coverage threshold

#### `integration-test`
- Spin up postgres + redis
- Run integration test suite
- Cleanup resources

#### `security-scan`
- Run bandit security scanner
- Upload results as artifact

**Matrix Strategy:**
- `fail-fast: false` - Continue testing all services even if one fails
- Parallel execution per service

---

### 3. `docker-build.yml` - Container Build & Push
**Trigger:** Push to main/develop, tags, or PRs

**Jobs:**

#### `build-matrix`
- Reads `ports.yaml`
- Generates dynamic build matrix
- Limits to 10 services for PR builds (efficiency)

#### `build-and-push` (matrix per service)
- Build Docker image
- Push to GitHub Container Registry (only on push events)
- Use BuildKit cache for efficiency
- Tag with: branch name, SHA, semantic version

#### `build-summary`
- Generate build summary in GitHub Actions UI

**Registry:** `ghcr.io/<org>/<service>:<tag>`

---

## Scripts

### `validate_ports.py`
**Purpose:** Comprehensive port registry validation

**Checks:**
1. Port uniqueness (no conflicts)
2. Range compliance (ports within category ranges)
3. Completeness (filesystem ↔ YAML sync)
4. Metadata accuracy

**Usage:**
```bash
cd backend
python scripts/validate_ports.py
```

**Exit Codes:**
- `0` - All validations passed
- `1` - Validation errors found

---

### `generate_docker_compose.py`
**Purpose:** Auto-generate docker-compose.yml from port registry

**Features:**
- Reads `ports.yaml` as single source of truth
- Generates complete compose file with all 83 services
- Includes health checks, networks, volumes
- Adds infrastructure services (postgres, redis)

**Usage:**
```bash
cd backend
python scripts/generate_docker_compose.py --output docker-compose.generated.yml
```

**Options:**
- `--output, -o` - Output file path (default: docker-compose.generated.yml)
- `--dry-run` - Print to stdout instead of file

---

### `validate_phase.sh`
**Purpose:** Validate implementation against architecture phases

**Checks:**
- Port registry existence and validity
- Library structure (Phase 1)
- Test coverage
- Absence of mocks/TODOs (Padrão Pagani)

**Usage:**
```bash
cd backend
bash scripts/validate_phase.sh 1  # Validate Phase 1
```

**Exit Codes:**
- `0` - Validation passed
- `1` - Validation failed

---

## Padrão Pagani Enforcement

All workflows enforce Constituição Vértice Article II (Padrão Pagani):

### Automated Checks:
1. **No mocks in production code**
   ```bash
   grep -r "mock\|Mock\|stub\|Stub" --include="*.py" --exclude-dir=tests
   ```

2. **No TODOs/FIXMEs**
   ```bash
   grep -r "TODO\|FIXME" --include="*.py" --exclude-dir=tests
   ```

3. **Coverage thresholds**
   - Libraries: 99% minimum
   - Services: 95% minimum

4. **Type safety**
   - mypy must pass on all code

5. **Code quality**
   - ruff must pass with zero violations

---

## Integration with Track 1 & 3

### Track 1 (Libraries)
- CI validates libs before services
- Services depend on lib validation passing
- Shared mypy/ruff configuration

### Track 3 (Services)
- Services use ports from registry
- Port changes trigger service rebuild
- Migration validation before deployment

---

## Performance Optimizations

### Matrix Builds
- Parallel execution of independent services
- Fail-fast disabled to test all services

### Docker BuildKit
- Layer caching via GitHub Actions cache
- Multi-stage builds for smaller images

### Smart Triggers
- Path-based workflow triggers
- Changed files detection
- Dynamic matrix generation

---

## Monitoring & Alerts

### GitHub Actions UI
- Build summary in step summary
- Artifact uploads for security scans
- Coverage reports

### Future: Integration with Observability Stack (Days 9-14)
- Prometheus metrics export
- Grafana dashboards
- Alert rules for failed builds

---

## Local Development

### Run validations locally:
```bash
# Port registry
cd backend
python scripts/validate_ports.py

# Phase validation
bash scripts/validate_phase.sh 1

# Generate docker-compose
python scripts/generate_docker_compose.py

# Run linting
ruff check backend/libs backend/services

# Run type checking
mypy backend/libs

# Run tests
cd backend/libs
pytest --cov --cov-report=term
```

---

## References

- **Constituição Vértice:** Article II (Padrão Pagani), Article V (Legislação Prévia)
- **Track 2 Blueprint:** `/docs/Arquitetura_Vertice_Backend/TRACK2_INFRAESTRUTURA.md`
- **Port Registry:** `/backend/ports.yaml`

---

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Status:** Days 4-8 Implementation Complete
