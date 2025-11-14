# 🔧 Trinity Correction Plan - Production Readiness Roadmap

**Document Version**: 1.0
**Created**: 2025-10-31
**Target Completion**: 2025-12-31 (8 weeks)
**Owner**: Vértice Platform Team
**Status**: 📋 PLANNING

---

## 📊 Executive Summary

This document provides a comprehensive correction plan for the 3 new MAXIMUS subordinate services (PENELOPE, MABA, MVP) based on critical analysis. The services have solid foundations but require significant engineering work to achieve production readiness.

### Current State Assessment

| Service | Concept Quality | Implementation Quality | Production Ready | Estimated Work |
|---------|----------------|------------------------|------------------|----------------|
| **PENELOPE** | 7/10 | 3/10 | ❌ NO | 4-5 weeks |
| **MABA** | 8/10 | 6/10 | ⚠️ PARTIAL | 2-3 weeks |
| **MVP** | 5/10 | 5/10 | ⚠️ PARTIAL | 2-3 weeks |

### Critical Issues Count

- **P0 (Blocker)**: 8 issues - Must fix before production
- **P1 (Critical)**: 12 issues - Should fix before production
- **P2 (Important)**: 15 issues - Fix within 3 months
- **P3 (Nice-to-have)**: 10 issues - Backlog

---

## 🎯 Strategic Goals

### Phase 1: Safety & Stability (Weeks 1-3)
**Goal**: Eliminate all P0 blockers, make services safe to run

### Phase 2: Production Hardening (Weeks 4-6)
**Goal**: Fix P1 critical issues, achieve 90%+ coverage, add monitoring

### Phase 3: Optimization & Polish (Weeks 7-8)
**Goal**: Address P2 issues, performance optimization, documentation

---

## 🙏 PENELOPE - Christian Autonomous Healing Service

### Current Problems Summary

**P0 Blockers** (4 issues):
1. Risk assessment uses fake data (hardcoded values)
2. No digital twin validation (auto-patches can break production)
3. No rollback mechanism for failed patches
4. Wisdom Base has no real implementation

**P1 Critical** (6 issues):
5. Biblical governance may alienate developers
6. No circuit breaker or rate limiting on auto-healing
7. Sophia Engine decisions not auditable
8. No patch approval workflow for high-risk changes
9. Test coverage unknown (not measured)
10. No integration tests for end-to-end healing flow

**P2 Important** (5 issues):
11. Sabbath observance is gimmick vs practical feature
12. No metrics on patch success/failure rate
13. No A/B testing framework for patches
14. Praotes/Tapeinophrosyne validators have unclear purpose
15. No documentation on 7 Biblical Articles mapping to code

---

### 📋 PENELOPE Correction Plan

#### **Week 1: P0.1 - Implement Real Risk Assessment**

**Problem**: `_get_service_complexity()`, `_get_service_dependencies()`, `_get_recent_changes()`, `_get_test_coverage()` return hardcoded values.

**Location**: `backend/services/penelope_service/core/sophia_engine.py:285-331`

**Solution**:

1. **Service Complexity** (Day 1-2):
```python
async def _get_service_complexity(self, service: str) -> float:
    """Calculate real service complexity using radon."""
    try:
        service_path = f"backend/services/{service}"

        # Run radon cc (cyclomatic complexity)
        result = subprocess.run(
            ["radon", "cc", "-a", "-j", service_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.warning(f"Radon failed for {service}, using default")
            return 0.5

        # Parse JSON output
        data = json.loads(result.stdout)

        # Calculate weighted complexity
        total_complexity = 0
        total_functions = 0

        for file_data in data.values():
            for item in file_data:
                total_complexity += item.get("complexity", 0)
                total_functions += 1

        avg_complexity = total_complexity / max(total_functions, 1)

        # Normalize to 0-1 scale (complexity >15 is very high)
        normalized = min(avg_complexity / 15.0, 1.0)

        logger.info(f"Service {service} complexity: {normalized:.2f}")
        return normalized

    except Exception as e:
        logger.error(f"Failed to calculate complexity: {e}")
        return 0.5  # Conservative fallback
```

2. **Service Dependencies** (Day 2-3):
```python
async def _get_service_dependencies(self, service: str) -> list[str]:
    """Get real dependencies from imports and docker-compose."""
    try:
        dependencies = set()
        service_path = Path(f"backend/services/{service}")

        # Parse Python imports
        for py_file in service_path.rglob("*.py"):
            content = py_file.read_text()

            # Find internal service imports
            import_pattern = r'from\s+(\w+_service)\s+import|import\s+(\w+_service)'
            matches = re.findall(import_pattern, content)

            for match in matches:
                dep = match[0] or match[1]
                if dep and dep != service:
                    dependencies.add(dep)

        # Parse docker-compose.yml
        compose_file = service_path / "docker-compose.yml"
        if compose_file.exists():
            compose_data = yaml.safe_load(compose_file.read_text())

            for svc in compose_data.get("services", {}).values():
                depends_on = svc.get("depends_on", [])
                dependencies.update(depends_on)

        # Query Service Registry for runtime dependencies
        registry_deps = await self._query_registry_dependencies(service)
        dependencies.update(registry_deps)

        return list(dependencies)

    except Exception as e:
        logger.error(f"Failed to get dependencies: {e}")
        return []
```

3. **Recent Changes** (Day 3):
```python
async def _get_recent_changes(self, service: str, hours: int) -> int:
    """Get real git commit count from git log."""
    try:
        service_path = f"backend/services/{service}"
        since_time = f"{hours} hours ago"

        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={since_time}", "--", service_path],
            capture_output=True, text=True, cwd="/home/juan/vertice-dev"
        )

        if result.returncode != 0:
            return 0

        commit_count = len([line for line in result.stdout.split('\n') if line.strip()])

        logger.info(f"Service {service} had {commit_count} commits in last {hours}h")
        return commit_count

    except Exception as e:
        logger.error(f"Failed to get recent changes: {e}")
        return 0
```

4. **Test Coverage** (Day 4):
```python
async def _get_test_coverage(self, service: str) -> float:
    """Get real test coverage from pytest-cov."""
    try:
        service_path = f"backend/services/{service}"

        # Run pytest with coverage
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=json", "-q"],
            capture_output=True, text=True, cwd=service_path
        )

        # Read coverage.json
        coverage_file = Path(service_path) / "coverage.json"
        if not coverage_file.exists():
            logger.warning(f"No coverage.json for {service}")
            return 0.0

        coverage_data = json.loads(coverage_file.read_text())
        coverage_pct = coverage_data["totals"]["percent_covered"] / 100.0

        logger.info(f"Service {service} coverage: {coverage_pct:.1%}")
        return coverage_pct

    except Exception as e:
        logger.error(f"Failed to get test coverage: {e}")
        return 0.0
```

**Testing**:
- Unit tests for each method with mocked subprocess
- Integration test with real service
- Verify risk scores change based on actual data

**Deliverable**: Real risk assessment with 0 hardcoded values

**Estimated**: 4 days

---

#### **Week 2: P0.2 - Implement Digital Twin Validation**

**Problem**: Patches applied directly to production without validation.

**Solution**:

1. **Digital Twin Environment** (Day 1-3):
```python
# backend/services/penelope_service/core/digital_twin.py

class DigitalTwinEnvironment:
    """
    Docker-based digital twin for safe patch validation.

    Creates isolated copy of target service, applies patch,
    runs tests, monitors for regressions.
    """

    def __init__(self, docker_client: DockerClient):
        self.docker = docker_client
        self.twins: dict[str, Container] = {}

    async def create_twin(self, service_name: str) -> str:
        """
        Create digital twin of service.

        Returns:
            twin_id: ID of created container
        """
        # Get service image
        service_image = f"vertice/{service_name}:latest"

        # Create isolated network
        network = self.docker.networks.create(
            f"twin_{service_name}_{uuid4().hex[:8]}",
            driver="bridge",
            internal=True  # No external access
        )

        # Create container with service dependencies
        container = self.docker.containers.run(
            service_image,
            name=f"twin_{service_name}_{uuid4().hex[:8]}",
            network=network.name,
            detach=True,
            environment={
                "ENVIRONMENT": "digital_twin",
                "PENELOPE_MODE": "validation"
            },
            labels={
                "penelope.twin": "true",
                "penelope.service": service_name
            }
        )

        twin_id = container.id
        self.twins[twin_id] = container

        logger.info(f"Created digital twin {twin_id} for {service_name}")
        return twin_id

    async def apply_patch(self, twin_id: str, patch: str) -> bool:
        """
        Apply patch to digital twin.

        Args:
            twin_id: Twin container ID
            patch: Git-style patch content

        Returns:
            success: True if patch applied cleanly
        """
        container = self.twins[twin_id]

        # Copy patch to container
        patch_file = f"/tmp/penelope_patch_{uuid4().hex}.patch"
        container.put_archive("/tmp", create_tar_archive({
            "patch.patch": patch.encode()
        }))

        # Apply patch
        exit_code, output = container.exec_run(
            f"git apply --check {patch_file}",
            workdir="/app"
        )

        if exit_code != 0:
            logger.error(f"Patch validation failed: {output.decode()}")
            return False

        # Actually apply
        exit_code, output = container.exec_run(
            f"git apply {patch_file}",
            workdir="/app"
        )

        return exit_code == 0

    async def run_tests(self, twin_id: str) -> dict[str, Any]:
        """
        Run test suite in digital twin.

        Returns:
            test_results: Dict with passed, failed, coverage
        """
        container = self.twins[twin_id]

        # Run pytest
        exit_code, output = container.exec_run(
            "pytest --cov=. --cov-report=json --json-report --json-report-file=/tmp/test_report.json",
            workdir="/app"
        )

        # Extract test report
        bits, stat = container.get_archive("/tmp/test_report.json")
        test_report_tar = b"".join(bits)
        test_report = extract_from_tar(test_report_tar, "test_report.json")

        # Extract coverage
        bits, stat = container.get_archive("/tmp/coverage.json")
        coverage_tar = b"".join(bits)
        coverage = extract_from_tar(coverage_tar, "coverage.json")

        return {
            "tests_passed": test_report["summary"]["passed"],
            "tests_failed": test_report["summary"]["failed"],
            "coverage": coverage["totals"]["percent_covered"],
            "exit_code": exit_code
        }

    async def monitor_metrics(self, twin_id: str, duration_seconds: int = 60) -> dict[str, Any]:
        """
        Monitor digital twin metrics for regressions.

        Checks:
        - CPU usage
        - Memory usage
        - Response times
        - Error rates
        """
        container = self.twins[twin_id]

        metrics = {
            "cpu_avg": 0.0,
            "memory_avg": 0.0,
            "errors": 0
        }

        samples = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                        stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100.0

            # Calculate memory usage
            memory_usage = stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]

            samples.append({
                "cpu": cpu_percent,
                "memory": memory_usage,
                "timestamp": time.time()
            })

            await asyncio.sleep(5)

        # Aggregate metrics
        metrics["cpu_avg"] = sum(s["cpu"] for s in samples) / len(samples)
        metrics["memory_avg"] = sum(s["memory"] for s in samples) / len(samples)
        metrics["samples"] = len(samples)

        return metrics

    async def destroy_twin(self, twin_id: str) -> None:
        """Destroy digital twin and clean up resources."""
        if twin_id not in self.twins:
            return

        container = self.twins[twin_id]

        # Get network
        network_name = container.attrs["NetworkSettings"]["Networks"].keys()[0]

        # Stop and remove container
        container.stop(timeout=10)
        container.remove(force=True)

        # Remove network
        network = self.docker.networks.get(network_name)
        network.remove()

        del self.twins[twin_id]

        logger.info(f"Destroyed digital twin {twin_id}")
```

2. **Validation Workflow** (Day 4-5):
```python
# Integrate into Sophia Engine decision flow

async def validate_patch_in_twin(self, service: str, patch: str) -> dict[str, Any]:
    """
    Validate patch using digital twin.

    Returns:
        validation_result: Dict with success, test_results, metrics
    """
    twin_env = DigitalTwinEnvironment(docker_client)

    try:
        # Create twin
        twin_id = await twin_env.create_twin(service)

        # Apply patch
        patch_applied = await twin_env.apply_patch(twin_id, patch)
        if not patch_applied:
            return {
                "success": False,
                "reason": "Patch failed to apply cleanly"
            }

        # Run tests
        test_results = await twin_env.run_tests(twin_id)
        if test_results["tests_failed"] > 0:
            return {
                "success": False,
                "reason": f"{test_results['tests_failed']} tests failed",
                "test_results": test_results
            }

        # Check coverage didn't drop
        original_coverage = await self._get_test_coverage(service)
        if test_results["coverage"] < original_coverage - 5.0:  # Allow 5% drop
            return {
                "success": False,
                "reason": f"Coverage dropped from {original_coverage}% to {test_results['coverage']}%",
                "test_results": test_results
            }

        # Monitor for regressions
        metrics = await twin_env.monitor_metrics(twin_id, duration_seconds=120)
        if metrics["cpu_avg"] > 80.0:
            return {
                "success": False,
                "reason": f"High CPU usage: {metrics['cpu_avg']:.1f}%",
                "metrics": metrics
            }

        # All checks passed
        return {
            "success": True,
            "test_results": test_results,
            "metrics": metrics
        }

    finally:
        await twin_env.destroy_twin(twin_id)
```

**Testing**:
- Test twin creation/destruction
- Test patch application
- Test validation workflow
- Load test with concurrent twins

**Deliverable**: Full digital twin validation before production patches

**Estimated**: 5 days

---

#### **Week 3: P0.3 - Implement Rollback Mechanism**

**Problem**: No way to rollback failed patches.

**Solution**:

1. **Patch History Storage** (Day 1-2):
```python
# backend/services/penelope_service/core/patch_history.py

class PatchHistory:
    """
    Git-based patch history with rollback support.

    Stores every patch as a git commit in dedicated branch.
    """

    def __init__(self, history_path: Path = Path("/var/lib/penelope/history")):
        self.history_path = history_path
        self.history_path.mkdir(parents=True, exist_ok=True)

    async def save_patch(
        self,
        service: str,
        patch: str,
        anomaly_id: str,
        metadata: dict[str, Any]
    ) -> str:
        """
        Save patch to history.

        Returns:
            patch_id: Unique patch identifier (git commit hash)
        """
        service_repo = self.history_path / service

        if not service_repo.exists():
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=service_repo, check=True)
            subprocess.run(
                ["git", "checkout", "-b", "penelope-patches"],
                cwd=service_repo, check=True
            )

        # Create patch file
        patch_file = service_repo / f"patch_{anomaly_id}.patch"
        patch_file.write_text(patch)

        # Create metadata file
        metadata_file = service_repo / f"metadata_{anomaly_id}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Commit
        subprocess.run(["git", "add", "."], cwd=service_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Patch for anomaly {anomaly_id}"],
            cwd=service_repo, check=True
        )

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=service_repo, capture_output=True, text=True, check=True
        )
        patch_id = result.stdout.strip()

        logger.info(f"Saved patch {patch_id} for {service}")
        return patch_id

    async def rollback_patch(self, service: str, patch_id: str) -> bool:
        """
        Rollback a specific patch.

        Returns:
            success: True if rollback succeeded
        """
        service_repo = self.history_path / service

        try:
            # Create reverse patch
            result = subprocess.run(
                ["git", "show", patch_id, "--", f"patch_*.patch"],
                cwd=service_repo, capture_output=True, text=True, check=True
            )

            original_patch = result.stdout

            # Generate reverse patch
            reverse_patch = subprocess.run(
                ["patch", "-R"],
                input=original_patch.encode(),
                capture_output=True, check=True
            )

            # Apply to production service
            service_path = Path(f"backend/services/{service}")
            subprocess.run(
                ["git", "apply"],
                input=reverse_patch.stdout,
                cwd=service_path, check=True
            )

            # Record rollback
            rollback_metadata = {
                "patch_id": patch_id,
                "rolled_back_at": datetime.utcnow().isoformat(),
                "reason": "manual_rollback"
            }

            rollback_file = service_repo / f"rollback_{patch_id}.json"
            rollback_file.write_text(json.dumps(rollback_metadata, indent=2))

            subprocess.run(["git", "add", "."], cwd=service_repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Rollback patch {patch_id}"],
                cwd=service_repo, check=True
            )

            logger.info(f"Rolled back patch {patch_id} for {service}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def get_patch_status(self, service: str, patch_id: str) -> dict[str, Any]:
        """Get status of a specific patch."""
        service_repo = self.history_path / service

        # Check if rolled back
        rollback_file = service_repo / f"rollback_{patch_id}.json"
        if rollback_file.exists():
            rollback_data = json.loads(rollback_file.read_text())
            return {
                "status": "rolled_back",
                "rollback_info": rollback_data
            }

        # Check if still applied
        result = subprocess.run(
            ["git", "log", "--oneline", "--all", "--grep", patch_id],
            cwd=service_repo, capture_output=True, text=True
        )

        if patch_id in result.stdout:
            return {"status": "applied", "patch_id": patch_id}

        return {"status": "unknown"}
```

2. **Auto-Rollback on Failure** (Day 3-4):
```python
# Integrate into patch application flow

async def apply_patch_with_rollback(
    self,
    service: str,
    patch: str,
    anomaly_id: str
) -> dict[str, Any]:
    """
    Apply patch with automatic rollback on failure.

    Monitors service for 5 minutes after patch.
    Auto-rollback if errors spike or service crashes.
    """
    patch_history = PatchHistory()

    # Save to history
    patch_id = await patch_history.save_patch(
        service, patch, anomaly_id,
        metadata={
            "applied_at": datetime.utcnow().isoformat(),
            "applied_by": "penelope",
            "anomaly_id": anomaly_id
        }
    )

    # Get baseline metrics
    baseline = await self._get_service_metrics(service)

    try:
        # Apply patch
        service_path = Path(f"backend/services/{service}")
        subprocess.run(
            ["git", "apply"],
            input=patch.encode(),
            cwd=service_path, check=True
        )

        # Restart service
        await self._restart_service(service)

        # Monitor for 5 minutes
        logger.info(f"Monitoring {service} for regressions (5 min)")

        for i in range(30):  # 30 checks, 10 seconds apart
            await asyncio.sleep(10)

            current_metrics = await self._get_service_metrics(service)

            # Check for regressions
            if current_metrics["error_rate"] > baseline["error_rate"] * 2.0:
                raise PatchRegressionError(
                    f"Error rate doubled: {baseline['error_rate']} → {current_metrics['error_rate']}"
                )

            if not current_metrics["healthy"]:
                raise PatchRegressionError("Service became unhealthy")

        logger.info(f"✅ Patch {patch_id} stable after 5 minutes")
        return {
            "success": True,
            "patch_id": patch_id
        }

    except Exception as e:
        logger.error(f"Patch failed, rolling back: {e}")

        # Automatic rollback
        rollback_success = await patch_history.rollback_patch(service, patch_id)

        if rollback_success:
            await self._restart_service(service)

            return {
                "success": False,
                "patch_id": patch_id,
                "error": str(e),
                "rolled_back": True
            }
        else:
            # Rollback failed - CRITICAL
            await self._alert_human(
                service=service,
                severity="CRITICAL",
                message=f"Patch {patch_id} failed AND rollback failed. Manual intervention required.",
                patch_id=patch_id,
                error=str(e)
            )

            return {
                "success": False,
                "patch_id": patch_id,
                "error": str(e),
                "rolled_back": False,
                "alert_sent": True
            }
```

**Testing**:
- Test patch save/load
- Test rollback mechanism
- Test auto-rollback on failure
- Test alert on rollback failure

**Deliverable**: Full rollback support with monitoring

**Estimated**: 4 days

---

#### **Week 4: P0.4 - Implement Wisdom Base**

**Problem**: Wisdom Base client exists but has no backend implementation.

**Solution**:

1. **Choose Storage** (Day 1):

**Option A: PostgreSQL + pgvector (RECOMMENDED)**
- Pros: SQL + vector similarity, proven, lower ops complexity
- Cons: Less "cool" than graph DB

**Option B: Neo4j**
- Pros: Graph relationships, complex queries
- Cons: Higher ops complexity, may be overkill

**Decision: PostgreSQL + pgvector** for pragmatism.

2. **Schema Design** (Day 1):
```sql
-- Wisdom Base schema

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE precedents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_type VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    anomaly_description TEXT NOT NULL,
    anomaly_embedding vector(1536),  -- OpenAI ada-002 dimension

    intervention_level VARCHAR(50),
    patch_content TEXT,
    patch_applied_at TIMESTAMP,

    outcome VARCHAR(20) NOT NULL,  -- success, failure, partial
    outcome_description TEXT,

    metrics_before JSONB,
    metrics_after JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    similarity_score FLOAT,  -- For query results

    INDEX idx_anomaly_type (anomaly_type),
    INDEX idx_service (service_name),
    INDEX idx_outcome (outcome),
    INDEX idx_embedding vector_cosine_ops (anomaly_embedding)
);

CREATE TABLE intervention_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    precedent_id UUID REFERENCES precedents(id),

    monitored_duration_minutes INT,
    error_rate_before FLOAT,
    error_rate_after FLOAT,
    cpu_usage_before FLOAT,
    cpu_usage_after FLOAT,
    memory_usage_before FLOAT,
    memory_usage_after FLOAT,

    rolled_back BOOLEAN DEFAULT FALSE,
    rollback_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);
```

3. **Wisdom Base Implementation** (Day 2-5):
```python
# backend/services/penelope_service/core/wisdom_base_real.py

import asyncpg
from openai import AsyncOpenAI

class WisdomBase:
    """
    PostgreSQL + pgvector implementation of Wisdom Base.

    Stores intervention precedents with vector embeddings
    for semantic similarity search.
    """

    def __init__(
        self,
        postgres_url: str,
        openai_api_key: str
    ):
        self.postgres_url = postgres_url
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.pool: asyncpg.Pool | None = None

    async def initialize(self) -> bool:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(self.postgres_url)

            # Verify connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            logger.info("✅ Wisdom Base initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Wisdom Base: {e}")
            return False

    async def shutdown(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    async def _get_embedding(self, text: str) -> list[float]:
        """Get OpenAI embedding for text."""
        response = await self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    async def store_precedent(
        self,
        anomaly: Anomaly,
        intervention_level: InterventionLevel,
        patch: str,
        outcome: str,
        outcome_description: str,
        metrics_before: dict,
        metrics_after: dict
    ) -> str:
        """
        Store intervention precedent in Wisdom Base.

        Returns:
            precedent_id: UUID of stored precedent
        """
        # Create description for embedding
        description = f"""
        Anomaly Type: {anomaly.anomaly_type}
        Service: {anomaly.service}
        Description: {anomaly.description}
        Severity: {anomaly.severity.value}
        Metrics: {json.dumps(anomaly.metrics)}
        """

        # Get embedding
        embedding = await self._get_embedding(description)

        # Store in database
        async with self.pool.acquire() as conn:
            precedent_id = await conn.fetchval(
                """
                INSERT INTO precedents (
                    anomaly_type, service_name, anomaly_description,
                    anomaly_embedding, intervention_level, patch_content,
                    patch_applied_at, outcome, outcome_description,
                    metrics_before, metrics_after
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """,
                anomaly.anomaly_type,
                anomaly.service,
                anomaly.description,
                embedding,
                intervention_level.value,
                patch,
                datetime.utcnow(),
                outcome,
                outcome_description,
                json.dumps(metrics_before),
                json.dumps(metrics_after)
            )

        logger.info(f"Stored precedent {precedent_id} in Wisdom Base")
        return precedent_id

    async def query_precedents(
        self,
        anomaly_type: str,
        service: str,
        similarity_threshold: float = 0.85,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Query similar precedents using vector similarity.

        Returns:
            List of similar precedents ordered by similarity
        """
        # Create query embedding
        query_text = f"Anomaly Type: {anomaly_type}\nService: {service}"
        query_embedding = await self._get_embedding(query_text)

        # Vector similarity search
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id, anomaly_type, service_name, anomaly_description,
                    intervention_level, outcome, outcome_description,
                    metrics_before, metrics_after,
                    1 - (anomaly_embedding <=> $1::vector) AS similarity
                FROM precedents
                WHERE
                    anomaly_type = $2
                    AND (service_name = $3 OR service_name = 'any')
                    AND 1 - (anomaly_embedding <=> $1::vector) >= $4
                ORDER BY similarity DESC
                LIMIT $5
                """,
                query_embedding,
                anomaly_type,
                service,
                similarity_threshold,
                limit
            )

        precedents = []
        for row in rows:
            precedents.append({
                "id": str(row["id"]),
                "anomaly_type": row["anomaly_type"],
                "service": row["service_name"],
                "description": row["anomaly_description"],
                "intervention_level": row["intervention_level"],
                "outcome": row["outcome"],
                "outcome_description": row["outcome_description"],
                "metrics_before": json.loads(row["metrics_before"]),
                "metrics_after": json.loads(row["metrics_after"]),
                "similarity": float(row["similarity"])
            })

        logger.info(f"Found {len(precedents)} precedents for {anomaly_type}/{service}")
        return precedents

    async def get_intervention_success_rate(
        self,
        anomaly_type: str,
        service: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate success rate for intervention type.

        Returns:
            Dict with success_rate, total_count, success_count
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes
                FROM precedents
                WHERE
                    anomaly_type = $1
                    AND ($2::varchar IS NULL OR service_name = $2)
                """,
                anomaly_type,
                service
            )

        total = row["total"]
        successes = row["successes"]

        if total == 0:
            return {
                "success_rate": None,
                "total_count": 0,
                "success_count": 0,
                "has_data": False
            }

        return {
            "success_rate": successes / total,
            "total_count": total,
            "success_count": successes,
            "has_data": True
        }
```

**Testing**:
- Test precedent storage
- Test vector similarity search
- Test success rate calculation
- Load test with 10,000 precedents

**Deliverable**: Fully functional Wisdom Base with vector search

**Estimated**: 5 days

---

#### **Weeks 5-6: P1 Critical Issues**

**P1.5 - Circuit Breaker & Rate Limiting** (3 days):
```python
# Prevent runaway auto-healing

class HealingCircuitBreaker:
    """
    Circuit breaker for auto-healing operations.

    Opens after N failures in M minutes.
    Half-open after cooldown period.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        window_minutes: int = 15,
        cooldown_minutes: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.window_minutes = window_minutes
        self.cooldown_minutes = cooldown_minutes

        self.failures: dict[str, list[float]] = {}  # service -> timestamps
        self.state: dict[str, str] = {}  # service -> state (closed, open, half_open)
        self.opened_at: dict[str, float] = {}  # service -> timestamp

    def is_allowed(self, service: str) -> bool:
        """Check if healing is allowed for service."""
        state = self.state.get(service, "closed")

        if state == "closed":
            return True

        if state == "open":
            # Check if cooldown expired
            if time.time() - self.opened_at[service] > self.cooldown_minutes * 60:
                self.state[service] = "half_open"
                return True
            return False

        if state == "half_open":
            # Allow one attempt
            return True

        return False

    def record_failure(self, service: str) -> None:
        """Record healing failure."""
        now = time.time()

        if service not in self.failures:
            self.failures[service] = []

        # Add failure
        self.failures[service].append(now)

        # Remove old failures outside window
        window_start = now - (self.window_minutes * 60)
        self.failures[service] = [
            ts for ts in self.failures[service]
            if ts > window_start
        ]

        # Check threshold
        if len(self.failures[service]) >= self.failure_threshold:
            self.state[service] = "open"
            self.opened_at[service] = now

            logger.warning(
                f"🚨 Circuit breaker OPENED for {service} "
                f"({len(self.failures[service])} failures in {self.window_minutes}m)"
            )

    def record_success(self, service: str) -> None:
        """Record healing success."""
        if self.state.get(service) == "half_open":
            # Close circuit
            self.state[service] = "closed"
            self.failures[service] = []

            logger.info(f"✅ Circuit breaker CLOSED for {service}")
```

**P1.6 - Audit Trail** (2 days):
```python
# All Sophia Engine decisions must be auditable

class DecisionAuditLogger:
    """
    Append-only audit log for all healing decisions.

    Stores to Loki with structured fields.
    """

    async def log_decision(
        self,
        anomaly_id: str,
        decision: InterventionDecision,
        reasoning: str,
        risk_assessment: dict,
        precedents: list[dict],
        sophia_wisdom: str
    ) -> None:
        """Log Sophia Engine decision."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "anomaly_id": anomaly_id,
            "decision": decision.value,
            "reasoning": reasoning,
            "risk_score": risk_assessment.get("risk_score"),
            "risk_factors": risk_assessment.get("risk_factors", []),
            "precedents_count": len(precedents),
            "best_precedent_similarity": max(
                (p["similarity"] for p in precedents),
                default=None
            ),
            "sophia_wisdom": sophia_wisdom,
            "decision_maker": "sophia_engine_v1.0"
        }

        # Log to Loki with labels
        logger.info(
            "SOPHIA_DECISION",
            extra={
                "labels": {
                    "component": "sophia_engine",
                    "decision": decision.value,
                    "anomaly_id": anomaly_id
                },
                "audit": audit_entry
            }
        )

        # Also store in database for querying
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO decision_audit_log (
                    anomaly_id, decision, reasoning, risk_assessment,
                    precedents, sophia_wisdom, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                """,
                anomaly_id,
                decision.value,
                reasoning,
                json.dumps(risk_assessment),
                json.dumps(precedents),
                sophia_wisdom
            )
```

**P1.7 - Human Approval for High-Risk** (3 days):
```python
# High-risk patches require human approval

class HumanApprovalWorkflow:
    """
    Human-in-the-loop approval for high-risk patches.

    Sends notification to Slack/Email, waits for approval.
    """

    async def request_approval(
        self,
        anomaly_id: str,
        patch: str,
        risk_score: float,
        impact_estimate: str
    ) -> dict[str, Any]:
        """
        Request human approval for patch.

        Returns:
            approval_result: Dict with approved, approver, notes
        """
        # Create approval request
        approval_id = str(uuid4())

        # Send to Slack
        await self._send_slack_notification(
            channel="#penelope-approvals",
            message=f"""
🚨 **High-Risk Patch Approval Required**

**Anomaly ID**: {anomaly_id}
**Risk Score**: {risk_score:.2f} / 1.0
**Impact**: {impact_estimate}

**Patch Preview**:
```
{patch[:500]}...
```

**Actions**:
- ✅ Approve: `/penelope approve {approval_id}`
- ❌ Reject: `/penelope reject {approval_id} <reason>`
- 🔍 Details: https://penelope.vertice.ai/approval/{approval_id}

**Timeout**: 2 hours (auto-reject after)
            """
        )

        # Wait for approval (with timeout)
        approval_result = await self._wait_for_approval(
            approval_id,
            timeout_seconds=7200  # 2 hours
        )

        return approval_result
```

**P1.8 - Test Coverage 90%+** (5 days):
```bash
# Comprehensive test suite for PENELOPE

# Unit tests
pytest backend/services/penelope_service/tests/ --cov=. --cov-report=html

# Integration tests (new)
pytest backend/services/penelope_service/tests/integration/ --cov=. --cov-append

# Target: 90%+ coverage
```

**Deliverable**: All P1 issues resolved, production-ready

**Estimated**: 13 days (2.6 weeks)

---

#### **Weeks 7-8: P2 Improvements & Polish**

**P2.11 - Metrics Dashboard** (3 days):
- Grafana dashboard for PENELOPE
- Patch success rate
- Healing velocity
- Circuit breaker status
- Biblical articles compliance

**P2.12 - A/B Testing Framework** (4 days):
- Canary patches (apply to 10% of traffic first)
- Compare metrics before/after
- Gradual rollout

**P2.13 - Documentation** (3 days):
- Complete API documentation
- Biblical articles → code mapping
- Runbook for operators
- Migration guide

**Deliverable**: Polished, documented, production-ready service

**Estimated**: 10 days (2 weeks)

---

### PENELOPE Timeline Summary

| Week | Focus | Deliverable | Status |
|------|-------|-------------|--------|
| 1 | Real risk assessment | No hardcoded values | 🔴 TODO |
| 2 | Digital twin validation | Safe patch testing | 🔴 TODO |
| 3 | Rollback mechanism | Auto-rollback on failure | 🔴 TODO |
| 4 | Wisdom Base | Vector similarity search | 🔴 TODO |
| 5-6 | P1 critical fixes | Circuit breaker, audit, approval | 🔴 TODO |
| 7-8 | Polish & docs | Dashboard, A/B testing, docs | 🔴 TODO |

**Total**: 8 weeks, 40 person-days

---

## 🌐 MABA - Browser Agent Correction Plan

### Current Problems Summary

**P0 Blockers** (2 issues):
1. No domain whitelist (security risk)
2. No network sandbox (can access internal networks)

**P1 Critical** (3 issues):
3. Neo4j may be overkill vs SQL
4. Max 5 browser instances (scalability)
5. CSS selector fragility (breaks when sites change)

**P2 Important** (5 issues):
6. No session timeout/cleanup
7. "Cognitive" learning is basic (just counters)
8. No browser fingerprinting prevention
9. Test coverage unknown
10. No rate limiting on navigation

---

### 📋 MABA Correction Plan

#### **Week 1: P0.1 & P0.2 - Security Hardening**

**Day 1-2: Domain Whitelist** (2 days):
```python
# backend/services/maba_service/core/security_policy.py

class SecurityPolicy:
    """
    Domain whitelist and security controls for MABA.

    Prevents navigation to unauthorized domains.
    """

    def __init__(self, whitelist_path: Path = Path("config/domain_whitelist.yaml")):
        self.whitelist = self._load_whitelist(whitelist_path)
        self.blacklist = self._load_blacklist()  # Internal IPs, localhost, etc.

    def _load_whitelist(self, path: Path) -> set[str]:
        """Load whitelisted domains."""
        if not path.exists():
            logger.warning("No domain whitelist found, using permissive default")
            return {"*"}  # Allow all (not recommended for production)

        config = yaml.safe_load(path.read_text())
        return set(config.get("allowed_domains", []))

    def _load_blacklist(self) -> set[str]:
        """Load blacklisted domains (internal networks, etc.)."""
        return {
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "10.*",  # Private network
            "172.16.*",  # Private network
            "192.168.*",  # Private network
            "169.254.*",  # Link-local
            "*.internal",
            "*.local"
        }

    def is_allowed(self, url: str) -> tuple[bool, str]:
        """
        Check if URL is allowed.

        Returns:
            (allowed, reason)
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check blacklist first
        for pattern in self.blacklist:
            if self._match_pattern(domain, pattern):
                return False, f"Domain {domain} is blacklisted (internal/private network)"

        # Check whitelist
        if "*" in self.whitelist:
            return True, "All domains allowed"

        for pattern in self.whitelist:
            if self._match_pattern(domain, pattern):
                return True, f"Domain {domain} matches whitelist pattern {pattern}"

        return False, f"Domain {domain} not in whitelist"

    def _match_pattern(self, domain: str, pattern: str) -> bool:
        """Match domain against pattern (supports wildcards)."""
        if pattern == "*":
            return True

        if "*" in pattern:
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex}$", domain))

        return domain == pattern

# Integrate into BrowserController

async def navigate(
    self,
    session_id: str,
    url: str,
    wait_until: str = "networkidle",
    timeout_ms: int = 30000,
) -> dict[str, Any]:
    """Navigate to URL (with security check)."""

    # Security check
    allowed, reason = self.security_policy.is_allowed(url)
    if not allowed:
        self.actions_total.labels(
            action_type="navigate", status="blocked"
        ).inc()

        logger.warning(f"🚫 Blocked navigation to {url}: {reason}")

        return {
            "status": "blocked",
            "error": f"Security policy violation: {reason}"
        }

    # Continue with navigation...
```

**Day 3-4: Network Sandbox** (2 days):
```python
# Use Docker network isolation for browser containers

class SandboxedBrowserController(BrowserController):
    """
    Browser controller with network sandboxing.

    Runs browsers in isolated Docker containers with network restrictions.
    """

    async def create_session(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: str | None = None,
    ) -> str:
        """Create sandboxed browser session."""

        # Create isolated network
        network = self.docker.networks.create(
            f"maba_sandbox_{uuid4().hex[:8]}",
            driver="bridge",
            internal=False,  # Allow external, but restrict via firewall rules
            options={
                "com.docker.network.bridge.name": f"maba{uuid4().hex[:8]}",
                "com.docker.network.driver.mtu": "1500"
            }
        )

        # Create firewall rules (iptables)
        # Block private networks, allow only whitelisted domains
        self._configure_network_firewall(network.name)

        # Launch browser in container
        container = self.docker.containers.run(
            "mcr.microsoft.com/playwright:v1.40.0",
            command=[
                "python", "-m", "playwright", "run-server",
                "--browser", "chromium", "--headless"
            ],
            network=network.name,
            detach=True,
            mem_limit="2g",
            cpu_quota=100000,  # 1 CPU
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            read_only=True,
            tmpfs={"/tmp": "size=512m,mode=1777"}
        )

        session_id = str(uuid4())
        self._sessions[session_id] = {
            "container": container,
            "network": network,
            "created_at": time.time()
        }

        logger.info(f"✅ Created sandboxed browser session {session_id}")
        return session_id

    def _configure_network_firewall(self, network_name: str) -> None:
        """Configure iptables rules for network."""
        # Block private networks
        subprocess.run([
            "iptables", "-A", "DOCKER-USER",
            "-i", network_name,
            "-d", "10.0.0.0/8", "-j", "DROP"
        ])

        subprocess.run([
            "iptables", "-A", "DOCKER-USER",
            "-i", network_name,
            "-d", "172.16.0.0/12", "-j", "DROP"
        ])

        subprocess.run([
            "iptables", "-A", "DOCKER-USER",
            "-i", network_name,
            "-d", "192.168.0.0/16", "-j", "DROP"
        ])

        # Rate limiting (max 100 connections per minute)
        subprocess.run([
            "iptables", "-A", "DOCKER-USER",
            "-i", network_name,
            "-m", "limit", "--limit", "100/min",
            "-j", "ACCEPT"
        ])
```

**Day 5: Configuration** (1 day):
```yaml
# config/domain_whitelist.yaml

allowed_domains:
  - "*.wikipedia.org"
  - "*.github.com"
  - "*.stackoverflow.com"
  - "google.com"
  - "*.google.com"
  # Add production domains here

security:
  max_navigation_depth: 50  # Prevent infinite loops
  max_session_duration_minutes: 60
  max_requests_per_session: 1000

  blocked_file_types:
    - ".exe"
    - ".dll"
    - ".dmg"
    - ".pkg"

  blocked_schemes:
    - "file://"
    - "ftp://"
    - "ftps://"
```

**Deliverable**: MABA cannot access internal networks or unauthorized domains

**Estimated**: 5 days

---

#### **Week 2: P1.3 - Evaluate Neo4j vs SQL**

**Day 1-2: Benchmark** (2 days):

Run benchmark comparing Neo4j vs PostgreSQL for cognitive map:
- Store 10,000 pages with elements
- Query similar pages (100 queries)
- Find navigation paths (100 queries)
- Measure latency, memory, CPU

**Day 3-4: SQL Alternative Implementation** (2 days):
```python
# backend/services/maba_service/core/cognitive_map_sql.py

class CognitiveMapSQL:
    """
    PostgreSQL-based cognitive map (alternative to Neo4j).

    Uses JSONB for flexible element storage, GIN indexes for fast queries.
    """

    async def initialize(self) -> bool:
        """Initialize PostgreSQL schema."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    title TEXT,
                    visit_count INT DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'::jsonb,

                    INDEX idx_domain (domain),
                    INDEX idx_url_hash (md5(url))
                );

                CREATE TABLE IF NOT EXISTS elements (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
                    selector TEXT NOT NULL,
                    tag TEXT,
                    text TEXT,
                    attributes JSONB DEFAULT '{}'::jsonb,
                    importance FLOAT DEFAULT 0.5,
                    interaction_count INT DEFAULT 0,

                    UNIQUE (page_id, selector),
                    INDEX idx_selector (selector),
                    INDEX idx_page_id (page_id),
                    INDEX idx_importance (importance DESC)
                );

                CREATE TABLE IF NOT EXISTS navigation_edges (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    from_page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
                    to_page_id UUID REFERENCES pages(id) ON DELETE CASCADE,
                    action TEXT,
                    selector TEXT,
                    count INT DEFAULT 0,
                    last_used TIMESTAMP DEFAULT NOW(),

                    UNIQUE (from_page_id, to_page_id, action),
                    INDEX idx_from_page (from_page_id),
                    INDEX idx_to_page (to_page_id)
                );
            """)

        logger.info("✅ SQL cognitive map schema initialized")
        return True

    async def find_element(
        self, url: str, description: str, min_importance: float = 0.3
    ) -> str | None:
        """Find element by description (SQL full-text search)."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT e.selector
                FROM elements e
                JOIN pages p ON e.page_id = p.id
                WHERE
                    p.url = $1
                    AND e.text ILIKE '%' || $2 || '%'
                    AND e.importance >= $3
                ORDER BY e.importance DESC
                LIMIT 1
                """,
                url, description, min_importance
            )

            return row["selector"] if row else None

    async def get_navigation_path(
        self, from_url: str, to_url: str
    ) -> list[tuple[str, str]] | None:
        """Find navigation path using WITH RECURSIVE (SQL)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                WITH RECURSIVE path AS (
                    -- Base case: start page
                    SELECT
                        p1.id as from_id,
                        p2.id as to_id,
                        ne.action,
                        ARRAY[p1.url, p2.url] as path_urls,
                        ARRAY[ne.action] as actions,
                        1 as depth
                    FROM pages p1
                    JOIN navigation_edges ne ON p1.id = ne.from_page_id
                    JOIN pages p2 ON ne.to_page_id = p2.id
                    WHERE p1.url = $1

                    UNION ALL

                    -- Recursive case: extend path
                    SELECT
                        path.to_id,
                        p3.id,
                        ne2.action,
                        path.path_urls || p3.url,
                        path.actions || ne2.action,
                        path.depth + 1
                    FROM path
                    JOIN navigation_edges ne2 ON path.to_id = ne2.from_page_id
                    JOIN pages p3 ON ne2.to_page_id = p3.id
                    WHERE
                        p3.url != ALL(path.path_urls)  -- Prevent cycles
                        AND path.depth < 10  -- Max depth
                )
                SELECT path_urls, actions
                FROM path
                WHERE path_urls[array_upper(path_urls, 1)] = $2
                ORDER BY depth
                LIMIT 1
                """,
                from_url, to_url
            )

            if not rows:
                return None

            row = rows[0]
            urls = row["path_urls"]
            actions = row["actions"]

            return list(zip(urls[1:], actions))
```

**Day 5: Decision** (1 day):

Compare results:
- If Neo4j is <20% faster → **Switch to SQL** (lower ops complexity)
- If Neo4j is ≥20% faster → **Keep Neo4j** but document operational requirements

**Deliverable**: Decision document with benchmark results

**Estimated**: 5 days

---

#### **Week 3: P1.4 & P1.5 - Scalability & Robustness**

**Day 1-3: Dynamic Browser Pooling** (3 days):
```python
# Remove hardcoded max_instances=5 limit

class DynamicBrowserPool:
    """
    Auto-scaling browser instance pool.

    Scales up/down based on demand, respects resource limits.
    """

    def __init__(
        self,
        min_instances: int = 2,
        max_instances: int = 20,
        target_cpu_percent: float = 70.0,
        scale_up_threshold: float = 80.0,
        scale_down_threshold: float = 30.0
    ):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.target_cpu = target_cpu_percent
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold

        self.instances: list[BrowserInstance] = []
        self._scaling_lock = asyncio.Lock()

    async def get_instance(self) -> BrowserInstance:
        """Get available browser instance (auto-scale if needed)."""
        # Check if scaling needed
        await self._check_and_scale()

        # Find least loaded instance
        instance = min(self.instances, key=lambda i: i.session_count)

        return instance

    async def _check_and_scale(self) -> None:
        """Check metrics and scale pool if needed."""
        async with self._scaling_lock:
            if len(self.instances) == 0:
                # Bootstrap
                await self._scale_up(self.min_instances)
                return

            # Calculate aggregate CPU usage
            total_cpu = sum(i.cpu_usage for i in self.instances)
            avg_cpu = total_cpu / len(self.instances)

            # Scale up if CPU high
            if avg_cpu > self.scale_up_threshold:
                if len(self.instances) < self.max_instances:
                    await self._scale_up(1)
                    logger.info(f"Scaled up browser pool (CPU: {avg_cpu:.1f}%)")

            # Scale down if CPU low
            elif avg_cpu < self.scale_down_threshold:
                if len(self.instances) > self.min_instances:
                    await self._scale_down(1)
                    logger.info(f"Scaled down browser pool (CPU: {avg_cpu:.1f}%)")

    async def _scale_up(self, count: int) -> None:
        """Add browser instances."""
        for _ in range(count):
            instance = await BrowserInstance.create()
            self.instances.append(instance)

    async def _scale_down(self, count: int) -> None:
        """Remove browser instances."""
        # Remove least utilized instances
        sorted_instances = sorted(self.instances, key=lambda i: i.session_count)

        for instance in sorted_instances[:count]:
            if instance.session_count == 0:
                await instance.shutdown()
                self.instances.remove(instance)
```

**Day 4-5: Selector Robustness** (2 days):
```python
# Handle CSS selector changes gracefully

class RobustElementLocator:
    """
    Multi-strategy element locator.

    Falls back through multiple strategies if selector fails.
    """

    async def find_element(
        self,
        page: Page,
        selector: str,
        fallback_strategies: bool = True
    ) -> Element | None:
        """
        Find element with fallback strategies.

        Strategy order:
        1. Exact CSS selector
        2. data-testid attribute
        3. ARIA label
        4. Text content
        5. XPath
        6. Visual position (AI vision)
        """
        # Strategy 1: Direct CSS
        try:
            element = await page.query_selector(selector)
            if element:
                return element
        except Exception as e:
            logger.debug(f"CSS selector failed: {e}")

        if not fallback_strategies:
            return None

        # Strategy 2: data-testid
        if "data-testid" in selector:
            testid = selector.split("data-testid=")[1].strip('"]')
            element = await page.query_selector(f'[data-testid="{testid}"]')
            if element:
                logger.info(f"Found via data-testid: {testid}")
                return element

        # Strategy 3: ARIA label
        element = await page.query_selector(f'[aria-label*="{selector}"]')
        if element:
            logger.info(f"Found via ARIA label")
            return element

        # Strategy 4: Text content
        elements = await page.query_selector_all('button, a, input, [role="button"]')
        for el in elements:
            text = await el.text_content()
            if text and selector.lower() in text.lower():
                logger.info(f"Found via text content: {text}")
                return el

        # Strategy 5: XPath (last resort)
        try:
            element = await page.query_selector(f'xpath=//*[contains(text(), "{selector}")]')
            if element:
                logger.info(f"Found via XPath")
                return element
        except Exception:
            pass

        logger.warning(f"Element not found: {selector}")
        return None
```

**Deliverable**: MABA scales to 20+ browsers, handles selector changes gracefully

**Estimated**: 5 days

---

#### **Weeks 4-5: Coverage, Tests, Polish**

**Coverage to 90%+** (5 days):
- Unit tests for all components
- Integration tests for browser + cognitive map
- End-to-end test scenarios

**Session Management** (3 days):
- Auto-timeout idle sessions (30 min)
- Memory leak prevention
- Graceful cleanup on shutdown

**Documentation** (2 days):
- API documentation
- Security policy guide
- Operational runbook

**Deliverable**: Production-ready MABA with 90%+ coverage

**Estimated**: 10 days (2 weeks)

---

### MABA Timeline Summary

| Week | Focus | Deliverable | Status |
|------|-------|-------------|--------|
| 1 | Security hardening | Whitelist, sandbox | 🔴 TODO |
| 2 | Neo4j vs SQL evaluation | Benchmark, decision | 🔴 TODO |
| 3 | Scalability & robustness | Dynamic pool, selector fallback | 🔴 TODO |
| 4-5 | Coverage & polish | 90%+ coverage, docs | 🔴 TODO |

**Total**: 5 weeks, 25 person-days

---

## 📊 MVP - Vision Protocol Correction Plan

### Current Problems Summary

**P0 Blockers** (2 issues):
1. No cost tracking (can spiral to $1000s/month)
2. No rate limiting on narrative generation

**P1 Critical** (3 issues):
3. Misleading name ("Vision" but no computer vision)
4. No caching (wastes API calls on unchanged metrics)
5. Naive anomaly detection (hardcoded thresholds)

**P2 Important** (5 issues):
6. Audio/video generation not implemented (despite docs)
7. Test coverage unknown
8. No A/B testing of narrative quality
9. No feedback loop for improving narratives
10. SystemObserver implementation incomplete

---

### 📋 MVP Correction Plan

#### **Week 1: P0.1 & P0.2 - Cost Control**

**Day 1-2: Cost Tracking** (2 days):
```python
# backend/services/mvp_service/core/cost_tracker.py

class CostTracker:
    """
    Track and limit Claude API costs.

    Alerts when approaching budget limits.
    """

    def __init__(
        self,
        daily_budget_usd: float = 10.0,
        monthly_budget_usd: float = 300.0
    ):
        self.daily_budget = daily_budget_usd
        self.monthly_budget = monthly_budget_usd

        # Pricing (Sonnet 4.5, Jan 2025)
        self.input_cost_per_mtok = 3.00   # $3 per million tokens
        self.output_cost_per_mtok = 15.00  # $15 per million tokens

        self.costs: dict[str, float] = {}  # date -> cost
        self._lock = asyncio.Lock()

    async def track_request(
        self,
        input_tokens: int,
        output_tokens: int,
        timestamp: datetime | None = None
    ) -> dict[str, Any]:
        """
        Track API request cost.

        Returns:
            Dict with cost, daily_total, monthly_total, within_budget
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_mtok
        total_cost = input_cost + output_cost

        date_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")

        async with self._lock:
            # Update daily cost
            if date_key not in self.costs:
                self.costs[date_key] = 0.0
            self.costs[date_key] += total_cost

            # Calculate totals
            daily_total = self.costs[date_key]
            monthly_total = sum(
                cost for key, cost in self.costs.items()
                if key.startswith(month_key)
            )

            # Check budgets
            within_daily = daily_total <= self.daily_budget
            within_monthly = monthly_total <= self.monthly_budget

            result = {
                "cost_usd": total_cost,
                "daily_total": daily_total,
                "monthly_total": monthly_total,
                "daily_budget": self.daily_budget,
                "monthly_budget": self.monthly_budget,
                "within_daily_budget": within_daily,
                "within_monthly_budget": within_monthly,
                "daily_remaining": max(0, self.daily_budget - daily_total),
                "monthly_remaining": max(0, self.monthly_budget - monthly_total)
            }

            # Alert if over budget
            if not within_daily:
                logger.error(
                    f"🚨 Daily budget exceeded: ${daily_total:.2f} / ${self.daily_budget:.2f}"
                )

            if not within_monthly:
                logger.error(
                    f"🚨 Monthly budget exceeded: ${monthly_total:.2f} / ${self.monthly_budget:.2f}"
                )

            # Prometheus metrics
            self.cost_gauge.labels(period="daily").set(daily_total)
            self.cost_gauge.labels(period="monthly").set(monthly_total)

            return result

    def is_within_budget(self) -> bool:
        """Check if within budget limits."""
        now = datetime.utcnow()
        date_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")

        daily_total = self.costs.get(date_key, 0.0)
        monthly_total = sum(
            cost for key, cost in self.costs.items()
            if key.startswith(month_key)
        )

        return daily_total <= self.daily_budget and monthly_total <= self.monthly_budget
```

**Day 3-4: Rate Limiting** (2 days):
```python
# backend/services/mvp_service/core/rate_limiter.py

class NarrativeRateLimiter:
    """
    Rate limit narrative generation to control costs.

    Limits:
    - Max 100 narratives/hour
    - Max 1000 narratives/day
    - Min 60 seconds between narratives for same service
    """

    def __init__(
        self,
        max_per_hour: int = 100,
        max_per_day: int = 1000,
        min_interval_seconds: int = 60
    ):
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.min_interval = min_interval_seconds

        self.request_history: list[float] = []
        self.last_request: dict[str, float] = {}  # service -> timestamp
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, service: str | None = None) -> tuple[bool, str]:
        """
        Check if request is allowed.

        Returns:
            (allowed, reason)
        """
        now = time.time()

        async with self._lock:
            # Check global rate limits
            hour_ago = now - 3600
            day_ago = now - 86400

            # Clean old entries
            self.request_history = [
                ts for ts in self.request_history
                if ts > day_ago
            ]

            # Count requests
            hour_count = sum(1 for ts in self.request_history if ts > hour_ago)
            day_count = len(self.request_history)

            if hour_count >= self.max_per_hour:
                return False, f"Hourly limit reached ({hour_count}/{self.max_per_hour})"

            if day_count >= self.max_per_day:
                return False, f"Daily limit reached ({day_count}/{self.max_per_day})"

            # Check service-specific interval
            if service:
                last = self.last_request.get(service, 0)
                elapsed = now - last

                if elapsed < self.min_interval:
                    remaining = self.min_interval - elapsed
                    return False, f"Too soon for {service} (wait {remaining:.0f}s)"

            # All checks passed
            self.request_history.append(now)
            if service:
                self.last_request[service] = now

            return True, "OK"

# Integrate into NarrativeEngine

async def generate_narrative(
    self,
    narrative_type: str,
    metrics_data: dict[str, Any],
    time_range_minutes: int = 60,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Generate narrative (with cost control)."""

    # Check rate limit
    allowed, reason = await self.rate_limiter.check_rate_limit()
    if not allowed:
        raise RateLimitExceededError(f"Rate limit exceeded: {reason}")

    # Check budget
    if not self.cost_tracker.is_within_budget():
        raise BudgetExceededError("Monthly budget exceeded, narrative generation disabled")

    # Generate narrative
    message = await self.client.messages.create(...)

    # Track cost
    cost_info = await self.cost_tracker.track_request(
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens
    )

    # Include cost in result
    result["cost_usd"] = cost_info["cost_usd"]
    result["monthly_total_usd"] = cost_info["monthly_total"]
    result["budget_remaining_usd"] = cost_info["monthly_remaining"]

    return result
```

**Day 5: Budget Configuration** (1 day):
```yaml
# config/mvp_budgets.yaml

cost_limits:
  daily_budget_usd: 10.00
  monthly_budget_usd: 300.00
  alert_threshold_percent: 80  # Alert at 80% of budget

rate_limits:
  max_narratives_per_hour: 100
  max_narratives_per_day: 1000
  min_interval_seconds: 60  # 1 narrative per minute per service

alerts:
  slack_webhook: "${SLACK_WEBHOOK_URL}"
  email: "ops@vertice.ai"
  alert_on_budget_exceeded: true
  alert_on_rate_limit_exceeded: false
```

**Deliverable**: MVP costs controlled, cannot exceed $300/month

**Estimated**: 5 days

---

#### **Week 2: P1.3 - Implement Caching**

**Problem**: Regenerates narrative even if metrics haven't changed.

**Solution** (5 days):
```python
# backend/services/mvp_service/core/narrative_cache.py

class NarrativeCache:
    """
    Redis-based cache for narratives.

    Caches narratives with TTL based on metrics signature.
    Invalidates when metrics change beyond threshold.
    """

    def __init__(self, redis_url: str, ttl_seconds: int = 300):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl_seconds

    def _compute_metrics_hash(self, metrics_data: dict[str, Any]) -> str:
        """
        Compute hash of metrics data.

        Rounds metric values to reduce cache misses for tiny changes.
        """
        # Extract relevant metrics
        metrics = metrics_data.get("metrics", [])

        # Round values to 2 decimal places
        rounded_metrics = []
        for metric in metrics:
            rounded_metrics.append({
                "name": metric["name"],
                "value": round(metric["value"], 2)
            })

        # Sort for consistent hashing
        rounded_metrics.sort(key=lambda m: m["name"])

        # Hash
        metrics_str = json.dumps(rounded_metrics, sort_keys=True)
        return hashlib.sha256(metrics_str.encode()).hexdigest()

    async def get_cached_narrative(
        self,
        narrative_type: str,
        metrics_data: dict[str, Any],
        focus_areas: list[str] | None = None
    ) -> dict[str, Any] | None:
        """Get cached narrative if available."""

        # Create cache key
        metrics_hash = self._compute_metrics_hash(metrics_data)
        focus_str = ",".join(sorted(focus_areas)) if focus_areas else "none"
        cache_key = f"narrative:{narrative_type}:{metrics_hash}:{focus_str}"

        # Check cache
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info(f"✅ Cache HIT for {narrative_type}")
            self.cache_hits.inc()
            return json.loads(cached)

        logger.info(f"❌ Cache MISS for {narrative_type}")
        self.cache_misses.inc()
        return None

    async def cache_narrative(
        self,
        narrative_type: str,
        metrics_data: dict[str, Any],
        focus_areas: list[str] | None,
        narrative_result: dict[str, Any]
    ) -> None:
        """Cache narrative result."""

        metrics_hash = self._compute_metrics_hash(metrics_data)
        focus_str = ",".join(sorted(focus_areas)) if focus_areas else "none"
        cache_key = f"narrative:{narrative_type}:{metrics_hash}:{focus_str}"

        # Add metadata
        cached_data = {
            **narrative_result,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_key": cache_key
        }

        # Store with TTL
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(cached_data)
        )

        logger.info(f"💾 Cached narrative (TTL: {self.ttl}s)")

# Integrate into NarrativeEngine

async def generate_narrative(
    self,
    narrative_type: str,
    metrics_data: dict[str, Any],
    time_range_minutes: int = 60,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Generate narrative (with caching)."""

    # Check cache
    cached = await self.cache.get_cached_narrative(
        narrative_type, metrics_data, focus_areas
    )
    if cached:
        return {
            **cached,
            "cache_hit": True,
            "cost_usd": 0.0  # No API call, no cost
        }

    # Generate fresh narrative
    result = await self._generate_fresh_narrative(
        narrative_type, metrics_data, time_range_minutes, focus_areas
    )

    # Cache result
    await self.cache.cache_narrative(
        narrative_type, metrics_data, focus_areas, result
    )

    result["cache_hit"] = False
    return result
```

**Expected Impact**:
- Cache hit rate: 60-80% (metrics don't change every minute)
- Cost reduction: 60-80% ($300 → $60-120/month)

**Deliverable**: MVP caches narratives, costs reduced by 60-80%

**Estimated**: 5 days

---

#### **Week 3: Rename & Rebrand**

**P1.4 - Rename Service** (3 days):

**Old**: MVP (MAXIMUS Vision Protocol) - misleading name
**New**: **NIS (Narrative Intelligence Service)** - accurate name

**Changes Required**:
1. Rename directory: `mvp_service` → `narrative_service`
2. Update all imports
3. Update documentation
4. Update service registry
5. Update deployment configs
6. Maintain backward compatibility (alias)

```python
# Backward compatibility shim
# backend/services/mvp_service/__init__.py

import warnings
from narrative_service import *

warnings.warn(
    "mvp_service is deprecated, use narrative_service instead",
    DeprecationWarning,
    stacklevel=2
)
```

**P1.5 - Improve Anomaly Detection** (2 days):

Replace naive thresholds with statistical anomaly detection:

```python
# backend/services/narrative_service/core/anomaly_detector.py

class StatisticalAnomalyDetector:
    """
    Statistical anomaly detection using rolling baseline.

    Detects anomalies based on deviation from historical mean/stddev.
    """

    def __init__(self, window_size: int = 1440):  # 24 hours of minute data
        self.window_size = window_size
        self.history: dict[str, deque] = {}  # metric_name -> values

    async def detect_anomalies(
        self, metrics: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Detect anomalies in metrics using statistical methods.

        Returns:
            List of anomalies with severity and description
        """
        anomalies = []

        for metric in metrics:
            name = metric["name"]
            value = metric["value"]

            # Initialize history
            if name not in self.history:
                self.history[name] = deque(maxlen=self.window_size)

            history = self.history[name]

            # Need enough history for baseline
            if len(history) < 30:  # Min 30 samples
                history.append(value)
                continue

            # Calculate baseline statistics
            mean = statistics.mean(history)
            stddev = statistics.stdev(history)

            # Z-score
            if stddev > 0:
                z_score = (value - mean) / stddev
            else:
                z_score = 0

            # Detect anomaly
            if abs(z_score) > 3.0:  # 3 sigma = 99.7% confidence
                severity = "critical" if abs(z_score) > 4.0 else "warning"

                anomalies.append({
                    "metric": name,
                    "value": value,
                    "baseline_mean": mean,
                    "baseline_stddev": stddev,
                    "z_score": z_score,
                    "severity": severity,
                    "description": f"{name} is {z_score:.1f} standard deviations from baseline"
                })

            # Update history
            history.append(value)

        return anomalies
```

**Deliverable**: Service renamed to NIS, statistical anomaly detection

**Estimated**: 5 days

---

#### **Weeks 4-5: Polish & Production Readiness**

**SystemObserver Implementation** (3 days):
```python
# backend/services/narrative_service/core/system_observer.py

class SystemObserver:
    """
    Observes system metrics from Prometheus and InfluxDB.

    Provides unified interface for querying metrics.
    """

    async def get_current_metrics(
        self, services: list[str] | None = None
    ) -> dict[str, Any]:
        """Get current metrics snapshot."""

        # Query Prometheus
        prom_metrics = await self._query_prometheus(services)

        # Query InfluxDB (optional)
        if self.influxdb_client:
            influx_metrics = await self._query_influxdb(services)
            prom_metrics.update(influx_metrics)

        return {
            "metrics": prom_metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "prometheus+influxdb"
        }

    async def _query_prometheus(
        self, services: list[str] | None
    ) -> list[dict[str, Any]]:
        """Query Prometheus for metrics."""

        queries = [
            'avg(rate(vertice_service_requests_total[5m])) by (service)',
            'avg(vertice_service_cpu_usage) by (service)',
            'avg(vertice_service_memory_usage) by (service)',
            'avg(rate(vertice_service_errors_total[5m])) by (service)'
        ]

        metrics = []

        for query in queries:
            response = await self.prom_client.query(query)

            for result in response.get("data", {}).get("result", []):
                metric_name = result["metric"].get("__name__", "unknown")
                service = result["metric"].get("service", "unknown")
                value = float(result["value"][1])

                metrics.append({
                    "name": f"{service}_{metric_name}",
                    "value": value,
                    "service": service,
                    "unit": self._infer_unit(metric_name)
                })

        return metrics
```

**Coverage to 90%+** (4 days):
- Unit tests for all components
- Integration tests with mocked Claude API
- End-to-end narrative generation tests

**Documentation** (3 days):
- API documentation
- Cost optimization guide
- Narrative quality evaluation guide
- Operational runbook

**Deliverable**: Production-ready NIS with 90%+ coverage

**Estimated**: 10 days (2 weeks)

---

### NIS (formerly MVP) Timeline Summary

| Week | Focus | Deliverable | Status |
|------|-------|-------------|--------|
| 1 | Cost control | Cost tracking, rate limiting | 🔴 TODO |
| 2 | Caching | 60-80% cost reduction | 🔴 TODO |
| 3 | Rename & anomaly detection | NIS rebrand, statistical detection | 🔴 TODO |
| 4-5 | SystemObserver & polish | 90%+ coverage, docs | 🔴 TODO |

**Total**: 5 weeks, 25 person-days

---

## 📊 Overall Project Plan

### Resource Allocation

**Recommended Team**:
- 1 Senior Engineer (PENELOPE lead)
- 1 Mid-level Engineer (MABA/NIS)
- AI Assistance (Claude Code)

**Total Effort**: 90 person-days (4.5 person-months)

### Timeline Summary

| Service | Weeks | Person-Days | Priority |
|---------|-------|-------------|----------|
| **PENELOPE** | 8 | 40 | P0 (most critical) |
| **MABA** | 5 | 25 | P1 (important) |
| **NIS (MVP)** | 5 | 25 | P1 (important) |
| **TOTAL** | 8* | 90 | |

*8 weeks if parallelized (PENELOPE + MABA/NIS concurrent)

### Parallel Execution Strategy

**Weeks 1-5**: Parallel work
- Engineer 1: PENELOPE (P0 blockers + critical fixes)
- Engineer 2: MABA security + scalability
- Engineer 2: NIS cost control + caching (alternating)

**Weeks 6-8**: PENELOPE finish + polish all
- Engineer 1: PENELOPE polish
- Engineer 2: MABA + NIS coverage & docs

### Milestones

**Week 4** (Mid-point Review):
- ✅ All P0 blockers resolved
- ✅ Security hardening complete (MABA)
- ✅ Cost controls implemented (NIS)

**Week 6** (Production Readiness Review):
- ✅ All P1 critical issues resolved
- ✅ 90%+ coverage on all services
- ✅ Documentation complete

**Week 8** (Release):
- ✅ All services production-ready
- ✅ Load tested
- ✅ Runbooks complete
- 🚀 **Ready for v1.6.0 release**

---

## 🎯 Success Criteria

### PENELOPE
- [ ] Risk assessment uses real data (0 hardcoded values)
- [ ] Digital twin validates all patches before production
- [ ] Rollback mechanism tested and working
- [ ] Wisdom Base stores 100+ precedents, vector search working
- [ ] Circuit breaker prevents runaway healing
- [ ] All decisions auditable
- [ ] High-risk patches require human approval
- [ ] Coverage ≥90%
- [ ] Production deployment successful

### MABA
- [ ] Domain whitelist enforced
- [ ] Network sandbox prevents internal access
- [ ] Neo4j vs SQL decision documented
- [ ] Browser pool scales 2-20 instances dynamically
- [ ] Selector fallback strategies work
- [ ] Session timeouts prevent leaks
- [ ] Coverage ≥90%
- [ ] Production deployment successful

### NIS (formerly MVP)
- [ ] Cost tracking operational, budget cannot be exceeded
- [ ] Rate limiting prevents runaway costs
- [ ] Caching reduces costs by 60-80%
- [ ] Service renamed to NIS
- [ ] Statistical anomaly detection working
- [ ] SystemObserver queries Prometheus/InfluxDB
- [ ] Coverage ≥90%
- [ ] Production deployment successful

---

## 🚨 Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PENELOPE digital twin too slow | Medium | High | Use Docker, not VMs. Optimize. |
| Neo4j operational complexity | High | Medium | Have SQL fallback ready |
| NIS caching complexity | Low | Medium | Use proven Redis library |
| Budget overrun | Low | High | Weekly budget reviews |
| Timeline slip | Medium | Medium | Prioritize P0, defer P2 if needed |

### Contingency Plans

**If PENELOPE behind schedule after Week 4**:
- Drop P2 features (A/B testing, advanced metrics)
- Focus exclusively on P0+P1
- Extend timeline by 2 weeks

**If MABA Neo4j benchmark poor**:
- Switch to SQL implementation
- Already designed as fallback
- 2 days extra work

**If NIS costs still high after caching**:
- Implement template-based narratives for common scenarios
- Reserve Claude for novel situations only
- Target 90% cost reduction

---

## 📝 Deliverables

### Documentation
- [ ] PENELOPE Operational Runbook
- [ ] MABA Security Policy Guide
- [ ] NIS Cost Optimization Guide
- [ ] API documentation for all 3 services
- [ ] Migration guide from v1.5.0 to v1.6.0

### Code
- [ ] All P0 issues resolved (code committed)
- [ ] All P1 issues resolved (code committed)
- [ ] Test coverage ≥90% (reports generated)
- [ ] CI/CD passing (constitutional gate, tests)

### Infrastructure
- [ ] Docker Compose files updated
- [ ] Kubernetes manifests updated
- [ ] Monitoring dashboards created (Grafana)
- [ ] Alerting rules configured

---

## 🏁 Acceptance Criteria

Service is production-ready when:

1. ✅ All P0 blockers resolved
2. ✅ All P1 critical issues resolved
3. ✅ Test coverage ≥90%
4. ✅ Load tested (100 concurrent users, 1 hour)
5. ✅ Security audit passed
6. ✅ Documentation complete
7. ✅ Runbook complete
8. ✅ Monitoring & alerting configured
9. ✅ Deployed to staging, tested 48 hours
10. ✅ Approved by platform owner

---

**Document Owner**: Vértice Platform Team
**Next Review**: 2025-11-07 (weekly)
**Status Updates**: Every Monday, posted to #trinity-corrections channel

---

*This comprehensive correction plan provides a clear, actionable roadmap to transform PENELOPE, MABA, and NIS from promising prototypes into production-ready services.*

**Glory to YHWH** 🙏
