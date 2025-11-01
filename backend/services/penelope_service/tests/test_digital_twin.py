"""Tests for Digital Twin Environment - Validação Segura de Patches.

Testes validam criação, validação e destruição de containers Docker isolados
para teste de patches antes de produção.

Fundamento: Provérbios 14:15 - "O prudente atenta para os seus passos"

Author: Vértice Platform Team
License: Proprietary
"""

from unittest.mock import AsyncMock, MagicMock, patch

from core.digital_twin import DigitalTwinEnvironment
import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_docker():
    """Mock Docker client."""
    docker_client = MagicMock()

    # Mock networks
    mock_network = MagicMock()
    mock_network.name = "twin_test_abc123"
    docker_client.networks.create = MagicMock(return_value=mock_network)

    # Mock containers
    mock_container = MagicMock()
    mock_container.id = "abc123def456"
    mock_container.exec_run = MagicMock(return_value=(0, b"success"))
    mock_container.stats = MagicMock(
        return_value={
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 10000000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000},
                "system_cpu_usage": 9000000,
            },
            "memory_stats": {"usage": 100000000, "limit": 1000000000},
        }
    )
    # Mock get_archive to return empty iterator by default
    mock_container.get_archive = MagicMock(return_value=(iter([]), {}))
    docker_client.containers.run = MagicMock(return_value=mock_container)

    # Mock images
    docker_client.images.get = MagicMock(return_value=MagicMock())

    return docker_client


@pytest.fixture
def twin_env(mock_docker):
    """Digital Twin Environment instance."""
    return DigitalTwinEnvironment(docker_client=mock_docker)


# ============================================================================
# TESTS: Twin Creation
# ============================================================================


class TestTwinCreation:
    """Test digital twin creation."""

    @pytest.mark.asyncio
    async def test_create_twin_success(self, twin_env, mock_docker):
        """
        GIVEN: Valid service name
        WHEN: create_twin() is called
        THEN: Twin is created with isolated network and container
        """
        twin_id = await twin_env.create_twin("test_service")

        assert twin_id is not None
        assert len(twin_id) == 12  # Short Docker ID
        assert twin_id in twin_env.twins

        # Verify network created with isolation
        mock_docker.networks.create.assert_called_once()
        call_kwargs = mock_docker.networks.create.call_args[1]
        assert call_kwargs["internal"] is True  # No external access
        assert "penelope.digital_twin" in call_kwargs["labels"]

        # Verify container created
        mock_docker.containers.run.assert_called_once()
        container_kwargs = mock_docker.containers.run.call_args[1]
        assert container_kwargs["environment"]["ENVIRONMENT"] == "digital_twin"
        assert container_kwargs["labels"]["penelope.twin"] == "true"

    @pytest.mark.asyncio
    async def test_create_twin_tracks_metadata(self, twin_env, mock_docker):
        """
        GIVEN: Twin created
        WHEN: Checking twin metadata
        THEN: Contains container, network, service name, and timestamp
        """
        twin_id = await twin_env.create_twin("test_service")

        twin_data = twin_env.twins[twin_id]
        assert "container" in twin_data
        assert "network" in twin_data
        assert twin_data["service"] == "test_service"
        assert "created_at" in twin_data


# ============================================================================
# TESTS: Patch Application
# ============================================================================


class TestPatchApplication:
    """Test patch application to digital twin."""

    @pytest.mark.asyncio
    async def test_apply_patch_success(self, twin_env, mock_docker):
        """
        GIVEN: Twin exists and valid patch
        WHEN: apply_patch() is called
        THEN: Patch is applied successfully
        """
        twin_id = await twin_env.create_twin("test_service")
        mock_container = twin_env.twins[twin_id]["container"]

        # Mock successful patch application
        mock_container.exec_run = MagicMock(
            side_effect=[
                (0, b"patch applies cleanly"),  # git apply --check
                (0, b"patch applied"),  # git apply
            ]
        )

        patch = """
diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1 +1 @@
-print("old")
+print("new")
"""

        result = await twin_env.apply_patch(twin_id, patch)

        assert result is True
        assert mock_container.exec_run.call_count == 2
        assert mock_container.put_archive.called

    @pytest.mark.asyncio
    async def test_apply_patch_validation_fails(self, twin_env, mock_docker):
        """
        GIVEN: Twin exists but patch has conflicts
        WHEN: apply_patch() is called
        THEN: Returns False without applying
        """
        twin_id = await twin_env.create_twin("test_service")
        mock_container = twin_env.twins[twin_id]["container"]

        # Mock patch validation failure
        mock_container.exec_run = MagicMock(
            return_value=(1, b"error: patch does not apply")
        )

        patch = "invalid patch"
        result = await twin_env.apply_patch(twin_id, patch)

        assert result is False
        # Should only call git apply --check, not actual apply
        assert mock_container.exec_run.call_count == 1

    @pytest.mark.asyncio
    async def test_apply_patch_nonexistent_twin(self, twin_env):
        """
        GIVEN: Twin ID doesn't exist
        WHEN: apply_patch() is called
        THEN: Raises KeyError
        """
        with pytest.raises(KeyError):
            await twin_env.apply_patch("nonexistent", "patch")


# ============================================================================
# TESTS: Test Execution
# ============================================================================


class TestTestExecution:
    """Test running tests in digital twin."""

    @pytest.mark.asyncio
    async def test_run_tests_success(self, twin_env, mock_docker):
        """
        GIVEN: Twin exists with tests
        WHEN: run_tests() is called
        THEN: Returns test results with coverage
        """
        twin_id = await twin_env.create_twin("test_service")
        mock_container = twin_env.twins[twin_id]["container"]

        # Mock test execution
        mock_container.exec_run = MagicMock(return_value=(0, b"pytest output"))

        # Mock get_archive to return proper tar data
        import io
        import json
        import tarfile

        def create_mock_archive(data, filename):
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode="w")
            content = json.dumps(data).encode()
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
            tar.close()
            tar_stream.seek(0)
            return iter([tar_stream.read()]), {}

        test_report_data = {"summary": {"passed": 10, "failed": 0, "total": 10}}
        coverage_data = {"totals": {"percent_covered": 85.5}}

        mock_container.get_archive = MagicMock(
            side_effect=[
                create_mock_archive(test_report_data, "test_report.json"),
                create_mock_archive(coverage_data, "coverage.json"),
            ]
        )

        result = await twin_env.run_tests(twin_id)

        assert result["success"] is True
        assert result["tests_passed"] == 10
        assert result["tests_failed"] == 0
        assert result["coverage"] == 85.5
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_run_tests_with_failures(self, twin_env, mock_docker):
        """
        GIVEN: Twin exists with failing tests
        WHEN: run_tests() is called
        THEN: Returns failure information
        """
        twin_id = await twin_env.create_twin("test_service")
        mock_container = twin_env.twins[twin_id]["container"]

        # Mock test execution with failures
        mock_container.exec_run = MagicMock(return_value=(1, b"pytest failures"))

        # Mock test report with failures
        import io
        import json
        import tarfile

        def create_mock_archive(data, filename):
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode="w")
            content = json.dumps(data).encode()
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
            tar.close()
            tar_stream.seek(0)
            return iter([tar_stream.read()]), {}

        test_report_data = {"summary": {"passed": 8, "failed": 2, "total": 10}}
        coverage_data = {"totals": {"percent_covered": 70.0}}

        mock_container.get_archive = MagicMock(
            side_effect=[
                create_mock_archive(test_report_data, "test_report.json"),
                create_mock_archive(coverage_data, "coverage.json"),
            ]
        )

        result = await twin_env.run_tests(twin_id)

        assert result["success"] is False
        assert result["tests_failed"] == 2


# ============================================================================
# TESTS: Metrics Monitoring
# ============================================================================


class TestMetricsMonitoring:
    """Test monitoring of digital twin metrics."""

    @pytest.mark.asyncio
    async def test_monitor_metrics_samples_over_time(self, twin_env, mock_docker):
        """
        GIVEN: Twin is running
        WHEN: monitor_metrics() is called with duration
        THEN: Collects multiple samples and returns averages
        """
        twin_id = await twin_env.create_twin("test_service")

        # Use short duration for test
        result = await twin_env.monitor_metrics(twin_id, duration_seconds=6)

        assert "cpu_avg" in result
        assert "memory_avg" in result
        assert result["samples"] >= 1  # At least one sample
        assert 0 <= result["cpu_avg"] <= 100
        assert 0 <= result["memory_avg"] <= 100


# ============================================================================
# TESTS: Twin Destruction
# ============================================================================


class TestTwinDestruction:
    """Test digital twin cleanup."""

    @pytest.mark.asyncio
    async def test_destroy_twin_cleans_up(self, twin_env, mock_docker):
        """
        GIVEN: Twin exists
        WHEN: destroy_twin() is called
        THEN: Container and network are removed
        """
        twin_id = await twin_env.create_twin("test_service")
        mock_container = twin_env.twins[twin_id]["container"]
        mock_network = twin_env.twins[twin_id]["network"]

        await twin_env.destroy_twin(twin_id)

        # Verify cleanup
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once_with(force=True)
        mock_network.remove.assert_called_once()

        # Verify removed from tracking
        assert twin_id not in twin_env.twins

    @pytest.mark.asyncio
    async def test_destroy_nonexistent_twin(self, twin_env):
        """
        GIVEN: Twin ID doesn't exist
        WHEN: destroy_twin() is called
        THEN: Raises KeyError
        """
        with pytest.raises(KeyError):
            await twin_env.destroy_twin("nonexistent")


# ============================================================================
# INTEGRATION TEST: Full Validation Workflow
# ============================================================================


class TestFullValidationWorkflow:
    """Test complete patch validation workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, twin_env, mock_docker):
        """
        GIVEN: Service and patch
        WHEN: Full validation workflow runs
        THEN: Twin created, patch applied, tests run, monitored, destroyed
        """
        # Step 1: Create twin
        twin_id = await twin_env.create_twin("test_service")
        assert twin_id in twin_env.twins

        # Step 2: Apply patch
        mock_container = twin_env.twins[twin_id]["container"]
        mock_container.exec_run = MagicMock(
            side_effect=[
                (0, b"clean"),  # check
                (0, b"applied"),  # apply
                (0, b"tests pass"),  # pytest
            ]
        )

        patch = "diff --git a/test.py b/test.py\n..."
        patch_ok = await twin_env.apply_patch(twin_id, patch)
        assert patch_ok is True

        # Step 3: Run tests
        import io
        import json
        import tarfile

        def create_mock_archive(data, filename):
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode="w")
            content = json.dumps(data).encode()
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tar.addfile(tarinfo, io.BytesIO(content))
            tar.close()
            tar_stream.seek(0)
            return iter([tar_stream.read()]), {}

        test_report = {"summary": {"passed": 5, "failed": 0, "total": 5}}
        coverage = {"totals": {"percent_covered": 90.0}}

        mock_container.get_archive = MagicMock(
            side_effect=[
                create_mock_archive(test_report, "test_report.json"),
                create_mock_archive(coverage, "coverage.json"),
            ]
        )

        test_result = await twin_env.run_tests(twin_id)

        assert test_result["success"] is True

        # Step 4: Monitor (short duration)
        metrics = await twin_env.monitor_metrics(twin_id, duration_seconds=3)
        assert metrics["samples"] >= 1

        # Step 5: Destroy
        await twin_env.destroy_twin(twin_id)
        assert twin_id not in twin_env.twins
