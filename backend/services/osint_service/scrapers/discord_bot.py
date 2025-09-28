"""
Discord Bot Scraper - Extração de dados do Discord
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class DiscordScraper(BaseScraper):
    """Scraper especializado para Discord"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://discord.com/api/v9"
        
    async def scrape(self, identifier: str, **kwargs) -> Dict:
        """Scrape Discord user/server data"""
        
        result = {
            "platform": "discord",
            "identifier": identifier,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }
        
        # Se for ID numérico (Snowflake)
        if identifier.isdigit():
            user_data = await self.analyze_snowflake(int(identifier))
            result["data"]["snowflake_analysis"] = user_data
            
        # Buscar informações públicas
        public_data = await self.get_public_info(identifier)
        result["data"]["public_info"] = public_data
        
        return result
        
    async def analyze_snowflake(self, snowflake_id: int) -> Dict:
        """Analisa Discord Snowflake ID"""
        
        # Discord Epoch (2015-01-01)
        DISCORD_EPOCH = 1420070400000
        
        # Extrair timestamp do Snowflake
        timestamp_ms = ((snowflake_id >> 22) + DISCORD_EPOCH)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
        
        # Extrair outros componentes
        worker_id = (snowflake_id & 0x3E0000) >> 17
        process_id = (snowflake_id & 0x1F000) >> 12
        increment = snowflake_id & 0xFFF
        
        return {
            "id": str(snowflake_id),
            "created_at": timestamp.isoformat(),
            "account_age_days": (datetime.utcnow() - timestamp).days,
            "technical": {
                "worker_id": worker_id,
                "process_id": process_id,
                "increment": increment,
                "timestamp_ms": timestamp_ms
            }
        }
        
    async def get_public_info(self, identifier: str) -> Dict:
        """Busca informações públicas"""
        
        info = {
            "found": False,
            "profile": None,
            "servers": [],
            "activities": []
        }
        
        # Verificar widgets públicos de servidores
        # Discord limita muito o acesso sem autenticação
        
        try:
            # Tentar buscar via widget (se for server ID)
            if identifier.isdigit():
                widget_url = f"https://discord.com/api/guilds/{identifier}/widget.json"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(widget_url) as response:
                        if response.status == 200:
                            widget_data = await response.json()
                            info["found"] = True
                            info["servers"].append({
                                "id": widget_data.get("id"),
                                "name": widget_data.get("name"),
                                "instant_invite": widget_data.get("instant_invite"),
                                "presence_count": widget_data.get("presence_count", 0),
                                "member_count": len(widget_data.get("members", []))
                            })
                            
        except Exception as e:
            logger.error(f"Erro ao buscar info Discord: {e}")
            
        return info
        
    async def search_invites(self, code: str) -> Optional[Dict]:
        """Busca informações de convite Discord"""
        
        try:
            invite_url = f"https://discord.com/api/v9/invites/{code}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(invite_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "code": code,
                            "guild": {
                                "id": data.get("guild", {}).get("id"),
                                "name": data.get("guild", {}).get("name"),
                                "description": data.get("guild", {}).get("description"),
                                "features": data.get("guild", {}).get("features", [])
                            },
                            "channel": {
                                "id": data.get("channel", {}).get("id"),
                                "name": data.get("channel", {}).get("name"),
                                "type": data.get("channel", {}).get("type")
                            },
                            "inviter": data.get("inviter")
                        }
                        
        except Exception as e:
            logger.error(f"Erro ao buscar invite: {e}")
            
        return None
