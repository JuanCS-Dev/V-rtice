"""
API Gateway Connector
Conecta ao API Gateway principal (porta 8000) para obter status de todos os serviços
"""

import os
from typing import Dict, Any, Optional, List
from .base import BaseConnector


class APIGatewayConnector(BaseConnector):
    """
    Connector para o API Gateway do Vértice Platform
    Permite verificar status de todos os 45 serviços backend
    """

    def __init__(self):
        """Inicializa connector com API Gateway URL"""
        base_url = os.getenv("VITE_API_GATEWAY_URL", "http://localhost:8000")
        super().__init__(service_name="API Gateway", base_url=base_url)

    async def health_check(self) -> bool:
        """
        Verifica se o API Gateway está online

        Returns:
            bool: True se o gateway está online
        """
        try:
            result = await self._get("/health")
            return result is not None and result.get("status") == "healthy"
        except Exception:
            return False

    async def get_gateway_status(self) -> Optional[Dict[str, Any]]:
        """
        Obtém status geral do API Gateway

        Returns:
            Optional[Dict]: Status do gateway com informações de sistema
        """
        return await self._get("/")

    async def get_services_status(self) -> Optional[Dict[str, Any]]:
        """
        Obtém status de todos os serviços backend

        Returns:
            Optional[Dict]: Dicionário com status de cada serviço
        """
        return await self._get("/api/services/status")

    async def get_services_list(self) -> Optional[List[Dict[str, Any]]]:
        """
        Lista todos os serviços disponíveis

        Returns:
            Optional[List]: Lista de serviços com suas informações
        """
        result = await self._get("/api/services")
        if result and isinstance(result, dict):
            return result.get("services", [])
        return []

    async def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Obtém métricas do sistema (CPU, Mem, Network)

        Returns:
            Optional[Dict]: Métricas do sistema
        """
        return await self._get("/api/metrics")

    async def get_system_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações gerais do sistema

        Returns:
            Optional[Dict]: Informações do sistema (uptime, version, etc)
        """
        return await self._get("/api/system/info")

    async def close(self) -> None:
        """Fecha a conexão HTTP"""
        await self.client.aclose()
