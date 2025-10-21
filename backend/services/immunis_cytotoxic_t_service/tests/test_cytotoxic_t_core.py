"""
Testes REAIS para immunis_cytotoxic_t_service - Cytotoxic T-Cell Core

OBJETIVO: 100% COBERTURA ABSOLUTA do cytotoxic_t_core.py
- Testa active defense (BLOCK_IP, KILL_PROCESS, ISOLATE_HOST, QUARANTINE_FILE)
- Testa Memory T-Cells (faster response, expiration)
- Testa Depletion Tracking (hourly/daily limits, exhaustion prevention)
- Testa dry-run vs production modes
- ZERO MOCKS desnecessários (dry_run=True permite testar sem ações reais)

Padrão Pagani Absoluto: Cytotoxic T-Cell mata ameaças diretamente.
"""

import pytest
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_cytotoxic_t_service")

from cytotoxic_t_core import (
    CytotoxicTCellCore,
    MemoryTCell,
    DepletionTracker,
    DefenseAction,
)


class TestMemoryTCell:
    """Testes de Memory T-Cell (long-term threat memory)."""

    def test_memory_tcell_creation(self):
        """Testa criação de Memory T-Cell."""
        iocs = {"ips": ["1.2.3.4"], "file_hashes": ["abc123"]}
        memory_cell = MemoryTCell("threat_001", "Emotet", iocs)

        assert memory_cell.threat_id == "threat_001"
        assert memory_cell.malware_family == "Emotet"
        assert memory_cell.iocs == iocs
        assert memory_cell.activation_count == 0
        assert isinstance(memory_cell.created_at, datetime)
        assert isinstance(memory_cell.last_activated, datetime)

    def test_memory_tcell_activate(self):
        """Testa ativação de Memory T-Cell."""
        memory_cell = MemoryTCell("threat_002", "Ryuk", {})

        initial_activations = memory_cell.activation_count
        initial_activated = memory_cell.last_activated

        # Ativa memory cell
        memory_cell.activate()

        assert memory_cell.activation_count == initial_activations + 1
        assert memory_cell.last_activated > initial_activated

    def test_memory_tcell_not_expired(self):
        """Testa que memory cell recém-criada não está expirada."""
        memory_cell = MemoryTCell("threat_003", "TrickBot", {})

        assert memory_cell.is_expired(ttl_days=90) is False

    def test_memory_tcell_expiration(self):
        """Testa expiração de memory cell."""
        memory_cell = MemoryTCell("threat_004", "OldThreat", {})

        # Simula cell antiga (manipula created_at)
        memory_cell.created_at = datetime.now() - timedelta(days=100)

        assert memory_cell.is_expired(ttl_days=90) is True

    def test_memory_tcell_expiration_boundary(self):
        """Testa boundary de expiração (exatamente 90 dias)."""
        memory_cell = MemoryTCell("threat_005", "BoundaryTest", {})

        # Exatamente 90 dias (não deve expirar pois > 90, não >= 90)
        memory_cell.created_at = datetime.now() - timedelta(days=90)
        assert memory_cell.is_expired(ttl_days=90) is False

        # 91 dias (deve expirar)
        memory_cell.created_at = datetime.now() - timedelta(days=91)
        assert memory_cell.is_expired(ttl_days=90) is True


class TestDepletionTracker:
    """Testes de Depletion Tracker (T-cell exhaustion prevention)."""

    def test_depletion_tracker_creation(self):
        """Testa criação de DepletionTracker."""
        tracker = DepletionTracker(max_actions_per_hour=50, max_actions_per_day=500)

        assert tracker.max_actions_per_hour == 50
        assert tracker.max_actions_per_day == 500
        assert len(tracker.action_history) == 0

    def test_depletion_tracker_can_act_initially(self):
        """Testa que tracker permite ação inicialmente."""
        tracker = DepletionTracker()

        assert tracker.can_act() is True

    def test_depletion_tracker_record_action(self):
        """Testa gravação de ações."""
        tracker = DepletionTracker()

        tracker.record_action()
        assert len(tracker.action_history) == 1

        tracker.record_action()
        tracker.record_action()
        assert len(tracker.action_history) == 3

    def test_depletion_tracker_hourly_limit(self):
        """Testa limite horário de ações."""
        tracker = DepletionTracker(max_actions_per_hour=5, max_actions_per_day=100)

        # Grava 5 ações (limite)
        for i in range(5):
            tracker.record_action()

        # Deve estar depleted
        assert tracker.can_act() is False

    def test_depletion_tracker_daily_limit(self):
        """Testa limite diário de ações."""
        tracker = DepletionTracker(max_actions_per_hour=100, max_actions_per_day=10)

        # Grava 10 ações (limite diário)
        for i in range(10):
            tracker.record_action()

        # Deve estar depleted
        assert tracker.can_act() is False

    def test_depletion_tracker_prunes_old_actions(self):
        """Testa que ações antigas (>24h) são removidas."""
        tracker = DepletionTracker()

        # Adiciona ação antiga
        old_action = datetime.now() - timedelta(hours=25)
        tracker.action_history.append(old_action)

        # Adiciona ação recente
        tracker.record_action()

        # can_act() deve limpar ação antiga
        tracker.can_act()

        # Apenas ação recente deve permanecer
        assert len(tracker.action_history) == 1

    def test_depletion_tracker_get_stats(self):
        """Testa get_depletion_stats."""
        tracker = DepletionTracker(max_actions_per_hour=10, max_actions_per_day=100)

        # Grava 3 ações
        for i in range(3):
            tracker.record_action()

        stats = tracker.get_depletion_stats()

        assert stats["hourly_actions"] == 3
        assert stats["hourly_limit"] == 10
        assert stats["hourly_capacity"] == 0.7  # (10-3)/10
        assert stats["daily_actions"] == 3
        assert stats["daily_limit"] == 100
        assert stats["daily_capacity"] == 0.97  # (100-3)/100
        assert stats["depleted"] is False


class TestCytotoxicTCellActivation:
    """Testes de ativação Cytotoxic T-Cell."""

    @pytest.mark.asyncio
    async def test_activate_basic(self):
        """Testa ativação básica com antigen."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_001",
            "malware_family": "Emotet",
            "severity": 0.6,
            "iocs": {
                "ips": ["192.168.1.100"],
                "process_ids": [],
                "file_paths": [],
            },
        }

        result = await core.activate(antigen)

        assert result["antigen_id"] == "ag_001"
        assert result["malware_family"] == "Emotet"
        assert len(result["actions_executed"]) >= 1  # Pelo menos 1 IP bloqueado
        assert result["memory_cell_created"] is True

    @pytest.mark.asyncio
    async def test_activate_creates_memory_cell(self):
        """Testa que ativação cria Memory T-Cell."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_002",
            "malware_family": "Ryuk",
            "severity": 0.5,
            "iocs": {"ips": ["10.0.0.1"]},
        }

        result = await core.activate(antigen)

        assert "Ryuk" in core.memory_cells
        assert core.memory_cells["Ryuk"].malware_family == "Ryuk"

    @pytest.mark.asyncio
    async def test_activate_uses_existing_memory_cell(self):
        """Testa que ativação usa Memory T-Cell existente (faster response)."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_003",
            "malware_family": "TrickBot",
            "severity": 0.5,
            "iocs": {"ips": ["10.0.0.2"]},
        }

        # Primeira ativação (cria memory cell)
        result1 = await core.activate(antigen)
        assert result1["memory_cell_created"] is True

        # Segunda ativação (usa memory cell existente)
        result2 = await core.activate(antigen)
        assert result2.get("memory_cell_activated") is True
        assert result2["memory_cell_created"] is False

        # Activation count deve ter aumentado
        assert core.memory_cells["TrickBot"].activation_count == 1

    @pytest.mark.asyncio
    async def test_activate_when_depleted(self):
        """Testa que ativação falha quando T-cell está depleted."""
        core = CytotoxicTCellCore(dry_run=True, max_actions_per_hour=1)

        antigen = {
            "antigen_id": "ag_004",
            "malware_family": "Malware1",
            "severity": 0.5,
            "iocs": {"ips": ["1.1.1.1"]},
        }

        # Primeira ativação (consome única ação permitida)
        result1 = await core.activate(antigen)
        assert len(result1["actions_executed"]) == 1

        # Segunda ativação (depleted)
        result2 = await core.activate(antigen)
        assert result2.get("depleted") is True
        assert len(result2["actions_executed"]) == 0


class TestDefenseActions:
    """Testes de determinação de ações de defesa."""

    @pytest.mark.asyncio
    async def test_defense_action_block_ips(self):
        """Testa que IPs maliciosos são bloqueados."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_ips",
            "malware_family": "Botnet",
            "severity": 0.6,
            "iocs": {
                "ips": ["1.2.3.4", "5.6.7.8", "9.10.11.12"],
            },
        }

        result = await core.activate(antigen)

        # Deve ter bloqueado 3 IPs
        actions = result["actions_executed"]
        block_ip_actions = [a for a in actions if a["action"] == "block_ip"]
        assert len(block_ip_actions) == 3

    @pytest.mark.asyncio
    async def test_defense_action_kill_processes(self):
        """Testa que processos maliciosos são terminados."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_procs",
            "malware_family": "CryptoMiner",
            "severity": 0.7,
            "iocs": {
                "process_ids": ["12345", "67890"],
            },
        }

        result = await core.activate(antigen)

        actions = result["actions_executed"]
        kill_process_actions = [a for a in actions if a["action"] == "kill_process"]
        assert len(kill_process_actions) == 2

    @pytest.mark.asyncio
    async def test_defense_action_quarantine_files(self):
        """Testa que arquivos maliciosos são colocados em quarentena."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_files",
            "malware_family": "Ransomware",
            "severity": 0.8,
            "iocs": {
                "file_paths": ["/tmp/malware.exe", "/tmp/cryptolocker.dll"],
            },
        }

        result = await core.activate(antigen)

        actions = result["actions_executed"]
        quarantine_actions = [a for a in actions if a["action"] == "quarantine_file"]
        assert len(quarantine_actions) == 2

    @pytest.mark.asyncio
    async def test_defense_action_isolate_host_high_severity(self):
        """Testa que host é isolado apenas para severity >= 0.8."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen_high_severity = {
            "antigen_id": "ag_high",
            "malware_family": "APT",
            "severity": 0.85,  # >= 0.8
            "iocs": {
                "host_id": "host-compromised-001",
            },
        }

        result = await core.activate(antigen_high_severity)

        actions = result["actions_executed"]
        isolate_actions = [a for a in actions if a["action"] == "isolate_host"]
        assert len(isolate_actions) == 1

    @pytest.mark.asyncio
    async def test_defense_action_no_isolate_low_severity(self):
        """Testa que host NÃO é isolado para severity < 0.8."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen_low_severity = {
            "antigen_id": "ag_low",
            "malware_family": "Adware",
            "severity": 0.5,  # < 0.8
            "iocs": {
                "host_id": "host-001",
            },
        }

        result = await core.activate(antigen_low_severity)

        actions = result["actions_executed"]
        isolate_actions = [a for a in actions if a["action"] == "isolate_host"]
        assert len(isolate_actions) == 0

    @pytest.mark.asyncio
    async def test_defense_action_limits(self):
        """Testa limites de ações (max 10 IPs, 5 processes, 10 files)."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_limits",
            "malware_family": "Massive",
            "severity": 0.6,
            "iocs": {
                "ips": [f"192.168.1.{i}" for i in range(20)],  # 20 IPs, max 10
                "process_ids": [str(i) for i in range(10)],  # 10 processes, max 5
                "file_paths": [f"/tmp/file{i}.exe" for i in range(15)],  # 15 files, max 10
            },
        }

        result = await core.activate(antigen)
        actions = result["actions_executed"]

        block_ip_count = sum(1 for a in actions if a["action"] == "block_ip")
        kill_process_count = sum(1 for a in actions if a["action"] == "kill_process")
        quarantine_count = sum(1 for a in actions if a["action"] == "quarantine_file")

        assert block_ip_count == 10  # Max 10
        assert kill_process_count == 5  # Max 5
        assert quarantine_count == 10  # Max 10


class TestDryRunMode:
    """Testes de dry-run vs production mode."""

    @pytest.mark.asyncio
    async def test_dry_run_mode_simulates_actions(self):
        """Testa que dry-run simula ações sem executá-las."""
        core = CytotoxicTCellCore(dry_run=True)

        antigen = {
            "antigen_id": "ag_dryrun",
            "malware_family": "Test",
            "severity": 0.5,
            "iocs": {"ips": ["1.2.3.4"]},
        }

        result = await core.activate(antigen)
        actions = result["actions_executed"]

        assert all(a["status"] == "simulated" for a in actions)
        assert all(a["dry_run"] is True for a in actions)

    def test_enable_production_mode(self):
        """Testa habilitação de production mode."""
        core = CytotoxicTCellCore(dry_run=True)

        assert core.dry_run is True

        core.enable_production_mode()

        assert core.dry_run is False


class TestMemoryCellCleanup:
    """Testes de limpeza de Memory T-Cells."""

    @pytest.mark.asyncio
    async def test_cleanup_memory_cells_removes_expired(self):
        """Testa que cleanup remove memory cells expiradas."""
        core = CytotoxicTCellCore(dry_run=True)

        # Cria 2 memory cells
        antigen1 = {"antigen_id": "ag1", "malware_family": "Old", "severity": 0.5, "iocs": {"ips": ["1.1.1.1"]}}
        antigen2 = {"antigen_id": "ag2", "malware_family": "Recent", "severity": 0.5, "iocs": {"ips": ["2.2.2.2"]}}

        await core.activate(antigen1)
        await core.activate(antigen2)

        assert len(core.memory_cells) == 2

        # Simula cell antiga (expira "Old")
        core.memory_cells["Old"].created_at = datetime.now() - timedelta(days=100)

        # Cleanup
        await core.cleanup_memory_cells(ttl_days=90)

        # Apenas "Recent" deve permanecer
        assert len(core.memory_cells) == 1
        assert "Recent" in core.memory_cells
        assert "Old" not in core.memory_cells


class TestStatus:
    """Testes do endpoint de status."""

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Testa get_status retorna informações corretas."""
        core = CytotoxicTCellCore(dry_run=True)

        # Ativa 2 threats
        antigen1 = {"antigen_id": "ag1", "malware_family": "Emotet", "severity": 0.6, "iocs": {"ips": ["1.1.1.1"]}}
        antigen2 = {"antigen_id": "ag2", "malware_family": "Ryuk", "severity": 0.7, "iocs": {"ips": ["2.2.2.2"]}}

        await core.activate(antigen1)
        await core.activate(antigen2)

        status = await core.get_status()

        assert status["status"] == "operational"
        assert status["dry_run_mode"] is True
        assert status["memory_cells_count"] == 2
        assert status["neutralization_records"] >= 2  # Pelo menos 2 ações
        assert status["last_action"] != "N/A"
        assert "depletion" in status


class TestIntegration:
    """Testes de integração end-to-end."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Testa ciclo completo: activate → memory → depletion → cleanup."""
        core = CytotoxicTCellCore(dry_run=True, max_actions_per_hour=10)

        # 1. Ativa com ransomware (múltiplas ações)
        antigen = {
            "antigen_id": "ag_ransomware",
            "malware_family": "WannaCry",
            "severity": 0.9,
            "iocs": {
                "ips": ["192.168.1.100", "192.168.1.101"],
                "process_ids": ["9999"],
                "file_paths": ["/tmp/wannacry.exe"],
                "host_id": "host-infected-001",
            },
        }

        result = await core.activate(antigen)

        # Deve ter executado múltiplas ações
        assert len(result["actions_executed"]) >= 4  # 2 IPs + 1 process + 1 file + 1 host
        assert result["memory_cell_created"] is True

        # 2. Reativa (memory cell)
        result2 = await core.activate(antigen)
        assert result2.get("memory_cell_activated") is True

        # 3. Verifica status
        status = await core.get_status()
        assert status["memory_cells_count"] == 1
        assert status["neutralization_records"] >= 8  # 2 ativações * ~4 ações

        # 4. Cleanup (memory cell não deve expirar, é recente)
        await core.cleanup_memory_cells(ttl_days=90)
        assert len(core.memory_cells) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
