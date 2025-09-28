"""
Rate Limiter - Controle de taxa de requisições
Projeto Vértice - SSP-GO
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Controla taxa de requisições por domínio"""
    
    def __init__(self, default_delay: float = 1.0):
        self.default_delay = default_delay
        self.domain_delays: Dict[str, float] = {}
        self.last_request: Dict[str, float] = defaultdict(float)
        self.request_counts: Dict[str, int] = defaultdict(int)
        
        # Configurações específicas por domínio
        self.domain_configs = {
            "instagram.com": {"delay": 3.0, "max_per_minute": 20},
            "twitter.com": {"delay": 2.0, "max_per_minute": 30},
            "linkedin.com": {"delay": 5.0, "max_per_minute": 10},
            "facebook.com": {"delay": 3.0, "max_per_minute": 20},
            "discord.com": {"delay": 1.0, "max_per_minute": 60}
        }
        
    async def wait_if_needed(self, domain: str):
        """Aguarda se necessário antes da próxima requisição"""
        
        # Extrair domínio base
        domain = self._extract_domain(domain)
        
        # Obter configuração do domínio
        config = self.domain_configs.get(domain, {})
        delay = config.get("delay", self.default_delay)
        max_per_minute = config.get("max_per_minute", 60)
        
        # Verificar última requisição
        last_request = self.last_request[domain]
        time_since_last = time.time() - last_request
        
        # Aguardar se necessário
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.debug(f"Rate limit: aguardando {wait_time:.2f}s para {domain}")
            await asyncio.sleep(wait_time)
            
        # Verificar limite por minuto
        current_minute = int(time.time() / 60)
        minute_key = f"{domain}:{current_minute}"
        
        if self.request_counts[minute_key] >= max_per_minute:
            wait_time = 60 - (time.time() % 60)
            logger.warning(f"Limite por minuto atingido para {domain}, aguardando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
        # Atualizar contadores
        self.last_request[domain] = time.time()
        self.request_counts[minute_key] += 1
        
    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
        else:
            domain = url.split("/")[0]
            
        # Remover www
        if domain.startswith("www."):
            domain = domain[4:]
            
        return domain
        
    def set_domain_delay(self, domain: str, delay: float):
        """Define delay específico para domínio"""
        self.domain_configs[domain] = {"delay": delay}
        
    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso"""
        stats = {
            "total_requests": sum(self.request_counts.values()),
            "domains_accessed": list(self.last_request.keys()),
            "current_minute_requests": {}
        }
        
        current_minute = int(time.time() / 60)
        for key, count in self.request_counts.items():
            if f":{current_minute}" in key:
                domain = key.split(":")[0]
                stats["current_minute_requests"][domain] = count
                
        return stats
