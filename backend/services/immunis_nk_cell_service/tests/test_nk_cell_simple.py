"""
Testes SIMPLES para immunis_nk_cell_service

OBJETIVO: Cobertura básica 70%+ (serviço complexo, 663 linhas)
ESTRATÉGIA: Testes básicos de init, métodos principais
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_nk_cell_service")

from nk_cell_core import ProcessWhitelist, MissingSelfDetector, DLLHijackDetector, NKCellCore


class TestBasics:
    """Testes básicos."""

    def test_whitelist_init(self):
        wl = ProcessWhitelist()
        assert wl.whitelist_path == "/app/whitelist/processes.json"

    def test_whitelist_load_default(self):
        wl = ProcessWhitelist(whitelist_path="/nonexistent.json")
        result = wl.load_whitelist()
        assert result["status"] == "default_loaded"

    def test_whitelist_load_file(self):
        data = {"hashes": ["abc"], "paths": ["/usr/bin"], "names": ["bash"]}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp = f.name

        try:
            wl = ProcessWhitelist(whitelist_path=temp)
            result = wl.load_whitelist()
            assert result["status"] == "loaded"
            assert result["hashes_count"] == 1
        finally:
            Path(temp).unlink()

    def test_is_whitelisted_by_hash(self):
        data = {"hashes": ["abc123"], "paths": [], "names": []}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(data, f)
            temp = f.name

        try:
            wl = ProcessWhitelist(whitelist_path=temp)
            wl.load_whitelist()
            result = wl.is_whitelisted("test.exe", "/path/test.exe", "abc123")
            assert result["whitelisted"] is True
        finally:
            Path(temp).unlink()

    def test_is_whitelisted_not_found(self):
        wl = ProcessWhitelist()
        wl.whitelisted_hashes = set()
        wl.whitelisted_paths = set()
        wl.whitelisted_names = set()
        result = wl.is_whitelisted("evil.exe", "/tmp/evil.exe", "unknown")
        assert result["whitelisted"] is False

    @pytest.mark.asyncio
    async def test_missing_self_detector(self):
        wl = ProcessWhitelist()
        wl.whitelisted_hashes = set()
        wl.whitelisted_paths = set()
        wl.whitelisted_names = set()
        detector = MissingSelfDetector(wl)

        process = {
            "pid": "1234",
            "name": "suspicious.exe",
            "path": "/tmp/suspicious.exe",
            "hash": "unknown",
            "parent_name": "cmd.exe",
            "cmdline": "suspicious.exe",
            "signed": False,
        }

        result = await detector.detect_missing_self(process)
        assert "missing_self_detected" in result

    def test_is_suspicious_path(self):
        wl = ProcessWhitelist()
        detector = MissingSelfDetector(wl)
        assert detector._is_suspicious_path("/tmp/evil.exe") is True
        assert detector._is_suspicious_path("/usr/bin/bash") is False

    @pytest.mark.asyncio
    async def test_dll_hijack_detector(self):
        detector = DLLHijackDetector()
        process = {"pid": "1234", "name": "test.exe", "signed": False}
        result = await detector.detect_dll_hijacking(process, [])
        assert "hijacking_detected" in result

    def test_nk_cell_init(self):
        nk = NKCellCore()
        assert nk.dry_run is True
        assert isinstance(nk.whitelist, ProcessWhitelist)

    @pytest.mark.asyncio
    async def test_scan_process(self):
        nk = NKCellCore()
        process = {
            "pid": "1234",
            "name": "test.exe",
            "path": "/tmp/test.exe",
            "hash": "unknown",
            "parent_name": "cmd.exe",
            "cmdline": "test.exe",
            "signed": False,
            "loaded_dlls": [],
        }
        result = await nk.scan_process(process)
        assert "missing_self" in result
        assert "dll_hijacking" in result

    @pytest.mark.asyncio
    async def test_eliminate_dry_run(self):
        nk = NKCellCore(dry_run=True)
        result = await nk.eliminate_entity("1234", "process", "test", 0.5)
        assert "action" in result

    @pytest.mark.asyncio
    async def test_get_status(self):
        nk = NKCellCore()
        status = await nk.get_status()
        assert "dry_run_mode" in status

    @pytest.mark.asyncio
    async def test_reload_whitelist(self):
        nk = NKCellCore()
        result = await nk.reload_whitelist()
        assert "status" in result

    def test_enable_production(self):
        nk = NKCellCore(dry_run=True)
        nk.enable_production_mode()
        assert nk.dry_run is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
