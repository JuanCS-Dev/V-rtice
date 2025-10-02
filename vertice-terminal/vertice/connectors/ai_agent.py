from typing import Dict, Any, Optional
from .base import BaseConnector

class AIAgentConnector(BaseConnector):
    """
    Conector para o Aurora AI Agent Service.
    Lida com a comunicação com o serviço de IA para queries e análises.
    """

    def __init__(self):
        """
        Inicializa o AIAgentConnector com o nome e a URL base para o serviço AI Agent.
        """
        # CORREÇÃO: Adicionamos o 'service_name' obrigatório na chamada do super().
        super().__init__(service_name="Aurora AI Agent", base_url="http://localhost:8001")

    async def health_check(self) -> bool:
        """
        Verifica a saúde do serviço Aurora AI Agent.
        """
        try:
            # O endpoint /health é mais comum que /, vamos usar ele.
            data = await self._get("/health")
            # A checagem de status pode variar, 'healthy' ou 'ok' são comuns.
            return data is not None and data.get("status") in ["healthy", "ok", "operational"]
        except Exception:
            return False

    async def query(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Envia uma pergunta para a Aurora AI e retorna sua resposta.
        """
        # O endpoint do blueprint é /chat. O corpo da requisição espera um JSON com a chave 'message'.
        return await self._post("/chat", json={"message": prompt})

    async def analyze(self, context: str) -> Optional[Dict[str, Any]]:
        """
        Envia um contexto para análise à Aurora AI.
        """
        # Supondo um endpoint /analyze que espera um JSON com a chave 'context'.
        return await self._post("/analyze", json={"context": context})

    async def investigate(self, incident: str) -> Optional[Dict[str, Any]]:
        """
        Envia um incidente para investigação à Aurora AI.
        """
        # Supondo um endpoint /investigate que espera um JSON com a chave 'incident'.
        return await self._post("/investigate", json={"incident": incident})
