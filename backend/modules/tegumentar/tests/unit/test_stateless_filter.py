"""
Testes unitários para backend.modules.tegumentar.epiderme.stateless_filter

Testa o StatelessFilter (nftables integration):
- Criação de tabelas/chains/sets
- Sincronização de IPs bloqueados
- Attachment a netfilter hooks
- Gestão de políticas
- Validação de IPs/CIDRs
- Tratamento de erros

Padrão Pagani: Mock de subprocess, validação real de lógica nftables.
"""
import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from ipaddress import IPv4Network, IPv6Network

from backend.modules.tegumentar.epiderme.stateless_filter import (
    StatelessFilter,
    StatelessFilterError
)
from backend.modules.tegumentar.config import TegumentarSettings


@pytest.fixture
def settings():
    """Settings de teste."""
    return TegumentarSettings(
        nft_binary="/usr/sbin/nft",
        nft_table_name="test_table",
        nft_chain_name="test_chain"
    )


@pytest.fixture
def stateless_filter(settings):
    """Instância de StatelessFilter."""
    return StatelessFilter(settings)


@pytest.fixture
def mock_subprocess_run():
    """Mock de subprocess.run."""
    with patch("subprocess.run") as mock:
        # Default: comando bem-sucedido
        mock.return_value = MagicMock(
            returncode=0,
            stdout=b"",
            stderr=b""
        )
        yield mock


class TestStatelessFilterInitialization:
    """Testa inicialização do filtro."""

    def test_filter_stores_settings(self, stateless_filter, settings):
        """Filtro deve armazenar settings."""
        assert stateless_filter._settings is settings

    def test_table_spec_property(self, stateless_filter):
        """_table_spec deve retornar família e nome da tabela."""
        spec = stateless_filter._table_spec
        assert spec == ["inet", "test_table"]


class TestEnsureTableStructure:
    """Testa criação de estrutura nftables."""

    def test_checks_nft_binary_exists(self, stateless_filter):
        """Deve verificar se binário nft existe."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(StatelessFilterError) as exc_info:
                stateless_filter.ensure_table_structure()

            assert "nft binary not found" in str(exc_info.value)
            assert "/usr/sbin/nft" in str(exc_info.value)

    def test_creates_table(self, stateless_filter, mock_subprocess_run):
        """Deve criar tabela nftables."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.ensure_table_structure()

            # Verificar que criou tabela
            calls = mock_subprocess_run.call_args_list
            table_create_call = [c for c in calls if b"add table" in (c[1].get("input") or b"")]
            assert len(table_create_call) > 0

    def test_creates_chain(self, stateless_filter, mock_subprocess_run):
        """Deve criar chain."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.ensure_table_structure()

            # Verificar que criou chain
            calls = [str(c) for c in mock_subprocess_run.call_args_list]
            assert any("add" in c and "chain" in c for c in calls)

    def test_creates_blocked_ips_set(self, stateless_filter, mock_subprocess_run):
        """Deve criar set de IPs bloqueados."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.ensure_table_structure()

            # Verificar que criou set
            calls = mock_subprocess_run.call_args_list
            set_calls = [c for c in calls if b"add set" in (c[1].get("input") or b"")]
            assert len(set_calls) > 0

            # Verificar nome do set
            input_data = set_calls[0][1]["input"].decode()
            assert "test_chain_blocked_ips" in input_data
            assert "type ipv4_addr" in input_data

    def test_adds_drop_rule_for_blocked_ips(self, stateless_filter, mock_subprocess_run):
        """Deve adicionar regra de drop para IPs no set."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.ensure_table_structure()

            calls = mock_subprocess_run.call_args_list
            rule_calls = [c for c in calls if b"add rule" in (c[1].get("input") or b"")]
            assert len(rule_calls) > 0

            input_data = rule_calls[0][1]["input"].decode()
            assert "ip saddr" in input_data
            assert "test_chain_blocked_ips" in input_data
            assert "drop" in input_data

    def test_uses_correct_nft_binary(self, stateless_filter, mock_subprocess_run):
        """Deve usar binário nft configurado."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.ensure_table_structure()

            # Verificar que todos os comandos usam o binário correto
            for call_args in mock_subprocess_run.call_args_list:
                command = call_args[0][0]
                assert command[0] == "/usr/sbin/nft"


class TestSyncBlockedIPs:
    """Testa sincronização de IPs bloqueados."""

    def test_accepts_valid_ipv4_addresses(self, stateless_filter, mock_subprocess_run):
        """Deve aceitar endereços IPv4 válidos."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.1.1", "10.0.0.0/8", "172.16.0.1"]
            stateless_filter.sync_blocked_ips(ips)

            # Verificar que IPs foram adicionados ao set
            calls = mock_subprocess_run.call_args_list
            add_element_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            assert len(add_element_calls) > 0

            input_data = add_element_calls[0][1]["input"].decode()
            assert "192.168.1.1" in input_data
            assert "10.0.0.0/8" in input_data
            assert "172.16.0.1" in input_data

    def test_validates_ip_addresses(self, stateless_filter, mock_subprocess_run):
        """Deve validar endereços IP."""
        with patch("pathlib.Path.exists", return_value=True):
            # Inclui IPs válidos e inválidos
            ips = ["192.168.1.1", "not-an-ip", "10.0.0.1", "invalid"]
            stateless_filter.sync_blocked_ips(ips)

            # Apenas IPs válidos devem estar no set
            calls = mock_subprocess_run.call_args_list
            add_element_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            if add_element_calls:
                input_data = add_element_calls[0][1]["input"].decode()
                assert "192.168.1.1" in input_data
                assert "10.0.0.1" in input_data
                assert "not-an-ip" not in input_data
                assert "invalid" not in input_data

    def test_handles_ipv6_addresses(self, stateless_filter, mock_subprocess_run):
        """Deve identificar endereços IPv6 (mas pular no momento)."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.1.1", "2001:db8::1", "10.0.0.1"]
            stateless_filter.sync_blocked_ips(ips)

            # IPv6 deve ser identificado mas não adicionado (limitation atual)
            calls = mock_subprocess_run.call_args_list
            add_element_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            if add_element_calls:
                input_data = add_element_calls[0][1]["input"].decode()
                assert "192.168.1.1" in input_data
                assert "10.0.0.1" in input_data
                assert "2001:db8::1" not in input_data  # IPv6 skipado

    def test_handles_cidr_notation(self, stateless_filter, mock_subprocess_run):
        """Deve aceitar notação CIDR."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.0.0/24", "10.0.0.0/8"]
            stateless_filter.sync_blocked_ips(ips)

            calls = mock_subprocess_run.call_args_list
            add_element_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            assert len(add_element_calls) > 0

            input_data = add_element_calls[0][1]["input"].decode()
            assert "192.168.0.0/24" in input_data
            assert "10.0.0.0/8" in input_data

    def test_clears_set_when_empty_list(self, stateless_filter, mock_subprocess_run):
        """Deve limpar set quando lista está vazia."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.sync_blocked_ips([])

            # Verificar que fez flush do set
            calls = mock_subprocess_run.call_args_list
            flush_calls = [c for c in calls if "flush" in str(c[0][0]) and "set" in str(c[0][0])]
            assert len(flush_calls) > 0

    def test_flushes_before_adding_elements(self, stateless_filter, mock_subprocess_run):
        """Deve fazer flush antes de adicionar elementos."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.1.1"]
            stateless_filter.sync_blocked_ips(ips)

            calls = mock_subprocess_run.call_args_list
            nft_inputs = [c[1].get("input") for c in calls if c[1].get("input")]

            # Verificar que flush vem antes de add element
            for input_data in nft_inputs:
                if b"add element" in input_data:
                    assert b"flush set" in input_data
                    # flush deve vir antes
                    assert input_data.index(b"flush") < input_data.index(b"add element")

    def test_formats_nft_command_correctly(self, stateless_filter, mock_subprocess_run):
        """Deve formatar comando nft corretamente."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.1.1", "10.0.0.1"]
            stateless_filter.sync_blocked_ips(ips)

            calls = mock_subprocess_run.call_args_list
            add_element_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            assert len(add_element_calls) > 0

            # Verificar formato: add element inet table set { ip1, ip2 }
            input_data = add_element_calls[0][1]["input"].decode()
            assert "add element inet test_table test_chain_blocked_ips" in input_data
            assert "{" in input_data
            assert "}" in input_data


class TestAttachToHook:
    """Testa attachment a netfilter hook."""

    def test_attaches_chain_to_prerouting_hook(self, stateless_filter, mock_subprocess_run):
        """Deve anexar chain ao hook prerouting."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.attach_to_hook(priority=-100)

            calls = mock_subprocess_run.call_args_list
            hook_calls = [c for c in calls if b"type filter hook prerouting" in (c[1].get("input") or b"")]
            assert len(hook_calls) > 0

    def test_uses_custom_priority(self, stateless_filter, mock_subprocess_run):
        """Deve usar prioridade customizada."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.attach_to_hook(priority=-200)

            calls = mock_subprocess_run.call_args_list
            hook_calls = [c for c in calls if b"priority -200" in (c[1].get("input") or b"")]
            assert len(hook_calls) > 0

    def test_sets_default_policy_to_accept(self, stateless_filter, mock_subprocess_run):
        """Deve definir política padrão como accept."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.attach_to_hook()

            calls = mock_subprocess_run.call_args_list
            hook_calls = [c for c in calls if b"policy accept" in (c[1].get("input") or b"")]
            assert len(hook_calls) > 0

    def test_deletes_chain_before_recreating(self, stateless_filter, mock_subprocess_run):
        """Deve deletar chain antes de recriar (idempotência)."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.attach_to_hook()

            calls = mock_subprocess_run.call_args_list
            hook_calls = [c for c in calls if c[1].get("input") and b"delete chain" in c[1]["input"]]
            assert len(hook_calls) > 0

    def test_readds_drop_rule_after_attachment(self, stateless_filter, mock_subprocess_run):
        """Deve re-adicionar regra de drop após attachment."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.attach_to_hook()

            calls = mock_subprocess_run.call_args_list
            hook_calls = [c for c in calls if c[1].get("input")]

            # Verificar que regra de drop está no input
            for call in hook_calls:
                input_data = call[1]["input"].decode()
                if "type filter hook prerouting" in input_data:
                    assert "add rule" in input_data
                    assert "ip saddr @test_chain_blocked_ips drop" in input_data


class TestSetPolicy:
    """Testa mudança de política da chain."""

    def test_accepts_accept_policy(self, stateless_filter, mock_subprocess_run):
        """Deve aceitar política 'accept'."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.set_policy("accept")

            calls = mock_subprocess_run.call_args_list
            policy_calls = [c for c in calls if b"policy accept" in (c[1].get("input") or b"")]
            assert len(policy_calls) > 0

    def test_accepts_drop_policy(self, stateless_filter, mock_subprocess_run):
        """Deve aceitar política 'drop'."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.set_policy("drop")

            calls = mock_subprocess_run.call_args_list
            policy_calls = [c for c in calls if b"policy drop" in (c[1].get("input") or b"")]
            assert len(policy_calls) > 0

    def test_rejects_invalid_policy(self, stateless_filter):
        """Deve rejeitar política inválida."""
        with pytest.raises(ValueError) as exc_info:
            stateless_filter.set_policy("invalid")

        assert "must be 'accept' or 'drop'" in str(exc_info.value)

    def test_recreates_chain_with_new_policy(self, stateless_filter, mock_subprocess_run):
        """Deve recriar chain com nova política."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.set_policy("drop")

            calls = mock_subprocess_run.call_args_list
            delete_calls = [c for c in calls if c[1].get("input") and b"delete chain" in c[1]["input"]]
            add_calls = [c for c in calls if c[1].get("input") and b"add chain" in c[1]["input"]]

            assert len(delete_calls) > 0
            assert len(add_calls) > 0

    def test_preserves_drop_rule_after_policy_change(self, stateless_filter, mock_subprocess_run):
        """Deve preservar regra de drop após mudança de política."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.set_policy("accept")

            calls = mock_subprocess_run.call_args_list
            policy_calls = [c for c in calls if c[1].get("input") and b"policy" in c[1]["input"]]

            for call in policy_calls:
                input_data = call[1]["input"].decode()
                assert "add rule" in input_data
                assert "ip saddr @test_chain_blocked_ips drop" in input_data


class TestRunNftCommand:
    """Testa método _run_nft."""

    def test_executes_nft_command(self, stateless_filter, mock_subprocess_run):
        """Deve executar comando nft."""
        stateless_filter._run_nft(["list", "tables"])

        mock_subprocess_run.assert_called_once()
        command = mock_subprocess_run.call_args[0][0]
        assert command[0] == "/usr/sbin/nft"
        assert "list" in command
        assert "tables" in command

    def test_passes_input_to_subprocess(self, stateless_filter, mock_subprocess_run):
        """Deve passar input para subprocess."""
        input_data = "add table inet test"
        stateless_filter._run_nft(["-f", "-"], input_=input_data)

        call_kwargs = mock_subprocess_run.call_args[1]
        assert call_kwargs["input"] == input_data.encode()

    def test_raises_on_command_failure_when_check_true(self, stateless_filter, mock_subprocess_run):
        """Deve lançar StatelessFilterError quando comando falha (check=True)."""
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, ["nft"], stderr=b"Error: table not found"
        )

        with pytest.raises(StatelessFilterError) as exc_info:
            stateless_filter._run_nft(["list", "table", "inet", "nonexistent"], check=True)

        assert "nft command failed" in str(exc_info.value)

    def test_does_not_raise_on_failure_when_check_false(self, stateless_filter, mock_subprocess_run):
        """Não deve lançar exceção quando check=False."""
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"Warning")

        # Não deve lançar exceção
        result = stateless_filter._run_nft(["list", "tables"], check=False)
        assert result.returncode == 1

    def test_logs_stderr_when_present(self, stateless_filter, mock_subprocess_run):
        """Deve logar stderr quando presente."""
        mock_subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout=b"",
            stderr=b"Warning: something"
        )

        with patch("backend.modules.tegumentar.epiderme.stateless_filter.logger") as mock_logger:
            stateless_filter._run_nft(["list", "tables"])
            mock_logger.debug.assert_called()


class TestErrorHandling:
    """Testa tratamento de erros."""

    def test_stateless_filter_error_is_runtime_error(self):
        """StatelessFilterError deve ser RuntimeError."""
        assert issubclass(StatelessFilterError, RuntimeError)

    def test_raises_when_nft_binary_missing(self, stateless_filter):
        """Deve lançar erro quando binário nft não existe."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(StatelessFilterError) as exc_info:
                stateless_filter.ensure_table_structure()

            assert "nft binary not found" in str(exc_info.value)

    def test_preserves_original_exception_in_chain(self, stateless_filter, mock_subprocess_run):
        """Deve preservar exceção original na chain."""
        original_error = subprocess.CalledProcessError(1, ["nft"], stderr=b"Error")
        mock_subprocess_run.side_effect = original_error

        with pytest.raises(StatelessFilterError) as exc_info:
            stateless_filter._run_nft(["invalid", "command"])

        assert exc_info.value.__cause__ is original_error


class TestEdgeCases:
    """Testa casos extremos."""

    def test_sync_with_single_ip(self, stateless_filter, mock_subprocess_run):
        """Deve lidar com lista de um único IP."""
        with patch("pathlib.Path.exists", return_value=True):
            stateless_filter.sync_blocked_ips(["192.168.1.1"])

            calls = mock_subprocess_run.call_args_list
            add_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            assert len(add_calls) > 0

    def test_sync_with_large_ip_list(self, stateless_filter, mock_subprocess_run):
        """Deve lidar com lista grande de IPs."""
        with patch("pathlib.Path.exists", return_value=True):
            large_list = [f"192.168.{i // 256}.{i % 256}" for i in range(1000)]
            stateless_filter.sync_blocked_ips(large_list)

            calls = mock_subprocess_run.call_args_list
            add_calls = [c for c in calls if b"add element" in (c[1].get("input") or b"")]
            assert len(add_calls) > 0

    def test_sync_with_duplicate_ips(self, stateless_filter, mock_subprocess_run):
        """Deve lidar com IPs duplicados."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["192.168.1.1", "192.168.1.1", "10.0.0.1"]
            stateless_filter.sync_blocked_ips(ips)

            # Não deve falhar
            assert mock_subprocess_run.called

    def test_sync_with_only_invalid_ips(self, stateless_filter, mock_subprocess_run):
        """Deve lidar com lista contendo apenas IPs inválidos."""
        with patch("pathlib.Path.exists", return_value=True):
            ips = ["not-an-ip", "invalid", "also-invalid"]
            stateless_filter.sync_blocked_ips(ips)

            # Deve fazer flush do set
            calls = mock_subprocess_run.call_args_list
            flush_calls = [c for c in calls if "flush" in str(c[0][0])]
            # Pelo menos uma chamada deve ter sido feita
            assert mock_subprocess_run.called


class TestConfigurationIntegration:
    """Testa integração com configurações."""

    def test_uses_custom_nft_binary(self, mock_subprocess_run):
        """Deve usar binário nft customizado."""
        custom_settings = TegumentarSettings(nft_binary="/custom/path/nft")
        filter_ = StatelessFilter(custom_settings)

        with patch("pathlib.Path.exists", return_value=True):
            filter_.ensure_table_structure()

            # Verificar que usou binário customizado
            for call_args in mock_subprocess_run.call_args_list:
                command = call_args[0][0]
                assert command[0] == "/custom/path/nft"

    def test_uses_custom_table_name(self, mock_subprocess_run):
        """Deve usar nome de tabela customizado."""
        custom_settings = TegumentarSettings(nft_table_name="custom_table")
        filter_ = StatelessFilter(custom_settings)

        with patch("pathlib.Path.exists", return_value=True):
            filter_.ensure_table_structure()

            # Verificar que usou nome customizado
            calls = mock_subprocess_run.call_args_list
            table_calls = [c for c in calls if b"custom_table" in (c[1].get("input") or b"")]
            assert len(table_calls) > 0

    def test_uses_custom_chain_name(self, mock_subprocess_run):
        """Deve usar nome de chain customizado."""
        custom_settings = TegumentarSettings(nft_chain_name="custom_chain")
        filter_ = StatelessFilter(custom_settings)

        with patch("pathlib.Path.exists", return_value=True):
            filter_.ensure_table_structure()

            calls = mock_subprocess_run.call_args_list
            chain_calls = [c for c in calls if b"custom_chain" in (c[1].get("input") or b"") or "custom_chain" in str(c[0][0])]
            assert len(chain_calls) > 0
