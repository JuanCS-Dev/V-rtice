"""
Base Scraper - Classe base para todos os scrapers
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fake_useragent import UserAgent
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Classe base abstrata para scrapers"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = self._get_default_headers()
        
    def _get_default_headers(self) -> dict:
        """Headers padrão para requisições"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    async def __aenter__(self):
        """Entrada do context manager"""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Saída do context manager"""
        if self.session:
            await self.session.close()
            
    async def create_session(self):
        """Cria sessão se não existir"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers
            )
            
    async def close_session(self):
        """Fecha sessão se existir"""
        if self.session:
            await self.session.close()
            self.session = None
            
    @abstractmethod
    async def scrape(self, *args, **kwargs) -> Dict[str, Any]:
        """Método abstrato para scraping - deve ser implementado"""
        pass
        
    async def fetch(self, url: str, method: str = "GET", **kwargs) -> Optional[str]:
        """Método genérico para fazer requisições"""
        try:
            await self.create_session()
            
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Status {response.status} para {url}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout ao acessar {url}")
            return None
        except Exception as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            return None
            
    def sanitize_input(self, text: str) -> str:
        """Sanitiza entrada do usuário"""
        if not text:
            return ""
        # Remove caracteres perigosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text.strip()
        
    def validate_url(self, url: str) -> bool:
        """Valida se URL é válida e segura"""
        if not url:
            return False
        
        # Verificar protocolo
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Verificar caracteres suspeitos
        suspicious = ['javascript:', 'data:', 'vbscript:', 'file:']
        for pattern in suspicious:
            if pattern in url.lower():
                return False
                
        return True
