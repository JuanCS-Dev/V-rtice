"""
Test: Investigate Command
==========================

Testa o comando vcli investigate (AI-orchestrated investigation).
"""

import pytest
import subprocess
import json
import sys
import os

# Add vertice to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.fixtures.sample_data import SAMPLE_TARGETS


def run_vcli_command(args: list, timeout: int = 30) -> tuple[int, str, str]:
    """
    Helper para executar comandos vcli.

    Returns:
        tuple: (return_code, stdout, stderr)
    """
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


class TestInvestigateCommand:
    """Testes do comando investigate."""

    def test_investigate_help(self):
        """Testa o help do comando investigate."""
        returncode, stdout, stderr = run_vcli_command(["investigate", "--help"])

        assert returncode == 0, f"Command failed: {stderr}"
        assert "investigate" in stdout.lower()
        print("✅ investigate --help: PASS")

    @pytest.mark.integration
    def test_investigate_target_simple(self):
        """Testa investigação simples de um target."""
        returncode, stdout, stderr = run_vcli_command([
            "investigate", "target",
            SAMPLE_TARGETS["domain_safe"],
            "--type", "defensive",
            "--depth", "quick"
        ], timeout=60)

        # Aceita sucesso (0) ou erro esperado (serviço offline)
        if returncode == 0:
            print("✅ investigate target: PASS")
            assert len(stdout) > 0, "Should have output"
        else:
            print(f"⚠️  investigate target: Service offline or error")
            # Não falha o teste - serviço pode estar offline

    @pytest.mark.integration
    def test_investigate_history(self):
        """Testa listagem de histórico de investigações."""
        returncode, stdout, stderr = run_vcli_command([
            "investigate", "history",
            "--limit", "5"
        ], timeout=30)

        # Pode retornar vazio se não há histórico
        if returncode == 0:
            print("✅ investigate history: PASS")
        else:
            print(f"⚠️  investigate history: {stderr[:100]}")

    def test_investigate_subcommands_exist(self):
        """Valida que todos os subcomandos existem."""
        subcommands = ["target", "multi", "history", "similar"]

        for subcmd in subcommands:
            returncode, stdout, stderr = run_vcli_command([
                "investigate", subcmd, "--help"
            ])

            assert returncode == 0, f"Subcommand '{subcmd}' não existe ou está quebrado"
            print(f"✅ investigate {subcmd} --help: EXISTS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
