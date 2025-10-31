"""Wisdom Base Client.

Cliente para acesso à Wisdom Base (repositório de precedentes históricos).

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class WisdomBaseClient:
    """
    Cliente para Wisdom Base.

    Wisdom Base armazena precedentes históricos de:
    - Diagnósticos passados e seus outcomes
    - Patches aplicados e seus resultados
    - Lições aprendidas de falhas
    - Padrões de sucesso

    FASE 1: Implementação simplificada (in-memory)
    FASE 2: Migrar para PostgreSQL + vector search
    """

    def __init__(self):
        """Inicializa Wisdom Base Client."""
        self.precedents = []  # In-memory para FASE 1
        self.lessons = []

    async def query_precedents(
        self, anomaly_type: str, service: str, similarity_threshold: float = 0.85
    ) -> list[dict[str, Any]]:
        """
        Busca precedentes similares na Wisdom Base.

        Args:
            anomaly_type: Tipo de anomalia
            service: Serviço afetado
            similarity_threshold: Limiar mínimo de similaridade

        Returns:
            Lista de precedentes ordenados por similaridade
        """
        logger.info(f"[WisdomBase] Querying precedents for {anomaly_type} in {service}")

        # FASE 1: Busca exata por tipo e serviço.
        # FASE 2: Implementar vector similarity search com embeddings.
        matching_precedents = [
            p
            for p in self.precedents
            if p["anomaly_type"] == anomaly_type and p["service"] == service
        ]

        return matching_precedents[:10]  # Top 10

    async def store_precedent(self, precedent: dict[str, Any]) -> str:
        """
        Armazena novo precedente na Wisdom Base.

        Args:
            precedent: Dados do precedente

        Returns:
            ID do precedent armazenado
        """
        precedent_id = f"precedent-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        precedent["precedent_id"] = precedent_id
        precedent["stored_at"] = datetime.now().isoformat()

        self.precedents.append(precedent)
        logger.info(f"[WisdomBase] Stored precedent {precedent_id}")

        return precedent_id

    async def store_lesson(self, lesson: dict[str, Any]) -> str:
        """
        Armazena lição aprendida.

        Args:
            lesson: Dados da lição

        Returns:
            ID da lição armazenada
        """
        lesson_id = f"lesson-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        lesson["lesson_id"] = lesson_id
        lesson["learned_at"] = datetime.now().isoformat()

        self.lessons.append(lesson)
        logger.info(f"[WisdomBase] Stored lesson: {lesson['lesson_learned']}")

        return lesson_id

    async def get_lessons_by_theme(self, theme: str) -> list[dict[str, Any]]:
        """
        Busca lições aprendidas por tema.

        Args:
            theme: Tema a buscar (ex: "regressão", "dependência")

        Returns:
            Lista de lições relacionadas
        """
        matching_lessons = [
            l
            for l in self.lessons
            if theme.lower() in l.get("lesson_learned", "").lower()
        ]

        return matching_lessons

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas da Wisdom Base."""
        return {
            "total_precedents": len(self.precedents),
            "total_lessons": len(self.lessons),
            "successful_precedents": sum(
                1 for p in self.precedents if p.get("outcome") == "success"
            ),
            "failed_precedents": sum(
                1 for p in self.precedents if p.get("outcome") == "failure"
            ),
        }
