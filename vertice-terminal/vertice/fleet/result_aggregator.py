"""
📊 Result Aggregator - Agrega resultados de queries do fleet

Responsável por:
- Deduplicação de resultados
- Statistical summaries
- Export formats (JSON, CSV)
- Result ranking/scoring
"""

import json
import csv
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import Counter
from io import StringIO


@dataclass
class AggregatedResult:
    """Resultado agregado de uma query cross-fleet"""
    total_rows: int = 0
    unique_rows: int = 0
    endpoints_responded: int = 0
    endpoints_errors: int = 0
    rows: List[Dict[str, Any]] = field(default_factory=list)
    dedup_stats: Dict[str, int] = field(default_factory=dict)
    field_stats: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"""Aggregated Result:
  Total Rows: {self.total_rows}
  Unique Rows: {self.unique_rows}
  Duplicates Removed: {self.total_rows - self.unique_rows}
  Endpoints Responded: {self.endpoints_responded}
  Endpoints with Errors: {self.endpoints_errors}"""


class ResultAggregator:
    """
    Agregador de resultados de queries distribuídas
    """

    def __init__(self, deduplicate: bool = True):
        """
        Args:
            deduplicate: Se True, remove duplicatas
        """
        self.deduplicate = deduplicate

    def aggregate(
        self,
        results: List[Dict[str, Any]],
        dedup_keys: Optional[List[str]] = None
    ) -> AggregatedResult:
        """
        Agrega múltiplos resultados de endpoints

        Args:
            results: Lista de resultados (cada um de um endpoint)
            dedup_keys: Campos para usar na deduplicação

        Returns:
            AggregatedResult com dados agregados
        """
        aggregated = AggregatedResult()

        all_rows = []
        seen_hashes: Set[str] = set()
        seen_endpoints: Set[str] = set()  # Track unique endpoint IDs

        # Processa cada resultado de endpoint
        for result in results:
            endpoint_id = result.get("endpoint_id", "unknown")

            if "error" in result:
                aggregated.endpoints_errors += 1
                continue

            # Count unique endpoints only
            seen_endpoints.add(endpoint_id)

            # Pega rows do endpoint
            rows = result.get("rows", [])

            for row in rows:
                aggregated.total_rows += 1

                # Deduplicação
                if self.deduplicate:
                    row_hash = self._hash_row(row, dedup_keys)

                    if row_hash in seen_hashes:
                        # Duplicado - conta estatística
                        aggregated.dedup_stats[endpoint_id] = \
                            aggregated.dedup_stats.get(endpoint_id, 0) + 1
                        continue

                    seen_hashes.add(row_hash)

                # Row único - adiciona
                aggregated.unique_rows += 1
                all_rows.append(row)

        aggregated.rows = all_rows
        aggregated.endpoints_responded = len(seen_endpoints)  # Set final count

        # Calcula estatísticas de campos
        aggregated.field_stats = self._calculate_field_stats(all_rows)

        return aggregated

    def _hash_row(
        self,
        row: Dict[str, Any],
        dedup_keys: Optional[List[str]] = None
    ) -> str:
        """
        Gera hash de uma row para deduplicação

        Args:
            row: Row para hashear
            dedup_keys: Campos específicos pra usar (None = usa todos)

        Returns:
            Hash string da row
        """
        if dedup_keys:
            # Usa apenas campos específicos
            key_values = tuple(sorted(
                (k, row.get(k)) for k in dedup_keys if k in row
            ))
        else:
            # Usa todos os campos (exceto endpoint metadata)
            key_values = tuple(sorted(
                (k, v) for k, v in row.items()
                if k not in ["endpoint", "endpoint_id", "_timestamp"]
            ))

        return str(hash(key_values))

    def _calculate_field_stats(
        self,
        rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas dos campos

        Args:
            rows: Rows para analisar

        Returns:
            Dicionário com estatísticas por campo
        """
        if not rows:
            return {}

        stats = {}

        # Pega todos os campos únicos
        all_fields = set()
        for row in rows:
            all_fields.update(row.keys())

        # Para cada campo, calcula estatísticas
        for field in all_fields:
            values = [row.get(field) for row in rows if field in row]

            if not values:
                continue

            # Conta valores únicos
            unique_values = len(set(str(v) for v in values))

            # Top 5 valores mais comuns
            counter = Counter(str(v) for v in values)
            top_values = counter.most_common(5)

            stats[field] = {
                "total": len(values),
                "unique": unique_values,
                "top_values": [
                    {"value": v, "count": c}
                    for v, c in top_values
                ],
            }

        return stats

    def export_json(self, result: AggregatedResult) -> str:
        """
        Exporta resultado para JSON

        Args:
            result: Resultado agregado

        Returns:
            JSON string
        """
        return json.dumps({
            "total_rows": result.total_rows,
            "unique_rows": result.unique_rows,
            "endpoints_responded": result.endpoints_responded,
            "rows": result.rows,
            "field_stats": result.field_stats,
        }, indent=2)

    def export_csv(self, result: AggregatedResult) -> str:
        """
        Exporta resultado para CSV

        Args:
            result: Resultado agregado

        Returns:
            CSV string
        """
        if not result.rows:
            return ""

        output = StringIO()

        # Pega todos os campos únicos
        fieldnames = set()
        for row in result.rows:
            fieldnames.update(row.keys())

        fieldnames = sorted(fieldnames)

        # Escreve CSV
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result.rows)

        return output.getvalue()

    def rank_by_score(
        self,
        result: AggregatedResult,
        score_field: str,
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Ranqueia resultados por um campo de score

        Args:
            result: Resultado agregado
            score_field: Campo numérico para ordenar
            reverse: True para ordem decrescente

        Returns:
            Lista ordenada de rows
        """
        return sorted(
            result.rows,
            key=lambda r: r.get(score_field, 0),
            reverse=reverse
        )
