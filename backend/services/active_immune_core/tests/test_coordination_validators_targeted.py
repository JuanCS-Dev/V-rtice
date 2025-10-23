"""
Coordination Validators - Targeted Coverage Tests

Objetivo: Cobrir coordination/validators.py (220 lines, 0% → 40%+)

Testa Pydantic models: CytokineMessage, HormoneMessage, validation, injection prevention

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import validators.py directly
validators_path = Path(__file__).parent.parent / "coordination" / "validators.py"
spec = importlib.util.spec_from_file_location("coordination.validators", validators_path)
validators_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators_module)

# Extract classes and functions
CytokineType = validators_module.CytokineType
CytokinePayload = validators_module.CytokinePayload
CytokineMessage = validators_module.CytokineMessage
HormoneMessage = validators_module.HormoneMessage
ApoptosisSignal = validators_module.ApoptosisSignal
ClonalExpansionRequest = validators_module.ClonalExpansionRequest
TemperatureAdjustment = validators_module.TemperatureAdjustment
AgentRegistration = validators_module.AgentRegistration
validate_cytokine = validators_module.validate_cytokine
validate_hormone = validators_module.validate_hormone
validate_clonal_expansion = validators_module.validate_clonal_expansion


# ===== CYTOKINE TYPE TESTS =====

def test_cytokine_type_enum_members():
    """
    SCENARIO: CytokineType enum
    EXPECTED: Has 8 standard cytokine types
    """
    assert CytokineType.IL1 == "IL1"
    assert CytokineType.IL6 == "IL6"
    assert CytokineType.IL8 == "IL8"
    assert CytokineType.IL10 == "IL10"
    assert CytokineType.IL12 == "IL12"
    assert CytokineType.TNF == "TNF"
    assert CytokineType.IFNgamma == "IFNgamma"
    assert CytokineType.TGFbeta == "TGFbeta"


# ===== CYTOKINE PAYLOAD TESTS =====

def test_cytokine_payload_initialization_minimal():
    """
    SCENARIO: CytokinePayload created with no fields
    EXPECTED: All fields are None (optional)
    """
    payload = CytokinePayload()

    assert payload.evento is None
    assert payload.is_threat is None
    assert payload.alvo is None
    assert payload.host_id is None
    assert payload.severity is None


def test_cytokine_payload_with_valid_severity():
    """
    SCENARIO: CytokinePayload with severity=0.8
    EXPECTED: Severity stored correctly
    """
    payload = CytokinePayload(severity=0.8)

    assert payload.severity == 0.8


def test_cytokine_payload_with_alvo_dict():
    """
    SCENARIO: CytokinePayload with alvo as dict
    EXPECTED: Alvo stored correctly
    """
    alvo = {"ip": "192.168.1.100", "port": 80}
    payload = CytokinePayload(alvo=alvo)

    assert payload.alvo == alvo


def test_cytokine_payload_alvo_validation_non_dict():
    """
    SCENARIO: CytokinePayload with alvo not a dict
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokinePayload(alvo="not a dict")


# ===== CYTOKINE MESSAGE TESTS =====

def test_cytokine_message_initialization_valid():
    """
    SCENARIO: CytokineMessage created with valid data
    EXPECTED: All fields stored correctly
    """
    timestamp = datetime.now().isoformat()

    msg = CytokineMessage(
        tipo=CytokineType.IL6,
        emissor_id="agent-123",
        area_alvo="subnet-10.0.1.0",
        prioridade=5,
        timestamp=timestamp,
    )

    assert msg.tipo == CytokineType.IL6
    assert msg.emissor_id == "agent-123"
    assert msg.area_alvo == "subnet-10.0.1.0"
    assert msg.prioridade == 5
    assert msg.timestamp == timestamp


def test_cytokine_message_timestamp_validation_invalid():
    """
    SCENARIO: CytokineMessage with invalid timestamp
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="agent-123",
            area_alvo="subnet-10.0.1.0",
            prioridade=5,
            timestamp="not-a-timestamp",
        )


def test_cytokine_message_injection_prevention_emissor():
    """
    SCENARIO: CytokineMessage with dangerous char in emissor_id
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="agent-123<script>",  # Injection attempt
            area_alvo="subnet-10.0.1.0",
            prioridade=5,
            timestamp=datetime.now().isoformat(),
        )


def test_cytokine_message_injection_prevention_area():
    """
    SCENARIO: CytokineMessage with dangerous char in area_alvo
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="agent-123",
            area_alvo="subnet; rm -rf /",  # Injection attempt
            prioridade=5,
            timestamp=datetime.now().isoformat(),
        )


def test_cytokine_message_prioridade_validation_max():
    """
    SCENARIO: CytokineMessage with prioridade > 10
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="agent-123",
            area_alvo="subnet-10.0.1.0",
            prioridade=15,  # > 10
            timestamp=datetime.now().isoformat(),
        )


def test_cytokine_message_emissor_id_min_length():
    """
    SCENARIO: CytokineMessage with empty emissor_id
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="",  # Too short
            area_alvo="subnet-10.0.1.0",
            prioridade=5,
            timestamp=datetime.now().isoformat(),
        )


# ===== HORMONE MESSAGE TESTS =====

def test_hormone_message_initialization_valid():
    """
    SCENARIO: HormoneMessage created with valid data
    EXPECTED: All fields stored correctly
    """
    timestamp = datetime.now().isoformat()

    msg = HormoneMessage(
        lymphnode_id="lymph-001",
        hormone_type="cortisol",
        level=0.6,
        source="homeostatic_controller",
        timestamp=timestamp,
    )

    assert msg.lymphnode_id == "lymph-001"
    assert msg.hormone_type == "cortisol"
    assert msg.level == 0.6
    assert msg.source == "homeostatic_controller"
    assert msg.timestamp == timestamp


def test_hormone_message_level_validation_max():
    """
    SCENARIO: HormoneMessage with level > 1.0
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        HormoneMessage(
            lymphnode_id="lymph-001",
            hormone_type="cortisol",
            level=1.5,  # > 1.0
            source="homeostatic_controller",
            timestamp=datetime.now().isoformat(),
        )


def test_hormone_message_timestamp_validation():
    """
    SCENARIO: HormoneMessage with invalid timestamp
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        HormoneMessage(
            lymphnode_id="lymph-001",
            hormone_type="cortisol",
            level=0.5,
            source="homeostatic_controller",
            timestamp="invalid-timestamp",
        )


# ===== APOPTOSIS SIGNAL TESTS =====

def test_apoptosis_signal_initialization_valid():
    """
    SCENARIO: ApoptosisSignal created with valid data
    EXPECTED: All fields stored correctly
    """
    timestamp = datetime.now().isoformat()

    signal = ApoptosisSignal(
        lymphnode_id="lymph-001",
        reason="resource exhaustion",
        timestamp=timestamp,
    )

    assert signal.lymphnode_id == "lymph-001"
    assert signal.reason == "resource exhaustion"
    assert signal.timestamp == timestamp


def test_apoptosis_signal_timestamp_validation():
    """
    SCENARIO: ApoptosisSignal with invalid timestamp
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        ApoptosisSignal(
            lymphnode_id="lymph-001",
            reason="test",
            timestamp="not-a-timestamp",
        )


# ===== CLONAL EXPANSION REQUEST TESTS =====

def test_clonal_expansion_request_initialization_valid():
    """
    SCENARIO: ClonalExpansionRequest created with valid data
    EXPECTED: All fields stored correctly
    """
    req = ClonalExpansionRequest(
        tipo_base="MACROFAGO",
        especializacao="antigen-presentation",
        quantidade=10,
    )

    assert req.tipo_base == "MACROFAGO"
    assert req.especializacao == "antigen-presentation"
    assert req.quantidade == 10


def test_clonal_expansion_request_quantidade_max():
    """
    SCENARIO: ClonalExpansionRequest with quantidade > 100
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        ClonalExpansionRequest(
            tipo_base="MACROFAGO",
            especializacao="test",
            quantidade=150,  # > 100
        )


def test_clonal_expansion_request_quantidade_min():
    """
    SCENARIO: ClonalExpansionRequest with quantidade < 1
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        ClonalExpansionRequest(
            tipo_base="MACROFAGO",
            especializacao="test",
            quantidade=0,  # < 1
        )


def test_clonal_expansion_request_injection_prevention():
    """
    SCENARIO: ClonalExpansionRequest with dangerous char in especializacao
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        ClonalExpansionRequest(
            tipo_base="MACROFAGO",
            especializacao="test<script>",  # Injection attempt
            quantidade=10,
        )


# ===== TEMPERATURE ADJUSTMENT TESTS =====

def test_temperature_adjustment_initialization_valid():
    """
    SCENARIO: TemperatureAdjustment created with valid data
    EXPECTED: All fields stored correctly
    """
    adj = TemperatureAdjustment(
        delta=2.5,
        reason="infection detected",
    )

    assert adj.delta == 2.5
    assert adj.reason == "infection detected"


def test_temperature_adjustment_delta_validation_max():
    """
    SCENARIO: TemperatureAdjustment with delta > 5.0
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        TemperatureAdjustment(
            delta=6.0,  # > 5.0
            reason="test",
        )


def test_temperature_adjustment_delta_validation_min():
    """
    SCENARIO: TemperatureAdjustment with delta < -5.0
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        TemperatureAdjustment(
            delta=-6.0,  # < -5.0
            reason="test",
        )


# ===== AGENT REGISTRATION TESTS =====

def test_agent_registration_initialization_valid():
    """
    SCENARIO: AgentRegistration created with valid data
    EXPECTED: All fields stored correctly
    """
    reg = AgentRegistration(
        id="agent-123",
        tipo="MACROFAGO",
        area_patrulha="subnet-10.0.1.0",
        sensibilidade=0.7,
        especializacao="antigen-presentation",
    )

    assert reg.id == "agent-123"
    assert reg.tipo == "MACROFAGO"
    assert reg.sensibilidade == 0.7


def test_agent_registration_sensibilidade_validation_max():
    """
    SCENARIO: AgentRegistration with sensibilidade > 1.0
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        AgentRegistration(
            id="agent-123",
            tipo="MACROFAGO",
            sensibilidade=1.5,  # > 1.0
        )


def test_agent_registration_injection_prevention():
    """
    SCENARIO: AgentRegistration with dangerous char in id
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        AgentRegistration(
            id="agent-123<script>",  # Injection attempt
            tipo="MACROFAGO",
            sensibilidade=0.7,
        )


# ===== HELPER FUNCTION TESTS =====

def test_validate_cytokine_function_valid():
    """
    SCENARIO: validate_cytokine() called with valid data
    EXPECTED: Returns CytokineMessage instance
    """
    data = {
        "tipo": "IL6",
        "emissor_id": "agent-123",
        "area_alvo": "subnet-10.0.1.0",
        "prioridade": 5,
        "timestamp": datetime.now().isoformat(),
    }

    result = validate_cytokine(data)

    assert isinstance(result, CytokineMessage)
    assert result.tipo == CytokineType.IL6


def test_validate_cytokine_function_invalid():
    """
    SCENARIO: validate_cytokine() called with invalid data
    EXPECTED: ValidationError raised
    """
    data = {
        "tipo": "IL6",
        "emissor_id": "",  # Invalid
        "area_alvo": "subnet-10.0.1.0",
        "prioridade": 5,
        "timestamp": datetime.now().isoformat(),
    }

    with pytest.raises(ValidationError):
        validate_cytokine(data)


def test_validate_hormone_function_valid():
    """
    SCENARIO: validate_hormone() called with valid data
    EXPECTED: Returns HormoneMessage instance
    """
    data = {
        "lymphnode_id": "lymph-001",
        "hormone_type": "cortisol",
        "level": 0.6,
        "source": "homeostatic_controller",
        "timestamp": datetime.now().isoformat(),
    }

    result = validate_hormone(data)

    assert isinstance(result, HormoneMessage)
    assert result.hormone_type == "cortisol"


def test_validate_clonal_expansion_function_valid():
    """
    SCENARIO: validate_clonal_expansion() called with valid params
    EXPECTED: Returns ClonalExpansionRequest instance
    """
    result = validate_clonal_expansion(
        tipo_base="MACROFAGO",
        especializacao="antigen-presentation",
        quantidade=10,
    )

    assert isinstance(result, ClonalExpansionRequest)
    assert result.quantidade == 10


def test_validate_clonal_expansion_function_invalid():
    """
    SCENARIO: validate_clonal_expansion() called with invalid quantidade
    EXPECTED: ValidationError raised
    """
    with pytest.raises(ValidationError):
        validate_clonal_expansion(
            tipo_base="MACROFAGO",
            especializacao="test",
            quantidade=200,  # > 100
        )


# ===== DOCSTRING TESTS =====

def test_module_docstring():
    """
    SCENARIO: coordination.validators module
    EXPECTED: Has module docstring mentioning validation and injection prevention
    """
    doc = validators_module.__doc__
    assert doc is not None
    assert "validator" in doc.lower() or "validat" in doc.lower()


def test_cytokine_message_docstring():
    """
    SCENARIO: CytokineMessage class
    EXPECTED: Has docstring
    """
    doc = CytokineMessage.__doc__
    assert doc is not None
    assert "cytokine" in doc.lower()
