"""
Testes unitários para backend.modules.tegumentar.derme.signature_engine

Testa o SignatureEngine - pattern matching de ameaças conhecidas:
- load(): Carrega signatures de arquivos YAML
- match(): Busca patterns em payloads (regex case-insensitive)
- Lazy loading quando _signatures vazio
- Defaults para severity/action
- Error handling (FileNotFoundError, decode errors)

Padrão Pagani: Signature matching 100%, YAML mocking, regex testing.

EM NOME DE JESUS - PATTERN MATCHING PERFEITO!
"""

from pathlib import Path
import re
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.signature_engine import (
    Signature,
    SignatureEngine,
)


@pytest.fixture
def settings(tmp_path):
    """Settings de teste com diretório temporário."""
    sig_dir = tmp_path / "signatures"
    sig_dir.mkdir()
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
        signature_directory=str(sig_dir),
    )


@pytest.fixture
def engine(settings):
    """SignatureEngine de teste."""
    return SignatureEngine(settings)


@pytest.fixture
def sample_yaml():
    """YAML de teste com signatures."""
    return {
        "signatures": [
            {
                "name": "SQL_INJECTION",
                "pattern": "SELECT.*FROM",
                "severity": "critical",
                "action": "block",
            },
            {
                "name": "XSS_ATTACK",
                "pattern": "<script>",
                "severity": "high",
                "action": "block",
            },
        ]
    }


class TestSignatureDataclass:
    """Testa dataclass Signature."""

    def test_signature_has_required_fields(self):
        """Signature deve ter name, pattern, severity, action."""
        pattern = re.compile(r"test", re.IGNORECASE)
        sig = Signature(
            name="TEST_SIG",
            pattern=pattern,
            severity="high",
            action="block",
        )

        assert sig.name == "TEST_SIG"
        assert sig.pattern is pattern
        assert sig.severity == "high"
        assert sig.action == "block"

    def test_signature_uses_slots(self):
        """Signature deve usar slots para eficiência."""
        pattern = re.compile(r"test")
        sig = Signature(name="TEST", pattern=pattern, severity="low", action="alert")

        # Slots não têm __dict__
        assert not hasattr(sig, "__dict__")


class TestSignatureEngineInitialization:
    """Testa inicialização do SignatureEngine."""

    def test_initializes_with_settings(self, settings):
        """Deve armazenar settings fornecido."""
        engine = SignatureEngine(settings)

        assert engine._settings is settings

    def test_initializes_with_default_settings(self):
        """Deve usar get_settings() quando não fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.signature_engine.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            engine = SignatureEngine()

            mock_get_settings.assert_called_once()
            assert engine._settings is mock_settings

    def test_creates_empty_signatures_dict(self, engine):
        """Deve inicializar com dict de signatures vazio."""
        assert engine._signatures == {}
        assert isinstance(engine._signatures, dict)


class TestLoad:
    """Testa método load() para carregar signatures."""

    def test_raises_file_not_found_when_directory_missing(self, settings):
        """Deve levantar FileNotFoundError quando diretório não existe."""
        settings.signature_directory = "/nonexistent/path"
        engine = SignatureEngine(settings)

        with pytest.raises(FileNotFoundError) as exc_info:
            engine.load()

        assert "/nonexistent/path" in str(exc_info.value)

    def test_loads_signatures_from_yaml_files(self, settings, sample_yaml):
        """Deve carregar signatures de arquivos .yaml."""
        sig_file = Path(settings.signature_directory) / "threats.yaml"
        sig_file.write_text(yaml.dump(sample_yaml), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        assert len(engine._signatures) == 2
        assert "SQL_INJECTION" in engine._signatures
        assert "XSS_ATTACK" in engine._signatures

    def test_compiles_regex_patterns_case_insensitive(self, settings, sample_yaml):
        """Deve compilar patterns com re.IGNORECASE."""
        sig_file = Path(settings.signature_directory) / "threats.yaml"
        sig_file.write_text(yaml.dump(sample_yaml), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        sql_sig = engine._signatures["SQL_INJECTION"]
        # Pattern deve ser case-insensitive
        assert sql_sig.pattern.search("select * from users")
        assert sql_sig.pattern.search("SELECT * FROM users")

    def test_stores_signature_with_all_fields(self, settings, sample_yaml):
        """Deve armazenar signature com name, pattern, severity, action."""
        sig_file = Path(settings.signature_directory) / "threats.yaml"
        sig_file.write_text(yaml.dump(sample_yaml), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        sql_sig = engine._signatures["SQL_INJECTION"]
        assert sql_sig.name == "SQL_INJECTION"
        assert isinstance(sql_sig.pattern, re.Pattern)
        assert sql_sig.severity == "critical"
        assert sql_sig.action == "block"

    def test_uses_default_severity_medium(self, settings):
        """Deve usar severity='medium' quando ausente."""
        yaml_data = {
            "signatures": [
                {
                    "name": "TEST_SIG",
                    "pattern": "test",
                    # severity ausente
                    "action": "alert",
                }
            ]
        }
        sig_file = Path(settings.signature_directory) / "test.yaml"
        sig_file.write_text(yaml.dump(yaml_data), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        assert engine._signatures["TEST_SIG"].severity == "medium"

    def test_uses_default_action_block(self, settings):
        """Deve usar action='block' quando ausente."""
        yaml_data = {
            "signatures": [
                {
                    "name": "TEST_SIG",
                    "pattern": "test",
                    "severity": "low",
                    # action ausente
                }
            ]
        }
        sig_file = Path(settings.signature_directory) / "test.yaml"
        sig_file.write_text(yaml.dump(yaml_data), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        assert engine._signatures["TEST_SIG"].action == "block"

    def test_loads_multiple_yaml_files(self, settings):
        """Deve carregar signatures de múltiplos arquivos .yaml."""
        sig_dir = Path(settings.signature_directory)

        # Arquivo 1
        yaml1 = {"signatures": [{"name": "SIG_1", "pattern": "pattern1"}]}
        (sig_dir / "file1.yaml").write_text(yaml.dump(yaml1), encoding="utf-8")

        # Arquivo 2
        yaml2 = {"signatures": [{"name": "SIG_2", "pattern": "pattern2"}]}
        (sig_dir / "file2.yaml").write_text(yaml.dump(yaml2), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        assert len(engine._signatures) == 2
        assert "SIG_1" in engine._signatures
        assert "SIG_2" in engine._signatures

    def test_skips_non_yaml_files(self, settings):
        """Deve processar apenas arquivos .yaml."""
        sig_dir = Path(settings.signature_directory)

        # Arquivo .yaml válido
        yaml_data = {"signatures": [{"name": "VALID_SIG", "pattern": "test"}]}
        (sig_dir / "valid.yaml").write_text(yaml.dump(yaml_data), encoding="utf-8")

        # Arquivo .txt (deve ser ignorado)
        (sig_dir / "readme.txt").write_text("This is not a yaml file")

        # Arquivo sem extensão (deve ser ignorado)
        (sig_dir / "noext").write_text("signatures: []")

        engine = SignatureEngine(settings)
        engine.load()

        # Deve ter apenas 1 signature do arquivo .yaml
        assert len(engine._signatures) == 1
        assert "VALID_SIG" in engine._signatures

    def test_handles_yaml_without_signatures_key(self, settings):
        """Deve lidar com YAML sem chave 'signatures'."""
        sig_file = Path(settings.signature_directory) / "empty.yaml"
        sig_file.write_text(yaml.dump({"other_key": "value"}), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        # Não deve criar signatures
        assert len(engine._signatures) == 0


class TestMatch:
    """Testa método match() para busca de patterns."""

    def test_lazy_loads_signatures_when_empty(self, settings, sample_yaml):
        """Deve chamar load() quando _signatures vazio."""
        sig_file = Path(settings.signature_directory) / "threats.yaml"
        sig_file.write_text(yaml.dump(sample_yaml), encoding="utf-8")

        engine = SignatureEngine(settings)
        # _signatures ainda vazio

        payload = b"SELECT * FROM users"
        result = engine.match(payload)

        # Deve ter carregado e retornado match
        assert result is not None
        assert result.name == "SQL_INJECTION"

    def test_decodes_payload_as_utf8(self, engine):
        """Deve decodificar payload como UTF-8."""
        engine._signatures["TEST"] = Signature(
            name="TEST",
            pattern=re.compile(r"hello", re.IGNORECASE),
            severity="low",
            action="alert",
        )

        payload = "hello world".encode("utf-8")
        result = engine.match(payload)

        assert result is not None
        assert result.name == "TEST"

    def test_returns_first_matching_signature(self, engine):
        """Deve retornar primeira signature que faz match."""
        engine._signatures["SIG_1"] = Signature(
            name="SIG_1",
            pattern=re.compile(r"attack", re.IGNORECASE),
            severity="high",
            action="block",
        )
        engine._signatures["SIG_2"] = Signature(
            name="SIG_2",
            pattern=re.compile(r"attack.*pattern", re.IGNORECASE),
            severity="critical",
            action="block",
        )

        payload = b"This is an attack pattern"
        result = engine.match(payload)

        # Deve retornar uma das signatures (ordem de dict)
        assert result is not None
        assert result.name in ["SIG_1", "SIG_2"]

    def test_returns_none_when_no_match(self, engine):
        """Deve retornar None quando nenhuma signature faz match."""
        engine._signatures["SQL_INJECTION"] = Signature(
            name="SQL_INJECTION",
            pattern=re.compile(r"SELECT.*FROM", re.IGNORECASE),
            severity="critical",
            action="block",
        )

        payload = b"Normal benign traffic"
        result = engine.match(payload)

        assert result is None

    def test_case_insensitive_matching(self, engine):
        """Deve fazer matching case-insensitive."""
        engine._signatures["XSS"] = Signature(
            name="XSS",
            pattern=re.compile(r"<script>", re.IGNORECASE),
            severity="high",
            action="block",
        )

        # Diferentes capitalizações
        assert engine.match(b"<script>alert()</script>") is not None
        assert engine.match(b"<SCRIPT>alert()</SCRIPT>") is not None
        assert engine.match(b"<ScRiPt>alert()</ScRiPt>") is not None

    def test_handles_decode_errors_gracefully(self, engine):
        """Deve lidar com erros de decodificação sem crash."""
        engine._signatures["TEST"] = Signature(
            name="TEST",
            pattern=re.compile(r"test", re.IGNORECASE),
            severity="low",
            action="alert",
        )

        # Payload com bytes inválidos UTF-8
        payload = b"\xff\xfe invalid utf-8"

        # Não deve crashear, deve retornar None
        result = engine.match(payload)

        # errors="ignore" deve permitir decodificação parcial
        # mas se pattern não encontrado, retorna None
        assert result is None

    def test_ignores_invalid_bytes_in_payload(self, engine):
        """Deve usar errors='ignore' na decodificação."""
        engine._signatures["PATTERN"] = Signature(
            name="PATTERN",
            pattern=re.compile(r"valid_text", re.IGNORECASE),
            severity="medium",
            action="block",
        )

        # Payload com bytes inválidos MAS contendo texto válido
        payload = b"\xff\xfe valid_text here \xfe\xff"
        result = engine.match(payload)

        # Deve ter encontrado "valid_text" ignorando bytes inválidos
        assert result is not None
        assert result.name == "PATTERN"

    def test_searches_all_signatures_in_order(self, engine):
        """Deve buscar em todas as signatures até encontrar match."""
        engine._signatures["NO_MATCH_1"] = Signature(
            name="NO_MATCH_1",
            pattern=re.compile(r"zzz", re.IGNORECASE),
            severity="low",
            action="alert",
        )
        engine._signatures["MATCH"] = Signature(
            name="MATCH",
            pattern=re.compile(r"attack", re.IGNORECASE),
            severity="high",
            action="block",
        )
        engine._signatures["NO_MATCH_2"] = Signature(
            name="NO_MATCH_2",
            pattern=re.compile(r"xxx", re.IGNORECASE),
            severity="low",
            action="alert",
        )

        payload = b"This is an attack"
        result = engine.match(payload)

        # Deve ter encontrado "MATCH"
        assert result is not None
        assert result.name == "MATCH"


class TestIntegration:
    """Testes de integração load() + match()."""

    def test_full_workflow_load_and_match(self, settings):
        """Deve carregar YAML e fazer matching corretamente."""
        sig_dir = Path(settings.signature_directory)
        yaml_data = {
            "signatures": [
                {
                    "name": "SQL_INJECTION",
                    "pattern": "SELECT.*FROM.*WHERE",
                    "severity": "critical",
                    "action": "block",
                },
                {
                    "name": "PATH_TRAVERSAL",
                    "pattern": "\\.\\./",
                    "severity": "high",
                    "action": "block",
                },
            ]
        }
        (sig_dir / "attacks.yaml").write_text(yaml.dump(yaml_data), encoding="utf-8")

        engine = SignatureEngine(settings)
        engine.load()

        # Teste SQL Injection
        sql_payload = b"SELECT * FROM users WHERE id=1"
        result = engine.match(sql_payload)
        assert result is not None
        assert result.name == "SQL_INJECTION"
        assert result.severity == "critical"

        # Teste Path Traversal
        path_payload = b"GET /../etc/passwd HTTP/1.1"
        result = engine.match(path_payload)
        assert result is not None
        assert result.name == "PATH_TRAVERSAL"
        assert result.severity == "high"

        # Teste tráfego normal (sem match)
        normal_payload = b"GET /index.html HTTP/1.1"
        result = engine.match(normal_payload)
        assert result is None
