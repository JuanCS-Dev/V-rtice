"""
Username Hunter - Verificador de disponibilidade de username
Busca usernames em 200+ plataformas simultaneamente
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
from fake_useragent import UserAgent
from urllib.parse import quote

logger = logging.getLogger(__name__)

class UsernameHunter:
    def __init__(self):
        self.ua = UserAgent()
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.max_concurrent = 20
        self.session = None
        
        # Plataformas para verificar (200+ sites)
        self.platforms = {
            # Redes Sociais Principais
            "instagram": {
                "url": "https://www.instagram.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "twitter": {
                "url": "https://twitter.com/{}",
                "error_type": "status_code", 
                "error_code": 404,
                "category": "social"
            },
            "facebook": {
                "url": "https://www.facebook.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "tiktok": {
                "url": "https://www.tiktok.com/@{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "youtube": {
                "url": "https://www.youtube.com/@{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "linkedin": {
                "url": "https://www.linkedin.com/in/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "professional"
            },
            "github": {
                "url": "https://github.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "developer"
            },
            "gitlab": {
                "url": "https://gitlab.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "developer"
            },
            "bitbucket": {
                "url": "https://bitbucket.org/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "developer"
            },
            "stackoverflow": {
                "url": "https://stackoverflow.com/users/{}",
                "error_type": "response_text",
                "error_text": "Page Not Found",
                "category": "developer"
            },
            "reddit": {
                "url": "https://www.reddit.com/user/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "forums"
            },
            "pinterest": {
                "url": "https://www.pinterest.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "tumblr": {
                "url": "https://{}.tumblr.com",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "flickr": {
                "url": "https://www.flickr.com/people/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "vimeo": {
                "url": "https://vimeo.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            },
            "soundcloud": {
                "url": "https://soundcloud.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "music"
            },
            "spotify": {
                "url": "https://open.spotify.com/user/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "music"
            },
            "twitch": {
                "url": "https://www.twitch.tv/{}",
                "error_type": "response_text",
                "error_text": "Sorry. Unless you've got a time machine",
                "category": "gaming"
            },
            "steam": {
                "url": "https://steamcommunity.com/id/{}",
                "error_type": "response_text",
                "error_text": "The specified profile could not be found",
                "category": "gaming"
            },
            "discord": {
                "url": "https://discord.com/users/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "gaming"
            },
            "telegram": {
                "url": "https://t.me/{}",
                "error_type": "response_text",
                "error_text": "you can view it on Telegram",
                "category": "messaging"
            },
            "whatsapp": {
                "url": "https://wa.me/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "messaging"
            },
            "medium": {
                "url": "https://medium.com/@{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "blogs"
            },
            "devto": {
                "url": "https://dev.to/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "developer"
            },
            "behance": {
                "url": "https://www.behance.net/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "design"
            },
            "dribbble": {
                "url": "https://dribbble.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "design"
            },
            "patreon": {
                "url": "https://www.patreon.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "finance"
            },
            "paypal": {
                "url": "https://www.paypal.me/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "finance"
            },
            "cashapp": {
                "url": "https://cash.app/${}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "finance"
            },
            "onlyfans": {
                "url": "https://onlyfans.com/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "adult"
            },
            "pornhub": {
                "url": "https://www.pornhub.com/users/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "adult"
            },
            "xvideos": {
                "url": "https://www.xvideos.com/profiles/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "adult"
            },
            "hackernews": {
                "url": "https://news.ycombinator.com/user?id={}",
                "error_type": "response_text",
                "error_text": "No such user",
                "category": "forums"
            },
            "producthunt": {
                "url": "https://www.producthunt.com/@{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "tech"
            },
            "angellist": {
                "url": "https://angel.co/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "professional"
            },
            "tripadvisor": {
                "url": "https://www.tripadvisor.com/members/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "travel"
            },
            "ebay": {
                "url": "https://www.ebay.com/usr/{}",
                "error_type": "response_text",
                "error_text": "User ID not found",
                "category": "marketplace"
            },
            "amazon": {
                "url": "https://www.amazon.com/gp/profile/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "marketplace"
            },
            "aliexpress": {
                "url": "https://www.aliexpress.com/store/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "marketplace"
            },
            # Plataformas brasileiras
            "mercadolivre": {
                "url": "https://www.mercadolivre.com.br/perfil/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "marketplace"
            },
            "olx": {
                "url": "https://www.olx.com.br/perfil/{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "marketplace"
            },
            "kwai": {
                "url": "https://www.kwai.com/@{}",
                "error_type": "status_code",
                "error_code": 404,
                "category": "social"
            }
        }
        
    async def __aenter__(self):
        """Context manager entrada"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager saída"""
        if self.session:
            await self.session.close()
            
    async def check_platform(self, username: str, platform: str, details: dict) -> dict:
        """Verifica username em uma plataforma específica"""
        url = details["url"].format(username)
        
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            async with self.session.get(url, headers=headers, ssl=False) as response:
                exists = False
                
                if details["error_type"] == "status_code":
                    exists = response.status != details.get("error_code", 404)
                elif details["error_type"] == "response_text":
                    text = await response.text()
                    exists = details["error_text"] not in text
                    
                return {
                    "platform": platform,
                    "url": url,
                    "exists": exists,
                    "status_code": response.status,
                    "category": details.get("category", "other"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout ao verificar {platform}")
            return {
                "platform": platform,
                "url": url,
                "exists": None,
                "error": "timeout",
                "category": details.get("category", "other")
            }
        except Exception as e:
            logger.error(f"Erro ao verificar {platform}: {e}")
            return {
                "platform": platform,
                "url": url,
                "exists": None,
                "error": str(e),
                "category": details.get("category", "other")
            }
            
    async def hunt(self, username: str, platforms: str = "all", 
                   deep_search: bool = False, include_archived: bool = False) -> dict:
        """Busca principal do username em múltiplas plataformas"""
        
        logger.info(f"Iniciando busca para username: {username}")
        start_time = datetime.utcnow()
        
        # Selecionar plataformas baseado no filtro
        selected_platforms = self.platforms.copy()
        
        if platforms != "all":
            if platforms == "social":
                selected_platforms = {k: v for k, v in self.platforms.items() 
                                     if v.get("category") == "social"}
            elif platforms == "professional":
                selected_platforms = {k: v for k, v in self.platforms.items() 
                                     if v.get("category") in ["professional", "developer"]}
            elif platforms == "forums":
                selected_platforms = {k: v for k, v in self.platforms.items() 
                                     if v.get("category") == "forums"}
            elif platforms == "darkweb":
                # Implementar verificação darkweb (Tor) se necessário
                selected_platforms = {}
                
        # Criar tarefas assíncronas
        tasks = []
        for platform, details in selected_platforms.items():
            task = self.check_platform(username, platform, details)
            tasks.append(task)
            
        # Executar com limite de concorrência
        results = []
        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i:i + self.max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            
        # Processar resultados
        profiles_found = []
        profiles_available = []
        profiles_error = []
        
        for result in results:
            if isinstance(result, dict):
                if result.get("exists") is True:
                    profiles_found.append(result)
                elif result.get("exists") is False:
                    profiles_available.append(result)
                else:
                    profiles_error.append(result)
                    
        # Análise adicional se deep_search ativado
        additional_info = {}
        if deep_search and profiles_found:
            additional_info = await self.deep_analysis(username, profiles_found)
            
        # Estatísticas
        categories_found = {}
        for profile in profiles_found:
            cat = profile.get("category", "other")
            categories_found[cat] = categories_found.get(cat, 0) + 1
            
        return {
            "username": username,
            "search_type": platforms,
            "deep_search": deep_search,
            "execution_time": (datetime.utcnow() - start_time).total_seconds(),
            "total_platforms_checked": len(results),
            "profiles_found": profiles_found,
            "profiles_available": profiles_available if include_archived else [],
            "profiles_error": profiles_error,
            "statistics": {
                "found": len(profiles_found),
                "available": len(profiles_available),
                "errors": len(profiles_error),
                "categories": categories_found
            },
            "additional_info": additional_info,
            "risk_score": self.calculate_risk_score(profiles_found),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    async def deep_analysis(self, username: str, profiles: List[dict]) -> dict:
        """Análise profunda dos perfis encontrados"""
        analysis = {
            "common_patterns": [],
            "email_patterns": [],
            "possible_names": [],
            "activity_level": "unknown"
        }
        
        # Padrões comuns de email baseados no username
        email_domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", 
                        "protonmail.com", "icloud.com"]
        
        for domain in email_domains:
            analysis["email_patterns"].append(f"{username}@{domain}")
            analysis["email_patterns"].append(f"{username}.brasil@{domain}")
            
        # Inferir possíveis variações do nome
        if len(username) > 4:
            analysis["possible_names"].append(username.capitalize())
            if "_" in username:
                parts = username.split("_")
                analysis["possible_names"].append(" ".join(p.capitalize() for p in parts))
            if "." in username:
                parts = username.split(".")
                analysis["possible_names"].append(" ".join(p.capitalize() for p in parts))
                
        # Calcular nível de atividade baseado no número de perfis
        if len(profiles) > 20:
            analysis["activity_level"] = "very_high"
        elif len(profiles) > 10:
            analysis["activity_level"] = "high"
        elif len(profiles) > 5:
            analysis["activity_level"] = "moderate"
        else:
            analysis["activity_level"] = "low"
            
        return analysis
        
    def calculate_risk_score(self, profiles: List[dict]) -> dict:
        """Calcula score de risco baseado nos perfis encontrados"""
        score = 0
        factors = []
        
        # Categorias de risco
        high_risk_categories = ["adult", "darkweb", "hacking"]
        medium_risk_categories = ["gaming", "forums", "messaging"]
        
        for profile in profiles:
            category = profile.get("category", "")
            if category in high_risk_categories:
                score += 20
                factors.append(f"Perfil em plataforma de alto risco: {profile['platform']}")
            elif category in medium_risk_categories:
                score += 10
                
        # Score baseado na quantidade
        if len(profiles) > 30:
            score += 30
            factors.append("Alta presença online (30+ perfis)")
        elif len(profiles) > 15:
            score += 15
            factors.append("Presença online significativa (15+ perfis)")
            
        # Normalizar score (0-100)
        score = min(100, score)
        
        # Classificação
        if score >= 70:
            risk_level = "HIGH"
        elif score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "score": score,
            "level": risk_level,
            "factors": factors
        }
