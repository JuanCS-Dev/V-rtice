from typing import Dict, Any, Optional
from .base import BaseConnector


class AIAgentConnector(BaseConnector):
    """
    Conector para o Maximus AI Agent Service.
    Lida com a comunicação com o serviço de IA para queries e análises.
    """

    def __init__(self):
        """
        Inicializa o AIAgentConnector com o nome e a URL base para o serviço AI Agent.
        """
        # CORREÇÃO: Porta correta é 8017 (ai_agent_service)
        super().__init__(
            service_name="Maximus AI Agent", base_url="http://localhost:8017"
        )

    async def health_check(self) -> bool:
        """
        Verifica a saúde do serviço Maximus AI Agent.
        """
        try:
            # O endpoint /health é mais comum que /, vamos usar ele.
            data = await self._get("/health")
            # A checagem de status pode variar, 'healthy' ou 'ok' são comuns.
            return data is not None and data.get("status") in [
                "healthy",
                "ok",
                "operational",
            ]
        except Exception:
            return False

    async def query(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Envia uma pergunta para a Maximus AI e retorna sua resposta.
        """
        # Schema real: messages array com role + content
        # Using /test-gemini for now (bypasses reasoning engine)
        return await self._post(
            "/test-gemini", data={"messages": [{"role": "user", "content": prompt}]}
        )

    async def analyze(self, context: str) -> Optional[Dict[str, Any]]:
        """
        Envia um contexto para análise à Maximus AI.
        """
        # Usa /chat com prompt de análise
        return await self._post(
            "/chat",
            data={
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analise o seguinte contexto:\n\n{context}",
                    }
                ]
            },
        )

    async def investigate(self, incident: str) -> Optional[Dict[str, Any]]:
        """
        Envia um incidente para investigação à Maximus AI.
        """
        # Usa /chat com prompt de investigação
        return await self._post(
            "/chat",
            data={
                "messages": [
                    {
                        "role": "user",
                        "content": f"Investigue este incidente de segurança:\n\n{incident}",
                    }
                ]
            },
        )
