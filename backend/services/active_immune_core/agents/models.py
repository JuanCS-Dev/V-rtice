"""Agent Models - Pydantic schemas

PRODUCTION-READY data models for immune agents.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent lifecycle states"""

    DORMINDO = "dormindo"  # Sleeping (homeostatic reserve)
    PATRULHANDO = "patrulhando"  # Active patrol
    INVESTIGANDO = "investigando"  # Investigating suspicious activity
    NEUTRALIZANDO = "neutralizando"  # Engaging threat
    REPORTANDO = "reportando"  # Reporting to lymphnode
    MEMORIA = "memoria"  # Creating immunological memory
    APOPTOSE = "apoptose"  # Self-destruction (malfunction)


class AgentType(str, Enum):
    """Agent cell types"""

    MACROFAGO = "macrofago"
    NK_CELL = "nk_cell"
    NEUTROFILO = "neutrofilo"
    DENDRITICA = "dendritica"
    LINFOCITO_T_CD8 = "linfocito_t_cd8"
    LINFOCITO_T_AUXILIAR = "linfocito_t_auxiliar"
    LINFOCITO_T_REGULADOR = "linfocito_t_regulador"
    LINFOCITO_B = "linfocito_b"


class AgenteState(BaseModel):
    """Agent state model - immutable snapshot"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID do agente")
    tipo: AgentType = Field(description="Tipo do agente (Macrófago, NK, etc.)")
    status: AgentStatus = Field(default=AgentStatus.DORMINDO, description="Status atual")
    ativo: bool = Field(default=False, description="Se está ativo ou dormindo")

    # Spatial
    localizacao_atual: str = Field(description="Node/subnet ID atual")
    area_patrulha: str = Field(description="Zona de patrulha")

    # Behavioral
    nivel_agressividade: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Nível de agressividade (0-1)",
    )
    sensibilidade: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sensibilidade de detecção (0-1)",
    )
    especializacao: Optional[str] = Field(None, description="Especialização clonal")

    # Metrics
    deteccoes_total: int = Field(default=0, ge=0, description="Total de detecções")
    neutralizacoes_total: int = Field(default=0, ge=0, description="Total de neutralizações")
    falsos_positivos: int = Field(default=0, ge=0, description="Total de falsos positivos")
    tempo_vida: timedelta = Field(
        default_factory=lambda: timedelta(hours=0),
        description="Tempo de vida do agente",
    )

    # Memory
    ultimas_ameacas: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="IDs das últimas ameaças detectadas",
    )
    padroes_aprendidos: List[str] = Field(
        default_factory=list,
        description="Padrões de ameaças aprendidos",
    )

    # Homeostasis
    energia: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Energia do agente (%)",
    )
    temperatura_local: float = Field(
        default=37.0,
        ge=36.0,
        le=42.0,
        description="Temperatura local (Celsius)",
    )

    # Timestamps
    criado_em: datetime = Field(default_factory=datetime.now, description="Data de criação")
    ultimo_heartbeat: datetime = Field(
        default_factory=datetime.now,
        description="Último heartbeat",
    )

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "tipo": "macrofago",
                "status": "patrulhando",
                "ativo": True,
                "localizacao_atual": "subnet_10_0_1_0",
                "area_patrulha": "subnet_10_0_1_0",
                "nivel_agressividade": 0.5,
                "sensibilidade": 0.7,
                "especializacao": None,
                "deteccoes_total": 42,
                "neutralizacoes_total": 38,
                "falsos_positivos": 4,
                "energia": 85.0,
                "temperatura_local": 37.5,
            }
        }
