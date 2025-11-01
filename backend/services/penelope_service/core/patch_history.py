"""Patch History - Git-based Patch Management with Rollback.

Armazena histórico completo de patches aplicados usando git commits.
Permite rollback automático quando patches causam problemas.

Fundamento Bíblico: Eclesiastes 3:6
"Tempo de buscar, e tempo de perder; tempo de guardar, e tempo de deitar fora."

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class PatchHistory:
    """Git-based patch history with rollback support.

    Stores every patch as a git commit in dedicated branch.
    Enables safe rollback of failed patches.

    Architecture:
    - Each service has its own git repository in /var/lib/penelope/history
    - Patches stored in 'penelope-patches' branch
    - Each patch is a commit with metadata
    - Rollbacks create reverse patches

    Biblical Principle: Learning from history (Deuteronomy 32:7)
    """

    def __init__(self, history_path: Path | None = None):
        """Initialize Patch History.

        Args:
            history_path: Base path for history storage (default: /var/lib/penelope/history)
        """
        self.history_path = history_path or Path("/var/lib/penelope/history")
        self.history_path.mkdir(parents=True, exist_ok=True)

    async def save_patch(
        self,
        service: str,
        patch: str,
        anomaly_id: str,
        metadata: dict[str, Any],
    ) -> str:
        """Save patch to git-based history.

        Creates git commit in service's patch history branch.

        Args:
            service: Service name (e.g., "penelope_service")
            patch: Git-style patch content
            anomaly_id: Anomaly identifier
            metadata: Additional metadata (applied_at, applied_by, etc.)

        Returns:
            patch_id: Git commit hash (SHA-1)

        Raises:
            subprocess.CalledProcessError: If git commands fail
        """
        try:
            service_repo = self.history_path / service

            # Initialize git repo if doesn't exist
            if not (service_repo / ".git").exists():
                logger.info(f"Initializing patch history repo for {service}")
                service_repo.mkdir(parents=True, exist_ok=True)

                subprocess.run(
                    ["git", "init"],
                    cwd=str(service_repo),
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    ["git", "checkout", "-b", "penelope-patches"],
                    cwd=str(service_repo),
                    check=True,
                    capture_output=True,
                )

                # Initial commit
                readme = service_repo / "README.md"
                readme.write_text(
                    f"# Patch History for {service}\n\n"
                    f"Managed by PENELOPE Self-Healing Service.\n"
                    f"Each commit represents a patch application.\n"
                )
                subprocess.run(
                    ["git", "add", "README.md"],
                    cwd=str(service_repo),
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit"],
                    cwd=str(service_repo),
                    check=True,
                    capture_output=True,
                )

            # Save patch file
            patch_file = service_repo / f"patch_{anomaly_id}.patch"
            patch_file.write_text(patch)

            # Save metadata
            metadata_enhanced = {
                **metadata,
                "anomaly_id": anomaly_id,
                "service": service,
                "saved_at": datetime.utcnow().isoformat(),
            }
            metadata_file = service_repo / f"metadata_{anomaly_id}.json"
            metadata_file.write_text(json.dumps(metadata_enhanced, indent=2))

            # Git add
            subprocess.run(
                ["git", "add", "."],
                cwd=str(service_repo),
                check=True,
                capture_output=True,
            )

            # Git commit
            commit_message = (
                f"Patch for anomaly {anomaly_id}\n\n"
                f"Applied at: {metadata.get('applied_at', 'unknown')}\n"
                f"Applied by: {metadata.get('applied_by', 'penelope')}\n"
                f"Anomaly type: {metadata.get('anomaly_type', 'unknown')}\n"
            )

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=str(service_repo),
                check=True,
                capture_output=True,
            )

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            patch_id = result.stdout.strip()

            logger.info(
                f"✅ Saved patch {patch_id[:8]} for {service} (anomaly: {anomaly_id})"
            )
            return patch_id

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to save patch: {e.stderr.decode() if e.stderr else str(e)}"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to save patch for {service}: {e}")
            raise

    async def rollback_patch(self, service: str, patch_id: str) -> bool:
        """Rollback a specific patch by creating reverse patch.

        Args:
            service: Service name
            patch_id: Git commit hash to rollback

        Returns:
            success: True if rollback succeeded

        Raises:
            FileNotFoundError: If service repo doesn't exist
        """
        service_repo = self.history_path / service

        if not service_repo.exists():
            raise FileNotFoundError(f"No patch history for service {service}")

        try:
            # Get the patch commit
            result = subprocess.run(
                ["git", "show", patch_id],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            commit_details = result.stdout

            # Extract patch content (find the .patch file in the commit)
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", patch_id],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
                check=True,
            )

            files = result.stdout.strip().split("\n")
            patch_file = next((f for f in files if f.endswith(".patch")), None)

            if not patch_file:
                logger.error(f"No .patch file found in commit {patch_id}")
                return False

            # Get original patch content
            result = subprocess.run(
                ["git", "show", f"{patch_id}:{patch_file}"],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
                check=True,
            )
            original_patch = result.stdout

            # Create reverse patch by applying to production service
            service_path = Path(f"/home/juan/vertice-dev/backend/services/{service}")

            # Apply reverse patch using patch -R
            result = subprocess.run(
                ["patch", "-R", "-p1"],
                input=original_patch.encode(),
                cwd=str(service_path),
                capture_output=True,
            )

            if result.returncode != 0:
                logger.error(
                    f"Reverse patch failed: {result.stderr.decode(errors='ignore')}"
                )
                return False

            # Record rollback in history
            rollback_metadata = {
                "patch_id": patch_id,
                "rolled_back_at": datetime.utcnow().isoformat(),
                "reason": "manual_rollback",
                "rollback_successful": True,
            }

            rollback_file = service_repo / f"rollback_{patch_id[:8]}.json"
            rollback_file.write_text(json.dumps(rollback_metadata, indent=2))

            subprocess.run(
                ["git", "add", "."],
                cwd=str(service_repo),
                check=True,
                capture_output=True,
            )

            subprocess.run(
                ["git", "commit", "-m", f"Rollback patch {patch_id[:8]}"],
                cwd=str(service_repo),
                check=True,
                capture_output=True,
            )

            logger.info(f"✅ Rolled back patch {patch_id[:8]} for {service}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Rollback failed: {e.stderr.decode() if e.stderr else str(e)}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to rollback patch {patch_id}: {e}")
            return False

    async def get_patch_status(self, service: str, patch_id: str) -> dict[str, Any]:
        """Get status of a specific patch.

        Args:
            service: Service name
            patch_id: Git commit hash

        Returns:
            status: Dict with status info
        """
        service_repo = self.history_path / service

        if not service_repo.exists():
            return {"status": "unknown", "error": "Service repo not found"}

        try:
            # Check if patch commit exists
            result = subprocess.run(
                ["git", "cat-file", "-t", patch_id],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {"status": "not_found", "patch_id": patch_id}

            # Check if rolled back
            rollback_file = service_repo / f"rollback_{patch_id[:8]}.json"
            if rollback_file.exists():
                rollback_data = json.loads(rollback_file.read_text())
                return {
                    "status": "rolled_back",
                    "patch_id": patch_id,
                    "rollback_info": rollback_data,
                }

            # Get commit details
            result = subprocess.run(
                [
                    "git",
                    "show",
                    "--format=%H%n%an%n%ae%n%at%n%s",
                    "--no-patch",
                    patch_id,
                ],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                return {
                    "status": "applied",
                    "patch_id": patch_id,
                    "commit_hash": lines[0] if len(lines) > 0 else patch_id,
                    "author": lines[1] if len(lines) > 1 else "unknown",
                    "email": lines[2] if len(lines) > 2 else "unknown",
                    "timestamp": int(lines[3]) if len(lines) > 3 else 0,
                    "message": lines[4] if len(lines) > 4 else "",
                }

            return {"status": "unknown", "patch_id": patch_id}

        except Exception as e:
            logger.error(f"Failed to get patch status: {e}")
            return {"status": "error", "error": str(e)}

    async def list_patches(self, service: str, limit: int = 50) -> list[dict[str, Any]]:
        """List recent patches for a service.

        Args:
            service: Service name
            limit: Max number of patches to return

        Returns:
            patches: List of patch info dicts
        """
        service_repo = self.history_path / service

        if not service_repo.exists():
            return []

        try:
            # Get git log
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--format=%H|%an|%at|%s",
                    f"-{limit}",
                    "penelope-patches",
                ],
                cwd=str(service_repo),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return []

            patches = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 3)
                if len(parts) >= 4:
                    patches.append(
                        {
                            "patch_id": parts[0],
                            "author": parts[1],
                            "timestamp": int(parts[2]),
                            "message": parts[3],
                        }
                    )

            return patches

        except Exception as e:
            logger.error(f"Failed to list patches: {e}")
            return []
