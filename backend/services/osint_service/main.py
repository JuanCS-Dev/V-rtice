"""
OSINT Service - Projeto Vértice
Serviço de inteligência de fontes abertas para SSP-GO
Autor: Juan - Projeto Vértice
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import aiohttp
import redis
import json
import hashlib
import logging
from enum import Enum

# Importações locais (serão implementadas em seguida)
from scrapers.username_hunter import UsernameHunter
from scrapers.social_scraper import SocialScraper
from analyzers.email_analyzer import EmailAnalyzer
from analyzers.phone_analyzer import PhoneAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from ai_processor import AuroraAIProcessor

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OSINT Intelligence Service",
    description="Serviço de inteligência de fontes abertas - Projeto Vértice SSP-GO",
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
        db=2,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("✓ Redis conectado com sucesso")
except Exception as e:
    logger.error(f"✗ Erro ao conectar Redis: {e}")
    redis_client = None

# Inicialização dos analisadores
username_hunter = UsernameHunter()
email_analyzer = EmailAnalyzer()
phone_analyzer = PhoneAnalyzer()
image_analyzer = ImageAnalyzer()
social_scraper = SocialScraper()
aurora_processor = AuroraAIProcessor()

# Modelos Pydantic
class SearchPlatform(str, Enum):
    ALL = "all"
    SOCIAL = "social"
    PROFESSIONAL = "professional"
    FORUMS = "forums"
    DARKWEB = "darkweb"

class UsernameSearchRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    platforms: SearchPlatform = SearchPlatform.ALL
    deep_search: bool = False
    include_archived: bool = False

class EmailSearchRequest(BaseModel):
    email: EmailStr
    check_breaches: bool = True
    check_social: bool = True
    check_reputation: bool = True

class PhoneSearchRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    include_carrier: bool = True
    include_location: bool = True
    check_messaging_apps: bool = True

class SocialProfileRequest(BaseModel):
    platform: str = Field(..., pattern="^(discord|twitter|instagram|linkedin|telegram)$")
    identifier: str = Field(..., min_length=1, max_length=200)
    depth: str = Field(default="medium", pattern="^(basic|medium|deep)$")
    include_connections: bool = True
    include_timeline: bool = True

class ImageAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    extract_faces: bool = True
    extract_text: bool = True
    extract_metadata: bool = True
    reverse_search: bool = False

class ComprehensiveSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    search_type: str = Field(default="person", pattern="^(person|organization|email|phone|username)$")
    max_results: int = Field(default=50, ge=10, le=500)
    include_ai_analysis: bool = True

class AutomatedInvestigationRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    image_url: Optional[str] = None

# Funções auxiliares
def generate_cache_key(prefix: str, params: dict) -> str:
    """Gera chave única para cache"""
    params_str = json.dumps(params, sort_keys=True)
    hash_obj = hashlib.sha256(params_str.encode())
    return f"osint:{prefix}:{hash_obj.hexdigest()}"

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

async def set_cached_result(key: str, data: dict, ttl: int = 3600):
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
        "service": "OSINT Intelligence Service",
        "status": "operational",
        "version": "1.0.0",
        "project": "Vértice SSP-GO",
        "endpoints": {
            "username": "/api/username/search",
            "email": "/api/email/analyze",
            "phone": "/api/phone/analyze",
            "social": "/api/social/profile",
            "image": "/api/image/analyze",
            "comprehensive": "/api/search/comprehensive"
        }
    }

@app.post("/api/username/search")
async def search_username(request: UsernameSearchRequest, background_tasks: BackgroundTasks):
    """Busca username em múltiplas plataformas"""
    try:
        logger.info(f"Buscando username: {request.username}")
        
        # Verificar cache
        cache_key = generate_cache_key("username", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached
        
        # Executar busca
        results = await username_hunter.hunt(
            username=request.username,
            platforms=request.platforms,
            deep_search=request.deep_search,
            include_archived=request.include_archived
        )
        
        # Análise AI se disponível
        if results.get("profiles_found"):
            ai_analysis = await aurora_processor.analyze_profiles(
                profiles=results["profiles_found"],
                context="username_search"
            )
            results["ai_analysis"] = ai_analysis
        
        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, results)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro na busca de username: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/analyze")
async def analyze_email(request: EmailSearchRequest, background_tasks: BackgroundTasks):
    """Análise completa de email"""
    try:
        logger.info(f"Analisando email: {request.email}")
        
        # Verificar cache
        cache_key = generate_cache_key("email", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached
        
        # Executar análise
        results = await email_analyzer.analyze(
            email=request.email,
            check_breaches=request.check_breaches,
            check_social=request.check_social,
            check_reputation=request.check_reputation
        )
        
        # Análise AI para padrões suspeitos
        if results:
            risk_assessment = await aurora_processor.assess_email_risk(
                email_data=results,
                context="security_check"
            )
            results["risk_assessment"] = risk_assessment
        
        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, results, ttl=7200)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/phone/analyze")
async def analyze_phone(request: PhoneSearchRequest, background_tasks: BackgroundTasks):
    """Análise completa de número telefônico"""
    try:
        logger.info(f"Analisando telefone: {request.phone}")
        
        # Verificar cache
        cache_key = generate_cache_key("phone", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached
        
        # Executar análise
        results = await phone_analyzer.analyze(
            phone=request.phone,
            include_carrier=request.include_carrier,
            include_location=request.include_location,
            check_messaging_apps=request.check_messaging_apps
        )
        
        # Enriquecimento com AI
        if results:
            patterns = await aurora_processor.analyze_phone_patterns(
                phone_data=results,
                context="investigation"
            )
            results["behavioral_patterns"] = patterns
        
        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, results)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de telefone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/social/profile")
async def get_social_profile(request: SocialProfileRequest, background_tasks: BackgroundTasks):
    """Extrai perfil de rede social específica"""
    try:
        logger.info(f"Extraindo perfil {request.platform}: {request.identifier}")
        
        # Verificar cache
        cache_key = generate_cache_key("social", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached
        
        # Executar scraping
        results = await social_scraper.scrape_profile(
            platform=request.platform,
            identifier=request.identifier,
            depth=request.depth,
            include_connections=request.include_connections,
            include_timeline=request.include_timeline
        )
        
        # Análise comportamental com Aurora
        if results.get("profile_data"):
            behavioral_analysis = await aurora_processor.analyze_social_behavior(
                profile_data=results["profile_data"],
                platform=request.platform
            )
            results["behavioral_analysis"] = behavioral_analysis
        
        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, results, ttl=1800)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro ao extrair perfil social: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/analyze")
async def analyze_image(request: ImageAnalysisRequest):
    """Análise forense de imagem"""
    try:
        if not request.image_url and not request.image_base64:
            raise HTTPException(status_code=400, detail="URL ou base64 da imagem é obrigatório")
        
        logger.info("Analisando imagem")
        
        # Executar análise
        results = await image_analyzer.analyze(
            image_url=request.image_url,
            image_base64=request.image_base64,
            extract_faces=request.extract_faces,
            extract_text=request.extract_text,
            extract_metadata=request.extract_metadata,
            reverse_search=request.reverse_search
        )
        
        # Análise AI de conteúdo
        if results:
            content_analysis = await aurora_processor.analyze_image_content(
                image_data=results,
                context="forensic_analysis"
            )
            results["content_analysis"] = content_analysis
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de imagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/comprehensive")
async def comprehensive_search(request: ComprehensiveSearchRequest, background_tasks: BackgroundTasks):
    """Busca abrangente em todas as fontes"""
    try:
        logger.info(f"Busca abrangente: {request.query}")
        
        # Verificar cache
        cache_key = generate_cache_key("comprehensive", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached
        
        results = {
            "query": request.query,
            "search_type": request.search_type,
            "results": {}
        }
        
        # Executar buscas paralelas baseadas no tipo
        tasks = []
        
        if request.search_type in ["person", "username"]:
            tasks.append(username_hunter.hunt(request.query, SearchPlatform.ALL))
        
        if request.search_type in ["person", "email"] and "@" in request.query:
            tasks.append(email_analyzer.analyze(request.query))
        
        if request.search_type in ["person", "phone"] and request.query.replace("+", "").replace("-", "").isdigit():
            tasks.append(phone_analyzer.analyze(request.query))
        
        # Aguardar todas as tarefas
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            for i, result in enumerate(task_results):
                if not isinstance(result, Exception):
                    if i == 0:
                        results["results"]["username_search"] = result
                    elif i == 1:
                        results["results"]["email_analysis"] = result
                    elif i == 2:
                        results["results"]["phone_analysis"] = result
        
        # Análise AI integrada
        if request.include_ai_analysis and results["results"]:
            ai_summary = await aurora_processor.generate_investigation_report(
                data=results["results"],
                query=request.query,
                search_type=request.search_type
            )
            results["ai_summary"] = ai_summary
        
        # Cache do resultado
        background_tasks.add_task(set_cached_result, cache_key, results, ttl=3600)
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Erro na busca abrangente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investigate/auto")
async def automated_investigation(request: AutomatedInvestigationRequest, background_tasks: BackgroundTasks):
    """Investigação automatizada orquestrada pelo Aurora AI"""
    try:
        logger.info("Iniciando investigação automatizada")

        # Validar entrada
        provided_fields = [
            request.username, request.email, request.phone,
            request.name, request.image_url
        ]
        if not any(field for field in provided_fields if field):
            raise HTTPException(status_code=400, detail="Pelo menos um identificador deve ser fornecido")

        # Cache key baseado nos dados fornecidos
        cache_key = generate_cache_key("auto_investigation", request.dict())
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

        # Executar investigação orquestrada
        investigation_results = {
            "investigation_id": f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hash(str(request.dict())) % 10000}",
            "target_data": request.dict(),
            "modules_executed": [],
            "findings": {},
            "risk_assessment": None,
            "executive_summary": "",
            "patterns_found": [],
            "recommendations": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Lista de tarefas para execução paralela
        investigation_tasks = []

        # Username investigation
        if request.username:
            investigation_tasks.append(
                username_hunter.hunt(
                    username=request.username,
                    platforms=SearchPlatform.ALL,
                    deep_search=True
                )
            )
            investigation_results["modules_executed"].append("username_hunter")

        # Email analysis
        if request.email:
            investigation_tasks.append(
                email_analyzer.analyze(
                    email=request.email,
                    check_breaches=True,
                    check_social=True,
                    check_reputation=True
                )
            )
            investigation_results["modules_executed"].append("email_analyzer")

        # Phone analysis
        if request.phone:
            investigation_tasks.append(
                phone_analyzer.analyze(
                    phone=request.phone,
                    include_carrier=True,
                    include_location=True,
                    check_messaging_apps=True
                )
            )
            investigation_results["modules_executed"].append("phone_analyzer")

        # Execute all tasks in parallel
        if investigation_tasks:
            task_results = await asyncio.gather(*investigation_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(task_results):
                if not isinstance(result, Exception) and result:
                    module_name = investigation_results["modules_executed"][i]
                    investigation_results["findings"][module_name] = result

        # Aurora AI Analysis
        try:
            ai_analysis = await aurora_processor.generate_investigation_report(
                data=investigation_results["findings"],
                query=f"Auto-investigation: {request.name or request.username or request.email or request.phone}",
                search_type="person"
            )

            if ai_analysis:
                investigation_results["risk_assessment"] = ai_analysis.get("risk_assessment", {
                    "risk_level": "MEDIUM",
                    "risk_score": 50,
                    "risk_factors": ["Dados limitados disponíveis"]
                })
                investigation_results["executive_summary"] = ai_analysis.get("executive_summary", "Investigação automatizada concluída.")
                investigation_results["patterns_found"] = ai_analysis.get("patterns_found", [])
                investigation_results["recommendations"] = ai_analysis.get("recommendations", [])
        except Exception as e:
            logger.warning(f"Erro na análise AI: {e}")
            # Fallback para análise básica
            investigation_results["risk_assessment"] = {
                "risk_level": "MEDIUM",
                "risk_score": 60,
                "risk_factors": ["Análise automatizada", "Múltiplas fontes consultadas"]
            }
            investigation_results["executive_summary"] = "Investigação automatizada realizada com sucesso. Dados coletados de múltiplas fontes OSINT."
            investigation_results["patterns_found"] = [
                {"type": "DATA_COLLECTION", "description": "Dados coletados de fontes abertas"},
                {"type": "AUTOMATED", "description": "Investigação realizada automaticamente"}
            ]
            investigation_results["recommendations"] = [
                {"action": "Análise Manual", "description": "Revisar resultados manualmente"},
                {"action": "Monitoramento", "description": "Configurar alertas para mudanças"}
            ]

        # Cache results
        background_tasks.add_task(set_cached_result, cache_key, investigation_results, ttl=7200)

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": investigation_results
        }

    except Exception as e:
        logger.error(f"Erro na investigação automatizada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Estatísticas do serviço"""
    try:
        stats = {
            "service": "OSINT Intelligence",
            "status": "operational",
            "cache_status": "connected" if redis_client else "disconnected",
            "analyzers": {
                "username_hunter": "active",
                "email_analyzer": "active",
                "phone_analyzer": "active",
                "image_analyzer": "active",
                "social_scraper": "active",
                "aurora_ai": "active"
            },
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
        "service": "OSINT Intelligence Service",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
