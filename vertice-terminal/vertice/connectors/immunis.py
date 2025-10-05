"""
Immunis Connector - AI Immune System
=====================================

Conector para o sistema imunológico AI (Immunis).

Serviços integrados:

FASE 4 (Basic Immune System):
    - Immunis API (coordenação geral)
    - Macrophage Service (detecção inicial)
    - Neutrophil Service (resposta rápida)
    - Dendritic Service (apresentação de antígenos)
    - B-Cell Service (memória imunológica)
    - Helper T Service (coordenação de resposta)
    - Cytotoxic T Service (eliminação de ameaças)
    - NK Cell Service (patrulha e vigilância)

FASE 9 (Immune Enhancement):
    - Regulatory T-Cells (false positive suppression)
    - Memory Consolidation (STM → LTM)
    - Adaptive Immunity (antibody diversification, affinity maturation)

Author: Vértice Team
Version: 2.0.0
"""

from typing import Dict, Any, Optional
from .base import BaseConnector


class ImmunisConnector(BaseConnector):
    """
    Conector para o sistema Immunis (AI Immune System).

    Immunis implementa um sistema imunológico inspirado biologicamente
    para detecção e resposta a ameaças de forma autônoma.
    """

    def __init__(self):
        """Inicializa ImmunisConnector via Maximus AI Core."""
        super().__init__(
            service_name="Immunis Services (via Maximus)",
            base_url="http://localhost:8001",
            timeout=120
        )

    async def health_check(self) -> bool:
        """Verifica saúde do Maximus AI Core."""
        try:
            data = await self._get("/health")
            return data is not None and data.get("status") == "healthy"
        except Exception:
            return False

    async def detect_threat(
        self,
        threat_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detecção de ameaça via sistema imune.

        Macrophages fazem detecção inicial, dendritics apresentam antígenos,
        e outras células são ativadas conforme necessário.

        Args:
            threat_data: Dados da potencial ameaça
                {
                    "source": str,
                    "data": Any,
                    "context": Dict
                }

        Returns:
            Análise de ameaça e células ativadas

        Examples:
            >>> results = await connector.detect_threat({
            ...     "source": "network_traffic",
            ...     "data": {"packets": [...]},
            ...     "context": {"interface": "eth0"}
            ... })
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "immunis_detect",
                "params": threat_data
            }
        )

    async def respond_to_threat(
        self,
        threat_id: str,
        response_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resposta coordenada a ameaça.

        Helper T cells coordenam, Cytotoxic T cells eliminam,
        NK cells patrulham, B cells criam memória.

        Args:
            threat_id: ID da ameaça detectada
            response_type: "contain" | "eliminate" | "quarantine" | "monitor"

        Returns:
            Resultado da resposta imune

        Examples:
            >>> results = await connector.respond_to_threat(
            ...     "threat_abc123",
            ...     response_type="eliminate"
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "immunis_respond",
                "params": {"threat_id": threat_id, "response": response_type}
            }
        )

    async def get_immune_status(self) -> Optional[Dict[str, Any]]:
        """
        Status consolidado do sistema imune.

        Returns:
            Status de todas as células imunes, ameaças ativas,
            memória imunológica, e métricas de saúde

        Examples:
            >>> status = await connector.get_immune_status()
            >>> print(f"Active threats: {status['active_threats']}")
            >>> print(f"Immune memory entries: {status['memory_entries']}")
        """
        query = "Forneça status completo do sistema Immunis"

        return await self._post(
            "/chat",
            data={
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 4096
            }
        )

    async def query_immune_memory(
        self,
        antigen_signature: str
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta memória imunológica (B-cells).

        Args:
            antigen_signature: Assinatura do antígeno (hash, padrão, etc)

        Returns:
            Histórico de encontros anteriores com este antígeno

        Examples:
            >>> results = await connector.query_immune_memory(
            ...     "malware_hash_abc123"
            ... )
        """
        query = f"Consulte memória imunológica para antígeno: {antigen_signature}"

        return await self._post(
            "/chat",
            data={
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 2048
            }
        )

    async def activate_nk_patrol(
        self,
        patrol_zone: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Ativa patrulha de NK cells.

        NK (Natural Killer) cells fazem vigilância contínua.

        Args:
            patrol_zone: Zona a patrulhar
                {
                    "scope": "network" | "filesystem" | "memory",
                    "targets": [...],
                    "duration_minutes": int
                }

        Returns:
            Status da patrulha ativada

        Examples:
            >>> results = await connector.activate_nk_patrol({
            ...     "scope": "network",
            ...     "targets": ["192.168.1.0/24"],
            ...     "duration_minutes": 60
            ... })
        """
        query = f"Ative patrulha NK cells: {patrol_zone}"

        return await self._post(
            "/chat",
            data={
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 2048
            }
        )

    async def train_immune_system(
        self,
        training_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Treina sistema imune com novos padrões.

        Cria memória imunológica (B-cells) para resposta mais rápida.

        Args:
            training_data: Dados de treinamento
                {
                    "threat_patterns": [...],
                    "benign_patterns": [...],
                    "context": Dict
                }

        Returns:
            Confirmação de treinamento

        Examples:
            >>> results = await connector.train_immune_system({
            ...     "threat_patterns": [
            ...         {"signature": "...", "severity": "high"},
            ...         ...
            ...     ],
            ...     "benign_patterns": [...],
            ...     "context": {"source": "incident_123"}
            ... })
        """
        query = f"Treine sistema imune com dados: {training_data}"

        return await self._post(
            "/chat",
            data={
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 4096
            }
        )

    # ========================================================================
    # FASE 9: Immune Enhancement Methods
    # ========================================================================

    async def suppress_false_positives(
        self,
        alerts: list,
        suppression_threshold: float = 0.6
    ) -> Optional[Dict[str, Any]]:
        """
        Suprime falsos positivos usando Regulatory T-Cells.

        Args:
            alerts: Lista de alertas para avaliar
            suppression_threshold: Threshold de tolerância para supressão (0-1)

        Returns:
            Resultados de avaliação com alertas suprimidos

        Examples:
            >>> results = await connector.suppress_false_positives(
            ...     alerts=[
            ...         {"id": "alert_001", "severity": "high", "entity": "192.168.1.10"},
            ...         {"id": "alert_002", "severity": "medium", "entity": "john.doe"}
            ...     ],
            ...     suppression_threshold=0.7
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "suppress_false_positives",
                "params": {
                    "alerts": alerts,
                    "suppression_threshold": suppression_threshold
                }
            }
        )

    async def get_tolerance_profile(
        self,
        entity_id: str,
        entity_type: str = "ip"
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém perfil de tolerância imune para entidade.

        Args:
            entity_id: Identificador da entidade (IP, user, domain)
            entity_type: Tipo de entidade (ip, user, domain, service)

        Returns:
            Perfil de tolerância com fingerprint comportamental e stats de FP

        Examples:
            >>> profile = await connector.get_tolerance_profile(
            ...     entity_id="192.168.1.50",
            ...     entity_type="ip"
            ... )
            >>> print(f"Tolerance score: {profile['tolerance_score']}")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "get_tolerance_profile",
                "params": {
                    "entity_id": entity_id,
                    "entity_type": entity_type
                }
            }
        )

    async def consolidate_memory(
        self,
        trigger_manual: bool = False,
        importance_threshold: float = 0.6
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger ciclo de consolidação de memória (STM → LTM).

        Args:
            trigger_manual: Trigger consolidação manual (bypass circadian rhythm)
            importance_threshold: Importância mínima para consolidação (0-1)

        Returns:
            Resultados de consolidação com padrões extraídos e memórias criadas

        Examples:
            >>> results = await connector.consolidate_memory(
            ...     trigger_manual=True,
            ...     importance_threshold=0.7
            ... )
            >>> print(f"Patterns extracted: {results['patterns_count']}")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "consolidate_memory",
                "params": {
                    "trigger_manual": trigger_manual,
                    "importance_threshold": importance_threshold
                }
            }
        )

    async def query_long_term_memory(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.5
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta memória imunológica de longo prazo.

        Args:
            query: Query de busca
            limit: Máximo de resultados a retornar
            min_importance: Threshold mínimo de importância (0-1)

        Returns:
            Memórias de longo prazo que correspondem à query

        Examples:
            >>> memories = await connector.query_long_term_memory(
            ...     query="ransomware campaigns targeting healthcare",
            ...     limit=5,
            ...     min_importance=0.8
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "query_long_term_memory",
                "params": {
                    "query": query,
                    "limit": limit,
                    "min_importance": min_importance
                }
            }
        )

    async def diversify_antibodies(
        self,
        threat_samples: list,
        repertoire_size: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Inicializa repertório de anticorpos a partir de threat samples.

        Args:
            threat_samples: Samples de ameaças para treino (V(D)J recombination)
            repertoire_size: Tamanho do repertório inicial de anticorpos

        Returns:
            Resultados de inicialização com stats do pool de anticorpos

        Examples:
            >>> results = await connector.diversify_antibodies(
            ...     threat_samples=[
            ...         {"type": "malware", "signature": "...", "features": {...}},
            ...         {"type": "phishing", "url": "...", "content": "..."}
            ...     ],
            ...     repertoire_size=150
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "diversify_antibodies",
                "params": {
                    "threat_samples": threat_samples,
                    "repertoire_size": repertoire_size
                }
            }
        )

    async def run_affinity_maturation(
        self,
        feedback_data: Dict[str, Dict[str, bool]]
    ) -> Optional[Dict[str, Any]]:
        """
        Executa ciclo de affinity maturation (somatic hypermutation).

        Args:
            feedback_data: Feedback de anticorpos (antibody_id -> {sample_id -> was_correct})

        Returns:
            Resultados de maturação com novos anticorpos criados

        Examples:
            >>> results = await connector.run_affinity_maturation(
            ...     feedback_data={
            ...         "antibody_001": {"sample_a": True, "sample_b": False},
            ...         "antibody_002": {"sample_a": True, "sample_b": True}
            ...     }
            ... )
            >>> print(f"New antibodies: {results['new_antibodies_count']}")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "run_affinity_maturation",
                "params": feedback_data
            }
        )

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
