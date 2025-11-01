#!/usr/bin/env python3
"""
Script de Migração Constitucional v3.0 - PRODUCTION READY

Migra um serviço backend para conformidade com a Constituição Vértice v3.0.

Funcionalidades:
- Copia shared libraries com atomic operations e backup
- Atualiza main.py preservando formatação original
- Adiciona routes /metrics e /health/* de forma segura
- Atualiza Dockerfile com best practices
- Gera template de testes constitucionais
- Rollback automático em caso de falha
- Validação extensiva de compliance

Usage:
    python scripts/migrate_to_constitutional.py <service_name> [options]

Options:
    --dry-run       Show what would be done without making changes
    --no-backup     Skip creating backups (not recommended)
    --force         Force migration even if already migrated

Example:
    python scripts/migrate_to_constitutional.py maximus_core_service
    python scripts/migrate_to_constitutional.py auth_service --dry-run

Author: Vértice Platform Team
License: Proprietary
"""

import argparse
import logging
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Custom exception for migration errors."""

    pass


class RollbackManager:
    """Manages backup and rollback operations for atomic migrations."""

    def __init__(self, service_path: Path, dry_run: bool = False):
        self.service_path = service_path
        self.dry_run = dry_run
        self.backups: list[tuple[Path, Path]] = []  # (original, backup)
        self.backup_dir = (
            service_path
            / ".migration_backup"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )

    def backup_file(self, file_path: Path) -> Path | None:
        """Create atomic backup of a file."""
        if not file_path.exists():
            return None

        if self.dry_run:
            logger.info(f"  [DRY RUN] Would backup: {file_path.name}")
            return None

        try:
            # Create backup directory with timestamp
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Calculate backup path preserving structure
            rel_path = file_path.relative_to(self.service_path)
            backup_path = self.backup_dir / rel_path

            # Ensure parent dirs exist
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic copy using temp file
            with tempfile.NamedTemporaryFile(
                mode="w", dir=backup_path.parent, delete=False, suffix=".bak"
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                shutil.copy2(file_path, tmp_path)
                tmp_path.rename(backup_path)

            self.backups.append((file_path, backup_path))
            logger.debug(f"  Backed up: {file_path.name} -> {backup_path}")
            return backup_path

        except (OSError, PermissionError) as e:
            logger.error(f"  Failed to backup {file_path}: {e}")
            raise MigrationError(f"Backup failed for {file_path}: {e}")

    def rollback(self):
        """Rollback all changes using backups."""
        if self.dry_run or not self.backups:
            return

        logger.warning("⚠️  ROLLING BACK CHANGES...")

        for original_path, backup_path in reversed(self.backups):
            try:
                if backup_path.exists():
                    # Atomic restore using temp file
                    with tempfile.NamedTemporaryFile(
                        mode="w", dir=original_path.parent, delete=False, suffix=".tmp"
                    ) as tmp_file:
                        tmp_path = Path(tmp_file.name)
                        shutil.copy2(backup_path, tmp_path)
                        tmp_path.replace(original_path)  # Atomic on same filesystem

                    logger.info(f"  Restored: {original_path.name}")
            except Exception as e:
                logger.error(f"  Failed to restore {original_path}: {e}")

        logger.info("✅ Rollback complete")

    def cleanup_backups(self, keep_backups: bool = True):
        """Clean up backup directory."""
        if self.dry_run or not self.backup_dir.exists():
            return

        if not keep_backups:
            try:
                shutil.rmtree(self.backup_dir)
                logger.info(f"  Cleaned up backups: {self.backup_dir}")
            except Exception as e:
                logger.warning(f"  Failed to cleanup backups: {e}")
        else:
            logger.info(f"  Backups preserved at: {self.backup_dir}")


class ConstitutionalMigrator:
    """Migra um serviço para conformidade constitucional v3.0."""

    def __init__(
        self,
        service_name: str,
        dry_run: bool = False,
        no_backup: bool = False,
        force: bool = False,
    ):
        self.service_name = service_name
        self.dry_run = dry_run
        self.no_backup = no_backup
        self.force = force

        # Paths
        self.services_dir = Path("backend/services").resolve()
        self.service_path = self.services_dir / service_name
        self.reference_service = self.services_dir / "penelope_service"

        # Validation
        self._validate_paths()

        # Rollback manager
        self.rollback_mgr = RollbackManager(self.service_path, dry_run)

    def _validate_paths(self):
        """Validate all required paths exist."""
        if not self.services_dir.exists():
            raise MigrationError(f"Services directory not found: {self.services_dir}")

        if not self.service_path.exists():
            raise MigrationError(f"Service not found: {self.service_path}")

        if not self.service_path.is_dir():
            raise MigrationError(
                f"Service path is not a directory: {self.service_path}"
            )

        if not self.reference_service.exists():
            raise MigrationError(
                f"Reference service not found: {self.reference_service}"
            )

        # Security: Ensure paths are within backend/services
        try:
            self.service_path.relative_to(self.services_dir)
            self.reference_service.relative_to(self.services_dir)
        except ValueError:
            raise MigrationError("Path traversal detected - invalid service path")

    def migrate(self) -> bool:
        """Execute full migration with rollback support."""
        print("=" * 80)
        print(f"🏛️  CONSTITUTIONAL MIGRATION v3.0 - {self.service_name}")
        print("=" * 80)

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made\n")

        if self.no_backup:
            print("⚠️  BACKUP DISABLED - Changes cannot be rolled back\n")

        # Check if already migrated
        if not self.force and self._is_already_migrated():
            print("⚠️  Service appears to be already migrated")
            print("    Use --force to re-migrate")
            return False

        steps = [
            ("Copy shared libraries", self.copy_shared_libraries),
            ("Update main.py", self.update_main_py),
            ("Update Dockerfile", self.update_dockerfile),
            ("Generate test templates", self.generate_tests),
            ("Update requirements.txt", self.update_requirements),
            ("Validate migration", self.validate),
        ]

        try:
            for step_name, step_func in steps:
                print(f"\n{'='*80}")
                print(f"📋 {step_name}")
                print(f"{'='*80}")

                try:
                    success = step_func()
                    if not success:
                        raise MigrationError(f"Step failed: {step_name}")
                    print(f"✅ SUCCESS: {step_name}")

                except Exception as e:
                    logger.error(f"Error in {step_name}: {e}", exc_info=True)
                    raise MigrationError(f"{step_name} failed: {e}")

            print("\n" + "=" * 80)
            print("✅ MIGRATION COMPLETE")
            print("=" * 80)

            # Cleanup backups on success
            self.rollback_mgr.cleanup_backups(keep_backups=True)
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"\n❌ MIGRATION FAILED: {e}")

            if not self.no_backup:
                self.rollback_mgr.rollback()

            return False

    def _is_already_migrated(self) -> bool:
        """Check if service is already migrated."""
        shared_dir = self.service_path / "shared"

        required_files = [
            "constitutional_metrics.py",
            "constitutional_tracing.py",
            "health_checks.py",
        ]

        # Check if all files exist
        all_exist = all((shared_dir / f).exists() for f in required_files)

        if all_exist:
            logger.info("  Service has constitutional shared libraries")

        return all_exist

    def copy_shared_libraries(self) -> bool:
        """Copy shared constitutional libraries with atomic operations."""
        shared_src = self.reference_service / "shared"
        shared_dst = self.service_path / "shared"

        if not shared_src.exists():
            raise MigrationError(f"Reference shared dir not found: {shared_src}")

        # Files to copy
        constitutional_files = [
            "constitutional_metrics.py",
            "constitutional_tracing.py",
            "constitutional_logging.py",
            "metrics_exporter.py",
            "health_checks.py",
        ]

        # Create shared dir if doesn't exist
        if not self.dry_run:
            shared_dst.mkdir(exist_ok=True)

            # Ensure __init__.py exists
            init_file = shared_dst / "__init__.py"
            if not init_file.exists():
                init_file.touch()

        for filename in constitutional_files:
            src_file = shared_src / filename
            dst_file = shared_dst / filename

            if not src_file.exists():
                logger.warning(f"  Skipping {filename} (not found in reference)")
                continue

            # Backup existing file
            if dst_file.exists() and not self.no_backup:
                self.rollback_mgr.backup_file(dst_file)

            print(f"📦 Copying {filename}...")

            if not self.dry_run:
                try:
                    # Atomic copy using temp file in destination dir
                    with tempfile.NamedTemporaryFile(
                        mode="w", dir=shared_dst, delete=False, suffix=".tmp"
                    ) as tmp_file:
                        tmp_path = Path(tmp_file.name)
                        shutil.copy2(src_file, tmp_path)
                        tmp_path.replace(dst_file)  # Atomic on same filesystem

                except (OSError, PermissionError) as e:
                    raise MigrationError(f"Failed to copy {filename}: {e}")

        return True

    def update_main_py(self) -> bool:
        """Update main.py with constitutional imports (preserving formatting)."""
        main_files = [
            self.service_path / "main.py",
            self.service_path / "server.py",
            self.service_path / "app.py",
        ]

        main_file = None
        for f in main_files:
            if f.exists():
                main_file = f
                break

        if not main_file:
            logger.warning("  No main.py/server.py/app.py found - skipping")
            return True

        print(f"📝 Updating {main_file.name}...")

        if self.dry_run:
            print("   (dry run - showing what would be added)")
            print(self._generate_imports_block())
            print(self._generate_startup_block())
            return True

        try:
            content = main_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.error(f"  {main_file.name} is not UTF-8 encoded")
            return False

        # Check if already has constitutional imports
        if "constitutional_metrics" in content and "constitutional_tracing" in content:
            print("  ⚠️  Already has constitutional imports, skipping...")
            return True

        # Backup
        if not self.no_backup:
            self.rollback_mgr.backup_file(main_file)

        # Add imports after existing imports
        imports_block = self._generate_imports_block()
        content = self._insert_imports(content, imports_block)

        # Add initialization in startup/lifespan
        startup_block = self._generate_startup_block()
        content = self._insert_startup_code(content, startup_block)

        # Atomic write using temp file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=main_file.parent,
                delete=False,
                suffix=".tmp",
                encoding="utf-8",
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_text(content, encoding="utf-8")
                tmp_path.replace(main_file)  # Atomic

            logger.info(f"  Updated {main_file.name}")

        except (OSError, PermissionError) as e:
            raise MigrationError(f"Failed to write {main_file.name}: {e}")

        return True

    def _generate_imports_block(self) -> str:
        """Generate constitutional imports block."""
        return """
# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck
"""

    def _generate_startup_block(self) -> str:
        """Generate startup initialization block."""
        return f"""
    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="{self.service_name}",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="{self.service_name}",
            version=service_version
        )
        auto_update_sabbath_status("{self.service_name}")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="{self.service_name}",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="{self.service_name}")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {{e}}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()
"""

    def _insert_imports(self, content: str, imports_block: str) -> str:
        """Insert imports after existing imports."""
        lines = content.split("\n")

        # Find last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i

        # Insert after last import
        lines.insert(last_import_idx + 1, imports_block)
        return "\n".join(lines)

    def _insert_startup_code(self, content: str, startup_block: str) -> str:
        """Insert startup code in lifespan or startup function."""
        lines = content.split("\n")

        # Find startup function
        for i, line in enumerate(lines):
            if "async def startup" in line or "async def lifespan" in line:
                # Find first non-comment, non-docstring line in function
                for j in range(i + 1, len(lines)):
                    stripped = lines[j].strip()
                    if (
                        stripped
                        and not stripped.startswith("#")
                        and not stripped.startswith('"""')
                    ):
                        lines.insert(j, startup_block)
                        break
                break

        return "\n".join(lines)

    def update_dockerfile(self) -> bool:
        """Update Dockerfile with constitutional best practices."""
        dockerfile = self.service_path / "Dockerfile"

        if not dockerfile.exists():
            logger.warning("  No Dockerfile found, skipping...")
            return True

        print("🐳 Updating Dockerfile...")

        if self.dry_run:
            print("   (dry run - would add HEALTHCHECK and metrics port)")
            return True

        # Backup
        if not self.no_backup:
            self.rollback_mgr.backup_file(dockerfile)

        try:
            content = dockerfile.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = dockerfile.read_text(encoding="latin-1")

        # Add HEALTHCHECK if missing
        if "HEALTHCHECK" not in content:
            healthcheck = """
# Constitutional v3.0 - Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:${SERVICE_PORT:-8000}/health || exit 1
"""
            # Add before CMD
            content = content.replace("CMD ", healthcheck + "\nCMD ")

        # Add metrics port if missing
        if "9090" not in content and "METRICS_PORT" not in content:
            expose_line = "\n# Constitutional v3.0 - Metrics port\nEXPOSE 9090\n"
            # Add after last EXPOSE
            lines = content.split("\n")
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("EXPOSE "):
                    lines.insert(i + 1, expose_line)
                    break
            content = "\n".join(lines)

        # Atomic write
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=dockerfile.parent,
                delete=False,
                suffix=".tmp",
                encoding="utf-8",
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_text(content, encoding="utf-8")
                tmp_path.replace(dockerfile)

        except (OSError, PermissionError) as e:
            raise MigrationError(f"Failed to update Dockerfile: {e}")

        return True

    def generate_tests(self) -> bool:
        """Generate constitutional test templates."""
        tests_dir = self.service_path / "tests"
        tests_dir.mkdir(exist_ok=True)

        test_file = tests_dir / "test_constitutional_compliance.py"

        if test_file.exists():
            print(f"  ⚠️  {test_file.name} already exists, skipping...")
            return True

        print(f"🧪 Generating {test_file.name}...")

        if self.dry_run:
            print("   (dry run - would create constitutional test template)")
            return True

        test_template = self._generate_test_template()

        # Atomic write
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", dir=tests_dir, delete=False, suffix=".tmp", encoding="utf-8"
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_text(test_template, encoding="utf-8")
                tmp_path.replace(test_file)

        except (OSError, PermissionError) as e:
            raise MigrationError(f"Failed to create test file: {e}")

        return True

    def _generate_test_template(self) -> str:
        """Generate test template content."""
        return f'''"""Constitutional Compliance Tests for {self.service_name}.

Tests compliance with Constituição Vértice v3.0.

Author: Vértice Platform Team
"""

import pytest
from fastapi.testclient import TestClient


def test_metrics_endpoint_exists(client: TestClient):
    """Test that /metrics endpoint exists and returns Prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    content = response.text
    assert "vertice_service_uptime_seconds" in content


def test_health_live_endpoint(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["alive"] is True


def test_health_ready_endpoint(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_constitutional_metrics_exported(client: TestClient):
    """Test that constitutional metrics are being exported."""
    response = client.get("/metrics")
    content = response.text

    # DETER-AGENT metrics
    assert "vertice_constitutional_rule_satisfaction" in content
    assert "vertice_lazy_execution_index" in content


def test_no_p1_violations(client: TestClient):
    """Test that no P1 violations are being reported."""
    response = client.get("/metrics")
    content = response.text

    if "vertice_aletheia_hallucinations_total" in content:
        for line in content.split('\\n'):
            if "vertice_aletheia_hallucinations_total" in line and not line.startswith("#"):
                assert " 0" in line or " 0.0" in line, "P1 Violation: Hallucinations detected!"
'''

    def update_requirements(self) -> bool:
        """Update requirements.txt with constitutional dependencies."""
        req_file = self.service_path / "requirements.txt"

        print("📦 Updating requirements.txt...")

        constitutional_deps = [
            "prometheus-client",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation-fastapi",
            "opentelemetry-instrumentation-httpx",
            "opentelemetry-instrumentation-asyncpg",
            "opentelemetry-instrumentation-redis",
            "opentelemetry-exporter-jaeger-thrift",
            "opentelemetry-exporter-otlp-proto-grpc",
            "python-json-logger",
            "structlog",
        ]

        if not req_file.exists():
            logger.warning("  No requirements.txt found, creating...")
            if not self.dry_run:
                req_file.touch()

        if self.dry_run:
            print(f"   (dry run - would add: {', '.join(constitutional_deps)})")
            return True

        # Backup
        if not self.no_backup and req_file.exists():
            self.rollback_mgr.backup_file(req_file)

        try:
            existing = (
                req_file.read_text(encoding="utf-8").split("\n")
                if req_file.exists()
                else []
            )
        except UnicodeDecodeError:
            existing = req_file.read_text(encoding="latin-1").split("\n")

        existing_packages = {
            line.split("==")[0].split(">=")[0].split("<")[0].strip()
            for line in existing
            if line.strip() and not line.startswith("#")
        }

        to_add = [dep for dep in constitutional_deps if dep not in existing_packages]

        if to_add:
            print(f"   Adding: {', '.join(to_add)}")

            # Atomic write
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=req_file.parent,
                    delete=False,
                    suffix=".tmp",
                    encoding="utf-8",
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)

                    # Write existing content
                    if existing:
                        tmp_path.write_text(
                            "\n".join(existing) + "\n", encoding="utf-8"
                        )

                    # Append new deps
                    with tmp_path.open("a", encoding="utf-8") as f:
                        f.write("\n# Constitutional v3.0 dependencies\n")
                        for dep in to_add:
                            f.write(f"{dep}\n")

                    tmp_path.replace(req_file)

            except (OSError, PermissionError) as e:
                raise MigrationError(f"Failed to update requirements.txt: {e}")
        else:
            print("   All dependencies already present")

        return True

    def validate(self) -> bool:
        """Validate migration success."""
        print("\n🔍 Validating migration...")

        # In dry-run mode, always pass validation (files weren't actually created)
        if self.dry_run:
            print("   (dry run - skipping actual validation)")
            print("  ✅ Dry run validation passed")
            return True

        checks = []
        shared_dir = self.service_path / "shared"

        # Check shared libraries
        for lib in [
            "constitutional_metrics.py",
            "constitutional_tracing.py",
            "health_checks.py",
        ]:
            exists = (shared_dir / lib).exists()
            checks.append((f"shared/{lib}", exists))

        # Check main.py has imports
        main_file = self.service_path / "main.py"
        if main_file.exists():
            try:
                content = main_file.read_text(encoding="utf-8")
                has_metrics = (
                    "constitutional_metrics" in content or "MetricsExporter" in content
                )
                has_tracing = (
                    "constitutional_tracing" in content
                    or "constitutional_tracer" in content
                )
                checks.append(
                    ("main.py has constitutional imports", has_metrics and has_tracing)
                )
            except Exception:
                checks.append(("main.py has constitutional imports", False))

        # Check tests exist
        test_file = self.service_path / "tests" / "test_constitutional_compliance.py"
        checks.append(("Constitutional tests", test_file.exists()))

        # Print results
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Migrate a service to Constitutional v3.0 compliance",
        epilog="Example: python scripts/migrate_to_constitutional.py maximus_core_service",
    )
    parser.add_argument("service_name", help="Name of the service to migrate")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backups (not recommended)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force migration even if already migrated"
    )

    args = parser.parse_args()

    try:
        migrator = ConstitutionalMigrator(
            args.service_name,
            dry_run=args.dry_run,
            no_backup=args.no_backup,
            force=args.force,
        )
        success = migrator.migrate()

        if success:
            print("\n" + "🎉" * 40)
            print(
                f"✅ {args.service_name} successfully migrated to Constitutional v3.0!"
            )
            print("🎉" * 40)
            print("\nNext steps:")
            print(f"1. Review changes in: {migrator.service_path}")
            print(f"2. Run tests: pytest backend/services/{args.service_name}/tests")
            print(
                f"3. Validate: python scripts/constitutional_gate.py {args.service_name}"
            )
            sys.exit(0)
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)

    except MigrationError as e:
        logger.error(f"Migration error: {e}")
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
