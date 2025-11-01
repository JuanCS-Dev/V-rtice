# 🚀 Constitutional Migration - Quick Start Guide

**Goal:** Migrate a backend service to Constitutional v3.0 compliance in 6 steps.

**Time Estimate:** 2-4 hours per service (depending on size and complexity)

---

## Prerequisites

- Python 3.11+
- Service is in `backend/services/<service_name>/`
- Git repository initialized

---

## 6-Step Migration Process

### Step 1: Dry-Run Test (5 minutes)

Test the migration without making any changes:

```bash
python scripts/migrate_to_constitutional.py <service_name> --dry-run
```

**Expected Output:**

```
✅ MIGRATION COMPLETE (dry run)

Next steps:
1. Review changes
2. Run actual migration
```

**If Failed:** Fix reported issues before proceeding.

---

### Step 2: Perform Migration (5 minutes)

Execute the actual migration:

```bash
python scripts/migrate_to_constitutional.py <service_name>
```

**What Happens:**

- ✅ Copies 5 constitutional libraries to `shared/`
- ✅ Updates `main.py` with observability code
- ✅ Updates `Dockerfile` with HEALTHCHECK
- ✅ Generates test template
- ✅ Updates `requirements.txt`
- ✅ Creates backup in `.migration_backup/<timestamp>/`

**If Failed:** Rollback is automatic. Review logs and try again.

---

### Step 3: Implement Placeholders (30-90 minutes)

Find and implement all placeholders:

```bash
cd backend/services/<service_name>
grep -r "placeholder for" --include="*.py" --exclude-dir={tests,test,.venv}
```

**Example Placeholder:**

```python
# placeholder for actual hallucination detection logic
def detect_hallucination(response: str) -> float:
    return 0.0  # Replace with real logic
```

**Real Implementation:**

```python
def detect_hallucination(response: str) -> float:
    """Detect hallucinations using semantic similarity."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Compare response with ground truth
    embedding1 = model.encode(response)
    embedding2 = model.encode(ground_truth)

    similarity = cosine_similarity(embedding1, embedding2)
    return 1.0 - similarity  # Return hallucination score
```

**Implement ALL placeholders** - don't just delete them!

---

### Step 4: Increase Test Coverage to >=90% (1-2 hours)

#### 4.1 Run Coverage Report

```bash
cd backend/services/<service_name>
pytest --cov --cov-report=html --cov-report=json
```

#### 4.2 View Coverage Report

```bash
open htmlcov/index.html  # Linux: xdg-open htmlcov/index.html
```

#### 4.3 Identify Gaps

Look for red/yellow highlighted lines in HTML report.

#### 4.4 Add Tests

For each uncovered function, add a test in `tests/`:

```python
# tests/test_<module>.py

def test_detect_hallucination():
    """Test hallucination detection."""
    # Test normal case
    score = detect_hallucination("valid response")
    assert 0.0 <= score <= 1.0

    # Test edge case
    score = detect_hallucination("")
    assert score == 1.0  # Empty response is hallucination
```

#### 4.5 Re-run Until >=90%

```bash
pytest --cov --cov-report=json
```

Check `coverage.json`:

```json
{
  "totals": {
    "percent_covered": 91.2 // Must be >= 90.0
  }
}
```

---

### Step 5: Validate Compliance (2 minutes)

Run the constitutional gate validator:

```bash
python scripts/constitutional_gate.py <service_name>
```

**Expected Output:**

```
================================================================================
🏛️  CONSTITUTIONAL GATE - <service_name>
================================================================================

📋 Observability...
  ✅ PASSED

📋 Test Coverage...
  📊 Coverage: 91.2%
  ✅ PASSED

📋 P1 Violations...
  ✅ PASSED

📋 Dockerfile...
  ✅ PASSED

================================================================================
✅ CONSTITUTIONAL GATE: PASSED
================================================================================
```

**If Failed:**

- Check violations/warnings list
- Fix issues
- Re-run validation

---

### Step 6: Commit Changes (5 minutes)

```bash
git add backend/services/<service_name>
git commit -m "feat(<service>): Migrate to Constitutional v3.0

- Add constitutional observability (metrics, tracing, logging)
- Add advanced health checks (K8s probes)
- Implement <N> placeholders with real functionality
- Increase test coverage to <X>%
- Full compliance with Constituição Vértice v3.0

🏛️ Constitutional v3.0 Migration
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Common Issues & Quick Fixes

### Issue: "Test coverage 85.2% < 90% requirement"

**Fix:** Add more tests (see Step 4)

```bash
# Find untested files
pytest --cov --cov-report=term-missing
```

---

### Issue: "P1 violations: TODO in main.py:123"

**Fix:** Implement or remove TODOs

```bash
# Find all TODOs
grep -rn "# TODO" --include="*.py" --exclude-dir={tests,.venv}
```

---

### Issue: "Missing constitutional libraries"

**Fix:** Re-run migration

```bash
python scripts/migrate_to_constitutional.py <service_name> --force
```

---

### Issue: "NotImplementedError in core.py:456"

**Fix:** Implement the function

```python
# ❌ Before
def process_data(data: dict) -> dict:
    raise NotImplementedError("TODO: Implement data processing")

# ✅ After
def process_data(data: dict) -> dict:
    """Process incoming data and return transformed result."""
    # Real implementation
    return {
        "status": "processed",
        "result": transform(data)
    }
```

---

## Batch Migration Example

Migrate 3 services sequentially:

```bash
#!/bin/bash

SERVICES=(
    "maximus_core_service"
    "maximus_orchestrator_service"
    "maximus_oraculo_v2"
)

for service in "${SERVICES[@]}"; do
    echo "========================================="
    echo "Migrating: $service"
    echo "========================================="

    # Step 1: Dry-run
    python scripts/migrate_to_constitutional.py "$service" --dry-run
    read -p "Continue with actual migration? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        continue
    fi

    # Step 2: Migrate
    python scripts/migrate_to_constitutional.py "$service"

    # Step 3: Manual - implement placeholders
    echo "⚠️  Implement placeholders in $service"
    echo "   Run: grep -r 'placeholder for' backend/services/$service --include='*.py'"
    read -p "Press Enter when placeholders implemented..."

    # Step 4: Manual - increase coverage
    echo "⚠️  Increase test coverage to >=90% for $service"
    echo "   Run: cd backend/services/$service && pytest --cov --cov-report=html"
    read -p "Press Enter when coverage >=90%..."

    # Step 5: Validate
    python scripts/constitutional_gate.py "$service"

    if [ $? -eq 0 ]; then
        echo "✅ $service passed validation"

        # Step 6: Commit
        git add "backend/services/$service"
        git commit -m "feat($service): Migrate to Constitutional v3.0"

        echo "✅ $service migration complete and committed"
    else
        echo "❌ $service failed validation - fix issues manually"
    fi

    echo ""
done
```

---

## Validation Only (No Migration)

Check compliance without migrating:

```bash
# Single service
python scripts/constitutional_gate.py <service_name>

# All services
python scripts/constitutional_gate.py --all

# JSON output (for CI/CD)
python scripts/constitutional_gate.py <service_name> --json
```

---

## Rollback Migration

If migration went wrong:

### Automatic Rollback (on failure)

Migration script automatically rolls back on error.

### Manual Rollback

```bash
cd backend/services/<service_name>
ls -la .migration_backup/

# Find backup timestamp
BACKUP_DIR=".migration_backup/20251031_182530"

# Restore files
cp -r $BACKUP_DIR/* .

# Remove backup
rm -rf .migration_backup
```

---

## Help & Debugging

### Get Script Help

```bash
python scripts/migrate_to_constitutional.py --help
python scripts/constitutional_gate.py --help
```

### Enable Verbose Logging

```bash
# Migration script (check logs in stderr)
python scripts/migrate_to_constitutional.py <service> 2>&1 | tee migration.log

# Constitutional gate
python scripts/constitutional_gate.py <service> --verbose
```

### Dry-Run Everything

```bash
# Test migration without changes
python scripts/migrate_to_constitutional.py <service> --dry-run
```

---

## Cheat Sheet

```bash
# 1️⃣ Dry-run test
python scripts/migrate_to_constitutional.py <service> --dry-run

# 2️⃣ Actual migration
python scripts/migrate_to_constitutional.py <service>

# 3️⃣ Find placeholders
grep -r "placeholder for" backend/services/<service> --include="*.py" --exclude-dir=tests

# 4️⃣ Check coverage
cd backend/services/<service> && pytest --cov --cov-report=html

# 5️⃣ Validate
python scripts/constitutional_gate.py <service>

# 6️⃣ Commit
git add backend/services/<service>
git commit -m "feat(<service>): Migrate to Constitutional v3.0"
```

---

## Next Steps After Migration

1. **Test Locally:**

   ```bash
   cd backend/services/<service>
   pytest
   ```

2. **Build Docker Image:**

   ```bash
   docker build -t <service>:constitutional-v3 .
   ```

3. **Test Health Checks:**

   ```bash
   docker run -p 8000:8000 -p 9090:9090 <service>:constitutional-v3
   curl http://localhost:8000/health/live
   curl http://localhost:8000/health/ready
   curl http://localhost:9090/metrics
   ```

4. **Push to Dev Environment:**

   ```bash
   git push origin feature/constitutional-migration-<service>
   ```

5. **Create Pull Request**

---

## Full Documentation

For complete documentation, see:

- 📚 [CONSTITUTIONAL_SCRIPTS_DOCUMENTATION.md](./CONSTITUTIONAL_SCRIPTS_DOCUMENTATION.md)
- 📋 [CONSTITUTIONAL_MIGRATION_PLAN.md](../CONSTITUTIONAL_MIGRATION_PLAN.md)
- 🏛️ [.claude/DOUTRINA_VERTICE.md](../.claude/DOUTRINA_VERTICE.md)

---

**Soli Deo Gloria** ✝️
