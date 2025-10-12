"""Tests for LLM Honeypot Backend.

Tests cover:
- Session management
- Command response generation
- TTP extraction
- Fallback responses
- Metrics

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from containment.honeypots import (
    HoneypotContext,
    HoneypotType,
    LLMHoneypotBackend,
)


@pytest.fixture
def llm_backend():
    """Create LLM honeypot backend instance."""
    return LLMHoneypotBackend(llm_client=None, realism_level="high")


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="mocked response")
    return client


@pytest.fixture
def test_context():
    """Create test honeypot context."""
    return HoneypotContext(
        session_id="test-session-123",
        attacker_ip="192.168.1.100",
        honeypot_type=HoneypotType.SSH,
        hostname="prod-web-01",
        username="root",
        current_directory="/root",
    )


class TestHoneypotContext:
    """Test HoneypotContext dataclass."""
    
    def test_context_creation(self):
        """Test basic context creation."""
        context = HoneypotContext(
            session_id="test-123",
            attacker_ip="1.2.3.4",
            honeypot_type=HoneypotType.SSH,
        )
        
        assert context.session_id == "test-123"
        assert context.attacker_ip == "1.2.3.4"
        assert context.os_type == "linux"
        assert context.shell_type == "bash"
    
    def test_context_to_dict(self):
        """Test context serialization."""
        context = HoneypotContext(
            session_id="test-123",
            attacker_ip="1.2.3.4",
            honeypot_type=HoneypotType.SSH,
            command_history=["whoami", "pwd", "ls"],
        )
        
        context_dict = context.to_dict()
        
        assert "os_type" in context_dict
        assert "hostname" in context_dict
        assert "command_history" in context_dict
        assert len(context_dict["command_history"]) == 3


class TestLLMHoneypotBackend:
    """Test LLM Honeypot Backend."""
    
    def test_initialization(self, llm_backend):
        """Test backend initialization."""
        assert llm_backend.realism_level == "high"
        assert len(llm_backend.active_sessions) == 0
        assert "commands_processed" in llm_backend.metrics
    
    @pytest.mark.asyncio
    async def test_start_session(self, llm_backend):
        """Test starting new session."""
        context = await llm_backend.start_session(
            attacker_ip="10.0.0.1",
            honeypot_type=HoneypotType.SSH
        )
        
        assert context.session_id is not None
        assert context.attacker_ip == "10.0.0.1"
        assert context.honeypot_type == HoneypotType.SSH
        assert context.session_id in llm_backend.active_sessions
    
    @pytest.mark.asyncio
    async def test_generate_fallback_response(self, llm_backend, test_context):
        """Test fallback response generation."""
        response = await llm_backend.generate_response(
            command="whoami",
            context=test_context
        )
        
        assert response == "root"
        assert "whoami" in test_context.command_history
    
    @pytest.mark.asyncio
    async def test_generate_fallback_pwd(self, llm_backend, test_context):
        """Test pwd command fallback."""
        response = await llm_backend.generate_response(
            command="pwd",
            context=test_context
        )
        
        assert response == "/root"
    
    @pytest.mark.asyncio
    async def test_generate_fallback_ls(self, llm_backend, test_context):
        """Test ls command fallback."""
        response = await llm_backend.generate_response(
            command="ls /tmp",
            context=test_context
        )
        
        assert "file" in response.lower() or "txt" in response.lower()
    
    @pytest.mark.asyncio
    async def test_generate_fallback_unknown_command(self, llm_backend, test_context):
        """Test unknown command fallback."""
        response = await llm_backend.generate_response(
            command="unknowncommand",
            context=test_context
        )
        
        assert "command not found" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_with_llm(self, mock_llm_client, test_context):
        """Test response generation with LLM client."""
        backend = LLMHoneypotBackend(llm_client=mock_llm_client)
        
        response = await backend.generate_response(
            command="whoami",
            context=test_context
        )
        
        assert response == "mocked response"
        mock_llm_client.generate.assert_called_once()
    
    def test_extract_ttps_whoami(self, llm_backend):
        """Test TTP extraction for account discovery."""
        ttps = llm_backend._extract_ttps("whoami")
        
        assert "T1087" in ttps  # Account Discovery
    
    def test_extract_ttps_cat_passwd(self, llm_backend):
        """Test TTP extraction for /etc/passwd access."""
        ttps = llm_backend._extract_ttps("cat /etc/passwd")
        
        assert "T1087" in ttps  # Account Discovery
    
    def test_extract_ttps_uname(self, llm_backend):
        """Test TTP extraction for system info discovery."""
        ttps = llm_backend._extract_ttps("uname -a")
        
        assert "T1082" in ttps  # System Information Discovery
    
    def test_extract_ttps_nmap(self, llm_backend):
        """Test TTP extraction for network scanning."""
        ttps = llm_backend._extract_ttps("nmap -sV 192.168.1.0/24")
        
        assert "T1046" in ttps  # Network Service Scanning
    
    def test_extract_ttps_multiple(self, llm_backend):
        """Test TTP extraction with multiple matches."""
        ttps = llm_backend._extract_ttps("sudo cat /etc/passwd")
        
        # Should match both sudo (T1078) and passwd (T1087)
        assert len(ttps) >= 1
    
    @pytest.mark.asyncio
    async def test_end_session(self, llm_backend):
        """Test ending session and collecting data."""
        # Start session
        context = await llm_backend.start_session(
            attacker_ip="10.0.0.1",
            honeypot_type=HoneypotType.SSH
        )
        
        # Execute some commands
        await llm_backend.generate_response("whoami", context)
        await llm_backend.generate_response("cat /etc/passwd", context)
        await llm_backend.generate_response("nmap localhost", context)
        
        # End session
        summary = await llm_backend.end_session(context.session_id)
        
        assert summary["session_id"] == context.session_id
        assert summary["attacker_ip"] == "10.0.0.1"
        assert summary["commands_executed"] == 3
        assert len(summary["ttps_identified"]) >= 2  # At least 2 TTPs
        assert context.session_id not in llm_backend.active_sessions
    
    @pytest.mark.asyncio
    async def test_end_session_not_found(self, llm_backend):
        """Test ending non-existent session."""
        with pytest.raises(ValueError, match="Session .* not found"):
            await llm_backend.end_session("nonexistent-session")
    
    def test_generate_realistic_hostname_ssh(self, llm_backend):
        """Test hostname generation for SSH honeypot."""
        hostname = llm_backend._generate_realistic_hostname(HoneypotType.SSH)
        
        assert "prod" in hostname or "staging" in hostname or "dev" in hostname
        assert hostname[-2:].isdigit()  # Ends with number
    
    def test_generate_realistic_hostname_http(self, llm_backend):
        """Test hostname generation for HTTP honeypot."""
        hostname = llm_backend._generate_realistic_hostname(HoneypotType.HTTP)
        
        assert "web" in hostname or "nginx" in hostname or "apache" in hostname
    
    def test_generate_environment(self, llm_backend):
        """Test environment variable generation."""
        env = llm_backend._generate_environment()
        
        assert "PATH" in env
        assert "HOME" in env
        assert "SHELL" in env
        assert env["USER"] == "root"
    
    def test_build_response_prompt(self, llm_backend, test_context):
        """Test LLM prompt building."""
        test_context.command_history = ["whoami", "pwd", "ls"]
        
        prompt = llm_backend._build_response_prompt("cat /etc/passwd", test_context)
        
        assert "linux" in prompt.lower()
        assert "prod-web-01" in prompt
        assert "root" in prompt
        assert "cat /etc/passwd" in prompt
        assert "whoami" in prompt  # Command history included
    
    @pytest.mark.asyncio
    async def test_command_history_tracking(self, llm_backend, test_context):
        """Test that command history is properly tracked."""
        commands = ["whoami", "pwd", "ls", "cat /etc/passwd"]
        
        for cmd in commands:
            await llm_backend.generate_response(cmd, test_context)
        
        assert test_context.command_history == commands
    
    @pytest.mark.asyncio
    async def test_generate_response_invalid_context(self, llm_backend):
        """Test response generation with invalid context."""
        invalid_context = HoneypotContext(
            session_id="",  # Invalid empty session_id
            attacker_ip="1.2.3.4",
            honeypot_type=HoneypotType.SSH,
        )
        
        with pytest.raises(ValueError, match="Invalid context"):
            await llm_backend.generate_response("whoami", invalid_context)


class TestTTPExtraction:
    """Test TTP extraction patterns."""
    
    @pytest.fixture
    def backend(self):
        return LLMHoneypotBackend()
    
    def test_command_scripting_interpreter(self, backend):
        """Test T1059 detection."""
        commands = [
            "bash -c 'whoami'",
            "python -c 'import os; os.system(\"ls\")'",
            "powershell -c Get-Process",
        ]
        
        for cmd in commands:
            ttps = backend._extract_ttps(cmd)
            assert "T1059" in ttps
    
    def test_account_discovery(self, backend):
        """Test T1087 detection."""
        commands = [
            "cat /etc/passwd",
            "net user",
            "id",
            "whoami",
        ]
        
        for cmd in commands:
            ttps = backend._extract_ttps(cmd)
            assert "T1087" in ttps
    
    def test_system_info_discovery(self, backend):
        """Test T1082 detection."""
        commands = [
            "uname -a",
            "systeminfo",
            "cat /proc/version",
        ]
        
        for cmd in commands:
            ttps = backend._extract_ttps(cmd)
            assert "T1082" in ttps
    
    def test_network_scanning(self, backend):
        """Test T1046 detection."""
        commands = [
            "nmap 192.168.1.0/24",
            "netstat -an",
            "ss -tulpn",
        ]
        
        for cmd in commands:
            ttps = backend._extract_ttps(cmd)
            assert "T1046" in ttps


@pytest.mark.integration
class TestLLMHoneypotIntegration:
    """Integration tests with real-like scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_attack_session(self):
        """Test complete attack session simulation."""
        backend = LLMHoneypotBackend()
        
        # Attacker connects
        context = await backend.start_session(
            attacker_ip="192.168.1.100",
            honeypot_type=HoneypotType.SSH
        )
        
        # Reconnaissance phase
        await backend.generate_response("whoami", context)
        await backend.generate_response("id", context)
        await backend.generate_response("uname -a", context)
        
        # Enumeration phase
        await backend.generate_response("cat /etc/passwd", context)
        await backend.generate_response("ls /home", context)
        
        # Scanning phase
        await backend.generate_response("netstat -an", context)
        
        # End session and collect TTPs
        summary = await backend.end_session(context.session_id)
        
        assert summary["commands_executed"] == 6
        assert len(summary["ttps_identified"]) >= 2
        assert "T1087" in summary["ttps_identified"]  # Account Discovery
        assert "T1082" in summary["ttps_identified"]  # System Info Discovery
