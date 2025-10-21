"""
Testes para 100% COBERTURA de immunis_cytotoxic_t_service

OBJETIVO: Cobrir as 66 linhas faltantes (33%) - código destrutivo de produção
ESTRATÉGIA: Mocks CIRÚRGICOS apenas para comandos destrutivos do OS
- Mock subprocess.run (iptables)
- Mock os.kill (kill process)
- Mock shutil.move (quarantine file)
- SEM mocks na lógica de negócio

Padrão Pagani: Testes REAIS, mocks APENAS para proteger o sistema.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_cytotoxic_t_service")

from cytotoxic_t_core import (
    CytotoxicTCellCore,
    DefenseAction,
)


class TestExecuteDefenseProductionMode:
    """Testa _execute_defense_action em modo PRODUCTION (DRY_RUN=False) com mocks seguros."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_block_ip_production_success(self, mock_subprocess):
        """Testa _block_ip com iptables mockado (success) - linhas 334-336, 369-383."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        mock_subprocess.return_value = mock_result

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.BLOCK_IP, "target": "192.168.1.100", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        mock_subprocess.assert_called_once()
        assert "iptables" in str(mock_subprocess.call_args)
        assert action_result["status"] == "success"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_block_ip_production_failure(self, mock_subprocess):
        """Testa _block_ip quando iptables falha - linhas 378-383."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"iptables error"
        mock_subprocess.return_value = mock_result

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.BLOCK_IP, "target": "10.0.0.1", "severity": 0.9}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_block_ip_exception(self, mock_subprocess):
        """Testa _block_ip exception handling - linhas 384-386."""
        mock_subprocess.side_effect = Exception("iptables not found")

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.BLOCK_IP, "target": "1.2.3.4", "severity": 0.7}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("os.kill")
    async def test_kill_process_production_success(self, mock_kill):
        """Testa _kill_process com os.kill mockado - linhas 337-338, 397-400."""
        mock_kill.return_value = None

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.KILL_PROCESS, "target": "1234", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        mock_kill.assert_called_once_with(1234, 9)  # SIGKILL
        assert action_result["status"] == "success"

    @pytest.mark.asyncio
    @patch("os.kill")
    async def test_kill_process_exception(self, mock_kill):
        """Testa _kill_process exception handling - linhas 401-403."""
        mock_kill.side_effect = ProcessLookupError("Process not found")

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.KILL_PROCESS, "target": "9999", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_isolate_host_production_success(self, mock_subprocess):
        """Testa _isolate_host com iptables mockado - linhas 339-340, 414-428."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        mock_subprocess.return_value = mock_result

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.ISOLATE_HOST, "target": "192.168.1.50", "severity": 0.9}

        action_result = await core._execute_defense_action(action_spec)

        assert "FORWARD" in str(mock_subprocess.call_args)
        assert action_result["status"] == "success"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_isolate_host_failure(self, mock_subprocess):
        """Testa _isolate_host failure - linhas 423, 426-428."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"isolation failed"
        mock_subprocess.return_value = mock_result

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.ISOLATE_HOST, "target": "10.0.0.50", "severity": 0.9}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_isolate_host_exception(self, mock_subprocess):
        """Testa _isolate_host exception handling - linhas 429-431."""
        mock_subprocess.side_effect = Exception("Network error")

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.ISOLATE_HOST, "target": "10.0.0.99", "severity": 0.9}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.basename")
    async def test_quarantine_file_production_success(self, mock_basename, mock_makedirs, mock_move):
        """Testa _quarantine_file com shutil.move mockado - linhas 341-342, 442-454."""
        mock_basename.return_value = "malware.exe"
        mock_makedirs.return_value = None
        mock_move.return_value = None

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.QUARANTINE_FILE, "target": "/tmp/malware.exe", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        mock_move.assert_called_once()
        mock_makedirs.assert_called_once_with("/var/quarantine", exist_ok=True)
        assert action_result["status"] == "success"

    @pytest.mark.asyncio
    @patch("shutil.move")
    @patch("os.makedirs")
    async def test_quarantine_file_exception(self, mock_makedirs, mock_move):
        """Testa _quarantine_file exception handling - linhas 455-457."""
        mock_makedirs.return_value = None
        mock_move.side_effect = FileNotFoundError("File not found")

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.QUARANTINE_FILE, "target": "/nonexistent/file.exe", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_drop_connection_production(self):
        """Testa _drop_connection (stub implementation) - linhas 343-344, 468-471."""
        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.DROP_CONNECTION, "target": "conn_12345", "severity": 0.7}

        action_result = await core._execute_defense_action(action_spec)

        # Drop connection é stub, sempre retorna sucesso
        assert action_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_defense_stores_in_history(self):
        """Testa que _execute_defense_action armazena resultado em history - linha 357."""
        core = CytotoxicTCellCore(dry_run=True)
        before_count = len(core.neutralization_history)

        action_spec = {"action": DefenseAction.BLOCK_IP, "target": "1.1.1.1", "severity": 0.5}
        await core._execute_defense_action(action_spec)

        assert len(core.neutralization_history) == before_count + 1


class TestExecuteDefenseExceptionHandling:
    """Testa exception handling geral no _execute_defense_action."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_execute_defense_general_exception(self, mock_subprocess):
        """Testa que exceptions gerais são capturadas - linhas 352-355."""
        mock_subprocess.side_effect = RuntimeError("Unexpected error")

        core = CytotoxicTCellCore(dry_run=False)
        action_spec = {"action": DefenseAction.BLOCK_IP, "target": "2.2.2.2", "severity": 0.8}

        action_result = await core._execute_defense_action(action_spec)

        assert action_result["status"] == "failed"
        # Message não contém erro porque exception foi capturada internamente


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
