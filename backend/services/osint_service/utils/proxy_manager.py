"""
Proxy Manager - Gerenciamento de proxies para scraping
Projeto Vértice - SSP-GO
"""

import random
from typing import List, Optional, Dict
import aiohttp
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    """Gerencia pool de proxies para rotação"""
    
    def __init__(self):
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.failed_proxies: set = set()
        
    def add_proxy(self, proxy: str, proxy_type: str = "http"):
        """Adiciona proxy ao pool"""
        proxy_dict = {
            "url": proxy,
            "type": proxy_type,
            "failures": 0,
            "last_used": None
        }
        self.proxies.append(proxy_dict)
        
    def get_proxy(self) -> Optional[str]:
        """Retorna próximo proxy disponível"""
        if not self.proxies:
            return None
            
        # Filtrar proxies que não falharam muito
        available = [p for p in self.proxies 
                    if p["url"] not in self.failed_proxies]
        
        if not available:
            # Reset failed proxies se não houver mais disponíveis
            self.failed_proxies.clear()
            available = self.proxies
            
        # Rotação round-robin
        proxy = available[self.current_index % len(available)]
        self.current_index += 1
        
        return proxy["url"]
        
    def mark_failed(self, proxy_url: str):
        """Marca proxy como falho"""
        self.failed_proxies.add(proxy_url)
        
        for proxy in self.proxies:
            if proxy["url"] == proxy_url:
                proxy["failures"] += 1
                if proxy["failures"] > 3:
                    logger.warning(f"Proxy {proxy_url} falhou múltiplas vezes")
                    
    async def test_proxy(self, proxy_url: str) -> bool:
        """Testa se proxy está funcionando"""
        test_url = "http://httpbin.org/ip"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Proxy {proxy_url} funcionando: {data.get('origin')}")
                        return True
                        
        except Exception as e:
            logger.error(f"Proxy {proxy_url} falhou: {e}")
            
        return False
        
    async def validate_all_proxies(self):
        """Valida todos os proxies do pool"""
        for proxy in self.proxies:
            is_working = await self.test_proxy(proxy["url"])
            if not is_working:
                self.failed_proxies.add(proxy["url"])
                
        logger.info(f"Proxies válidos: {len(self.proxies) - len(self.failed_proxies)}/{len(self.proxies)}")
