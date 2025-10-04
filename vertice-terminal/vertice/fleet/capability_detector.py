"""
🔍 Capability Detector - Detecta capabilities de endpoints

Detecta:
- OS e versão
- Ferramentas de segurança instaladas
- Python version, PowerShell, etc
- Disk space, RAM, CPU cores
"""

from typing import Dict, Any, List
import platform
import shutil


class CapabilityDetector:
    """
    Detecta capabilities de um endpoint
    """

    @staticmethod
    def detect_local() -> Dict[str, Any]:
        """
        Detecta capabilities do endpoint local

        Returns:
            Dicionário com capabilities
        """
        capabilities = {}

        # OS Info
        capabilities["os"] = {
            "type": platform.system().lower(),
            "version": platform.version(),
            "release": platform.release(),
            "machine": platform.machine(),
        }

        # Python
        capabilities["python"] = {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        }

        # Ferramentas de segurança
        tools = {}

        # Check common security tools
        security_tools = [
            "nmap",
            "tcpdump",
            "wireshark",
            "volatility",
            "yara",
            "clamav",
            "osquery",
        ]

        for tool in security_tools:
            tools[tool] = shutil.which(tool) is not None

        capabilities["security_tools"] = tools

        # Comandos de sistema
        system_commands = {}

        # Windows commands
        if capabilities["os"]["type"] == "windows":
            windows_commands = [
                "powershell.exe",
                "cmd.exe",
                "wmic.exe",
                "netstat.exe",
                "tasklist.exe",
            ]
            for cmd in windows_commands:
                system_commands[cmd] = shutil.which(cmd) is not None

        # Linux/macOS commands
        else:
            unix_commands = [
                "bash",
                "sh",
                "ps",
                "netstat",
                "ss",
                "lsof",
            ]
            for cmd in unix_commands:
                system_commands[cmd] = shutil.which(cmd) is not None

        capabilities["system_commands"] = system_commands

        return capabilities

    @staticmethod
    def get_required_capabilities(query_type: str) -> List[str]:
        """
        Retorna capabilities necessárias para tipo de query

        Args:
            query_type: Tipo de query (process, network, file, etc)

        Returns:
            Lista de capabilities necessárias
        """
        requirements = {
            "process": ["ps", "tasklist.exe"],
            "network": ["netstat", "ss", "netstat.exe"],
            "file": ["find", "where.exe"],
            "registry": ["reg.exe"],  # Windows only
        }

        return requirements.get(query_type, [])

    @staticmethod
    def can_execute_query(
        capabilities: Dict[str, Any],
        query_type: str
    ) -> bool:
        """
        Verifica se endpoint pode executar query

        Args:
            capabilities: Capabilities do endpoint
            query_type: Tipo de query

        Returns:
            True se pode executar, False caso contrário
        """
        required = CapabilityDetector.get_required_capabilities(query_type)

        if not required:
            return True

        # Verifica se pelo menos uma das ferramentas necessárias está disponível
        system_commands = capabilities.get("system_commands", {})

        for req in required:
            if system_commands.get(req, False):
                return True

        return False
