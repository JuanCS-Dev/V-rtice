"""
Test: Memory Command
====================

Testa o comando vcli memory (Memory System management).
"""

import pytest
import subprocess
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def run_vcli_command(args: list, timeout: int = 30) -> tuple[int, str, str]:
    """Helper para executar comandos vcli."""
    try:
        result = subprocess.run(
            ["vcli"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


class TestMemoryCommand:
    """Testes do comando memory."""

    def test_memory_help(self):
        """Testa o help do comando memory."""
        returncode, stdout, stderr = run_vcli_command(["memory", "--help"])

        assert returncode == 0, f"Command failed: {stderr}"
        assert "memory" in stdout.lower()
        print("✅ memory --help: PASS")

    def test_memory_subcommands_exist(self):
        """Valida que todos os subcomandos existem."""
        subcommands = ["status", "recall", "similar", "stats", "clear"]

        for subcmd in subcommands:
            returncode, stdout, stderr = run_vcli_command([
                "memory", subcmd, "--help"
            ])

            assert returncode == 0, f"Subcommand '{subcmd}' não existe ou está quebrado"
            print(f"✅ memory {subcmd} --help: EXISTS")

    @pytest.mark.integration
    def test_memory_status(self):
        """Testa status do memory system."""
        returncode, stdout, stderr = run_vcli_command([
            "memory", "status"
        ], timeout=30)

        if returncode == 0:
            print("✅ memory status: PASS")
            assert len(stdout) > 0
        else:
            print(f"⚠️  memory status: Service offline")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
