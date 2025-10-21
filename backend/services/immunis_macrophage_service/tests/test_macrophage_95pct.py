"""
Testes ADICIONAIS para atingir 95%+ cobertura no Macrophage Service

OBJETIVO: Cobrir as linhas restantes que SÃO testáveis sem infra externa
ESTRATÉGIA: Testes para edge cases, cleanup volumoso, exception paths

Padrão Pagani REAL: 95% mínimo.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_macrophage_service")

from macrophage_core import MacrophageCore
from api import app
from fastapi.testclient import TestClient


class TestMacrophageCoreCleanupVolume:
    """Testa cleanup com volumes altos (linhas 385-386, 392-393)."""

    @pytest.mark.asyncio
    async def test_cleanup_with_1000plus_artifacts(self):
        """Testa cleanup quando há > 1000 artifacts."""
        core = MacrophageCore()

        # Adiciona 1100 artifacts
        for i in range(1100):
            core.processed_artifacts.append({
                "sample_hash": f"hash_{i}",
                "malware_family": f"family_{i}",
            })

        result = await core.cleanup_debris()

        # Deve ter removido 100 (1100 - 1000)
        assert result["artifacts_removed"] == 100
        assert len(core.processed_artifacts) == 1000

    @pytest.mark.asyncio
    async def test_cleanup_with_500plus_signatures(self):
        """Testa cleanup quando há > 500 signatures."""
        core = MacrophageCore()

        # Adiciona 600 signatures
        for i in range(600):
            core.generated_signatures.append(f"rule test_{i} {{}}")

        result = await core.cleanup_debris()

        # Deve ter removido 100 (600 - 500)
        assert result["signatures_removed"] == 100
        assert len(core.generated_signatures) == 500

    @pytest.mark.asyncio
    async def test_cleanup_with_both_volumes_high(self):
        """Testa cleanup com ambos os volumes altos."""
        core = MacrophageCore()

        # Adiciona volumes altos
        for i in range(1200):
            core.processed_artifacts.append({"hash": f"h_{i}"})
        for i in range(700):
            core.generated_signatures.append(f"rule r_{i} {{}}")

        result = await core.cleanup_debris()

        assert result["artifacts_removed"] == 200  # 1200 - 1000
        assert result["signatures_removed"] == 200  # 700 - 500
        assert len(core.processed_artifacts) == 1000
        assert len(core.generated_signatures) == 500


class TestAPIStartupShutdown:
    """Testa startup/shutdown events (linhas 75-78, 84-90)."""

    def test_startup_shutdown_logging(self, caplog):
        """Testa que startup/shutdown events executam."""
        import logging
        caplog.set_level(logging.INFO)

        # TestClient triggera startup automaticamente
        with TestClient(app) as client:
            response = client.get("/health", headers={"Authorization": "Bearer trusted-token"})
            assert response.status_code == 200

        # Verifica que algum log foi gerado (startup/shutdown)
        assert len(caplog.records) > 0


class TestAPIExceptionPaths:
    """Testa exception paths na API (linhas 160-161, 170-172, 199-201)."""

    @patch("os.unlink")
    def test_phagocytose_cleanup_fails(self, mock_unlink):
        """Testa quando cleanup de arquivo temporário falha (linhas 160-161)."""
        mock_unlink.side_effect = OSError("Permission denied")

        client = TestClient(app)

        file_content = b"MZ\x90\x00TestMalware"

        response = client.post(
            "/phagocytose",
            files={"file": ("malware.exe", file_content, "application/octet-stream")},
            data={"malware_family": "TestFamily"},
            headers={"Authorization": "Bearer trusted-token"},
        )

        # Deve ter sucesso mesmo com cleanup falhando
        assert response.status_code == 200
        # Log de warning deve ter sido gerado
        mock_unlink.assert_called()

    def test_phagocytose_core_exception(self):
        """Testa exception no core.phagocytose (linhas 170-172)."""
        from api import macrophage_core
        from unittest.mock import AsyncMock

        # Salva original
        original_phagocytose = macrophage_core.phagocytose

        # Mock para lançar exception
        async def failing_phagocytose(*args, **kwargs):
            raise RuntimeError("Phagocytosis failed")

        macrophage_core.phagocytose = failing_phagocytose

        try:
            client = TestClient(app)

            file_content = b"MZ\x90\x00Test"

            response = client.post(
                "/phagocytose",
                files={"file": ("test.exe", file_content, "application/octet-stream")},
                headers={"Authorization": "Bearer trusted-token"},
            )

            # Deve retornar 500
            assert response.status_code == 500
        finally:
            # Restaura
            macrophage_core.phagocytose = original_phagocytose

    def test_present_antigen_exception(self):
        """Testa exception no present_antigen (linhas 199-201)."""
        from api import macrophage_core
        from unittest.mock import AsyncMock

        # Salva original
        original_present = macrophage_core.present_antigen

        # Mock para lançar exception
        async def failing_present(*args, **kwargs):
            raise RuntimeError("Kafka exploded")

        macrophage_core.present_antigen = failing_present

        try:
            client = TestClient(app)

            artifact = {
                "sample_hash": "abc123",
                "malware_family": "Test",
                "analysis": {"severity": 0.5},
                "iocs": {},
                "yara_signature": "rule test {}",
            }

            response = client.post(
                "/present_antigen",
                json={"artifact": artifact},
                headers={"Authorization": "Bearer trusted-token"},
            )

            # Deve retornar 500
            assert response.status_code == 500
        finally:
            # Restaura
            macrophage_core.present_antigen = original_present


class TestCuckooTimeoutEdgeCase:
    """Testa Cuckoo timeout edge case (linhas 87-88)."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("asyncio.sleep")  # Mock sleep para não esperar 5s * 60 = 300s
    async def test_cuckoo_analysis_timeout_after_60_polls(self, mock_sleep, mock_client_class):
        """Testa que após 60 polls sem 'reported', usa fallback (linha 87-88)."""
        from macrophage_core import CuckooSandboxClient

        mock_sleep.return_value = None  # Sleep instantâneo

        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock POST response (submit)
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"task_id": 999}
        mock_client.post.return_value = mock_post_response

        # Mock GET response (status NUNCA fica "reported")
        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {"task": {"status": "pending"}}
        mock_client.get.return_value = mock_status_response

        client = CuckooSandboxClient()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"TestSample")
            temp_path = f.name

        try:
            # Vai dar timeout após 60 iterações (mas instantâneo com mock sleep)
            result = await client.submit_sample(temp_path, timeout=1)

            # Deve usar fallback
            assert result["fallback"] is True
            assert result["info"]["id"] == "static_analysis"
        finally:
            Path(temp_path).unlink()


class TestMainEntryPoint:
    """Testa que main entry point existe (linha 287)."""

    def test_main_entry_point_exists(self):
        """Verifica que __main__ block existe."""
        import api

        # Lê o arquivo fonte
        import inspect
        source = inspect.getsource(api)

        # Verifica que main block existe
        assert 'if __name__ == "__main__"' in source
        assert "uvicorn.run" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
