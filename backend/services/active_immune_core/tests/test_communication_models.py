"""Communication models tests - Unit tests for Pydantic models"""

import pytest
from pydantic import ValidationError

from active_immune_core.communication import (
    CytokineMessage,
    CytokineType,
    HormoneMessage,
    HormoneType,
)


class TestCytokineType:
    """Test CytokineType enumeration"""

    def test_all_cytokine_types(self):
        """Test that all() returns all cytokine types"""
        all_types = CytokineType.all()

        assert len(all_types) == 10
        assert CytokineType.IL1 in all_types
        assert CytokineType.IL6 in all_types
        assert CytokineType.TNF in all_types

    def test_pro_inflammatory_cytokines(self):
        """Test pro-inflammatory cytokine classification"""
        pro_inflammatory = CytokineType.pro_inflammatory()

        assert CytokineType.IL1 in pro_inflammatory
        assert CytokineType.IL6 in pro_inflammatory
        assert CytokineType.TNF in pro_inflammatory
        assert CytokineType.IL10 not in pro_inflammatory  # Anti-inflammatory

    def test_anti_inflammatory_cytokines(self):
        """Test anti-inflammatory cytokine classification"""
        anti_inflammatory = CytokineType.anti_inflammatory()

        assert CytokineType.IL10 in anti_inflammatory
        assert CytokineType.TGF_BETA in anti_inflammatory
        assert CytokineType.IL1 not in anti_inflammatory  # Pro-inflammatory


class TestCytokineMessage:
    """Test CytokineMessage Pydantic model"""

    def test_create_valid_cytokine_message(self):
        """Test creating valid cytokine message"""
        message = CytokineMessage(
            tipo="IL1",
            emissor_id="agent_123",
            prioridade=8,
            payload={"evento": "test"},
            area_alvo="subnet_1",
            ttl_segundos=300,
        )

        assert message.tipo == "IL1"
        assert message.emissor_id == "agent_123"
        assert message.prioridade == 8
        assert message.payload["evento"] == "test"
        assert message.area_alvo == "subnet_1"
        assert message.ttl_segundos == 300

    def test_cytokine_message_default_values(self):
        """Test default values in cytokine message"""
        message = CytokineMessage(
            tipo="IL6",
            emissor_id="agent_456",
            payload={"test": "data"},
        )

        assert message.prioridade == 5  # Default
        assert message.ttl_segundos == 300  # Default
        assert message.area_alvo is None  # Default (broadcast)

    def test_cytokine_message_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated"""
        message = CytokineMessage(
            tipo="TNF",
            emissor_id="agent_789",
            payload={},
        )

        assert message.timestamp is not None
        assert isinstance(message.timestamp, str)

    def test_cytokine_message_priority_validation(self):
        """Test priority validation (1-10)"""
        # Valid priority
        message = CytokineMessage(
            tipo="IL1",
            emissor_id="test",
            prioridade=10,
            payload={},
        )
        assert message.prioridade == 10

        # Invalid priority (too high)
        with pytest.raises(ValidationError):
            CytokineMessage(
                tipo="IL1",
                emissor_id="test",
                prioridade=11,
                payload={},
            )

        # Invalid priority (too low)
        with pytest.raises(ValidationError):
            CytokineMessage(
                tipo="IL1",
                emissor_id="test",
                prioridade=0,
                payload={},
            )

    def test_cytokine_message_ttl_validation(self):
        """Test TTL validation (10-3600)"""
        # Valid TTL
        message = CytokineMessage(
            tipo="IL1",
            emissor_id="test",
            payload={},
            ttl_segundos=3600,
        )
        assert message.ttl_segundos == 3600

        # Invalid TTL (too low)
        with pytest.raises(ValidationError):
            CytokineMessage(
                tipo="IL1",
                emissor_id="test",
                payload={},
                ttl_segundos=5,
            )

        # Invalid TTL (too high)
        with pytest.raises(ValidationError):
            CytokineMessage(
                tipo="IL1",
                emissor_id="test",
                payload={},
                ttl_segundos=4000,
            )


class TestHormoneType:
    """Test HormoneType enumeration"""

    def test_all_hormone_types(self):
        """Test that all() returns all hormone types"""
        all_types = HormoneType.all()

        assert len(all_types) == 5
        assert HormoneType.CORTISOL in all_types
        assert HormoneType.ADRENALINE in all_types
        assert HormoneType.MELATONIN in all_types


class TestHormoneMessage:
    """Test HormoneMessage Pydantic model"""

    def test_create_valid_hormone_message(self):
        """Test creating valid hormone message"""
        message = HormoneMessage(
            tipo="cortisol",
            emissor="lymphnode_1",
            nivel=8.5,
            payload={"evento": "stress"},
            duracao_estimada_segundos=600,
        )

        assert message.tipo == "cortisol"
        assert message.emissor == "lymphnode_1"
        assert message.nivel == 8.5
        assert message.payload["evento"] == "stress"
        assert message.duracao_estimada_segundos == 600

    def test_hormone_message_default_values(self):
        """Test default values in hormone message"""
        message = HormoneMessage(
            tipo="adrenalina",
            emissor="global",
            nivel=9.0,
            payload={},
        )

        assert message.duracao_estimada_segundos == 300  # Default

    def test_hormone_message_nivel_validation(self):
        """Test hormone level validation (0-10)"""
        # Valid level
        message = HormoneMessage(
            tipo="cortisol",
            emissor="test",
            nivel=10.0,
            payload={},
        )
        assert message.nivel == 10.0

        # Invalid level (too high)
        with pytest.raises(ValidationError):
            HormoneMessage(
                tipo="cortisol",
                emissor="test",
                nivel=11.0,
                payload={},
            )

        # Invalid level (negative)
        with pytest.raises(ValidationError):
            HormoneMessage(
                tipo="cortisol",
                emissor="test",
                nivel=-1.0,
                payload={},
            )

    def test_hormone_message_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated"""
        message = HormoneMessage(
            tipo="melatonina",
            emissor="test",
            nivel=5.0,
            payload={},
        )

        assert message.timestamp is not None
        assert isinstance(message.timestamp, str)
