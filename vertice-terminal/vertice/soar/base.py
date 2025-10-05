"""
🔌 SOAR Base Connector - Abstract Base Class (Adapter Pattern)

Define interface comum para todos os SOAR platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class IncidentSeverity(Enum):
    """Severidade de incidente"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(Enum):
    """Status de incidente"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Artifact:
    """Artifact de evidência (IOC, arquivo, etc)"""
    type: str  # ip, domain, hash, file, etc
    value: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Incident:
    """Incidente SOAR"""
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.NEW
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    artifacts: List[Artifact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, artifact: Artifact) -> None:
        """Adiciona artifact ao incidente"""
        self.artifacts.append(artifact)

    def add_tag(self, tag: str) -> None:
        """Adiciona tag"""
        if tag not in self.tags:
            self.tags.append(tag)


class SOARConnector(ABC):
    """
    Abstract Base Class para conectores SOAR

    Implementa Adapter Pattern para múltiplas plataformas SOAR.
    Cada plataforma implementa esta interface.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Args:
            base_url: URL base da plataforma SOAR
            api_key: API key para autenticação
        """
        self.base_url = base_url
        self.api_key = api_key

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verifica conectividade com plataforma SOAR

        Returns:
            True se conectado, False caso contrário
        """
        pass

    @abstractmethod
    async def create_incident(self, incident: Incident) -> str:
        """
        Cria incidente na plataforma SOAR

        Args:
            incident: Incidente para criar

        Returns:
            ID do incidente criado

        Raises:
            ValueError: Se falhar ao criar incidente
        """
        pass

    @abstractmethod
    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Busca incidente por ID

        Args:
            incident_id: ID do incidente

        Returns:
            Incident ou None se não encontrado
        """
        pass

    @abstractmethod
    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza incidente

        Args:
            incident_id: ID do incidente
            updates: Campos para atualizar

        Returns:
            True se atualizado com sucesso
        """
        pass

    @abstractmethod
    async def add_artifact(
        self,
        incident_id: str,
        artifact: Artifact
    ) -> bool:
        """
        Adiciona artifact a um incidente

        Args:
            incident_id: ID do incidente
            artifact: Artifact para adicionar

        Returns:
            True se adicionado com sucesso
        """
        pass

    @abstractmethod
    async def execute_playbook(
        self,
        playbook_id: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Executa playbook na plataforma SOAR

        Args:
            playbook_id: ID do playbook
            parameters: Parâmetros para passar ao playbook

        Returns:
            ID da execução do playbook

        Raises:
            ValueError: Se playbook não existir ou falhar
        """
        pass

    @abstractmethod
    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 100
    ) -> List[Incident]:
        """
        Lista incidentes

        Args:
            status: Filtrar por status
            severity: Filtrar por severidade
            limit: Máximo de incidentes para retornar

        Returns:
            Lista de incidentes
        """
        pass

    async def close(self) -> None:
        """Fecha conexão"""
        pass
