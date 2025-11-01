"""Tests for Patch History - Git-based Rollback Mechanism.

Testes validam salvamento, listagem e rollback de patches usando git.

Fundamento: Eclesiastes 3:6 - "Tempo de guardar, e tempo de deitar fora"

Author: Vértice Platform Team
License: Proprietary
"""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from core.patch_history import PatchHistory
import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_history_path():
    """Temporary directory for patch history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def patch_history(temp_history_path):
    """PatchHistory instance with temp directory."""
    return PatchHistory(history_path=temp_history_path)


@pytest.fixture
def sample_patch():
    """Sample git patch."""
    return """
diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1 +1 @@
-print("old")
+print("new")
"""


# ============================================================================
# TESTS: Patch Saving
# ============================================================================


class TestPatchSaving:
    """Test patch saving to git history."""

    @pytest.mark.asyncio
    async def test_save_patch_creates_git_repo(
        self, patch_history, temp_history_path, sample_patch
    ):
        """
        GIVEN: New service without history
        WHEN: save_patch() is called
        THEN: Git repo is created with initial commit
        """
        patch_id = await patch_history.save_patch(
            service="test_service",
            patch=sample_patch,
            anomaly_id="test-001",
            metadata={"test": "data"},
        )

        assert patch_id is not None
        assert len(patch_id) == 40  # SHA-1 hash

        # Verify git repo exists
        service_repo = temp_history_path / "test_service"
        assert (service_repo / ".git").exists()
        assert (service_repo / "README.md").exists()

    @pytest.mark.asyncio
    async def test_save_patch_stores_patch_and_metadata(
        self, patch_history, temp_history_path, sample_patch
    ):
        """
        GIVEN: Patch to save
        WHEN: save_patch() is called
        THEN: Patch file and metadata are saved
        """
        patch_id = await patch_history.save_patch(
            service="test_service",
            patch=sample_patch,
            anomaly_id="test-002",
            metadata={"applied_by": "penelope"},
        )

        service_repo = temp_history_path / "test_service"
        patch_file = service_repo / "patch_test-002.patch"
        metadata_file = service_repo / "metadata_test-002.json"

        assert patch_file.exists()
        assert metadata_file.exists()

        # Verify content
        assert sample_patch.strip() == patch_file.read_text().strip()

        import json

        metadata = json.loads(metadata_file.read_text())
        assert metadata["anomaly_id"] == "test-002"
        assert metadata["applied_by"] == "penelope"
        assert "saved_at" in metadata

    @pytest.mark.asyncio
    async def test_save_multiple_patches(self, patch_history, sample_patch):
        """
        GIVEN: Multiple patches to save
        WHEN: save_patch() is called multiple times
        THEN: All patches are stored in git history
        """
        patch_id_1 = await patch_history.save_patch(
            "test_service", sample_patch, "anomaly-001", {}
        )

        patch_id_2 = await patch_history.save_patch(
            "test_service", sample_patch, "anomaly-002", {}
        )

        patch_id_3 = await patch_history.save_patch(
            "test_service", sample_patch, "anomaly-003", {}
        )

        # All should be unique commit hashes
        assert patch_id_1 != patch_id_2
        assert patch_id_2 != patch_id_3
        assert len({patch_id_1, patch_id_2, patch_id_3}) == 3


# ============================================================================
# TESTS: Patch Status
# ============================================================================


class TestPatchStatus:
    """Test getting patch status."""

    @pytest.mark.asyncio
    async def test_get_patch_status_applied(self, patch_history, sample_patch):
        """
        GIVEN: Patch that has been applied
        WHEN: get_patch_status() is called
        THEN: Returns status="applied" with commit info
        """
        patch_id = await patch_history.save_patch(
            "test_service", sample_patch, "test-001", {}
        )

        status = await patch_history.get_patch_status("test_service", patch_id)

        assert status["status"] == "applied"
        assert status["patch_id"] == patch_id
        assert "commit_hash" in status
        assert "timestamp" in status

    @pytest.mark.asyncio
    async def test_get_patch_status_not_found(self, patch_history, sample_patch):
        """
        GIVEN: Service exists but patch ID doesn't
        WHEN: get_patch_status() is called
        THEN: Returns status="not_found"
        """
        # Create service first
        await patch_history.save_patch("test_service", sample_patch, "test-001", {})

        # Query nonexistent patch
        status = await patch_history.get_patch_status(
            "test_service", "0" * 40  # Invalid hash
        )

        assert status["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_patch_status_service_not_found(self, patch_history):
        """
        GIVEN: Service doesn't exist
        WHEN: get_patch_status() is called
        THEN: Returns status="unknown"
        """
        status = await patch_history.get_patch_status("nonexistent", "abc123")

        assert status["status"] == "unknown"


# ============================================================================
# TESTS: Patch Listing
# ============================================================================


class TestPatchListing:
    """Test listing patch history."""

    @pytest.mark.asyncio
    async def test_list_patches_empty(self, patch_history):
        """
        GIVEN: Service with no patches
        WHEN: list_patches() is called
        THEN: Returns empty list
        """
        patches = await patch_history.list_patches("nonexistent_service")

        assert patches == []

    @pytest.mark.asyncio
    async def test_list_patches_returns_recent_patches(
        self, patch_history, sample_patch
    ):
        """
        GIVEN: Service with multiple patches
        WHEN: list_patches() is called
        THEN: Returns patches in reverse chronological order
        """
        await patch_history.save_patch("test_service", sample_patch, "test-001", {})
        await patch_history.save_patch("test_service", sample_patch, "test-002", {})
        await patch_history.save_patch("test_service", sample_patch, "test-003", {})

        patches = await patch_history.list_patches("test_service", limit=10)

        assert len(patches) >= 3  # Plus initial commit
        # Most recent first
        assert isinstance(patches[0], dict)
        assert "patch_id" in patches[0]
        assert "timestamp" in patches[0]
        assert "message" in patches[0]

    @pytest.mark.asyncio
    async def test_list_patches_respects_limit(self, patch_history, sample_patch):
        """
        GIVEN: Service with 5 patches
        WHEN: list_patches(limit=3) is called
        THEN: Returns only 3 most recent patches
        """
        for i in range(5):
            await patch_history.save_patch(
                "test_service", sample_patch, f"test-{i:03d}", {}
            )

        patches = await patch_history.list_patches("test_service", limit=3)

        assert len(patches) == 3


# ============================================================================
# TESTS: Rollback - MOCKED (no real file changes)
# ============================================================================


class TestRollbackMocked:
    """Test rollback mechanism with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_rollback_patch_success(
        self, patch_history, temp_history_path, sample_patch
    ):
        """
        GIVEN: Patch that was applied
        WHEN: rollback_patch() is called
        THEN: Reverse patch is applied and recorded
        """
        # Save patch first
        patch_id = await patch_history.save_patch(
            "test_service", sample_patch, "test-001", {}
        )

        # Mock subprocess calls for rollback
        with patch("subprocess.run") as mock_run:
            # Mock git show (get commit)
            mock_run.return_value = MagicMock(
                returncode=0, stdout=f"commit {patch_id}\nDiff content"
            )

            # Mock the actual rollback (patch -R)
            def subprocess_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])

                if "diff-tree" in cmd:
                    return MagicMock(
                        returncode=0,
                        stdout="patch_test-001.patch\nmetadata_test-001.json",
                    )
                elif "show" in cmd and ":" in cmd:
                    return MagicMock(returncode=0, stdout=sample_patch)
                elif "patch" in cmd and "-R" in cmd:
                    return MagicMock(returncode=0, stdout=b"", stderr=b"")
                else:
                    return MagicMock(returncode=0, stdout="", stderr=b"")

            mock_run.side_effect = subprocess_side_effect

            result = await patch_history.rollback_patch("test_service", patch_id)

            assert result is True

            # Verify rollback was recorded
            service_repo = temp_history_path / "test_service"
            rollback_file = service_repo / f"rollback_{patch_id[:8]}.json"
            assert rollback_file.exists()

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_service(self, patch_history):
        """
        GIVEN: Service doesn't exist
        WHEN: rollback_patch() is called
        THEN: Raises FileNotFoundError
        """
        with pytest.raises(FileNotFoundError):
            await patch_history.rollback_patch("nonexistent", "abc123")

    @pytest.mark.asyncio
    async def test_rollback_patch_application_fails(self, patch_history, sample_patch):
        """
        GIVEN: Patch that can't be reversed
        WHEN: rollback_patch() is called
        THEN: Returns False
        """
        # Save patch first
        patch_id = await patch_history.save_patch(
            "test_service", sample_patch, "test-001", {}
        )

        # Mock subprocess to fail on patch -R
        with patch("subprocess.run") as mock_run:

            def subprocess_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])

                if "diff-tree" in cmd:
                    return MagicMock(returncode=0, stdout="patch_test-001.patch")
                elif "show" in cmd and ":" in cmd:
                    return MagicMock(returncode=0, stdout=sample_patch)
                elif "patch" in cmd and "-R" in cmd:
                    # Patch reverse fails
                    return MagicMock(
                        returncode=1,
                        stdout=b"",
                        stderr=b"patch does not apply",
                    )
                else:
                    return MagicMock(returncode=0, stdout="")

            mock_run.side_effect = subprocess_side_effect

            result = await patch_history.rollback_patch("test_service", patch_id)

            assert result is False


# ============================================================================
# INTEGRATION TEST: Full Workflow
# ============================================================================


class TestFullWorkflow:
    """Test complete patch history workflow."""

    @pytest.mark.asyncio
    async def test_full_patch_lifecycle(self, patch_history, sample_patch):
        """
        GIVEN: New service
        WHEN: Save patch → Check status → List patches
        THEN: All operations work correctly
        """
        # Step 1: Save patch
        patch_id = await patch_history.save_patch(
            "workflow_test", sample_patch, "wf-001", {"test": "full"}
        )
        assert patch_id is not None

        # Step 2: Check status
        status = await patch_history.get_patch_status("workflow_test", patch_id)
        assert status["status"] == "applied"
        assert status["patch_id"] == patch_id

        # Step 3: List patches
        patches = await patch_history.list_patches("workflow_test")
        assert len(patches) >= 1
        assert any(p["patch_id"] == patch_id for p in patches)

        # Step 4: Save another patch
        patch_id_2 = await patch_history.save_patch(
            "workflow_test", sample_patch, "wf-002", {}
        )

        # Step 5: List again
        patches = await patch_history.list_patches("workflow_test")
        assert len(patches) >= 2
