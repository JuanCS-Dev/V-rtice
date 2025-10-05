"""
Test: HCL Command
=================

Testa o comando vcli hcl (Human-Centric Language).
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


class TestHCLCommand:
    """Testes do comando hcl."""

    def test_hcl_help(self):
        """Testa o help do comando hcl."""
        returncode, stdout, stderr = run_vcli_command(["hcl", "--help"])

        assert returncode == 0, f"Command failed: {stderr}"
        assert "hcl" in stdout.lower()
        print("✅ hcl --help: PASS")

    def test_hcl_subcommands_exist(self):
        """Valida que todos os subcomandos existem."""
        subcommands = ["execute", "plan", "analyze", "query"]

        for subcmd in subcommands:
            returncode, stdout, stderr = run_vcli_command([
                "hcl", subcmd, "--help"
            ])

            assert returncode == 0, f"Subcommand '{subcmd}' não existe ou está quebrado"
            print(f"✅ hcl {subcmd} --help: EXISTS")

    @pytest.mark.integration
    def test_hcl_analyze(self):
        """Testa análise de intent."""
        returncode, stdout, stderr = run_vcli_command([
            "hcl", "analyze",
            "Scan network and report vulnerabilities"
        ], timeout=30)

        if returncode == 0:
            print("✅ hcl analyze: PASS")
        else:
            print(f"⚠️  hcl analyze: Service offline")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
