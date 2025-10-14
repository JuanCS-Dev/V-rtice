"""
MIP Client Implementation

Cliente HTTP para Motor de Integridade Processual.
Wrapper sobre httpx com retry logic e circuit breaker.

Autor: Juan Carlos de Souza
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx


logger = logging.getLogger(__name__)


class MIPClientError(Exception):
    """Base exception para erros do MIP Client."""
    pass


class MIPTimeoutError(MIPClientError):
    """Exception para timeouts."""
    pass


class MIPClient:
    """
    Cliente HTTP para MIP API.
    
    Features:
    - Async HTTP calls via httpx
    - Retry logic com exponential backoff
    - Circuit breaker pattern
    - Timeout configuration
    - Graceful degradation
    
    Example:
        ```python
        mip = MIPClient("http://mip:8100")
        
        verdict = await mip.evaluate(action_plan)
        if verdict["status"] == "approved":
            # Execute plan
            pass
        ```
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8100",
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """
        Inicializa MIP Client.
        
        Args:
            base_url: URL base do MIP API
            timeout: Timeout em segundos
            max_retries: Máximo de tentativas
            circuit_breaker_threshold: Falhas antes de abrir circuit
            circuit_breaker_timeout: Tempo até retry após circuit abrir
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Circuit breaker
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.circuit_failures = 0
        self.circuit_open_until: Optional[datetime] = None
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )
        
        logger.info(f"MIP Client initialized: {self.base_url}")
    
    async def close(self):
        """Fecha HTTP client."""
        await self.client.aclose()
    
    def _is_circuit_open(self) -> bool:
        """Verifica se circuit breaker está aberto."""
        if self.circuit_open_until is None:
            return False
        
        if datetime.now() >= self.circuit_open_until:
            # Timeout expirou, reset circuit
            logger.info("Circuit breaker timeout expired, resetting")
            self.circuit_failures = 0
            self.circuit_open_until = None
            return False
        
        return True
    
    def _record_failure(self):
        """Registra falha e abre circuit se threshold atingido."""
        self.circuit_failures += 1
        
        if self.circuit_failures >= self.circuit_breaker_threshold:
            self.circuit_open_until = datetime.now() + timedelta(
                seconds=self.circuit_breaker_timeout
            )
            logger.warning(
                f"Circuit breaker opened after {self.circuit_failures} failures. "
                f"Will retry at {self.circuit_open_until}"
            )
    
    def _record_success(self):
        """Registra sucesso e reset circuit."""
        if self.circuit_failures > 0:
            logger.info(f"Request succeeded, resetting {self.circuit_failures} failures")
            self.circuit_failures = 0
            self.circuit_open_until = None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica health do MIP service.
        
        Returns:
            Dict com status e informações
            
        Raises:
            MIPClientError: Se health check falha
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise MIPClientError(f"Health check failed: {e}")
    
    async def evaluate(
        self,
        action_plan: Dict[str, Any],
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Avalia um ActionPlan.
        
        Args:
            action_plan: Dicionário com ActionPlan serializado
            retry: Se True, faz retry com exponential backoff
            
        Returns:
            Dict com EthicalVerdict e timing
            
        Raises:
            MIPClientError: Se avaliação falha
            MIPTimeoutError: Se timeout
        """
        # Check circuit breaker
        if self._is_circuit_open():
            raise MIPClientError(
                f"Circuit breaker is open until {self.circuit_open_until}. "
                "MIP service temporarily unavailable."
            )
        
        # Prepare request
        payload = {"plan": action_plan}
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries if retry else 1):
            try:
                logger.debug(f"MIP evaluate attempt {attempt + 1}/{self.max_retries}")
                
                response = await self.client.post(
                    "/evaluate",
                    json=payload,
                    timeout=self.timeout,
                )
                
                response.raise_for_status()
                result = response.json()
                
                self._record_success()
                logger.info(
                    f"MIP evaluate succeeded: {result['verdict']['status']} "
                    f"(score: {result['verdict'].get('aggregate_score', 'N/A')})"
                )
                
                return result
                
            except httpx.TimeoutException as e:
                last_error = MIPTimeoutError(f"MIP request timeout after {self.timeout}s")
                logger.warning(f"Attempt {attempt + 1} timeout: {e}")
                
            except httpx.HTTPStatusError as e:
                last_error = MIPClientError(
                    f"MIP returned {e.response.status_code}: {e.response.text}"
                )
                logger.error(f"Attempt {attempt + 1} HTTP error: {e}")
                
                # Don't retry 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    break
                
            except Exception as e:
                last_error = MIPClientError(f"MIP request failed: {e}")
                logger.error(f"Attempt {attempt + 1} error: {e}")
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, ...
                logger.debug(f"Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        self._record_failure()
        raise last_error
    
    async def get_principle(self, principle_id: str) -> Dict[str, Any]:
        """
        Busca princípio por ID.
        
        Args:
            principle_id: UUID do princípio
            
        Returns:
            Dict com Principle
            
        Raises:
            MIPClientError: Se falha
        """
        try:
            response = await self.client.get(f"/principles/{principle_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MIPClientError(f"Failed to get principle: {e}")
    
    async def list_principles(
        self,
        level: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Lista princípios.
        
        Args:
            level: Filtrar por level (opcional)
            
        Returns:
            Lista de princípios
        """
        try:
            params = {"level": level} if level else {}
            response = await self.client.get("/principles", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MIPClientError(f"Failed to list principles: {e}")
    
    async def get_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Busca decisão do audit trail.
        
        Args:
            decision_id: UUID da decisão
            
        Returns:
            Dict com Decision
        """
        try:
            response = await self.client.get(f"/decisions/{decision_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MIPClientError(f"Failed to get decision: {e}")
    
    async def get_audit_trail(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Dict[str, Any]]:
        """
        Lista audit trail.
        
        Args:
            limit: Máximo de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de decisões
        """
        try:
            params = {"limit": limit, "offset": offset}
            response = await self.client.get("/audit-trail", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MIPClientError(f"Failed to get audit trail: {e}")


# Context manager support
class MIPClientContext:
    """Context manager para MIPClient."""
    
    def __init__(self, *args, **kwargs):
        self.client = MIPClient(*args, **kwargs)
    
    async def __aenter__(self):
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()
