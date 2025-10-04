"""
Base classes for Tool Orchestration
====================================

Abstract base classes for tool execution and output parsing.

Design Pattern:
- ToolExecutor: Spawns external tools, manages subprocess, captures output
- ToolParser: Parses tool-specific output into unified format
- ExecutionResult: Standard result container

Example Implementation:
    class NmapExecutor(ToolExecutor):
        tool_name = "nmap"
        version_command = ["nmap", "--version"]

        def build_command(self, target, scan_type="quick", **kwargs):
            cmd = ["nmap"]
            if scan_type == "full":
                cmd.extend(["-p-", "-sV", "-sC"])
            elif scan_type == "quick":
                cmd.extend(["-F"])
            cmd.extend(["-oX", "-", target])
            return cmd
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from subprocess import Popen, PIPE, TimeoutExpired
from pathlib import Path
import shutil
import time
import logging

logger = logging.getLogger(__name__)


# ===== EXCEPTIONS =====

class ToolError(Exception):
    """Base exception for tool execution errors."""
    pass


class ToolNotFoundError(ToolError):
    """Raised when tool binary is not found in PATH."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds timeout."""
    pass


# ===== DATA STRUCTURES =====

@dataclass
class ExecutionResult:
    """
    Standard result container for tool execution.

    Attributes:
        tool: Tool name (e.g., "nmap", "nuclei")
        command: Full command executed
        returncode: Exit code
        stdout: Standard output (raw)
        stderr: Standard error
        duration: Execution time in seconds
        success: Whether execution was successful
        metadata: Additional tool-specific metadata
    """
    tool: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"<ExecutionResult tool={self.tool} status={status} duration={self.duration:.2f}s>"


# ===== BASE CLASSES =====

class ToolExecutor(ABC):
    """
    Abstract base class for tool execution.

    Responsibilities:
    - Check if tool is installed
    - Build command from parameters
    - Execute tool subprocess
    - Capture stdout/stderr
    - Handle timeouts
    - Return ExecutionResult

    Subclasses must implement:
    - tool_name: str
    - version_command: List[str]
    - build_command(**kwargs) -> List[str]
    """

    tool_name: str = None  # e.g., "nmap"
    version_command: List[str] = None  # e.g., ["nmap", "--version"]
    default_timeout: int = 300  # 5 minutes

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize tool executor.

        Args:
            timeout: Maximum execution time in seconds (None = use default)

        Raises:
            ToolNotFoundError: If tool binary not found
        """
        if not self.tool_name:
            raise ValueError("Subclass must define tool_name")

        self.timeout = timeout or self.default_timeout
        self._validate_tool_installed()

    def _validate_tool_installed(self):
        """Check if tool is installed and in PATH."""
        if not shutil.which(self.tool_name):
            raise ToolNotFoundError(
                f"{self.tool_name} not found in PATH. "
                f"Install it first: apt install {self.tool_name} (or equivalent)"
            )

    def get_version(self) -> str:
        """
        Get tool version.

        Returns:
            Version string

        Raises:
            ToolExecutionError: If version check fails
        """
        if not self.version_command:
            return "unknown"

        try:
            process = Popen(
                self.version_command,
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=5)
            return stdout.strip() if stdout else stderr.strip()
        except Exception as e:
            raise ToolExecutionError(f"Failed to get {self.tool_name} version: {e}")

    @abstractmethod
    def build_command(self, **kwargs) -> List[str]:
        """
        Build command array from parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Command array (e.g., ["nmap", "-sV", "10.10.1.5"])

        Example:
            def build_command(self, target, ports="1-1000", **kwargs):
                return ["nmap", "-p", ports, target]
        """
        pass

    def execute(self, **kwargs) -> ExecutionResult:
        """
        Execute tool with given parameters.

        Args:
            **kwargs: Parameters passed to build_command()

        Returns:
            ExecutionResult object

        Raises:
            ToolExecutionError: If execution fails
            ToolTimeoutError: If execution exceeds timeout
        """
        # Build command
        command = self.build_command(**kwargs)
        logger.info(f"Executing: {' '.join(command)}")

        start_time = time.time()

        try:
            # Spawn process
            process = Popen(
                command,
                stdout=PIPE,
                stderr=PIPE,
                text=True
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except TimeoutExpired:
                process.kill()
                process.wait()
                duration = time.time() - start_time
                raise ToolTimeoutError(
                    f"{self.tool_name} execution exceeded timeout ({self.timeout}s)"
                )

            duration = time.time() - start_time
            success = process.returncode == 0

            result = ExecutionResult(
                tool=self.tool_name,
                command=command,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                success=success
            )

            if not success:
                logger.warning(
                    f"{self.tool_name} failed (exit code {process.returncode}): {stderr[:200]}"
                )

            return result

        except ToolTimeoutError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{self.tool_name} execution failed: {e}")
            raise ToolExecutionError(f"{self.tool_name} execution failed: {e}")


class ToolParser(ABC):
    """
    Abstract base class for tool output parsing.

    Responsibilities:
    - Parse tool-specific output format (XML, JSON, text)
    - Convert to unified data structure
    - Handle parsing errors gracefully

    Subclasses must implement:
    - parse(output: str) -> Dict[str, Any]
    """

    @abstractmethod
    def parse(self, output: str) -> Dict[str, Any]:
        """
        Parse tool output into structured data.

        Args:
            output: Raw tool output (stdout)

        Returns:
            Structured data (format varies by tool)

        Raises:
            ValueError: If output is invalid/unparseable

        Example:
            def parse(self, output: str) -> Dict[str, Any]:
                # Parse Nmap XML
                tree = ET.fromstring(output)
                hosts = []
                for host_elem in tree.findall(".//host"):
                    hosts.append({
                        "ip": host_elem.find("address").get("addr"),
                        "ports": [...]
                    })
                return {"hosts": hosts}
        """
        pass
