"""
Testes unitários para backend.modules.tegumentar.derme.ml.feature_extractor

Testa o FeatureExtractor - transformação de observações em vetores numéricos:
- FeatureVector: dataclass com 7 features, as_list()
- transform(): payload_length, entropy, ratios, tcp_flag_score, interval
- _shannon_entropy(): cálculo de entropia de Shannon (bits)
- _tcp_flag_score(): scoring de flags TCP (SYN, FIN, PSH)

Padrão Pagani: ML feature engineering 100%, matemática correta.

EM NOME DE JESUS - FEATURE EXTRACTION PERFEITA!
"""

import math

import pytest

from backend.modules.tegumentar.derme.ml.feature_extractor import (
    FeatureExtractor,
    FeatureVector,
)
from backend.modules.tegumentar.derme.stateful_inspector import FlowObservation


@pytest.fixture
def extractor():
    """FeatureExtractor de teste."""
    return FeatureExtractor()


@pytest.fixture
def observation():
    """FlowObservation de teste."""
    return FlowObservation(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        src_port=54321,
        dst_port=443,
        protocol="TCP",
        flags="ACK",
        payload_size=1024,
        timestamp=1000.0,
    )


class TestFeatureVector:
    """Testa dataclass FeatureVector."""

    def test_feature_vector_has_all_fields(self):
        """FeatureVector deve ter 7 campos."""
        fv = FeatureVector(
            payload_length=100,
            entropy=4.5,
            printable_ratio=0.8,
            digit_ratio=0.2,
            average_byte_value=65.3,
            tcp_flag_score=1.0,
            inter_packet_interval=0.05,
        )

        assert fv.payload_length == 100
        assert fv.entropy == 4.5
        assert fv.printable_ratio == 0.8
        assert fv.digit_ratio == 0.2
        assert fv.average_byte_value == 65.3
        assert fv.tcp_flag_score == 1.0
        assert fv.inter_packet_interval == 0.05

    def test_as_list_returns_float_list(self):
        """as_list() deve retornar lista de 7 floats."""
        fv = FeatureVector(
            payload_length=100,
            entropy=4.5,
            printable_ratio=0.8,
            digit_ratio=0.2,
            average_byte_value=65.3,
            tcp_flag_score=1.0,
            inter_packet_interval=0.05,
        )

        result = fv.as_list()

        assert isinstance(result, list)
        assert len(result) == 7
        assert result == [100.0, 4.5, 0.8, 0.2, 65.3, 1.0, 0.05]
        assert all(isinstance(x, float) for x in result)

    def test_as_list_converts_int_to_float(self):
        """as_list() deve converter payload_length (int) para float."""
        fv = FeatureVector(
            payload_length=42,
            entropy=0.0,
            printable_ratio=0.0,
            digit_ratio=0.0,
            average_byte_value=0.0,
            tcp_flag_score=0.0,
            inter_packet_interval=0.0,
        )

        result = fv.as_list()

        # Primeiro elemento deve ser float(42)
        assert result[0] == 42.0
        assert isinstance(result[0], float)

    def test_feature_vector_uses_slots(self):
        """FeatureVector deve usar slots para eficiência."""
        fv = FeatureVector(
            payload_length=1,
            entropy=0.0,
            printable_ratio=0.0,
            digit_ratio=0.0,
            average_byte_value=0.0,
            tcp_flag_score=0.0,
            inter_packet_interval=0.0,
        )

        # Slots não têm __dict__
        assert not hasattr(fv, "__dict__")


class TestFeatureExtractorInitialization:
    """Testa inicialização do FeatureExtractor."""

    def test_initializes_with_last_timestamp_none(self, extractor):
        """Deve inicializar _last_timestamp como None."""
        assert extractor._last_timestamp is None


class TestTransform:
    """Testa método transform() para extração de features."""

    def test_returns_feature_vector(self, extractor, observation):
        """Deve retornar FeatureVector."""
        payload = b"Hello World"
        result = extractor.transform(observation, payload)

        assert isinstance(result, FeatureVector)

    def test_calculates_payload_length(self, extractor, observation):
        """payload_length deve ser len(payload)."""
        payload = b"Test payload with 30 characters"
        result = extractor.transform(observation, payload)

        assert result.payload_length == len(payload)
        assert result.payload_length == 31

    def test_calculates_entropy(self, extractor, observation):
        """entropy deve usar _shannon_entropy()."""
        # Payload uniforme (baixa entropia)
        payload = b"aaaaaaaaaa"
        result = extractor.transform(observation, payload)

        # Entropia de sequência uniforme é 0.0
        assert result.entropy == 0.0

    def test_calculates_printable_ratio(self, extractor, observation):
        """printable_ratio deve ser proporção de bytes printable (32-126)."""
        # "ABC" = 3 printable, "\x01\x02" = 2 non-printable
        payload = b"ABC\x01\x02"
        result = extractor.transform(observation, payload)

        # 3/5 = 0.6
        assert result.printable_ratio == 0.6

    def test_calculates_digit_ratio(self, extractor, observation):
        """digit_ratio deve ser proporção de dígitos (48-57)."""
        # "123ABC" = 3 digits, 3 letters
        payload = b"123ABC"
        result = extractor.transform(observation, payload)

        # 3/6 = 0.5
        assert result.digit_ratio == 0.5

    def test_calculates_average_byte_value(self, extractor, observation):
        """average_byte_value deve ser média dos valores dos bytes."""
        # bytes([65, 66, 67]) = "ABC", média = (65+66+67)/3 = 66.0
        payload = b"ABC"
        result = extractor.transform(observation, payload)

        assert result.average_byte_value == 66.0

    def test_calculates_tcp_flag_score(self, extractor, observation):
        """tcp_flag_score deve usar _tcp_flag_score()."""
        observation.flags = "S"  # SYN sem ACK = score 1.0
        payload = b"test"
        result = extractor.transform(observation, payload)

        assert result.tcp_flag_score == 1.0

    def test_calculates_inter_packet_interval_first_packet(
        self, extractor, observation
    ):
        """inter_packet_interval deve ser 0.0 para primeiro pacote."""
        # _last_timestamp é None inicialmente
        payload = b"first packet"
        result = extractor.transform(observation, payload)

        # Primeiro pacote = intervalo 0.0
        assert result.inter_packet_interval == 0.0

    def test_calculates_inter_packet_interval_subsequent_packets(
        self, extractor, observation
    ):
        """inter_packet_interval deve ser diferença de timestamps."""
        # Primeiro pacote (timestamp=1000.0)
        observation.timestamp = 1000.0
        extractor.transform(observation, b"first")

        # Segundo pacote (timestamp=1000.5)
        observation.timestamp = 1000.5
        result = extractor.transform(observation, b"second")

        # Intervalo = 1000.5 - 1000.0 = 0.5
        assert result.inter_packet_interval == 0.5

    def test_updates_last_timestamp(self, extractor, observation):
        """Deve atualizar _last_timestamp após transform()."""
        observation.timestamp = 1234.5
        extractor.transform(observation, b"test")

        assert extractor._last_timestamp == 1234.5

    def test_handles_empty_payload(self, extractor, observation):
        """Deve lidar com payload vazio sem crash."""
        payload = b""
        result = extractor.transform(observation, payload)

        assert result.payload_length == 0
        assert result.entropy == 0.0
        assert result.printable_ratio == 0.0
        assert result.digit_ratio == 0.0
        assert result.average_byte_value == 0.0  # sum([]) / max(0, 1) = 0/1 = 0


class TestShannonEntropy:
    """Testa método _shannon_entropy() para cálculo de entropia."""

    def test_returns_zero_for_empty_data(self):
        """Deve retornar 0.0 para dados vazios."""
        result = FeatureExtractor._shannon_entropy(b"")

        assert result == 0.0

    def test_returns_zero_for_uniform_data(self):
        """Deve retornar 0.0 para dados uniformes (1 símbolo)."""
        result = FeatureExtractor._shannon_entropy(b"aaaaaaaaaa")

        # Entropia de distribuição uniforme (p=1) = -1 * log2(1) = 0
        assert result == 0.0

    def test_calculates_entropy_for_binary_distribution(self):
        """Deve calcular entropia para distribuição 50/50."""
        # "aabb" = 2x'a', 2x'b', p(a)=0.5, p(b)=0.5
        # H = -0.5*log2(0.5) - 0.5*log2(0.5) = -0.5*(-1) - 0.5*(-1) = 1.0
        result = FeatureExtractor._shannon_entropy(b"aabb")

        assert abs(result - 1.0) < 0.001  # ~1.0 bit

    def test_calculates_entropy_for_random_data(self):
        """Deve calcular entropia alta para dados aleatórios."""
        # Dados com distribuição variada
        data = bytes(range(256))  # Todos os bytes 0-255
        result = FeatureExtractor._shannon_entropy(data)

        # Entropia máxima para 256 símbolos = log2(256) = 8.0 bits
        assert abs(result - 8.0) < 0.001

    def test_uses_log2_for_calculation(self):
        """Deve usar log2 (não ln ou log10)."""
        # "ab" = 1x'a', 1x'b', p=0.5 cada
        # H = -0.5*log2(0.5) - 0.5*log2(0.5) = 1.0
        result = FeatureExtractor._shannon_entropy(b"ab")

        assert abs(result - 1.0) < 0.001

    def test_counts_byte_frequencies_correctly(self):
        """Deve contar frequências de bytes corretamente."""
        # "aaab" = 3x'a' (p=0.75), 1x'b' (p=0.25)
        # H = -0.75*log2(0.75) - 0.25*log2(0.25)
        data = b"aaab"
        result = FeatureExtractor._shannon_entropy(data)

        # Cálculo esperado
        p_a = 0.75
        p_b = 0.25
        expected = -(p_a * math.log2(p_a) + p_b * math.log2(p_b))

        assert abs(result - expected) < 0.001


class TestTCPFlagScore:
    """Testa método _tcp_flag_score() para scoring de flags TCP."""

    def test_returns_zero_for_none(self):
        """Deve retornar 0.0 quando flags é None."""
        result = FeatureExtractor._tcp_flag_score(None)

        assert result == 0.0

    def test_returns_zero_for_empty_string(self):
        """Deve retornar 0.0 quando flags é string vazia."""
        result = FeatureExtractor._tcp_flag_score("")

        assert result == 0.0

    def test_scores_syn_without_ack_as_1_0(self):
        """SYN sem ACK deve retornar 1.0 (SYN flood indicator)."""
        result = FeatureExtractor._tcp_flag_score("S")

        assert result == 1.0

    def test_scores_syn_with_ack_as_0_0(self):
        """SYN com ACK deve retornar 0.0 (handshake normal)."""
        result = FeatureExtractor._tcp_flag_score("SA")

        assert result == 0.0

    def test_scores_fin_as_0_5(self):
        """FIN deve adicionar 0.5 ao score."""
        result = FeatureExtractor._tcp_flag_score("F")

        assert result == 0.5

    def test_scores_psh_as_0_2(self):
        """PSH deve adicionar 0.2 ao score."""
        result = FeatureExtractor._tcp_flag_score("P")

        assert result == 0.2

    def test_combines_multiple_flags(self):
        """Deve combinar scores de múltiplas flags."""
        # FIN + PSH = 0.5 + 0.2 = 0.7
        result = FeatureExtractor._tcp_flag_score("FP")

        assert result == 0.7

    def test_ack_only_returns_zero(self):
        """ACK sozinho deve retornar 0.0."""
        result = FeatureExtractor._tcp_flag_score("A")

        assert result == 0.0

    def test_syn_fin_psh_combination(self):
        """SYN + FIN + PSH deve combinar todos os scores."""
        # SYN sem ACK (1.0) + FIN (0.5) + PSH (0.2) = 1.7
        result = FeatureExtractor._tcp_flag_score("SFP")

        assert result == 1.7

    def test_ignores_unknown_flags(self):
        """Deve ignorar flags desconhecidas."""
        # Apenas P (0.2), ignorando 'X', 'Y', 'Z'
        result = FeatureExtractor._tcp_flag_score("PXYZ")

        assert result == 0.2


class TestIntegration:
    """Testes de integração do FeatureExtractor."""

    def test_full_workflow_multiple_packets(self, extractor):
        """Deve extrair features corretamente para múltiplos pacotes."""
        # Packet 1
        obs1 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="S",
            payload_size=100,
            timestamp=1000.0,
        )
        payload1 = b"GET /index.html HTTP/1.1"
        result1 = extractor.transform(obs1, payload1)

        assert result1.payload_length == len(payload1)
        assert result1.tcp_flag_score == 1.0  # SYN sem ACK
        assert result1.inter_packet_interval == 0.0  # Primeiro pacote

        # Packet 2
        obs2 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="A",
            payload_size=200,
            timestamp=1000.1,
        )
        payload2 = b"User-Agent: Mozilla/5.0"
        result2 = extractor.transform(obs2, payload2)

        assert result2.payload_length == len(payload2)
        assert result2.tcp_flag_score == 0.0  # ACK apenas
        assert (
            abs(result2.inter_packet_interval - 0.1) < 0.001
        )  # ~0.1 (float precision)

    def test_realistic_http_request(self, extractor):
        """Deve extrair features de requisição HTTP realista."""
        obs = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="93.184.216.34",
            src_port=49152,
            dst_port=80,
            protocol="TCP",
            flags="PA",  # PSH + ACK
            payload_size=150,
            timestamp=1234567890.5,
        )
        payload = b"GET /path?query=value HTTP/1.1\r\nHost: example.com\r\n\r\n"

        result = extractor.transform(obs, payload)

        # Verificações básicas
        assert result.payload_length == len(payload)
        assert 0.0 <= result.printable_ratio <= 1.0
        assert 0.0 <= result.digit_ratio <= 1.0
        assert result.entropy > 0.0  # Payload variado
        assert result.tcp_flag_score == 0.2  # PSH apenas (SA não conta)
