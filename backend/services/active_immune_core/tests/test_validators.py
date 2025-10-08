"""Tests for coordination/validators.py

100% deterministic tests - no flakiness allowed.

Authors: Juan + Claude
Date: 2025-10-07
"""

import pytest
from pydantic import ValidationError

from coordination.validators import (
    AgentRegistration,
    ApoptosisSignal,
    ClonalExpansionRequest,
    CytokineType,
    HormoneMessage,
    TemperatureAdjustment,
    validate_cytokine,
)

# ==================== CYTOKINE VALIDATION ====================


class TestCytokineValidation:
    """Test cytokine message validation"""

    def test_valid_cytokine_all_fields(self):
        """Test validation with all required fields present"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "network-zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
            "payload": {"evento": "ameaca_detectada", "alvo": {"id": "host-1"}},
        }

        validated = validate_cytokine(cytokine)

        assert validated.tipo == CytokineType.IL1
        assert validated.emissor_id == "agent-123"
        assert validated.area_alvo == "network-zone-1"
        assert validated.prioridade == 5
        assert validated.payload.evento == "ameaca_detectada"  # Access as attribute, not dict

    def test_valid_cytokine_minimal_fields(self):
        """Test validation with minimal required fields"""
        cytokine = {
            "tipo": "IL6",
            "emissor_id": "agent-456",
            "area_alvo": "zone-2",
            "prioridade": 0,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        validated = validate_cytokine(cytokine)

        assert validated.tipo == CytokineType.IL6
        assert validated.payload == {}  # Default empty dict

    def test_invalid_cytokine_type(self):
        """Test rejection of invalid cytokine type"""
        cytokine = {
            "tipo": "INVALID_TYPE",
            "emissor_id": "agent-123",
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "tipo" in str(exc_info.value)

    def test_invalid_priority_too_high(self):
        """Test rejection of priority > 10"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "zone-1",
            "prioridade": 11,  # Too high
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "prioridade" in str(exc_info.value)

    def test_invalid_priority_negative(self):
        """Test rejection of negative priority"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "zone-1",
            "prioridade": -1,  # Negative
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "prioridade" in str(exc_info.value)

    def test_string_sanitization_null_byte(self):
        """Test rejection of null byte in string fields"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent\x00malicious",  # Null byte
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "Dangerous character" in str(exc_info.value)

    def test_string_sanitization_newline(self):
        """Test rejection of newline in string fields"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "zone\n1",  # Newline
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "Dangerous character" in str(exc_info.value)

    def test_string_sanitization_html_brackets(self):
        """Test rejection of HTML brackets in string fields"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "<script>alert('xss')</script>",  # HTML injection attempt
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "Dangerous character" in str(exc_info.value)

    def test_string_sanitization_shell_chars(self):
        """Test rejection of shell command characters"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123; rm -rf /",  # Shell injection attempt
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "Dangerous character" in str(exc_info.value)

    def test_missing_required_field(self):
        """Test rejection when required field missing"""
        cytokine = {
            "tipo": "IL1",
            # Missing emissor_id
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "emissor_id" in str(exc_info.value)

    def test_extra_fields_forbidden(self):
        """Test rejection of extra fields (extra='forbid')"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
            "extra_malicious_field": "should_be_rejected",  # Extra field
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "extra" in str(exc_info.value).lower()

    def test_string_field_max_length_emissor_id(self):
        """Test rejection of too-long emissor_id"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "a" * 129,  # 129 chars, max is 128
            "area_alvo": "zone-1",
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "emissor_id" in str(exc_info.value)

    def test_string_field_max_length_area_alvo(self):
        """Test rejection of too-long area_alvo"""
        cytokine = {
            "tipo": "IL1",
            "emissor_id": "agent-123",
            "area_alvo": "z" * 257,  # 257 chars, max is 256
            "prioridade": 5,
            "timestamp": "2025-10-07T10:00:00Z",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_cytokine(cytokine)

        assert "area_alvo" in str(exc_info.value)

    def test_all_cytokine_types_valid(self):
        """Test that all cytokine types are accepted"""
        valid_types = ["IL1", "IL6", "IL8", "IL10", "IL12", "TNF", "IFNgamma", "TGFbeta"]

        for cytokine_type in valid_types:
            cytokine = {
                "tipo": cytokine_type,
                "emissor_id": "agent-123",
                "area_alvo": "zone-1",
                "prioridade": 5,
                "timestamp": "2025-10-07T10:00:00Z",
            }

            validated = validate_cytokine(cytokine)
            assert validated.tipo.value == cytokine_type


# ==================== HORMONE VALIDATION ====================


class TestHormoneValidation:
    """Test hormone message validation"""

    def test_valid_hormone_message(self):
        """Test validation of valid hormone message"""
        hormone = HormoneMessage(
            lymphnode_id="lymphnode-global",
            hormone_type="cortisol",
            level=0.8,
            source="regional-coordination",
            timestamp="2025-10-07T10:00:00Z",
        )

        assert hormone.hormone_type == "cortisol"
        assert hormone.lymphnode_id == "lymphnode-global"
        assert hormone.level == 0.8

    def test_hormone_level_min_boundary(self):
        """Test hormone level at minimum boundary (0.0)"""
        hormone = HormoneMessage(
            lymphnode_id="lymphnode-1",
            hormone_type="adrenalina",
            level=0.0,
            source="test",
            timestamp="2025-10-07T10:00:00Z",
        )

        assert hormone.level == 0.0

    def test_hormone_level_max_boundary(self):
        """Test hormone level at maximum boundary (1.0)"""
        hormone = HormoneMessage(
            lymphnode_id="lymphnode-1",
            hormone_type="adrenalina",
            level=1.0,
            source="test",
            timestamp="2025-10-07T10:00:00Z",
        )

        assert hormone.level == 1.0

    def test_hormone_level_too_high(self):
        """Test rejection of hormone level > 1.0"""
        with pytest.raises(ValidationError) as exc_info:
            HormoneMessage(
                lymphnode_id="lymphnode-1",
                hormone_type="adrenalina",
                level=1.1,  # Too high
                source="test",
                timestamp="2025-10-07T10:00:00Z",
            )

        assert "level" in str(exc_info.value)

    def test_hormone_level_negative(self):
        """Test rejection of negative hormone level"""
        with pytest.raises(ValidationError) as exc_info:
            HormoneMessage(
                lymphnode_id="lymphnode-1",
                hormone_type="adrenalina",
                level=-0.1,  # Negative
                source="test",
                timestamp="2025-10-07T10:00:00Z",
            )

        assert "level" in str(exc_info.value)

    def test_all_hormone_types_valid(self):
        """Test that all hormone types are accepted"""
        valid_types = ["cortisol", "adrenalina", "insulin"]

        for hormone_type in valid_types:
            hormone = HormoneMessage(
                lymphnode_id="lymphnode-1",
                hormone_type=hormone_type,
                level=0.5,
                source="test",
                timestamp="2025-10-07T10:00:00Z",
            )

            assert hormone.hormone_type == hormone_type

    def test_hormone_invalid_timestamp(self):
        """Test rejection of invalid timestamp format"""
        with pytest.raises(ValidationError) as exc_info:
            HormoneMessage(
                lymphnode_id="lymphnode-1",
                hormone_type="cortisol",
                level=0.5,
                source="test",
                timestamp="invalid-timestamp",
            )

        assert "timestamp" in str(exc_info.value).lower()


# ==================== APOPTOSIS SIGNAL VALIDATION ====================


class TestApoptosisSignalValidation:
    """Test apoptosis signal validation"""

    def test_valid_apoptosis_signal(self):
        """Test validation of valid apoptosis signal"""
        signal = ApoptosisSignal(
            lymphnode_id="lymphnode-regional-1",
            reason="lymphnode_directive",
            timestamp="2025-10-07T10:00:00Z",
        )

        assert signal.lymphnode_id == "lymphnode-regional-1"
        assert signal.reason == "lymphnode_directive"

    def test_apoptosis_signal_min_length_lymphnode_id(self):
        """Test rejection of empty lymphnode_id"""
        with pytest.raises(ValidationError) as exc_info:
            ApoptosisSignal(
                lymphnode_id="",  # Empty
                reason="test",
                timestamp="2025-10-07T10:00:00Z",
            )

        assert "lymphnode_id" in str(exc_info.value)

    def test_apoptosis_signal_max_length_reason(self):
        """Test rejection of too-long reason"""
        with pytest.raises(ValidationError) as exc_info:
            ApoptosisSignal(
                lymphnode_id="lymphnode-1",
                reason="r" * 257,  # 257 chars, max is 256
                timestamp="2025-10-07T10:00:00Z",
            )

        assert "reason" in str(exc_info.value)

    def test_apoptosis_signal_invalid_timestamp(self):
        """Test rejection of invalid timestamp format"""
        with pytest.raises(ValidationError) as exc_info:
            ApoptosisSignal(
                lymphnode_id="lymphnode-1",
                reason="test",
                timestamp="not-a-timestamp",
            )

        assert "timestamp" in str(exc_info.value).lower()


# ==================== CLONAL EXPANSION REQUEST VALIDATION ====================


class TestClonalExpansionRequestValidation:
    """Test clonal expansion request validation"""

    def test_valid_clonal_expansion_request(self):
        """Test validation of valid clonal expansion request"""
        request = ClonalExpansionRequest(
            tipo_base="NEUTROFILO",
            especializacao="threat_host-1",
            quantidade=10,
        )

        assert request.tipo_base == "NEUTROFILO"
        assert request.especializacao == "threat_host-1"
        assert request.quantidade == 10

    def test_clonal_expansion_quantidade_min_boundary(self):
        """Test quantidade at minimum boundary (1)"""
        request = ClonalExpansionRequest(
            tipo_base="NEUTROFILO",
            especializacao="test",
            quantidade=1,
        )

        assert request.quantidade == 1

    def test_clonal_expansion_quantidade_max_boundary(self):
        """Test quantidade at maximum boundary (100)"""
        request = ClonalExpansionRequest(
            tipo_base="NEUTROFILO",
            especializacao="test",
            quantidade=100,
        )

        assert request.quantidade == 100

    def test_clonal_expansion_quantidade_too_high(self):
        """Test rejection of quantidade > 100"""
        with pytest.raises(ValidationError) as exc_info:
            ClonalExpansionRequest(
                tipo_base="NEUTROFILO",
                especializacao="test",
                quantidade=101,  # Too high
            )

        assert "quantidade" in str(exc_info.value)

    def test_clonal_expansion_quantidade_zero(self):
        """Test rejection of quantidade = 0"""
        with pytest.raises(ValidationError) as exc_info:
            ClonalExpansionRequest(
                tipo_base="NEUTROFILO",
                especializacao="test",
                quantidade=0,  # Too low
            )

        assert "quantidade" in str(exc_info.value)

    def test_clonal_expansion_quantidade_negative(self):
        """Test rejection of negative quantidade"""
        with pytest.raises(ValidationError) as exc_info:
            ClonalExpansionRequest(
                tipo_base="NEUTROFILO",
                especializacao="test",
                quantidade=-5,  # Negative
            )

        assert "quantidade" in str(exc_info.value)


# ==================== TEMPERATURE ADJUSTMENT VALIDATION ====================


class TestTemperatureAdjustmentValidation:
    """Test temperature adjustment validation"""

    def test_valid_temperature_adjustment_positive(self):
        """Test validation of positive temperature adjustment"""
        adjustment = TemperatureAdjustment(
            delta=2.5,
            reason="inflammation",
        )

        assert adjustment.delta == 2.5
        assert adjustment.reason == "inflammation"

    def test_valid_temperature_adjustment_negative(self):
        """Test validation of negative temperature adjustment"""
        adjustment = TemperatureAdjustment(
            delta=-1.5,
            reason="anti-inflammatory",
        )

        assert adjustment.delta == -1.5

    def test_temperature_adjustment_max_positive_boundary(self):
        """Test delta at maximum positive boundary (+5.0)"""
        adjustment = TemperatureAdjustment(
            delta=5.0,
            reason="test",
        )

        assert adjustment.delta == 5.0

    def test_temperature_adjustment_max_negative_boundary(self):
        """Test delta at maximum negative boundary (-5.0)"""
        adjustment = TemperatureAdjustment(
            delta=-5.0,
            reason="test",
        )

        assert adjustment.delta == -5.0

    def test_temperature_adjustment_too_high(self):
        """Test rejection of delta > 5.0"""
        with pytest.raises(ValidationError) as exc_info:
            TemperatureAdjustment(
                delta=5.1,  # Too high
                reason="test",
            )

        assert "delta" in str(exc_info.value)

    def test_temperature_adjustment_too_low(self):
        """Test rejection of delta < -5.0"""
        with pytest.raises(ValidationError) as exc_info:
            TemperatureAdjustment(
                delta=-5.1,  # Too low
                reason="test",
            )

        assert "delta" in str(exc_info.value)


# ==================== AGENT REGISTRATION VALIDATION ====================


class TestAgentRegistrationValidation:
    """Test agent registration validation"""

    def test_valid_agent_registration(self):
        """Test validation of valid agent registration"""
        registration = AgentRegistration(
            id="agent-abc-123",  # Uses 'id', not 'agent_id'
            tipo="NEUTROFILO",
            area_patrulha="network-zone-1",
            sensibilidade=0.7,
        )

        assert registration.id == "agent-abc-123"
        assert registration.tipo == "NEUTROFILO"
        assert registration.sensibilidade == 0.7

    def test_agent_registration_sensibilidade_min_boundary(self):
        """Test sensibilidade at minimum boundary (0.0)"""
        registration = AgentRegistration(
            id="agent-123",
            tipo="NEUTROFILO",
            area_patrulha="zone-1",
            sensibilidade=0.0,
        )

        assert registration.sensibilidade == 0.0

    def test_agent_registration_sensibilidade_max_boundary(self):
        """Test sensibilidade at maximum boundary (1.0)"""
        registration = AgentRegistration(
            id="agent-123",
            tipo="NEUTROFILO",
            area_patrulha="zone-1",
            sensibilidade=1.0,
        )

        assert registration.sensibilidade == 1.0

    def test_agent_registration_sensibilidade_too_high(self):
        """Test rejection of sensibilidade > 1.0"""
        with pytest.raises(ValidationError) as exc_info:
            AgentRegistration(
                id="agent-123",
                tipo="NEUTROFILO",
                area_patrulha="zone-1",
                sensibilidade=1.1,  # Too high
            )

        assert "sensibilidade" in str(exc_info.value)

    def test_agent_registration_sensibilidade_negative(self):
        """Test rejection of negative sensibilidade"""
        with pytest.raises(ValidationError) as exc_info:
            AgentRegistration(
                id="agent-123",
                tipo="NEUTROFILO",
                area_patrulha="zone-1",
                sensibilidade=-0.1,  # Negative
            )

        assert "sensibilidade" in str(exc_info.value)

    def test_agent_registration_optional_especializacao(self):
        """Test that especializacao is optional"""
        registration = AgentRegistration(
            id="agent-123",
            tipo="NEUTROFILO",
            area_patrulha="zone-1",
            sensibilidade=0.7,
            # especializacao omitted
        )

        assert registration.especializacao is None
