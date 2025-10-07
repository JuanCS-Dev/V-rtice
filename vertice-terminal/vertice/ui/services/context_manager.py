"""
TUI Context Manager para Vértice
UI/UX Blueprint v1.2 - Deep linking CLI→TUI

Características:
- State persistence entre CLI e TUI
- Deep linking (vcli investigate IP --tui)
- Session management
- Implementação completa
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class WorkspaceType(Enum):
    """Tipos de workspaces TUI."""
    SITUATIONAL_AWARENESS = "situational_awareness"
    INVESTIGATION = "investigation"
    ETHICAL_GOVERNANCE = "ethical_governance"


@dataclass
class TUIContext:
    """
    Contexto de inicialização da TUI.

    Permite deep linking do CLI para TUI com dados pre-carregados.
    """
    workspace: WorkspaceType
    entity_id: Optional[str] = None  # IP, domain, host, etc.
    entity_type: Optional[str] = None  # "ip", "domain", "host"
    incident_id: Optional[str] = None
    decision_id: Optional[str] = None
    filters: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    timestamp: str = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TUIContextManager:
    """
    Gerenciador de contexto para deep linking CLI→TUI.

    Example:
        # No CLI
        manager = TUIContextManager()
        manager.set_context(
            workspace=WorkspaceType.INVESTIGATION,
            entity_id="192.168.1.100",
            entity_type="ip"
        )

        # Na TUI
        context = manager.get_context()
        # TUI carrega Workspace Investigation com dados do IP
    """

    def __init__(self):
        """Inicializa manager."""
        self.context_dir = Path.home() / ".vertice" / "tui_context"
        self.context_file = self.context_dir / "current_context.json"

        # Cria diretório se não existir
        self.context_dir.mkdir(parents=True, exist_ok=True)

        self._current_context: Optional[TUIContext] = None

    def set_context(
        self,
        workspace: WorkspaceType,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        incident_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Define contexto para próxima inicialização da TUI.

        Args:
            workspace: Workspace a ser carregado
            entity_id: ID da entidade (IP, domain, etc.)
            entity_type: Tipo da entidade
            incident_id: ID do incidente
            decision_id: ID da decisão HITL
            filters: Filtros adicionais
            metadata: Metadados customizados

        Returns:
            bool: True se salvou com sucesso

        Example:
            manager.set_context(
                workspace=WorkspaceType.INVESTIGATION,
                entity_id="8.8.8.8",
                entity_type="ip",
                filters={"timeframe": "24h"}
            )
        """
        try:
            context = TUIContext(
                workspace=workspace,
                entity_id=entity_id,
                entity_type=entity_type,
                incident_id=incident_id,
                decision_id=decision_id,
                filters=filters or {},
                metadata=metadata or {},
            )

            self._current_context = context

            # Salva em arquivo
            with open(self.context_file, "w") as f:
                json.dump(
                    {
                        "workspace": context.workspace.value,
                        "entity_id": context.entity_id,
                        "entity_type": context.entity_type,
                        "incident_id": context.incident_id,
                        "decision_id": context.decision_id,
                        "filters": context.filters,
                        "metadata": context.metadata,
                        "timestamp": context.timestamp,
                    },
                    f,
                    indent=2,
                )

            return True

        except Exception:
            return False

    def get_context(self, clear_after: bool = True) -> Optional[TUIContext]:
        """
        Obtém contexto atual e opcionalmente limpa.

        Args:
            clear_after: Limpar contexto após ler (default: True)

        Returns:
            TUIContext ou None

        Example:
            context = manager.get_context()
            if context:
                # Carrega workspace com contexto
                load_workspace(context.workspace, context.entity_id)
        """
        try:
            if not self.context_file.exists():
                return None

            with open(self.context_file, "r") as f:
                data = json.load(f)

            context = TUIContext(
                workspace=WorkspaceType(data["workspace"]),
                entity_id=data.get("entity_id"),
                entity_type=data.get("entity_type"),
                incident_id=data.get("incident_id"),
                decision_id=data.get("decision_id"),
                filters=data.get("filters", {}),
                metadata=data.get("metadata", {}),
                timestamp=data.get("timestamp"),
            )

            if clear_after:
                self.clear_context()

            return context

        except Exception:
            return None

    def clear_context(self):
        """Limpa contexto atual."""
        self._current_context = None

        if self.context_file.exists():
            try:
                self.context_file.unlink()
            except Exception:
                pass

    def has_context(self) -> bool:
        """
        Verifica se há contexto pendente.

        Returns:
            bool: True se há contexto
        """
        return self.context_file.exists()

    def get_context_age_seconds(self) -> Optional[float]:
        """
        Retorna idade do contexto em segundos.

        Returns:
            float: Segundos desde criação do contexto ou None
        """
        try:
            if not self.context_file.exists():
                return None

            with open(self.context_file, "r") as f:
                data = json.load(f)

            timestamp_str = data.get("timestamp")
            if not timestamp_str:
                return None

            context_time = datetime.fromisoformat(timestamp_str)
            age = (datetime.now() - context_time).total_seconds()

            return age

        except Exception:
            return None

    def is_context_stale(self, max_age_seconds: int = 3600) -> bool:
        """
        Verifica se contexto está "stale" (expirado).

        Args:
            max_age_seconds: Idade máxima em segundos (default: 1h)

        Returns:
            bool: True se stale
        """
        age = self.get_context_age_seconds()

        if age is None:
            return True

        return age > max_age_seconds

    @staticmethod
    def create_investigation_context(entity_id: str, entity_type: str) -> Dict[str, Any]:
        """
        Helper estático para criar contexto de investigação.

        Args:
            entity_id: ID da entidade (IP, domain, etc.)
            entity_type: Tipo da entidade

        Returns:
            Dict com contexto pronto para uso

        Example:
            context = TUIContextManager.create_investigation_context("8.8.8.8", "ip")
        """
        return {
            "workspace": WorkspaceType.INVESTIGATION,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "filters": {
                "timeframe": "24h",
                "auto_refresh": True,
            },
            "metadata": {
                "source": "cli_investigate",
            },
        }

    @staticmethod
    def create_decision_context(decision_id: str) -> Dict[str, Any]:
        """
        Helper estático para criar contexto de decisão ética.

        Args:
            decision_id: ID da decisão HITL

        Returns:
            Dict com contexto pronto

        Example:
            context = TUIContextManager.create_decision_context("DEC-12345")
        """
        return {
            "workspace": WorkspaceType.ETHICAL_GOVERNANCE,
            "decision_id": decision_id,
            "filters": {
                "highlight_pending": True,
            },
            "metadata": {
                "source": "cli_decision_review",
            },
        }


# Instância global para uso conveniente
global_context_manager = TUIContextManager()


__all__ = [
    "TUIContext",
    "TUIContextManager",
    "WorkspaceType",
    "global_context_manager",
]
