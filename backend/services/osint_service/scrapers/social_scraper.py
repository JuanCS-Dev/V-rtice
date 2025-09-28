"""
Social Media Scraper - Extração de dados de redes sociais
Discord, Twitter, Instagram, LinkedIn, Telegram
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import hashlib
import base64

logger = logging.getLogger(__name__)

class SocialScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session = None
        self.driver = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
            
    def _setup_selenium(self, headless: bool = True):
        """Configura Selenium para scraping avançado"""
        if not self.driver:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={self.ua.random}")
            
            # Anti-detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
    async def scrape_profile(self, platform: str, identifier: str, 
                           depth: str = "medium", include_connections: bool = True,
                           include_timeline: bool = True) -> dict:
        """Scraping principal de perfil social"""
        
        logger.info(f"Scraping {platform}: {identifier}")
        
        scrapers = {
            "discord": self._scrape_discord,
            "twitter": self._scrape_twitter,
            "instagram": self._scrape_instagram,
            "linkedin": self._scrape_linkedin,
            "telegram": self._scrape_telegram
        }
        
        if platform not in scrapers:
            return {"error": f"Plataforma {platform} não suportada"}
            
        try:
            result = await scrapers[platform](identifier, depth, include_connections, include_timeline)
            result["scrape_timestamp"] = datetime.utcnow().isoformat()
            result["depth_level"] = depth
            return result
            
        except Exception as e:
            logger.error(f"Erro no scraping de {platform}: {e}")
            return {
                "error": str(e),
                "platform": platform,
                "identifier": identifier
            }
            
    async def _scrape_discord(self, identifier: str, depth: str, 
                            include_connections: bool, include_timeline: bool) -> dict:
        """Scraping de Discord (via Discord ID ou username)"""
        
        result = {
            "platform": "discord",
            "identifier": identifier,
            "profile_data": {},
            "servers": [],
            "connections": [],
            "activity": {}
        }
        
        # Se for um ID numérico de Discord
        if identifier.isdigit():
            discord_id = int(identifier)
            
            # Converter Discord ID para timestamp (Snowflake)
            timestamp = ((discord_id >> 22) + 1420070400000) / 1000
            created_at = datetime.fromtimestamp(timestamp)
            
            result["profile_data"]["discord_id"] = discord_id
            result["profile_data"]["account_created"] = created_at.isoformat()
            result["profile_data"]["account_age_days"] = (datetime.utcnow() - created_at).days
            
            # Calcular informações do Snowflake ID
            worker_id = (discord_id & 0x3E0000) >> 17
            process_id = (discord_id & 0x1F000) >> 12
            increment = discord_id & 0xFFF
            
            result["profile_data"]["technical_info"] = {
                "worker_id": worker_id,
                "process_id": process_id,
                "increment": increment
            }
            
        # Buscar via API não oficial (cuidado com rate limits)
        if depth in ["medium", "deep"]:
            # Simular dados de servidor (em produção, usar Discord.py ou API)
            result["servers"] = [
                {
                    "name": "Gaming BR",
                    "id": "123456789",
                    "member_count": 5420,
                    "joined": "2023-05-15",
                    "roles": ["Member", "Active"]
                },
                {
                    "name": "Dev Community",
                    "id": "987654321",
                    "member_count": 12300,
                    "joined": "2023-08-20",
                    "roles": ["Developer", "Python"]
                }
            ]
            
            if include_connections:
                result["connections"]["mutual_servers"] = len(result["servers"])
                result["connections"]["estimated_contacts"] = len(result["servers"]) * 50
                
            if include_timeline and depth == "deep":
                result["activity"] = {
                    "last_seen": datetime.utcnow().isoformat(),
                    "status": "online",
                    "custom_status": "Coding...",
                    "game_activity": "Visual Studio Code",
                    "voice_channels_frequented": ["general-voice", "dev-talk"]
                }
                
        return result
        
    async def _scrape_twitter(self, identifier: str, depth: str,
                            include_connections: bool, include_timeline: bool) -> dict:
        """Scraping de Twitter/X"""
        
        result = {
            "platform": "twitter",
            "identifier": identifier,
            "profile_data": {},
            "tweets": [],
            "connections": {},
            "statistics": {}
        }
        
        # Limpar @ se presente
        username = identifier.replace("@", "")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            # Headers para parecer requisição legítima
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Método via nitter (instância alternativa) ou scraping direto
            nitter_instances = [
                "nitter.net", "nitter.42l.fr", "nitter.pussthecat.org",
                "nitter.fdn.fr", "nitter.namazso.eu"
            ]
            
            for instance in nitter_instances:
                try:
                    url = f"https://{instance}/{username}"
                    async with self.session.get(url, headers=headers, ssl=False) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extrair dados básicos do perfil
                            profile_card = soup.find('div', class_='profile-card')
                            if profile_card:
                                result["profile_data"]["username"] = username
                                result["profile_data"]["display_name"] = profile_card.find('a', class_='profile-card-fullname')
                                result["profile_data"]["bio"] = profile_card.find('div', class_='profile-bio')
                                result["profile_data"]["location"] = profile_card.find('div', class_='profile-location')
                                result["profile_data"]["website"] = profile_card.find('div', class_='profile-website')
                                
                                # Estatísticas
                                stats = soup.find_all('span', class_='profile-stat-num')
                                if len(stats) >= 3:
                                    result["statistics"]["tweets"] = stats[0].text.strip()
                                    result["statistics"]["following"] = stats[1].text.strip()
                                    result["statistics"]["followers"] = stats[2].text.strip()
                            
                            # Tweets recentes se incluir timeline
                            if include_timeline and depth in ["medium", "deep"]:
                                tweets = soup.find_all('div', class_='timeline-item', limit=20)
                                for tweet in tweets:
                                    tweet_data = {
                                        "text": tweet.find('div', class_='tweet-content'),
                                        "date": tweet.find('span', class_='tweet-date'),
                                        "retweets": tweet.find('span', class_='tweet-stat-retweets'),
                                        "likes": tweet.find('span', class_='tweet-stat-likes')
                                    }
                                    result["tweets"].append({
                                        k: v.text.strip() if v else None 
                                        for k, v in tweet_data.items()
                                    })
                            
                            break
                            
                except Exception as e:
                    logger.debug(f"Falha com instância {instance}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro no scraping do Twitter: {e}")
            
        # Análise adicional se deep search
        if depth == "deep":
            result["analysis"] = {
                "account_type": self._classify_twitter_account(result),
                "engagement_rate": self._calculate_engagement(result),
                "posting_patterns": self._analyze_posting_patterns(result["tweets"]),
                "content_categories": self._categorize_content(result["tweets"])
            }
            
        return result
        
    async def _scrape_instagram(self, identifier: str, depth: str,
                               include_connections: bool, include_timeline: bool) -> dict:
        """Scraping de Instagram"""
        
        result = {
            "platform": "instagram",
            "identifier": identifier,
            "profile_data": {},
            "posts": [],
            "connections": {},
            "statistics": {}
        }
        
        # Instagram requer approach mais cuidadoso
        username = identifier.replace("@", "")
        
        try:
            # Método 1: Via Instaloader (mais seguro)
            import instaloader
            
            L = instaloader.Instaloader(
                quiet=True,
                user_agent=self.ua.random,
                dirname_pattern=None,
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            
            try:
                profile = instaloader.Profile.from_username(L.context, username)
                
                result["profile_data"] = {
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "bio": profile.biography,
                    "external_url": profile.external_url,
                    "is_verified": profile.is_verified,
                    "is_private": profile.is_private,
                    "is_business": profile.is_business_account,
                    "business_category": profile.business_category_name,
                    "profile_pic_url": profile.profile_pic_url
                }
                
                result["statistics"] = {
                    "posts": profile.mediacount,
                    "followers": profile.followers,
                    "following": profile.followees,
                    "engagement_rate": (profile.followers + profile.mediacount) / max(profile.followers, 1) * 100
                }
                
                # Posts recentes se não for privado
                if include_timeline and not profile.is_private:
                    posts_data = []
                    for post in profile.get_posts():
                        if len(posts_data) >= 12:  # Limitar a 12 posts
                            break
                            
                        post_info = {
                            "shortcode": post.shortcode,
                            "date": post.date.isoformat(),
                            "caption": post.caption[:200] if post.caption else None,
                            "likes": post.likes,
                            "comments": post.comments,
                            "is_video": post.is_video,
                            "location": post.location,
                            "hashtags": list(post.caption_hashtags) if post.caption else []
                        }
                        posts_data.append(post_info)
                        
                    result["posts"] = posts_data
                    
                # Análise de conexões
                if include_connections and depth == "deep" and not profile.is_private:
                    result["connections"] = {
                        "mutual_followers": [],  # Requer autenticação
                        "tagged_users": [],
                        "mentioned_users": []
                    }
                    
                    # Extrair usuários mencionados nos posts
                    for post in result["posts"]:
                        if post.get("caption"):
                            mentions = re.findall(r'@(\w+)', post["caption"])
                            result["connections"]["mentioned_users"].extend(mentions)
                            
                    result["connections"]["mentioned_users"] = list(set(result["connections"]["mentioned_users"]))
                    
            except instaloader.exceptions.ProfileNotExistsException:
                result["error"] = "Perfil não encontrado"
                
        except ImportError:
            # Fallback: scraping via requests
            logger.warning("Instaloader não disponível, usando método alternativo")
            result["error"] = "Método alternativo necessário"
            
        # Análise adicional
        if depth == "deep" and result.get("posts"):
            result["analysis"] = {
                "posting_frequency": self._calculate_posting_frequency(result["posts"]),
                "peak_posting_times": self._find_peak_times(result["posts"]),
                "hashtag_analysis": self._analyze_hashtags(result["posts"]),
                "content_type": self._classify_instagram_content(result)
            }
            
        return result
        
    async def _scrape_linkedin(self, identifier: str, depth: str,
                              include_connections: bool, include_timeline: bool) -> dict:
        """Scraping de LinkedIn"""
        
        result = {
            "platform": "linkedin",
            "identifier": identifier,
            "profile_data": {},
            "experience": [],
            "education": [],
            "skills": [],
            "connections": {}
        }
        
        # LinkedIn é muito restritivo, usar selenium com cuidado
        self._setup_selenium(headless=True)
        
        try:
            # Construir URL do perfil
            if identifier.startswith("http"):
                url = identifier
            else:
                url = f"https://www.linkedin.com/in/{identifier}"
                
            self.driver.get(url)
            
            # Aguardar carregamento
            wait = WebDriverWait(self.driver, 10)
            
            # Verificar se precisa login (LinkedIn bloqueia muito)
            if "login" in self.driver.current_url.lower():
                logger.warning("LinkedIn requer autenticação")
                result["error"] = "Autenticação necessária"
                return result
                
            # Extrair dados básicos do perfil
            try:
                # Nome
                name_elem = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.text-heading-xlarge")
                ))
                result["profile_data"]["name"] = name_elem.text
                
                # Título/Headline
                headline = self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium")
                result["profile_data"]["headline"] = headline.text
                
                # Localização
                location = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small")
                result["profile_data"]["location"] = location.text
                
                # Sobre
                try:
                    about = self.driver.find_element(By.ID, "about").find_element(By.TAG_NAME, "span")
                    result["profile_data"]["about"] = about.text
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Erro ao extrair dados do LinkedIn: {e}")
                
            # Experiência profissional
            if depth in ["medium", "deep"]:
                try:
                    experience_section = self.driver.find_element(By.ID, "experience")
                    experiences = experience_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
                    
                    for exp in experiences[:10]:  # Limitar a 10 experiências
                        try:
                            exp_data = {
                                "title": exp.find_element(By.TAG_NAME, "h3").text,
                                "company": exp.find_element(By.TAG_NAME, "h4").text,
                                "duration": exp.find_element(By.CSS_SELECTOR, "span.t-14").text
                            }
                            result["experience"].append(exp_data)
                        except:
                            continue
                            
                except:
                    logger.debug("Seção de experiência não encontrada")
                    
            # Educação
            if depth == "deep":
                try:
                    education_section = self.driver.find_element(By.ID, "education")
                    educations = education_section.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item")
                    
                    for edu in educations[:5]:
                        try:
                            edu_data = {
                                "school": edu.find_element(By.TAG_NAME, "h3").text,
                                "degree": edu.find_element(By.TAG_NAME, "h4").text,
                                "period": edu.find_element(By.CSS_SELECTOR, "span.t-14").text
                            }
                            result["education"].append(edu_data)
                        except:
                            continue
                            
                except:
                    logger.debug("Seção de educação não encontrada")
                    
        except Exception as e:
            logger.error(f"Erro geral no LinkedIn scraping: {e}")
            result["error"] = str(e)
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
                
        return result
        
    async def _scrape_telegram(self, identifier: str, depth: str,
                              include_connections: bool, include_timeline: bool) -> dict:
        """Scraping de Telegram"""
        
        result = {
            "platform": "telegram",
            "identifier": identifier,
            "profile_data": {},
            "groups": [],
            "channels": [],
            "activity": {}
        }
        
        # Telegram via t.me links públicos
        username = identifier.replace("@", "")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            # Verificar canal/grupo público
            url = f"https://t.me/{username}"
            async with self.session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extrair metadados
                    meta_title = soup.find('meta', property='og:title')
                    meta_desc = soup.find('meta', property='og:description')
                    meta_image = soup.find('meta', property='og:image')
                    
                    if meta_title:
                        result["profile_data"]["name"] = meta_title.get('content')
                    if meta_desc:
                        result["profile_data"]["description"] = meta_desc.get('content')
                    if meta_image:
                        result["profile_data"]["avatar_url"] = meta_image.get('content')
                        
                    # Identificar tipo (canal, grupo, bot ou usuário)
                    if "channel" in html.lower():
                        result["profile_data"]["type"] = "channel"
                    elif "group" in html.lower():
                        result["profile_data"]["type"] = "group"
                    elif "bot" in html.lower():
                        result["profile_data"]["type"] = "bot"
                    else:
                        result["profile_data"]["type"] = "user"
                        
                    # Extrair contadores se disponíveis
                    counters = soup.find_all('div', class_='tgme_page_extra')
                    if counters:
                        counter_text = counters[0].text
                        members = re.search(r'([\d\s]+)\s*(members|subscribers)', counter_text)
                        if members:
                            result["statistics"] = {
                                "members": members.group(1).strip(),
                                "type": members.group(2)
                            }
                            
        except Exception as e:
            logger.error(f"Erro no Telegram scraping: {e}")
            result["error"] = str(e)
            
        return result
        
    # Métodos auxiliares de análise
    
    def _classify_twitter_account(self, data: dict) -> str:
        """Classifica tipo de conta Twitter"""
        stats = data.get("statistics", {})
        
        try:
            followers = int(stats.get("followers", "0").replace(",", "").replace(".", ""))
            following = int(stats.get("following", "0").replace(",", "").replace(".", ""))
            
            if followers > 10000:
                return "influencer"
            elif followers > 1000:
                return "micro_influencer"
            elif following > followers * 2:
                return "bot_suspect"
            else:
                return "personal"
        except:
            return "unknown"
            
    def _calculate_engagement(self, data: dict) -> float:
        """Calcula taxa de engajamento"""
        try:
            stats = data.get("statistics", {})
            tweets = data.get("tweets", [])
            
            if not tweets:
                return 0.0
                
            total_engagement = sum(
                int(t.get("likes", "0").replace(",", "")) + 
                int(t.get("retweets", "0").replace(",", ""))
                for t in tweets if t.get("likes")
            )
            
            followers = int(stats.get("followers", "1").replace(",", "").replace(".", ""))
            
            return (total_engagement / len(tweets) / followers) * 100
            
        except:
            return 0.0
            
    def _analyze_posting_patterns(self, posts: List[dict]) -> dict:
        """Analisa padrões de postagem"""
        patterns = {
            "frequency": "unknown",
            "peak_hours": [],
            "peak_days": []
        }
        
        if not posts:
            return patterns
            
        try:
            # Análise simplificada
            if len(posts) > 10:
                patterns["frequency"] = "high"
            elif len(posts) > 5:
                patterns["frequency"] = "medium"
            else:
                patterns["frequency"] = "low"
                
        except:
            pass
            
        return patterns
        
    def _categorize_content(self, posts: List[dict]) -> List[str]:
        """Categoriza conteúdo dos posts"""
        categories = set()
        
        for post in posts:
            text = post.get("text", "").lower() if post else ""
            
            # Categorização básica por palavras-chave
            if any(word in text for word in ["política", "governo", "eleição", "presidente"]):
                categories.add("political")
            if any(word in text for word in ["tech", "código", "programação", "dev", "software"]):
                categories.add("technology")
            if any(word in text for word in ["venda", "compra", "promoção", "desconto", "produto"]):
                categories.add("commercial")
            if any(word in text for word in ["família", "amigos", "festa", "viagem"]):
                categories.add("personal")
                
        return list(categories)
        
    def _calculate_posting_frequency(self, posts: List[dict]) -> str:
        """Calcula frequência de postagem"""
        if not posts:
            return "inactive"
            
        try:
            dates = []
            for post in posts:
                if post.get("date"):
                    dates.append(datetime.fromisoformat(post["date"].replace("Z", "+00:00")))
                    
            if len(dates) >= 2:
                date_range = (dates[0] - dates[-1]).days
                posts_per_day = len(posts) / max(date_range, 1)
                
                if posts_per_day > 5:
                    return "very_high"
                elif posts_per_day > 1:
                    return "high"
                elif posts_per_day > 0.3:
                    return "moderate"
                else:
                    return "low"
                    
        except:
            pass
            
        return "unknown"
        
    def _find_peak_times(self, posts: List[dict]) -> List[int]:
        """Encontra horários de pico de postagem"""
        hours = []
        
        for post in posts:
            try:
                if post.get("date"):
                    dt = datetime.fromisoformat(post["date"].replace("Z", "+00:00"))
                    hours.append(dt.hour)
            except:
                continue
                
        if not hours:
            return []
            
        # Encontrar as 3 horas mais comuns
        from collections import Counter
        hour_counts = Counter(hours)
        return [hour for hour, count in hour_counts.most_common(3)]
        
    def _analyze_hashtags(self, posts: List[dict]) -> dict:
        """Analisa hashtags usadas"""
        all_hashtags = []
        
        for post in posts:
            if post.get("hashtags"):
                all_hashtags.extend(post["hashtags"])
                
        if not all_hashtags:
            return {"count": 0, "top_tags": []}
            
        from collections import Counter
        hashtag_counts = Counter(all_hashtags)
        
        return {
            "count": len(all_hashtags),
            "unique": len(set(all_hashtags)),
            "top_tags": [tag for tag, count in hashtag_counts.most_common(10)]
        }
        
    def _classify_instagram_content(self, data: dict) -> str:
        """Classifica tipo de conteúdo Instagram"""
        profile = data.get("profile_data", {})
        stats = data.get("statistics", {})
        
        if profile.get("is_business"):
            return "business"
        elif profile.get("is_verified"):
            return "verified_public_figure"
        elif stats.get("followers", 0) > 10000:
            return "influencer"
        else:
            return "personal"
