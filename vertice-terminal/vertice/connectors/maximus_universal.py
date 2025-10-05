"""
Maximus Universal Connector - AI-First Orchestration
=====================================================

Conector universal que usa Maximus AI Core para orquestração inteligente.

Arquitetura:
    CLI → MaximusUniversalConnector → Maximus AI Core → Autonomous Tool Selection → Services

Capabilities:
    - Intelligent query processing with reasoning engine
    - Autonomous tool selection based on context
    - Parallel tool execution via Tool Orchestrator
    - Memory-aware conversations (working + episodic + semantic)
    - Confidence scoring and validation
    - Graceful degradation

Author: Vértice Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from .base import BaseConnector
import uuid


class MaximusUniversalConnector(BaseConnector):
    """
    Conector universal para Maximus AI Core.

    Este conector permite interação inteligente com todos os 60+ serviços
    do backend através do Maximus AI, que decide autonomamente quais tools
    usar baseado no contexto e intent do usuário.
    """

    def __init__(self):
        """
        Inicializa o MaximusUniversalConnector.

        Conecta ao Maximus AI Core (porta 8001) que orquestra todos os serviços.
        """
        super().__init__(
            service_name="Maximus AI Core",
            base_url="http://localhost:8001",
            timeout=120  # Timeout maior para operações complexas
        )

    async def health_check(self) -> bool:
        """
        Verifica a saúde do Maximus AI Core.

        Returns:
            bool: True se Maximus está online e operacional
        """
        try:
            data = await self._get("/health")
            return data is not None and data.get("status") in [
                "healthy",
                "ok",
                "operational",
            ]
        except Exception:
            return False

    async def intelligent_query(
        self,
        query: str,
        mode: str = "autonomous",
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: str = "cli_user"
    ) -> Optional[Dict[str, Any]]:
        """
        Faz uma query inteligente para Maximus AI.

        Maximus usa seu reasoning engine para:
        1. Entender o intent do usuário
        2. Decidir quais tools usar (pode ser múltiplas)
        3. Executar tools em paralelo (quando possível)
        4. Consolidar resultados com contexto e memória
        5. Retornar resposta acionável com confidence score

        Args:
            query: Pergunta/comando em linguagem natural
            mode: "autonomous" (Maximus decide tudo) | "guided" (com hints) | "deep" (análise profunda)
            context: Contexto adicional (ex: {"investigation_type": "defensive"})
            session_id: ID da sessão (para memória conversacional)
            user_id: ID do usuário (default: cli_user)

        Returns:
            Dict contendo:
                - response: str (resposta principal)
                - tools_used: List[Dict] (tools executadas)
                - reasoning_trace: Dict (chain-of-thought completo)
                - confidence: float (0-100)
                - session_id: str (para continuar conversa)

        Examples:
            >>> connector = MaximusUniversalConnector()
            >>> result = await connector.intelligent_query("Analise vulnerabilidades em example.com")
            >>> print(result["response"])
            >>> print(f"Confidence: {result['confidence']}%")
            >>> print(f"Tools used: {[t['tool_name'] for t in result['tools_used']]}")
        """
        # Gera session_id se não fornecido
        if not session_id:
            session_id = str(uuid.uuid4())

        # Build message payload
        messages = [{"role": "user", "content": query}]

        # Add context as system message if provided
        if context:
            system_msg = f"Context: {context}"
            messages.insert(0, {"role": "system", "content": system_msg})

        # Adjust parameters based on mode
        max_tokens = 4096
        temperature = 0.7

        if mode == "deep":
            max_tokens = 8192
            temperature = 0.5  # More focused for deep analysis
        elif mode == "guided":
            temperature = 0.9  # More creative for guided exploration

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "conversation_id": session_id,
            "user_id": user_id
        }

        # Call Maximus AI Core - usa /chat endpoint com reasoning engine completo
        return await self._post("/chat", data=payload)

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa uma tool específica via Maximus AI Core.

        Útil quando você sabe exatamente qual tool quer executar,
        mas ainda quer aproveitar:
        - Validation automática de inputs
        - Confidence scoring
        - Error handling robusto
        - Result caching

        Args:
            tool_name: Nome da tool (ex: "threat_intel", "nmap_scan", "osint_search")
            params: Parâmetros da tool
            context: Contexto adicional

        Returns:
            Dict contendo resultado da tool execution

        Examples:
            >>> result = await connector.execute_tool(
            ...     "threat_intel",
            ...     {"target": "1.2.3.4", "target_type": "ip"}
            ... )
        """
        payload = {
            "tool_name": tool_name,
            "params": params,
            "context": context or {}
        }

        return await self._post("/api/tool-call", data=payload)

    async def multi_tool_investigation(
        self,
        target: str,
        investigation_type: str = "auto",
        tools: Optional[List[str]] = None,
        parallel: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Executa investigação multi-tool em paralelo.

        Maximus AI Core usa o Tool Orchestrator para:
        - Executar múltiplas tools simultaneamente (max 5 concurrent)
        - Aplicar caching automático (TTL 5 min)
        - Retry inteligente em caso de falha
        - Validar resultados com confidence scoring
        - Consolidar findings

        Args:
            target: Target da investigação (IP, domain, hash, username, etc)
            investigation_type: "auto" | "defensive" | "offensive" | "full"
            tools: Lista de tools específicas (None = Maximus decide)
            parallel: Se True, executa tools em paralelo

        Returns:
            Dict contendo:
                - summary: str (resumo executivo)
                - findings: List[Dict] (findings organizados por severidade)
                - tools_executed: List[str] (tools que foram executadas)
                - execution_time_ms: int (tempo total)
                - confidence: float (confiança geral)

        Examples:
            >>> result = await connector.multi_tool_investigation(
            ...     target="example.com",
            ...     investigation_type="defensive"
            ... )
            >>> print(result["summary"])
            >>> for finding in result["findings"]:
            ...     print(f"[{finding['severity']}] {finding['description']}")
        """
        # Build investigation request
        payload = {
            "target": target,
            "investigation_type": investigation_type,
            "parallel": parallel
        }

        if tools:
            payload["tools"] = tools

        # Call Maximus investigation endpoint
        # Maximus vai usar o reasoning engine para decidir estratégia
        query = f"Investigue o target '{target}' usando análise {investigation_type}."

        if tools:
            query += f" Use as seguintes tools: {', '.join(tools)}."

        return await self.intelligent_query(query, mode="deep", context=payload)

    async def get_available_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retorna lista de todas as tools disponíveis no Maximus AI Core.

        Inclui:
        - World-class tools (17 NSA-grade)
        - Offensive arsenal tools (15)
        - All services tools (29)

        Returns:
            List de dicts contendo:
                - name: str
                - category: str
                - description: str
                - complexity: str
                - avg_execution_time: str

        Examples:
            >>> tools = await connector.get_available_tools()
            >>> for tool in tools:
            ...     print(f"{tool['name']}: {tool['description']}")
        """
        data = await self._get("/api/tools/complete")

        if not data:
            return None

        # Flatten tool catalog
        all_tools = []

        # World-class tools
        for tool_name, tool_info in data.get("world_class_tools", {}).get("catalog", {}).items():
            all_tools.append({
                "name": tool_name,
                "category": "world_class",
                "description": tool_info.get("description", ""),
                "complexity": tool_info.get("complexity", "medium"),
                "avg_execution_time": tool_info.get("avg_execution_time", "unknown")
            })

        # Offensive arsenal
        for tool_name in data.get("offensive_arsenal", {}).get("tools", []):
            all_tools.append({
                "name": tool_name,
                "category": "offensive",
                "description": data["offensive_arsenal"]["catalog"].get(tool_name, ""),
                "complexity": "high",
                "avg_execution_time": "varies"
            })

        # All services tools
        categories = data.get("all_services", {}).get("categories", {})
        for category, tool_names in categories.items():
            for tool_name in tool_names:
                all_tools.append({
                    "name": tool_name,
                    "category": category,
                    "description": f"{category.upper()} service integration",
                    "complexity": "medium",
                    "avg_execution_time": "varies"
                })

        return all_tools

    async def get_tool_stats(self, tool_name: str, last_n_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Retorna estatísticas de uso de uma tool.

        Args:
            tool_name: Nome da tool
            last_n_days: Últimos N dias de dados

        Returns:
            Dict contendo:
                - total_executions: int
                - success_rate: float
                - avg_execution_time_ms: float
                - error_types: Dict[str, int]
        """
        return await self._get(f"/memory/tool-stats/{tool_name}?last_n_days={last_n_days}")

    async def get_memory_stats(self) -> Optional[Dict[str, Any]]:
        """
        Retorna estatísticas do sistema de memória do Maximus.

        Returns:
            Dict contendo:
                - total_conversations: int
                - total_messages: int
                - total_investigations: int
                - memory_usage_mb: float
        """
        return await self._get("/memory/stats")

    async def recall_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera uma conversa anterior da memória.

        Args:
            session_id: ID da sessão a recuperar

        Returns:
            Dict contendo histórico da conversa
        """
        return await self._get(f"/memory/conversation/{session_id}")

    async def find_similar_investigations(
        self,
        target: str,
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Busca investigações similares ao target fornecido.

        Maximus usa embeddings semânticos para encontrar investigações
        relacionadas no histórico.

        Args:
            target: Target para buscar similares
            limit: Número máximo de resultados

        Returns:
            Lista de investigações similares
        """
        return await self._get(f"/memory/investigations/similar/{target}?limit={limit}")

    async def close(self):
        """Fecha o cliente HTTP."""
        await self.client.aclose()
