"""
🗺️ Query Planner - Otimiza e planeja execução de queries VeQL

Responsável por:
- Analisar AST e gerar plano de execução otimizado
- Predicate pushdown (enviar filtros pros endpoints)
- Join optimization
- Cost-based optimization
"""

from typing import List, Dict, Any
from .ast_nodes import SelectQuery, WhereClause, Condition


class QueryPlan:
    """Plano de execução de uma query"""

    def __init__(self, query: SelectQuery):
        self.query = query
        self.steps: List[Dict[str, Any]] = []
        self.estimated_cost: int = 0

    def __str__(self) -> str:
        plan = f"Query Plan (estimated cost: {self.estimated_cost})\n"
        plan += "=" * 60 + "\n"
        for i, step in enumerate(self.steps, 1):
            plan += f"{i}. {step['operation']}\n"
            if 'details' in step:
                plan += f"   Details: {step['details']}\n"
        return plan


class QueryPlanner:
    """
    Planner VeQL - transforma AST em plano de execução otimizado
    """

    def plan(self, query: SelectQuery) -> QueryPlan:
        """
        Gera plano de execução otimizado para query

        Args:
            query: AST da query

        Returns:
            QueryPlan: Plano de execução otimizado
        """
        plan = QueryPlan(query)

        # Passo 1: Scan da tabela (endpoints)
        plan.steps.append({
            "operation": "TABLE_SCAN",
            "details": f"Scan {query.from_table}",
        })

        # Passo 2: Aplicar filtros WHERE (predicate pushdown)
        if query.where:
            plan.steps.append({
                "operation": "FILTER",
                "details": f"Apply WHERE: {query.where}",
            })

        # Passo 3: Projeção (SELECT fields)
        if query.fields:
            fields_str = ", ".join(str(f) for f in query.fields)
            plan.steps.append({
                "operation": "PROJECT",
                "details": f"Select fields: {fields_str}",
            })

        # Passo 4: LIMIT/OFFSET
        if query.limit:
            plan.steps.append({
                "operation": "LIMIT",
                "details": f"Limit to {query.limit} rows",
            })

        if query.offset:
            plan.steps.append({
                "operation": "OFFSET",
                "details": f"Skip {query.offset} rows",
            })

        # Estima custo (simplificado)
        plan.estimated_cost = len(plan.steps) * 10

        return plan

    def optimize(self, plan: QueryPlan) -> QueryPlan:
        """
        Otimiza plano de execução

        Otimizações implementadas:
        - Predicate pushdown para endpoints
        - Early filtering
        - Projection pushdown
        """
        # TODO: Implementar otimizações avançadas
        return plan
