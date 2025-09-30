"""
Google OSINT Service - Projeto Vértice
Serviço especializado em investigação através do Google (Google Dorking/Hacking)
Autor: Juan - Projeto Vértice
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import asyncio
import aiohttp
import redis
import json
import hashlib
import logging
import random
import time
from enum import Enum
import urllib.parse
import re

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Google OSINT Service",
    description="Serviço especializado em investigação através do Google - Projeto Vértice SSP-GO",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis para cache
try:
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        db=3,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("✓ Redis conectado com sucesso")
except Exception as e:
    logger.error(f"✗ Erro ao conectar Redis: {e}")
    redis_client = None

# Modelos Pydantic
class SearchType(str, Enum):
    PERSON = "person"
    EMAIL = "email"
    PHONE = "phone"
    DOMAIN = "domain"
    DOCUMENT = "document"
    IMAGE = "image"
    SOCIAL = "social"
    VULNERABILITY = "vulnerability"
    CREDENTIAL = "credential"
    CUSTOM = "custom"

class GoogleDorkRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    search_type: SearchType = SearchType.PERSON
    max_results: int = Field(default=50, ge=10, le=200)
    language: str = Field(default="pt", pattern="^(pt|en|es)$")
    region: str = Field(default="BR", pattern="^[A-Z]{2}$")
    time_range: Optional[str] = Field(default=None, pattern="^(day|week|month|year)$")
    include_images: bool = False
    include_news: bool = False
    include_documents: bool = True
    safe_search: bool = True

class AdvancedDorkRequest(BaseModel):
    target: str = Field(..., min_length=2, max_length=200)
    search_types: List[SearchType] = [SearchType.PERSON]
    deep_search: bool = False
    include_related_sites: bool = True
    include_cached_pages: bool = False
    include_social_media: bool = True
    max_results_per_type: int = Field(default=30, ge=5, le=100)

class DocumentSearchRequest(BaseModel):
    keywords: str = Field(..., min_length=2, max_length=300)
    file_types: List[str] = Field(default=["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"])
    site: Optional[str] = None
    exact_match: bool = False
    max_results: int = Field(default=50, ge=10, le=150)

class ImageSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    image_url: Optional[HttpUrl] = None
    reverse_search: bool = False
    include_metadata: bool = True
    max_results: int = Field(default=30, ge=5, le=100)

class SocialDorkRequest(BaseModel):
    target: str = Field(..., min_length=2, max_length=150)
    platforms: List[str] = Field(default=["twitter", "facebook", "instagram", "linkedin", "youtube"])
    include_profiles: bool = True
    include_posts: bool = True
    max_results: int = Field(default=40, ge=10, le=100)

# Google Dork Patterns
DORK_PATTERNS = {
    "person": [
        '"{target}" site:linkedin.com',
        '"{target}" site:facebook.com',
        '"{target}" site:twitter.com',
        '"{target}" site:instagram.com',
        '"{target}" CV OR currículo filetype:pdf',
        '"{target}" contato OR email OR telefone',
        '"{target}" endereço OR localização'
    ],
    "email": [
        '"{target}"',
        '"{target}" site:linkedin.com',
        'site:facebook.com "{target}"',
        '"{target}" filetype:pdf',
        '"{target}" "contact" OR "contato"',
        'intext:"{target}"'
    ],
    "phone": [
        '"{target}"',
        '"{target}" site:reclameaqui.com.br',
        '"{target}" site:linkedin.com',
        '"{target}" contato OR telefone',
        '"{target}" WhatsApp OR telegram'
    ],
    "domain": [
        'site:{target}',
        'inurl:{target}',
        '"{target}" site:whois.net',
        '"{target}" site:registro.br',
        'cache:{target}',
        'related:{target}'
    ],
    "document": [
        'site:{target} filetype:pdf',
        'site:{target} filetype:doc',
        'site:{target} filetype:docx',
        'site:{target} filetype:xls',
        'site:{target} filetype:xlsx',
        'site:{target} filetype:ppt'
    ],
    "vulnerability": [
        'site:{target} "index of"',
        'site:{target} "directory listing"',
        'site:{target} "login" OR "admin"',
        'site:{target} "config" filetype:txt',
        'site:{target} "backup" filetype:sql',
        'site:{target} inurl:wp-admin',
        'site:{target} "error" OR "warning"'
    ],
    "social": [
        '"{target}" site:twitter.com',
        '"{target}" site:facebook.com',
        '"{target}" site:instagram.com',
        '"{target}" site:linkedin.com',
        '"{target}" site:youtube.com',
        '"{target}" site:tiktok.com'
    ]
}

# User Agents rotativos para evitar detecção
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

class GoogleDorker:
    def __init__(self):
        self.session = None
        self.request_count = 0
        self.last_request_time = 0

    async def get_session(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def get_random_headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    async def rate_limit(self):
        """Implementa rate limiting para evitar bloqueio"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Espera mínima entre requests
        min_wait = random.uniform(2, 5)
        if time_since_last < min_wait:
            await asyncio.sleep(min_wait - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

        # Rate limiting mais agressivo após muitos requests
        if self.request_count % 10 == 0:
            await asyncio.sleep(random.uniform(10, 20))

    def build_google_url(self, query: str, params: dict = None):
        """Constrói URL do Google com parâmetros"""
        base_url = "https://www.google.com/search"
        default_params = {
            'q': query,
            'hl': 'pt-BR',
            'gl': 'BR',
            'num': 50
        }

        if params:
            default_params.update(params)

        # Encode da query
        query_string = urllib.parse.urlencode(default_params)
        return f"{base_url}?{query_string}"

    async def search_google(self, query: str, max_results: int = 50, **kwargs):
        """Executa busca no Google"""
        try:
            await self.rate_limit()
            session = await self.get_session()

            # Parâmetros da busca
            params = {
                'num': min(max_results, 100),
                'start': 0
            }

            # Adicionar filtros específicos
            if kwargs.get('time_range'):
                params['tbs'] = f"qdr:{kwargs['time_range'][0]}"

            if kwargs.get('language'):
                params['hl'] = kwargs['language']

            if kwargs.get('region'):
                params['gl'] = kwargs['region']

            url = self.build_google_url(query, params)
            headers = self.get_random_headers()

            logger.info(f"Executando busca: {query}")

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self.parse_google_results(html, query)
                elif response.status == 429:
                    logger.warning("Rate limit do Google detectado")
                    await asyncio.sleep(random.uniform(30, 60))
                    return {"error": "Rate limit", "retry": True}
                else:
                    logger.error(f"Erro HTTP {response.status}")
                    return {"error": f"HTTP {response.status}"}

        except Exception as e:
            logger.error(f"Erro na busca Google: {e}")
            return {"error": str(e)}

    async def parse_google_results(self, html: str, query: str):
        """Parse dos resultados do Google"""
        results = {
            "query": query,
            "results": [],
            "total_found": 0,
            "search_time": datetime.utcnow().isoformat(),
            "has_captcha": False
        }

        # Detectar CAPTCHA
        if "captcha" in html.lower() or "robots" in html.lower():
            results["has_captcha"] = True
            return results

        # Regex patterns para extrair resultados
        # Pattern para links de resultado
        link_pattern = r'<a[^>]*href="(/url\?q=([^&]+))[^"]*"[^>]*>'
        title_pattern = r'<h3[^>]*>([^<]+)</h3>'
        snippet_pattern = r'<span[^>]*class="[^"]*st[^"]*"[^>]*>([^<]+)</span>'

        links = re.findall(link_pattern, html)
        titles = re.findall(title_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        # Combinar resultados
        for i, (full_url, clean_url) in enumerate(links[:50]):
            try:
                # Decode URL
                decoded_url = urllib.parse.unquote(clean_url)

                result = {
                    "position": i + 1,
                    "title": titles[i] if i < len(titles) else "Título não disponível",
                    "url": decoded_url,
                    "snippet": snippets[i] if i < len(snippets) else "Snippet não disponível",
                    "domain": urllib.parse.urlparse(decoded_url).netloc,
                    "found_timestamp": datetime.utcnow().isoformat()
                }

                results["results"].append(result)

            except Exception as e:
                logger.warning(f"Erro ao processar resultado {i}: {e}")
                continue

        results["total_found"] = len(results["results"])
        return results

# Instância global do dorker
google_dorker = GoogleDorker()

# Funções auxiliares
def generate_cache_key(prefix: str, params: dict) -> str:
    """Gera chave única para cache"""
    params_str = json.dumps(params, sort_keys=True)
    hash_obj = hashlib.sha256(params_str.encode())
    return f"google_osint:{prefix}:{hash_obj.hexdigest()}"

async def get_cached_result(key: str) -> Optional[dict]:
    """Busca resultado em cache"""
    if not redis_client:
        return None
    try:
        cached = redis_client.get(key)
        if cached:
            logger.info(f"Cache hit: {key}")
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Erro ao buscar cache: {e}")
    return None

async def set_cached_result(key: str, data: dict, ttl: int = 7200):
    """Armazena resultado em cache"""
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(data))
        logger.info(f"Cache set: {key}")
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {e}")

# Endpoints principais

@app.get("/")
async def root():
    """Status do serviço"""
    return {
        "service": "Google OSINT Service",
        "status": "operational",
        "version": "1.0.0",
        "project": "Vértice SSP-GO",
        "capabilities": [
            "Google Dorking",
            "Advanced Search",
            "Document Discovery",
            "Image Search",
            "Social Media Search",
            "Vulnerability Research"
        ],
        "endpoints": {
            "basic_search": "/api/search/basic",
            "advanced_search": "/api/search/advanced",
            "document_search": "/api/search/documents",
            "image_search": "/api/search/images",
            "social_search": "/api/search/social"
        }
    }

@app.post("/api/search/basic")
async def basic_google_search(request: GoogleDorkRequest, background_tasks: BackgroundTasks):
    """Busca básica com Google Dorks"""
    try:
        logger.info(f"Busca básica: {request.query}")

        # Verificar cache
        cache_key = generate_cache_key("basic", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

        # Preparar queries baseadas no tipo
        queries = []
        if request.search_type in DORK_PATTERNS:
            patterns = DORK_PATTERNS[request.search_type]
            for pattern in patterns[:5]:  # Limitar para evitar sobrecarga
                query = pattern.replace("{target}", request.query)
                queries.append(query)
        else:
            queries = [request.query]

        # Executar buscas
        all_results = []
        for query in queries:
            result = await google_dorker.search_google(
                query=query,
                max_results=request.max_results // len(queries),
                language=request.language,
                region=request.region,
                time_range=request.time_range
            )

            if result and not result.get("error"):
                all_results.extend(result.get("results", []))

            # Rate limiting entre queries
            await asyncio.sleep(random.uniform(3, 7))

        # Remover duplicatas e ordenar por relevância
        unique_results = []
        seen_urls = set()

        for result in all_results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)

        # Limitar resultados finais
        final_results = unique_results[:request.max_results]

        response_data = {
            "query": request.query,
            "search_type": request.search_type,
            "total_queries_executed": len(queries),
            "total_results": len(final_results),
            "results": final_results,
            "metadata": {
                "language": request.language,
                "region": request.region,
                "safe_search": request.safe_search,
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }

        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, response_data)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": response_data
        }

    except Exception as e:
        logger.error(f"Erro na busca básica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/advanced")
async def advanced_google_search(request: AdvancedDorkRequest, background_tasks: BackgroundTasks):
    """Busca avançada com múltiplos tipos de dorks"""
    try:
        logger.info(f"Busca avançada para: {request.target}")

        # Verificar cache
        cache_key = generate_cache_key("advanced", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

        investigation_results = {
            "target": request.target,
            "search_types": request.search_types,
            "results_by_type": {},
            "summary": {
                "total_results": 0,
                "types_executed": len(request.search_types),
                "domains_found": set(),
                "file_types_found": set()
            },
            "execution_time": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        start_time = time.time()

        # Executar buscas para cada tipo
        for search_type in request.search_types:
            type_results = []

            if search_type in DORK_PATTERNS:
                patterns = DORK_PATTERNS[search_type]

                for pattern in patterns:
                    query = pattern.replace("{target}", request.target)

                    result = await google_dorker.search_google(
                        query=query,
                        max_results=request.max_results_per_type // len(patterns)
                    )

                    if result and not result.get("error"):
                        for res in result.get("results", []):
                            res["dork_pattern"] = pattern
                            res["search_type"] = search_type
                            type_results.append(res)

                            # Coletar estatísticas
                            investigation_results["summary"]["domains_found"].add(res["domain"])

                            # Detectar tipos de arquivo
                            if "filetype:" in pattern or any(ext in res["url"] for ext in [".pdf", ".doc", ".xls", ".ppt"]):
                                for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
                                    if ext in res["url"]:
                                        investigation_results["summary"]["file_types_found"].add(ext)

                    # Rate limiting
                    await asyncio.sleep(random.uniform(4, 8))

            # Remover duplicatas por tipo
            unique_type_results = []
            seen_urls = set()

            for result in type_results:
                if result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_type_results.append(result)

            investigation_results["results_by_type"][search_type] = unique_type_results[:request.max_results_per_type]

        # Finalizar estatísticas
        investigation_results["summary"]["total_results"] = sum(
            len(results) for results in investigation_results["results_by_type"].values()
        )
        investigation_results["summary"]["domains_found"] = list(investigation_results["summary"]["domains_found"])
        investigation_results["summary"]["file_types_found"] = list(investigation_results["summary"]["file_types_found"])
        investigation_results["execution_time"] = round(time.time() - start_time, 2)

        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, investigation_results, ttl=10800)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": investigation_results
        }

    except Exception as e:
        logger.error(f"Erro na busca avançada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/documents")
async def search_documents(request: DocumentSearchRequest, background_tasks: BackgroundTasks):
    """Busca especializada em documentos"""
    try:
        logger.info(f"Busca de documentos: {request.keywords}")

        # Verificar cache
        cache_key = generate_cache_key("documents", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

        document_results = {
            "keywords": request.keywords,
            "file_types": request.file_types,
            "documents_found": [],
            "statistics": {
                "total_found": 0,
                "by_file_type": {},
                "by_domain": {}
            },
            "search_timestamp": datetime.utcnow().isoformat()
        }

        # Construir queries para cada tipo de arquivo
        for file_type in request.file_types:
            query_parts = [f'"{request.keywords}"', f"filetype:{file_type}"]

            if request.site:
                query_parts.append(f"site:{request.site}")

            if request.exact_match:
                query = " ".join(query_parts)
            else:
                # Busca mais flexível
                base_keywords = request.keywords.replace('"', '')
                query = f"{base_keywords} filetype:{file_type}"
                if request.site:
                    query += f" site:{request.site}"

            result = await google_dorker.search_google(
                query=query,
                max_results=request.max_results // len(request.file_types)
            )

            if result and not result.get("error"):
                for doc in result.get("results", []):
                    doc["file_type"] = file_type
                    doc["detected_type"] = file_type

                    # Tentar extrair informações adicionais da URL
                    if "." + file_type in doc["url"]:
                        doc["likely_file"] = True
                        filename = doc["url"].split("/")[-1]
                        doc["filename"] = filename

                    document_results["documents_found"].append(doc)

                    # Estatísticas
                    domain = doc["domain"]
                    if file_type not in document_results["statistics"]["by_file_type"]:
                        document_results["statistics"]["by_file_type"][file_type] = 0
                    document_results["statistics"]["by_file_type"][file_type] += 1

                    if domain not in document_results["statistics"]["by_domain"]:
                        document_results["statistics"]["by_domain"][domain] = 0
                    document_results["statistics"]["by_domain"][domain] += 1

            await asyncio.sleep(random.uniform(3, 6))

        document_results["statistics"]["total_found"] = len(document_results["documents_found"])

        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, document_results)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": document_results
        }

    except Exception as e:
        logger.error(f"Erro na busca de documentos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/social")
async def search_social_media(request: SocialDorkRequest, background_tasks: BackgroundTasks):
    """Busca especializada em redes sociais"""
    try:
        logger.info(f"Busca social para: {request.target}")

        # Verificar cache
        cache_key = generate_cache_key("social", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

        social_results = {
            "target": request.target,
            "platforms": request.platforms,
            "profiles_found": [],
            "posts_found": [],
            "statistics": {
                "total_profiles": 0,
                "total_posts": 0,
                "platforms_with_results": []
            },
            "search_timestamp": datetime.utcnow().isoformat()
        }

        platform_sites = {
            "twitter": "twitter.com",
            "facebook": "facebook.com",
            "instagram": "instagram.com",
            "linkedin": "linkedin.com",
            "youtube": "youtube.com",
            "tiktok": "tiktok.com"
        }

        for platform in request.platforms:
            if platform not in platform_sites:
                continue

            site = platform_sites[platform]

            # Buscar perfis
            if request.include_profiles:
                profile_query = f'"{request.target}" site:{site}'
                profile_result = await google_dorker.search_google(
                    query=profile_query,
                    max_results=request.max_results // len(request.platforms)
                )

                if profile_result and not profile_result.get("error"):
                    for profile in profile_result.get("results", []):
                        profile["platform"] = platform
                        profile["result_type"] = "profile"
                        social_results["profiles_found"].append(profile)

                        if platform not in social_results["statistics"]["platforms_with_results"]:
                            social_results["statistics"]["platforms_with_results"].append(platform)

                await asyncio.sleep(random.uniform(2, 4))

            # Buscar posts/conteúdo
            if request.include_posts:
                posts_query = f'site:{site} "{request.target}" -inurl:profile -inurl:user'
                posts_result = await google_dorker.search_google(
                    query=posts_query,
                    max_results=request.max_results // len(request.platforms)
                )

                if posts_result and not posts_result.get("error"):
                    for post in posts_result.get("results", []):
                        post["platform"] = platform
                        post["result_type"] = "post"
                        social_results["posts_found"].append(post)

                await asyncio.sleep(random.uniform(2, 4))

        social_results["statistics"]["total_profiles"] = len(social_results["profiles_found"])
        social_results["statistics"]["total_posts"] = len(social_results["posts_found"])

        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, social_results)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": social_results
        }

    except Exception as e:
        logger.error(f"Erro na busca social: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dorks/patterns")
async def get_dork_patterns():
    """Retorna padrões de dorks disponíveis"""
    return {
        "patterns": DORK_PATTERNS,
        "categories": list(DORK_PATTERNS.keys()),
        "total_patterns": sum(len(patterns) for patterns in DORK_PATTERNS.values())
    }

@app.get("/api/stats")
async def get_stats():
    """Estatísticas do serviço"""
    try:
        stats = {
            "service": "Google OSINT Service",
            "status": "operational",
            "cache_status": "connected" if redis_client else "disconnected",
            "request_count": google_dorker.request_count,
            "last_request": google_dorker.last_request_time,
            "available_patterns": len(DORK_PATTERNS),
            "timestamp": datetime.utcnow().isoformat()
        }

        if redis_client:
            try:
                stats["cache_info"] = {
                    "keys": redis_client.dbsize(),
                    "memory": redis_client.info("memory")["used_memory_human"]
                }
            except:
                pass

        return stats

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Google OSINT Service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup ao parar o serviço"""
    await google_dorker.close_session()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)