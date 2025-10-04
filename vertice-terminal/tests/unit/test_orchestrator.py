"""
Unit tests for Orchestration Engine
====================================

Tests for tool execution and output parsing.

Coverage:
- ToolExecutor base class
- NmapExecutor
- NmapParser
- Workspace integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from vertice.core import (
    ExecutionResult,
    ToolExecutor,
    ToolParser,
    ToolError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError,
    NmapExecutor,
    NmapParser
)


# ===== FIXTURES =====

@pytest.fixture
def sample_nmap_xml():
    """Sample Nmap XML output for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -F 10.10.1.5" start="1704670800" version="7.80">
<host starttime="1704670800" endtime="1704670850">
    <status state="up" reason="echo-reply"/>
    <address addr="10.10.1.5" addrtype="ipv4"/>
    <hostnames>
        <hostname name="target.local" type="PTR"/>
    </hostnames>
    <ports>
        <port protocol="tcp" portid="22">
            <state state="open" reason="syn-ack"/>
            <service name="ssh" product="OpenSSH" version="8.2p1 Ubuntu" extrainfo="Ubuntu Linux; protocol 2.0"/>
        </port>
        <port protocol="tcp" portid="80">
            <state state="open" reason="syn-ack"/>
            <service name="http" product="nginx" version="1.18.0"/>
        </port>
        <port protocol="tcp" portid="443">
            <state state="open" reason="syn-ack"/>
            <service name="https" product="nginx" version="1.18.0"/>
        </port>
    </ports>
    <os>
        <osmatch name="Linux 4.15 - 5.8" accuracy="95"/>
    </os>
</host>
<runstats>
    <finished time="1704670850"/>
    <hosts up="1" down="0" total="1"/>
</runstats>
</nmaprun>"""


@pytest.fixture
def sample_nmap_xml_multiple_hosts():
    """Sample Nmap XML with multiple hosts."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -F 10.10.1.0/24" start="1704670800">
<host>
    <status state="up"/>
    <address addr="10.10.1.1" addrtype="ipv4"/>
    <ports>
        <port protocol="tcp" portid="22">
            <state state="open"/>
            <service name="ssh"/>
        </port>
    </ports>
</host>
<host>
    <status state="up"/>
    <address addr="10.10.1.2" addrtype="ipv4"/>
    <ports>
        <port protocol="tcp" portid="80">
            <state state="open"/>
            <service name="http"/>
        </port>
        <port protocol="tcp" portid="443">
            <state state="open"/>
            <service name="https"/>
        </port>
    </ports>
</host>
<runstats>
    <finished time="1704670850"/>
    <hosts up="2" down="0" total="2"/>
</runstats>
</nmaprun>"""


# ===== EXECUTION RESULT TESTS =====

class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """Test creating ExecutionResult."""
        result = ExecutionResult(
            tool="nmap",
            command=["nmap", "-F", "10.10.1.5"],
            returncode=0,
            stdout="test output",
            stderr="",
            duration=5.0,
            success=True
        )

        assert result.tool == "nmap"
        assert result.command == ["nmap", "-F", "10.10.1.5"]
        assert result.returncode == 0
        assert result.success is True
        assert result.duration == 5.0

    def test_execution_result_failed(self):
        """Test failed ExecutionResult."""
        result = ExecutionResult(
            tool="nmap",
            command=["nmap", "invalid"],
            returncode=1,
            stdout="",
            stderr="Error: invalid target",
            duration=1.0,
            success=False
        )

        assert result.success is False
        assert result.returncode == 1
        assert "Error" in result.stderr


# ===== TOOL EXECUTOR TESTS =====

class DummyExecutor(ToolExecutor):
    """Dummy executor for testing base class."""
    tool_name = "echo"
    version_command = ["echo", "--version"]

    def build_command(self, message="test", **kwargs):
        return ["echo", message]


class TestToolExecutor:
    """Test ToolExecutor base class."""

    def test_executor_initialization(self):
        """Test that executor initializes correctly."""
        executor = DummyExecutor()
        assert executor.tool_name == "echo"
        assert executor.timeout == 300  # default

    def test_executor_custom_timeout(self):
        """Test custom timeout."""
        executor = DummyExecutor(timeout=60)
        assert executor.timeout == 60

    @patch('vertice.core.base.shutil.which')
    def test_tool_not_found(self, mock_which):
        """Test that ToolNotFoundError is raised when tool not in PATH."""
        mock_which.return_value = None

        with pytest.raises(ToolNotFoundError):
            DummyExecutor()

    def test_build_command(self):
        """Test build_command method."""
        executor = DummyExecutor()
        cmd = executor.build_command(message="hello world")

        assert cmd == ["echo", "hello world"]

    def test_execute_success(self):
        """Test successful tool execution."""
        executor = DummyExecutor()
        result = executor.execute(message="test")

        assert isinstance(result, ExecutionResult)
        assert result.tool == "echo"
        assert result.success is True
        assert result.returncode == 0
        assert "test" in result.stdout

    def test_execute_timeout(self):
        """Test execution timeout."""
        # Create executor with very short timeout
        executor = DummyExecutor(timeout=0.001)

        # sleep command that will timeout
        executor.tool_name = "sleep"
        executor.build_command = lambda **kwargs: ["sleep", "10"]

        with pytest.raises(ToolTimeoutError):
            executor.execute()


# ===== NMAP EXECUTOR TESTS =====

class TestNmapExecutor:
    """Test NmapExecutor."""

    @patch('vertice.core.base.shutil.which')
    def test_nmap_executor_init(self, mock_which):
        """Test NmapExecutor initialization."""
        mock_which.return_value = "/usr/bin/nmap"

        executor = NmapExecutor()
        assert executor.tool_name == "nmap"
        assert executor.default_timeout == 600

    @patch('vertice.core.base.shutil.which')
    def test_build_command_quick_scan(self, mock_which):
        """Test building quick scan command."""
        mock_which.return_value = "/usr/bin/nmap"
        executor = NmapExecutor()

        cmd = executor.build_command(target="10.10.1.5", scan_type="quick")

        assert "nmap" in cmd
        assert "-F" in cmd  # Fast scan
        assert "-oX" in cmd  # XML output
        assert "-" in cmd  # stdout
        assert "10.10.1.5" in cmd

    @patch('vertice.core.base.shutil.which')
    def test_build_command_full_scan(self, mock_which):
        """Test building full scan command."""
        mock_which.return_value = "/usr/bin/nmap"
        executor = NmapExecutor()

        cmd = executor.build_command(target="192.168.1.0/24", scan_type="full")

        assert "nmap" in cmd
        assert "-p-" in cmd  # All ports
        assert "-sV" in cmd  # Version detection
        assert "-sC" in cmd  # Default scripts
        assert "192.168.1.0/24" in cmd

    @patch('vertice.core.base.shutil.which')
    def test_build_command_with_options(self, mock_which):
        """Test building command with custom options."""
        mock_which.return_value = "/usr/bin/nmap"
        executor = NmapExecutor()

        cmd = executor.build_command(
            target="example.com",
            scan_type="service",
            os_detection=True,
            timing="T4",
            ports="22,80,443"
        )

        assert "nmap" in cmd
        assert "-sV" in cmd  # Service scan
        assert "-O" in cmd  # OS detection
        assert "-T4" in cmd  # Timing
        assert "-p" in cmd
        assert "22,80,443" in cmd
        assert "example.com" in cmd


# ===== NMAP PARSER TESTS =====

class TestNmapParser:
    """Test NmapParser."""

    def test_parser_initialization(self):
        """Test NmapParser initialization."""
        parser = NmapParser()
        assert parser is not None

    def test_parse_valid_xml(self, sample_nmap_xml):
        """Test parsing valid Nmap XML."""
        parser = NmapParser()
        result = parser.parse(sample_nmap_xml)

        assert "scan_info" in result
        assert "hosts" in result

        # Check scan info
        scan_info = result["scan_info"]
        assert scan_info["total_hosts"] == 1
        assert scan_info["up_hosts"] == 1

        # Check hosts
        hosts = result["hosts"]
        assert len(hosts) == 1

        host = hosts[0]
        assert host["ip"] == "10.10.1.5"
        assert host["hostname"] == "target.local"
        assert host["state"] == "up"

    def test_parse_ports(self, sample_nmap_xml):
        """Test parsing port information."""
        parser = NmapParser()
        result = parser.parse(sample_nmap_xml)

        host = result["hosts"][0]
        ports = host["ports"]

        assert len(ports) == 3

        # Check SSH port
        ssh_port = next(p for p in ports if p["port"] == 22)
        assert ssh_port["protocol"] == "tcp"
        assert ssh_port["state"] == "open"
        assert ssh_port["service"] == "ssh"
        assert "OpenSSH" in ssh_port["version"]

        # Check HTTP port
        http_port = next(p for p in ports if p["port"] == 80)
        assert http_port["service"] == "http"
        assert "nginx" in http_port["version"]

    def test_parse_os_detection(self, sample_nmap_xml):
        """Test parsing OS detection results."""
        parser = NmapParser()
        result = parser.parse(sample_nmap_xml)

        host = result["hosts"][0]
        assert host["os_family"] == "Linux"
        assert "Linux" in host["os_version"]

    def test_parse_multiple_hosts(self, sample_nmap_xml_multiple_hosts):
        """Test parsing multiple hosts."""
        parser = NmapParser()
        result = parser.parse(sample_nmap_xml_multiple_hosts)

        hosts = result["hosts"]
        assert len(hosts) == 2

        # Check first host
        host1 = next(h for h in hosts if h["ip"] == "10.10.1.1")
        assert len(host1["ports"]) == 1
        assert host1["ports"][0]["port"] == 22

        # Check second host
        host2 = next(h for h in hosts if h["ip"] == "10.10.1.2")
        assert len(host2["ports"]) == 2
        port_numbers = [p["port"] for p in host2["ports"]]
        assert 80 in port_numbers
        assert 443 in port_numbers

    def test_parse_invalid_xml(self):
        """Test parsing invalid XML."""
        parser = NmapParser()

        with pytest.raises(ValueError, match="Invalid Nmap XML"):
            parser.parse("not valid xml")

    def test_parse_down_host(self):
        """Test that down hosts are skipped."""
        xml = """<?xml version="1.0"?>
        <nmaprun>
        <host>
            <status state="down"/>
            <address addr="10.10.1.5" addrtype="ipv4"/>
        </host>
        <runstats>
            <finished time="1704670850"/>
            <hosts up="0" down="1" total="1"/>
        </runstats>
        </nmaprun>"""

        parser = NmapParser()
        result = parser.parse(xml)

        # Down host should be filtered out
        assert len(result["hosts"]) == 0

    def test_parse_closed_ports(self):
        """Test parsing closed/filtered ports."""
        xml = """<?xml version="1.0"?>
        <nmaprun>
        <host>
            <status state="up"/>
            <address addr="10.10.1.5" addrtype="ipv4"/>
            <ports>
                <port protocol="tcp" portid="22">
                    <state state="open"/>
                    <service name="ssh"/>
                </port>
                <port protocol="tcp" portid="23">
                    <state state="closed"/>
                    <service name="telnet"/>
                </port>
                <port protocol="tcp" portid="80">
                    <state state="filtered"/>
                    <service name="http"/>
                </port>
            </ports>
        </host>
        <runstats>
            <finished time="1704670850"/>
            <hosts up="1" down="0" total="1"/>
        </runstats>
        </nmaprun>"""

        parser = NmapParser()
        result = parser.parse(xml)

        ports = result["hosts"][0]["ports"]
        assert len(ports) == 3

        # Check states
        states = {p["port"]: p["state"] for p in ports}
        assert states[22] == "open"
        assert states[23] == "closed"
        assert states[80] == "filtered"


# ===== INTEGRATION TESTS =====

class TestOrchestratorIntegration:
    """Test full orchestrator workflow (execute + parse)."""

    @patch('vertice.core.base.shutil.which')
    @patch('vertice.core.base.Popen')
    def test_full_workflow(self, mock_popen, mock_which, sample_nmap_xml):
        """Test execute → parse workflow."""
        mock_which.return_value = "/usr/bin/nmap"

        # Mock Popen to return sample XML
        mock_process = MagicMock()
        mock_process.communicate.return_value = (sample_nmap_xml, "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Execute
        executor = NmapExecutor()
        exec_result = executor.execute(target="10.10.1.5", scan_type="quick")

        assert exec_result.success is True
        assert sample_nmap_xml in exec_result.stdout

        # Parse
        parser = NmapParser()
        parsed = parser.parse(exec_result.stdout)

        assert len(parsed["hosts"]) == 1
        assert parsed["hosts"][0]["ip"] == "10.10.1.5"
        assert len(parsed["hosts"][0]["ports"]) == 3


# ===== WORKSPACE INTEGRATION TESTS =====

class TestWorkspaceIntegration:
    """Test workspace auto-population from scan results."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        import tempfile
        import shutil
        from vertice.workspace import WorkspaceManager

        temp_dir = Path(tempfile.mkdtemp())
        ws = WorkspaceManager(workspace_root=temp_dir)
        ws.create_project("test-integration")

        yield ws

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_populate_from_nmap(self, temp_workspace, sample_nmap_xml):
        """Test populating workspace from Nmap results."""
        from vertice.core.workspace_integration import populate_from_nmap

        # Parse Nmap output
        parser = NmapParser()
        parsed = parser.parse(sample_nmap_xml)

        # Populate workspace
        stats = populate_from_nmap(temp_workspace, parsed)

        assert stats["hosts_added"] == 1
        assert stats["ports_added"] == 3

        # Verify data in workspace
        hosts = temp_workspace.query_hosts()
        assert len(hosts) == 1

        host = hosts[0]
        assert host.ip_address == "10.10.1.5"
        assert host.hostname == "target.local"

        # Verify ports
        from vertice.workspace.models import Port
        ports = temp_workspace._session.query(Port).filter_by(host_id=host.id).all()
        assert len(ports) == 3

        port_numbers = [p.port for p in ports]
        assert 22 in port_numbers
        assert 80 in port_numbers
        assert 443 in port_numbers

        # Check service info
        ssh_port = next(p for p in ports if p.port == 22)
        assert ssh_port.service == "ssh"
        assert "OpenSSH" in ssh_port.version

    def test_populate_multiple_hosts(self, temp_workspace, sample_nmap_xml_multiple_hosts):
        """Test populating workspace with multiple hosts."""
        from vertice.core.workspace_integration import populate_from_nmap

        parser = NmapParser()
        parsed = parser.parse(sample_nmap_xml_multiple_hosts)

        stats = populate_from_nmap(temp_workspace, parsed)

        assert stats["hosts_added"] == 2
        assert stats["ports_added"] == 3  # 1 + 2

        hosts = temp_workspace.query_hosts()
        assert len(hosts) == 2

    def test_populate_updates_existing(self, temp_workspace, sample_nmap_xml):
        """Test that re-population updates existing hosts."""
        from vertice.core.workspace_integration import populate_from_nmap

        parser = NmapParser()
        parsed = parser.parse(sample_nmap_xml)

        # First population
        stats1 = populate_from_nmap(temp_workspace, parsed)
        assert stats1["hosts_added"] == 1

        # Second population (should update)
        stats2 = populate_from_nmap(temp_workspace, parsed)
        assert stats2["hosts_updated"] == 1
        assert stats2["hosts_added"] == 0

        # Should still have only 1 host
        hosts = temp_workspace.query_hosts()
        assert len(hosts) == 1
