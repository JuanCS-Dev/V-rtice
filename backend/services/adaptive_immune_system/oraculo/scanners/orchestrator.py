"""
Dependency Orchestrator - Coordinates multi-ecosystem dependency scanning.

Manages parallel scanning across Python, JavaScript, Go, and Docker ecosystems,
deduplication, and database persistence.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from ...database import DatabaseClient, get_db_client
from ...database.models import Dependency
from ...models.dependency import DependencyCreate
from .python_scanner import PythonScanner, PythonPackage
from .javascript_scanner import JavaScriptScanner, JavaScriptPackage
from .go_scanner import GoScanner, GoPackage
from .docker_scanner import DockerScanner, DockerPackage

logger = logging.getLogger(__name__)


class DependencyOrchestrator:
    """
    Orchestrates dependency scanning across multiple ecosystems.

    Features:
    - Parallel scanning of Python, JavaScript, Go, Docker
    - Automatic ecosystem detection
    - Deduplication by (project, name, version, ecosystem)
    - Database persistence
    - Scan statistics tracking
    """

    def __init__(
        self,
        db_client: DatabaseClient,
        project_name: str,
        project_path: Optional[Path] = None,
    ):
        """
        Initialize dependency orchestrator.

        Args:
            db_client: Database client instance
            project_name: Project identifier (e.g., "backend-api")
            project_path: Path to project root (default: current directory)
        """
        self.db_client = db_client
        self.project_name = project_name
        self.project_path = Path(project_path) if project_path else Path.cwd()

        self.stats = {
            "python": {"total": 0, "new": 0, "updated": 0, "errors": 0},
            "javascript": {"total": 0, "new": 0, "updated": 0, "errors": 0},
            "go": {"total": 0, "new": 0, "updated": 0, "errors": 0},
            "docker": {"total": 0, "new": 0, "updated": 0, "errors": 0},
        }

        logger.info(
            f"DependencyOrchestrator initialized: "
            f"project={self.project_name}, path={self.project_path}"
        )

    async def scan_all_ecosystems(
        self,
        include_python: bool = True,
        include_javascript: bool = True,
        include_go: bool = True,
        docker_images: Optional[List[str]] = None,
    ) -> Dict[str, dict]:
        """
        Scan dependencies across all ecosystems.

        Args:
            include_python: Scan Python dependencies
            include_javascript: Scan JavaScript dependencies
            include_go: Scan Go dependencies
            docker_images: List of Docker image names to scan

        Returns:
            Dictionary with stats per ecosystem
        """
        start_time = datetime.utcnow()

        logger.info(f"🚀 Starting dependency scan for project: {self.project_name}")

        # Reset stats
        for ecosystem in self.stats:
            self.stats[ecosystem] = {"total": 0, "new": 0, "updated": 0, "errors": 0}

        # Create tasks for each ecosystem
        tasks = []

        if include_python and self._detect_python():
            tasks.append(self._scan_python())

        if include_javascript and self._detect_javascript():
            tasks.append(self._scan_javascript())

        if include_go and self._detect_go():
            tasks.append(self._scan_go())

        if docker_images:
            for image_name in docker_images:
                tasks.append(self._scan_docker(image_name))

        # Run tasks in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.warning("No ecosystems detected or enabled for scanning")

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log summary
        total_new = sum(s["new"] for s in self.stats.values())
        total_updated = sum(s["updated"] for s in self.stats.values())
        total_errors = sum(s["errors"] for s in self.stats.values())

        logger.info(
            f"✅ Dependency scan complete: "
            f"duration={duration:.1f}s, new={total_new}, "
            f"updated={total_updated}, errors={total_errors}"
        )

        return {
            "stats": self.stats,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _scan_python(self) -> None:
        """Scan Python dependencies."""
        ecosystem = "python"
        logger.info(f"📥 Starting Python dependency scan")

        try:
            scanner = PythonScanner(self.project_path)
            packages = await asyncio.to_thread(scanner.scan)

            self.stats[ecosystem]["total"] = len(packages)

            with self.db_client.get_session() as session:
                for pkg in packages:
                    try:
                        dep_data = DependencyCreate(
                            project=self.project_name,
                            name=pkg.name,
                            version=pkg.version,
                            ecosystem="pypi",
                            is_direct=pkg.is_direct,
                            parent_packages=pkg.parent_packages,
                            metadata={
                                "location": pkg.location,
                            },
                        )

                        is_new = self._upsert_dependency(session, dep_data)

                        if is_new:
                            self.stats[ecosystem]["new"] += 1
                        else:
                            self.stats[ecosystem]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing Python package {pkg.name}: {e}")
                        self.stats[ecosystem]["errors"] += 1

            logger.info(
                f"✅ Python scan complete: "
                f"total={self.stats[ecosystem]['total']}, "
                f"new={self.stats[ecosystem]['new']}"
            )

        except Exception as e:
            logger.error(f"Python dependency scan failed: {e}")
            self.stats[ecosystem]["errors"] += 1

    async def _scan_javascript(self) -> None:
        """Scan JavaScript/npm dependencies."""
        ecosystem = "javascript"
        logger.info(f"📥 Starting JavaScript dependency scan")

        try:
            scanner = JavaScriptScanner(self.project_path)
            packages = await asyncio.to_thread(scanner.scan)

            self.stats[ecosystem]["total"] = len(packages)

            with self.db_client.get_session() as session:
                for pkg in packages:
                    try:
                        dep_data = DependencyCreate(
                            project=self.project_name,
                            name=pkg.name,
                            version=pkg.version,
                            ecosystem="npm",
                            is_direct=pkg.is_direct,
                            parent_packages=pkg.parent_packages,
                            metadata={
                                "is_dev": pkg.is_dev,
                            },
                        )

                        is_new = self._upsert_dependency(session, dep_data)

                        if is_new:
                            self.stats[ecosystem]["new"] += 1
                        else:
                            self.stats[ecosystem]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing JavaScript package {pkg.name}: {e}")
                        self.stats[ecosystem]["errors"] += 1

            logger.info(
                f"✅ JavaScript scan complete: "
                f"total={self.stats[ecosystem]['total']}, "
                f"new={self.stats[ecosystem]['new']}"
            )

        except Exception as e:
            logger.error(f"JavaScript dependency scan failed: {e}")
            self.stats[ecosystem]["errors"] += 1

    async def _scan_go(self) -> None:
        """Scan Go module dependencies."""
        ecosystem = "go"
        logger.info(f"📥 Starting Go dependency scan")

        try:
            scanner = GoScanner(self.project_path)
            packages = await asyncio.to_thread(scanner.scan)

            self.stats[ecosystem]["total"] = len(packages)

            with self.db_client.get_session() as session:
                for pkg in packages:
                    try:
                        dep_data = DependencyCreate(
                            project=self.project_name,
                            name=pkg.name,
                            version=pkg.version,
                            ecosystem="go",
                            is_direct=pkg.is_direct,
                            parent_packages=pkg.parent_packages,
                            metadata={
                                "replace": pkg.replace,
                            },
                        )

                        is_new = self._upsert_dependency(session, dep_data)

                        if is_new:
                            self.stats[ecosystem]["new"] += 1
                        else:
                            self.stats[ecosystem]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing Go package {pkg.name}: {e}")
                        self.stats[ecosystem]["errors"] += 1

            logger.info(
                f"✅ Go scan complete: "
                f"total={self.stats[ecosystem]['total']}, "
                f"new={self.stats[ecosystem]['new']}"
            )

        except Exception as e:
            logger.error(f"Go dependency scan failed: {e}")
            self.stats[ecosystem]["errors"] += 1

    async def _scan_docker(self, image_name: str) -> None:
        """Scan Docker image dependencies."""
        ecosystem = "docker"
        logger.info(f"📥 Starting Docker scan for: {image_name}")

        try:
            scanner = DockerScanner(image_name)
            image_info, packages = await asyncio.to_thread(scanner.scan)

            self.stats[ecosystem]["total"] += len(packages)

            with self.db_client.get_session() as session:
                for pkg in packages:
                    try:
                        dep_data = DependencyCreate(
                            project=f"{self.project_name}:docker:{image_name}",
                            name=pkg.name,
                            version=pkg.version,
                            ecosystem=pkg.ecosystem,
                            is_direct=False,  # Docker packages are all transitive
                            parent_packages=[],
                            metadata={
                                "image_name": image_name,
                                "image_id": image_info.image_id,
                                "layer_id": pkg.layer_id,
                                "source": pkg.source,
                            },
                        )

                        is_new = self._upsert_dependency(session, dep_data)

                        if is_new:
                            self.stats[ecosystem]["new"] += 1
                        else:
                            self.stats[ecosystem]["updated"] += 1

                    except Exception as e:
                        logger.error(f"Error processing Docker package {pkg.name}: {e}")
                        self.stats[ecosystem]["errors"] += 1

            logger.info(
                f"✅ Docker scan complete for {image_name}: "
                f"total={len(packages)}, "
                f"new={self.stats[ecosystem]['new']}"
            )

        except Exception as e:
            logger.error(f"Docker scan failed for {image_name}: {e}")
            self.stats[ecosystem]["errors"] += 1

    def _upsert_dependency(self, session: Session, dep_data: DependencyCreate) -> bool:
        """
        Insert or update dependency in database.

        Args:
            session: Database session
            dep_data: DependencyCreate data

        Returns:
            True if new dependency created, False if updated
        """
        # Check if dependency exists
        existing = (
            session.query(Dependency)
            .filter(
                Dependency.project == dep_data.project,
                Dependency.name == dep_data.name,
                Dependency.version == dep_data.version,
                Dependency.ecosystem == dep_data.ecosystem,
            )
            .first()
        )

        if existing:
            # Update existing dependency
            for key, value in dep_data.model_dump().items():
                setattr(existing, key, value)
            existing.last_seen_at = datetime.utcnow()
            session.commit()
            return False
        else:
            # Create new dependency
            dependency = Dependency(**dep_data.model_dump())
            session.add(dependency)
            session.commit()
            return True

    def _detect_python(self) -> bool:
        """Detect if project has Python dependencies."""
        python_files = [
            self.project_path / "requirements.txt",
            self.project_path / "pyproject.toml",
            self.project_path / "poetry.lock",
            self.project_path / "setup.py",
            self.project_path / "Pipfile",
        ]
        return any(f.exists() for f in python_files)

    def _detect_javascript(self) -> bool:
        """Detect if project has JavaScript dependencies."""
        js_files = [
            self.project_path / "package.json",
            self.project_path / "package-lock.json",
            self.project_path / "yarn.lock",
            self.project_path / "pnpm-lock.yaml",
        ]
        return any(f.exists() for f in js_files)

    def _detect_go(self) -> bool:
        """Detect if project has Go dependencies."""
        go_files = [
            self.project_path / "go.mod",
            self.project_path / "go.sum",
        ]
        return any(f.exists() for f in go_files)

    def get_stats(self) -> Dict[str, dict]:
        """Get current scan statistics."""
        return self.stats.copy()

    def get_dependency_count(self) -> Dict[str, int]:
        """
        Get dependency counts per ecosystem from database.

        Returns:
            Dictionary mapping ecosystem to count
        """
        with self.db_client.get_session() as session:
            results = (
                session.query(
                    Dependency.ecosystem,
                    session.query(Dependency)
                    .filter(Dependency.project == self.project_name)
                    .count(),
                )
                .filter(Dependency.project == self.project_name)
                .group_by(Dependency.ecosystem)
                .all()
            )

            return {ecosystem: count for ecosystem, count in results}

    def clear_stale_dependencies(self, days: int = 30) -> int:
        """
        Remove dependencies not seen in N days.

        Args:
            days: Number of days threshold

        Returns:
            Number of dependencies removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.db_client.get_session() as session:
            deleted = (
                session.query(Dependency)
                .filter(
                    Dependency.project == self.project_name,
                    Dependency.last_seen_at < cutoff_date,
                )
                .delete()
            )
            session.commit()

            logger.info(f"Removed {deleted} stale dependencies older than {days} days")
            return deleted


from datetime import timedelta
