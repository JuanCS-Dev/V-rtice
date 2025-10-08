"""Lymphnode Input Validators

Pydantic models for validating all inputs to LinfonodoDigital.
Ensures data integrity and prevents injection attacks.

Authors: Juan + Claude
Date: 2025-10-07
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CytokineType(str, Enum):
    """Valid cytokine types"""

    IL1 = "IL1"
    IL6 = "IL6"
    IL8 = "IL8"
    IL10 = "IL10"
    IL12 = "IL12"
    TNF = "TNF"
    IFNgamma = "IFNgamma"
    TGFbeta = "TGFbeta"


class CytokinePayload(BaseModel):
    """Cytokine payload validation"""

    model_config = ConfigDict(extra="allow")

    evento: Optional[str] = None
    is_threat: Optional[bool] = None
    alvo: Optional[Dict[str, Any]] = None
    host_id: Optional[str] = None
    severity: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("alvo")
    @classmethod
    def validate_alvo(cls, v):
        """Ensure alvo has required fields if present"""
        if v is not None and not isinstance(v, dict):
            raise ValueError("alvo must be a dictionary")
        return v


class CytokineMessage(BaseModel):
    """Validated cytokine message from Kafka"""

    model_config = ConfigDict(extra="forbid")

    tipo: CytokineType
    emissor_id: str = Field(..., min_length=1, max_length=128)
    area_alvo: str = Field(..., min_length=1, max_length=256)
    prioridade: int = Field(..., ge=0, le=10)
    timestamp: str  # ISO format
    payload: CytokinePayload = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format"""
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")
        return v

    @field_validator("emissor_id", "area_alvo")
    @classmethod
    def sanitize_string_fields(cls, v):
        """Prevent injection attacks in string fields"""
        # Remove control characters and dangerous chars
        dangerous_chars = ["\x00", "\n", "\r", "\t", "<", ">", ";", "&", "|"]
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"Dangerous character '{repr(char)}' not allowed")
        return v.strip()


class HormoneMessage(BaseModel):
    """Validated hormone message for Redis publish"""

    model_config = ConfigDict(extra="forbid")

    lymphnode_id: str = Field(..., min_length=1, max_length=128)
    hormone_type: str = Field(..., min_length=1, max_length=64)
    level: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., min_length=1, max_length=256)
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format"""
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")
        return v


class ApoptosisSignal(BaseModel):
    """Validated apoptosis signal"""

    model_config = ConfigDict(extra="forbid")

    lymphnode_id: str = Field(..., min_length=1, max_length=128)
    reason: str = Field(..., min_length=1, max_length=256)
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format"""
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")
        return v


class ClonalExpansionRequest(BaseModel):
    """Validated clonal expansion parameters"""

    model_config = ConfigDict(extra="forbid")

    tipo_base: str = Field(..., min_length=1, max_length=64)
    especializacao: str = Field(..., min_length=1, max_length=256)
    quantidade: int = Field(..., ge=1, le=100)  # Max 100 clones per request

    @field_validator("especializacao")
    @classmethod
    def sanitize_especializacao(cls, v):
        """Prevent injection in specialization field"""
        if any(char in v for char in ["\x00", "\n", "\r", "<", ">", ";"]):
            raise ValueError("Dangerous characters not allowed in specialization")
        return v.strip()


class TemperatureAdjustment(BaseModel):
    """Validated temperature adjustment"""

    model_config = ConfigDict(extra="forbid")

    delta: float = Field(..., ge=-5.0, le=5.0)  # Max ±5°C per adjustment
    reason: str = Field(..., min_length=1, max_length=256)


class AgentRegistration(BaseModel):
    """Validated agent registration"""

    model_config = ConfigDict(extra="allow")  # Allow extra fields from AgenteState

    id: str = Field(..., min_length=1, max_length=128)
    tipo: str = Field(..., min_length=1, max_length=64)
    area_patrulha: Optional[str] = Field(None, max_length=256)
    sensibilidade: float = Field(..., ge=0.0, le=1.0)
    especializacao: Optional[str] = Field(None, max_length=256)

    @field_validator("id", "tipo")
    @classmethod
    def sanitize_string_fields(cls, v):
        """Prevent injection attacks"""
        if any(char in v for char in ["\x00", "\n", "\r", "<", ">", ";", "&", "|"]):
            raise ValueError("Dangerous characters not allowed")
        return v.strip()


def validate_cytokine(data: Dict[str, Any]) -> CytokineMessage:
    """
    Validate cytokine message from Kafka.

    Args:
        data: Raw cytokine data

    Returns:
        Validated CytokineMessage

    Raises:
        ValidationError: If data is invalid
    """
    return CytokineMessage(**data)


def validate_hormone(data: Dict[str, Any]) -> HormoneMessage:
    """
    Validate hormone message for Redis.

    Args:
        data: Raw hormone data

    Returns:
        Validated HormoneMessage

    Raises:
        ValidationError: If data is invalid
    """
    return HormoneMessage(**data)


def validate_clonal_expansion(tipo_base: str, especializacao: str, quantidade: int) -> ClonalExpansionRequest:
    """
    Validate clonal expansion request.

    Args:
        tipo_base: Base agent type
        especializacao: Specialization marker
        quantidade: Number of clones

    Returns:
        Validated ClonalExpansionRequest

    Raises:
        ValidationError: If parameters are invalid
    """
    return ClonalExpansionRequest(tipo_base=tipo_base, especializacao=especializacao, quantidade=quantidade)
