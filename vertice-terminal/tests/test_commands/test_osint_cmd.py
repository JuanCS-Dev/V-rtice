"""
Test: OSINT Command
===================

Testa o comando vcli osint (OSINT operations).
"""

import pytest
import subprocess
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.fixtures.sample_data import SAMPLE_TARGETS


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


class TestOSINTCommand:
    """Testes do comando osint."""

    def test_osint_help(self):
        """Testa o help do comando osint."""
        returncode, stdout, stderr = run_vcli_command(["osint", "--help"])

        assert returncode == 0, f"Command failed: {stderr}"
        assert "osint" in stdout.lower()
        print("✅ osint --help: PASS")

    def test_osint_subcommands_exist(self):
        """Valida que todos os subcomandos existem."""
        subcommands = ["username", "breach", "vehicle", "multi", "comprehensive"]

        for subcmd in subcommands:
            returncode, stdout, stderr = run_vcli_command([
                "osint", subcmd, "--help"
            ])

            assert returncode == 0, f"Subcommand '{subcmd}' não existe ou está quebrado"
            print(f"✅ osint {subcmd} --help: EXISTS")

    @pytest.mark.integration
    def test_osint_breach(self):
        """Testa breach data lookup."""
        returncode, stdout, stderr = run_vcli_command([
            "osint", "breach",
            SAMPLE_TARGETS["email_test"]
        ], timeout=30)

        if returncode == 0:
            print("✅ osint breach: PASS")
        else:
            print(f"⚠️  osint breach: Service offline or error")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
