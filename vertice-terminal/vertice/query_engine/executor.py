"""
⚡ Query Executor - Executa queries VeQL contra endpoints

Responsável por:
- Executar query plan nos endpoints
- Parallel execution (async)
- Result aggregation com Fleet Manager
- Timeout handling
"""

import asyncio
from typing import List, Dict, Any, Optional
from .planner import QueryPlan
from .ast_nodes import SelectQuery


class QueryResult:
    """Resultado de uma query VeQL"""

    def __init__(self):
        self.rows: List[Dict[str, Any]] = []
        self.total_rows: int = 0
        self.execution_time_ms: float = 0
        self.endpoints_queried: int = 0
        self.errors: List[str] = []

    def add_row(self, row: Dict[str, Any]) -> None:
        """Adiciona linha ao resultado"""
        self.rows.append(row)
        self.total_rows += 1

    def __str__(self) -> str:
        result = f"Query Result\n"
        result += "=" * 60 + "\n"
        result += f"Rows: {self.total_rows}\n"
        result += f"Execution Time: {self.execution_time_ms:.2f}ms\n"
        result += f"Endpoints Queried: {self.endpoints_queried}\n"
        if self.errors:
            result += f"Errors: {len(self.errors)}\n"
        return result


class QueryExecutor:
    """
    Executor VeQL - executa queries contra fleet de endpoints
    """

    def __init__(
        self,
        endpoints: Optional[List[str]] = None,
        registry = None,  # EndpointRegistry
        aggregator = None,  # ResultAggregator
    ):
        """
        Args:
            endpoints: Lista de endpoint IDs (se None, usa todos do registry)
            registry: EndpointRegistry para buscar endpoints
            aggregator: ResultAggregator para agregar resultados
        """
        self.endpoints = endpoints
        self.registry = registry
        self.aggregator = aggregator

    async def execute(self, plan: QueryPlan) -> QueryResult:
        """
        Executa query plan e retorna resultados

        Args:
            plan: Plano de execução gerado pelo Planner

        Returns:
            QueryResult: Resultados agregados da query
        """
        import time
        start = time.time()

        result = QueryResult()

        # Resolve endpoints para executar
        target_endpoints = await self._resolve_endpoints()
        result.endpoints_queried = len(target_endpoints)

        # Executa em paralelo em todos os endpoints
        if target_endpoints:
            tasks = [
                self._execute_on_endpoint(ep_id, plan)
                for ep_id in target_endpoints
            ]
            endpoint_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Agrega resultados com ResultAggregator se disponível
            if self.aggregator:
                formatted_results = []
                for i, ep_result in enumerate(endpoint_results):
                    if isinstance(ep_result, Exception):
                        formatted_results.append({
                            "endpoint_id": target_endpoints[i],
                            "error": str(ep_result),
                        })
                        result.errors.append(str(ep_result))
                    else:
                        formatted_results.append({
                            "endpoint_id": target_endpoints[i],
                            "rows": ep_result,
                        })

                aggregated = self.aggregator.aggregate(formatted_results)
                result.rows = aggregated.rows
                result.total_rows = aggregated.unique_rows
            else:
                # Sem aggregator - apenas junta tudo
                for ep_result in endpoint_results:
                    if isinstance(ep_result, Exception):
                        result.errors.append(str(ep_result))
                    elif ep_result:
                        for row in ep_result:
                            result.add_row(row)

        # Calcula tempo de execução
        result.execution_time_ms = (time.time() - start) * 1000

        return result

    async def _resolve_endpoints(self) -> List[str]:
        """
        Resolve lista de endpoints para executar query

        Returns:
            Lista de endpoint IDs
        """
        # Se endpoints foi especificado, usa eles
        if self.endpoints:
            return self.endpoints

        # Senão, busca todos ONLINE do registry
        if self.registry:
            from ..fleet import EndpointStatus
            endpoints = self.registry.list(status=EndpointStatus.ONLINE)
            return [ep.id for ep in endpoints]

        # Fallback - nenhum endpoint
        return []

    async def _execute_on_endpoint(
        self, endpoint: str, plan: QueryPlan
    ) -> List[Dict[str, Any]]:
        """
        Executa query em um endpoint específico

        Args:
            endpoint: Endpoint ID/hostname
            plan: Plano de execução

        Returns:
            List de rows retornadas do endpoint
        """
        # Simula latência de rede
        await asyncio.sleep(0.1)

        # TODO: Implementar comunicação real com endpoints (gRPC)
        # Por enquanto, retorna dados mock

        return [
            {
                "endpoint": endpoint,
                "process.name": "powershell.exe",
                "process.pid": 1234,
            }
        ]

    def execute_sync(self, plan: QueryPlan) -> QueryResult:
        """
        Versão síncrona do execute (wrapper)

        Args:
            plan: Plano de execução

        Returns:
            QueryResult: Resultados da query
        """
        return asyncio.run(self.execute(plan))
