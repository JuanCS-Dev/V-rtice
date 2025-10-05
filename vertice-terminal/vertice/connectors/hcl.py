"""
HCL Connector - Human-Centric Language
======================================

Conector para serviços HCL (Human-Centric Language).

Serviços integrados:
    - HCL Analyzer (intent analysis)
    - HCL Executor (workflow execution)
    - HCL Planner (plan generation)
    - HCL KB (knowledge base)
    - HCL Monitor (execution monitoring)

Author: Vértice Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from .base import BaseConnector


class HCLConnector(BaseConnector):
    """
    Conector para serviços HCL (Human-Centric Language).

    HCL é uma linguagem de alto nível que permite expressar intents
    complexos em linguagem natural/semi-estruturada.
    """

    def __init__(self):
        """Inicializa HCLConnector via Maximus AI Core."""
        super().__init__(
            service_name="HCL Services (via Maximus)",
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

    async def analyze_intent(self, hcl_code: str) -> Optional[Dict[str, Any]]:
        """
        Analisa intent de código HCL.

        Args:
            hcl_code: Código HCL ou intent em linguagem natural

        Returns:
            Intent estruturado e plano de execução

        Examples:
            >>> results = await connector.analyze_intent(
            ...     "Scan network 192.168.1.0/24 and report vulnerabilities"
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "hcl_analyze",
                "params": {"code": hcl_code}
            }
        )

    async def execute_workflow(
        self,
        hcl_code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa workflow HCL.

        Args:
            hcl_code: Código HCL ou workflow
            context: Contexto de execução (variáveis, configs, etc)

        Returns:
            Resultado da execução

        Examples:
            >>> results = await connector.execute_workflow(
            ...     '''
            ...     workflow "security_audit" {
            ...         scan network = "10.0.0.0/8"
            ...         analyze vulnerabilities
            ...         report high_severity
            ...     }
            ...     ''',
            ...     context={"notification_email": "admin@example.com"}
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "hcl_execute",
                "params": {"code": hcl_code, "context": context or {}}
            }
        )

    async def generate_plan(self, objective: str) -> Optional[Dict[str, Any]]:
        """
        Gera plano de execução HCL para objetivo.

        Args:
            objective: Objetivo em linguagem natural

        Returns:
            Plano HCL gerado

        Examples:
            >>> results = await connector.generate_plan(
            ...     "Perform comprehensive security assessment of web application"
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "hcl_plan",
                "params": {"objective": objective}
            }
        )

    async def query_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta knowledge base HCL.

        Args:
            query: Query de busca
            category: Categoria (None = todas)

        Returns:
            Conhecimento relevante do KB

        Examples:
            >>> results = await connector.query_knowledge_base(
            ...     "best practices for API security testing",
            ...     category="security"
            ... )
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "hcl_kb_query",
                "params": {"query": query, "category": category}
            }
        )

    async def monitor_execution(
        self,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Monitora execução de workflow HCL.

        Args:
            execution_id: ID da execução

        Returns:
            Status e progresso da execução

        Examples:
            >>> results = await connector.monitor_execution("exec_123")
        """
        return await self._post(
            "/api/tool-call",
            data={
                "tool_name": "hcl_monitor",
                "params": {"execution_id": execution_id}
            }
        )

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
