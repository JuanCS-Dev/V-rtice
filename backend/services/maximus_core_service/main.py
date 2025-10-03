"""
AI Agent Service - O CÉREBRO DO VÉRTICE
Sistema AI-FIRST com tool calling (function calling) para acesso maestro a todos os serviços.

Inspirado no Claude Code: A AI pode chamar tools/funções para executar ações reais.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
import httpx
import json
import os
import asyncio

# COGNITIVE CORE - The brain that makes Aurora think
from reasoning_engine import ReasoningEngine, ThoughtChain

# MEMORY SYSTEM - Maximus's memory (short-term, long-term, semantic)
from memory_system import MemorySystem, ConversationContext

# MAXIMUS AI 2.0 INTEGRATED SYSTEM - Complete AI Brain
from maximus_integrated import (
    MaximusIntegratedSystem,
    MaximusRequest,
    MaximusResponse,
    ResponseMode
)

# MAXIMUS AI 2.0 COGNITIVE SYSTEMS
from rag_system import RAGSystem, Source, SourceType
from chain_of_thought import ChainOfThoughtEngine, ReasoningType
from confidence_scoring import ConfidenceScoringSystem
from self_reflection import SelfReflectionEngine

# GEMINI CLIENT
from gemini_client import GeminiClient, GeminiConfig


# WORLD-CLASS TOOLS - NSA-grade arsenal
from tools_world_class import (
    WORLD_CLASS_TOOLS,
    get_tool_catalog,
    # Cyber Security
    exploit_search,
    dns_enumeration,
    subdomain_discovery,
    web_crawler,
    javascript_analysis,
    container_scan,
    # OSINT
    social_media_deep_dive,
    breach_data_search,
    # Analytics
    pattern_recognition,
    anomaly_detection,
    time_series_analysis,
    graph_analysis,
    nlp_entity_extraction,
)

# TOOL ORCHESTRATOR - Parallel execution, caching, validation
from tool_orchestrator import ToolOrchestrator, ToolExecution, ValidationLevel

app = FastAPI(
    title="Vértice AI Agent - AI-FIRST Brain",
    description="Sistema de IA conversacional com acesso maestro a todos os serviços via tool calling",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
THREAT_INTEL_URL = os.getenv("THREAT_INTEL_SERVICE_URL", "http://threat_intel_service:80")
MALWARE_ANALYSIS_URL = os.getenv("MALWARE_ANALYSIS_SERVICE_URL", "http://malware_analysis_service:80")
SSL_MONITOR_URL = os.getenv("SSL_MONITOR_SERVICE_URL", "http://ssl_monitor_service:80")
IP_INTEL_URL = os.getenv("IP_INTEL_SERVICE_URL", "http://ip_intelligence_service:80")
NMAP_SERVICE_URL = os.getenv("NMAP_SERVICE_URL", "http://nmap_service:80")
VULN_SCANNER_URL = os.getenv("VULN_SCANNER_SERVICE_URL", "http://vuln_scanner_service:80")
DOMAIN_SERVICE_URL = os.getenv("DOMAIN_SERVICE_URL", "http://domain_service:80")
AURORA_PREDICT_URL = os.getenv("AURORA_PREDICT_URL", "http://aurora_predict:80")
OSINT_SERVICE_URL = os.getenv("OSINT_SERVICE_URL", "http://osint-service:8007")

# API Key para LLM (OpenAI, Anthropic, etc)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # anthropic, openai, local
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


# Initialize Gemini Client
gemini_client = None
if GEMINI_API_KEY:
    gemini_config = GeminiConfig(
        api_key=GEMINI_API_KEY,
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        max_tokens=4096
    )
    gemini_client = GeminiClient(gemini_config)
    print("✅ Gemini client initialized")

# Create wrapper for Gemini client to match reasoning engine interface
async def gemini_wrapper(messages: list) -> dict:
    """Adapts Gemini client to reasoning engine's expected interface"""
    import logging
    logger = logging.getLogger(__name__)

    # Extract the last user message as the prompt
    prompt = messages[-1]["content"] if messages else ""
    logger.info(f"[Gemini Wrapper] Calling Gemini with prompt length: {len(prompt)}")

    response = await gemini_client.generate_text(prompt=prompt)
    logger.info(f"[Gemini Wrapper] Received response: {response.keys()}")
    logger.info(f"[Gemini Wrapper] Text length: {len(response.get('text', ''))}")

    # Return in format expected by reasoning engine
    return {"content": response.get("text", "")}

# Initialize Reasoning Engine
reasoning_engine = ReasoningEngine(
    llm_provider=LLM_PROVIDER,
    anthropic_api_key=ANTHROPIC_API_KEY,
    openai_api_key=OPENAI_API_KEY,
    llm_callable=gemini_wrapper  # Pass wrapped Gemini client
)

# Initialize Memory System
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/aurora")
ENABLE_SEMANTIC_MEMORY = os.getenv("ENABLE_SEMANTIC_MEMORY", "false").lower() == "true"

memory_system = MemorySystem(
    redis_url=REDIS_URL,
    postgres_url=POSTGRES_URL,
    enable_semantic=ENABLE_SEMANTIC_MEMORY
)

# Initialize Tool Orchestrator
tool_orchestrator = ToolOrchestrator(
    max_concurrent=5,
    enable_cache=True,
    cache_ttl=300,  # 5 minutes
    default_timeout=30
)


# Initialize Maximus AI 2.0 Integrated System
maximus_system = MaximusIntegratedSystem(
    llm_client=gemini_client,
    enable_rag=True,
    enable_reasoning=True,
    enable_memory=True,
    enable_reflection=True
)

# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Inicializa sistemas na startup"""
    # Memory System é opcional - app funciona sem ele
    try:
        await memory_system.initialize()
        print("✅ Memory System initialized")
    except Exception as e:
        print(f"⚠️  Memory System initialization failed: {e}")
        print("   Maximus will run without persistent memory")

    # Maximus System também é opcional
    # try:
    #     await maximus_system.initialize()
    #     print("✅ Maximus AI 2.0 Integrated System initialized")
    # except Exception as e:
    #     print(f"⚠️  Maximus AI 2.0 initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Desliga sistemas no shutdown"""
    try:
        await memory_system.shutdown()
        print("👋 Memory System shutdown")
    except:
        pass

    # try:
    #     await maximus_system.shutdown()
    #     print("👋 Maximus AI 2.0 shutdown")
    # except:
    #     pass

# ========================================
# TOOL DEFINITIONS (Function Calling)
# ========================================

TOOLS = [
    {
        "name": "analyze_threat_intelligence",
        "description": "Analisa ameaças de um target (IP, domain, hash) usando threat intelligence offline-first. Retorna threat score, reputação, e recomendações.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "O target a ser analisado (IP, domain, hash, URL)"
                },
                "target_type": {
                    "type": "string",
                    "enum": ["auto", "ip", "domain", "hash", "url"],
                    "description": "Tipo do target. Use 'auto' para detecção automática"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "analyze_malware",
        "description": "Analisa malware usando hash MD5/SHA1/SHA256. Sistema offline-first com database local. Retorna se é malicioso, família de malware, e recomendações.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hash_value": {
                    "type": "string",
                    "description": "Hash do arquivo (MD5, SHA1 ou SHA256)"
                },
                "hash_type": {
                    "type": "string",
                    "enum": ["auto", "md5", "sha1", "sha256"],
                    "description": "Tipo do hash. Use 'auto' para detecção automática"
                }
            },
            "required": ["hash_value"]
        }
    },
    {
        "name": "check_ssl_certificate",
        "description": "Analisa certificado SSL/TLS de um domínio. Verifica vulnerabilidades, compliance (PCI-DSS, HIPAA, NIST), e retorna security score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Domínio ou IP para verificar SSL"
                },
                "port": {
                    "type": "integer",
                    "description": "Porta SSL (default: 443)",
                    "default": 443
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "get_ip_intelligence",
        "description": "Obtém informações detalhadas sobre um IP: geolocalização, ISP, ASN, hostname, organização.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ip": {
                    "type": "string",
                    "description": "Endereço IP a ser analisado"
                }
            },
            "required": ["ip"]
        }
    },
    {
        "name": "scan_ports_nmap",
        "description": "Executa scan de portas usando Nmap. Detecta serviços, versões, e possíveis vulnerabilidades.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP ou domínio para scan"
                },
                "scan_type": {
                    "type": "string",
                    "enum": ["quick", "full", "stealth"],
                    "description": "Tipo de scan: quick (top 100 portas), full (todas), stealth (evita detecção)"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "scan_vulnerabilities",
        "description": "Escaneia vulnerabilidades conhecidas em um target. Retorna CVEs, severidade, e exploits conhecidos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "IP, domínio ou URL para scan de vulnerabilidades"
                },
                "scan_depth": {
                    "type": "string",
                    "enum": ["basic", "deep"],
                    "description": "Profundidade do scan"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "lookup_domain",
        "description": "Lookup completo de domínio: WHOIS, DNS records, subdomains, histórico.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Domínio para lookup"
                }
            },
            "required": ["domain"]
        }
    },
    {
        "name": "predict_crime_hotspots",
        "description": "Analisa dados de criminalidade e prediz hotspots usando IA. Retorna locais de risco com scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "occurrences": {
                    "type": "array",
                    "description": "Lista de ocorrências criminais com lat, lng, timestamp, tipo",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"},
                            "timestamp": {"type": "string"},
                            "tipo": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["occurrences"]
        }
    },
    {
        "name": "osint_username",
        "description": "Investiga um username em múltiplas plataformas sociais. Retorna perfis encontrados, informações públicas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Username para investigação OSINT"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "investigate_comprehensive",
        "description": "Investigação COMPLETA usando Aurora Orchestrator. Executa múltiplos serviços em paralelo e retorna análise agregada.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target para investigação completa"
                },
                "investigation_type": {
                    "type": "string",
                    "enum": ["auto", "defensive", "offensive", "full"],
                    "description": "Tipo de investigação"
                }
            },
            "required": ["target"]
        }
    }
]

# ========================================
# TOOL IMPLEMENTATIONS
# ========================================

async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Executa uma tool e retorna o resultado"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if tool_name == "analyze_threat_intelligence":
                response = await client.post(
                    f"{THREAT_INTEL_URL}/api/threat-intel/check",
                    json={
                        "target": tool_input["target"],
                        "target_type": tool_input.get("target_type", "auto")
                    }
                )
                return response.json()

            elif tool_name == "analyze_malware":
                response = await client.post(
                    f"{MALWARE_ANALYSIS_URL}/api/malware/analyze-hash",
                    json={
                        "hash_value": tool_input["hash_value"],
                        "hash_type": tool_input.get("hash_type", "auto")
                    }
                )
                return response.json()

            elif tool_name == "check_ssl_certificate":
                response = await client.post(
                    f"{SSL_MONITOR_URL}/api/ssl/check",
                    json={
                        "target": tool_input["target"],
                        "port": tool_input.get("port", 443)
                    }
                )
                return response.json()

            elif tool_name == "get_ip_intelligence":
                response = await client.get(
                    f"{IP_INTEL_URL}/api/ip-intelligence/{tool_input['ip']}"
                )
                return response.json()

            elif tool_name == "scan_ports_nmap":
                response = await client.post(
                    f"{NMAP_SERVICE_URL}/api/nmap/scan",
                    json={
                        "target": tool_input["target"],
                        "scan_type": tool_input.get("scan_type", "quick")
                    }
                )
                return response.json()

            elif tool_name == "scan_vulnerabilities":
                response = await client.post(
                    f"{VULN_SCANNER_URL}/api/vuln/scan",
                    json={
                        "target": tool_input["target"],
                        "scan_depth": tool_input.get("scan_depth", "basic")
                    }
                )
                return response.json()

            elif tool_name == "lookup_domain":
                response = await client.get(
                    f"{DOMAIN_SERVICE_URL}/api/domain/lookup/{tool_input['domain']}"
                )
                return response.json()

            elif tool_name == "predict_crime_hotspots":
                response = await client.post(
                    f"{AURORA_PREDICT_URL}/predict/crime-hotspots",
                    json={"occurrences": tool_input["occurrences"]}
                )
                return response.json()

            elif tool_name == "osint_username":
                response = await client.post(
                    f"{OSINT_SERVICE_URL}/api/osint/username",
                    json={"username": tool_input["username"]}
                )
                return response.json()

            elif tool_name == "investigate_comprehensive":
                # Aurora Orchestrator
                response = await client.post(
                    "http://aurora_orchestrator_service:80/api/aurora/investigate",
                    json={
                        "target": tool_input["target"],
                        "investigation_type": tool_input.get("investigation_type", "auto")
                    }
                )
                return response.json()

            else:
                return {"error": f"Tool '{tool_name}' not implemented"}

        except Exception as e:
            return {"error": str(e), "tool": tool_name}

# ========================================
# MODELS
# ========================================

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "claude-3-5-sonnet-20241022"
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7

class ToolUse(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    tools_used: List[ToolUse]
    conversation_id: Optional[str] = None
    timestamp: str
    reasoning_trace: Optional[Dict[str, Any]] = None  # Chain-of-Thought transparency

# ========================================
# LLM INTEGRATION
# ========================================

async def call_llm_with_tools(messages: List[Dict], tools: List[Dict]) -> Dict:
    """
    Chama o LLM com tool calling support (Gemini, Anthropic Claude, OpenAI GPT)
    """
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return await call_google_gemini(messages, tools)
    elif LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        return await call_anthropic_claude(messages, tools)
    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return await call_openai_gpt(messages, tools)
    else:
        # Fallback: resposta simulada
        return {
            "role": "assistant",
            "content": "⚠️ LLM não configurado. Configure ANTHROPIC_API_KEY ou OPENAI_API_KEY para habilitar a IA conversacional completa.",
            "tool_calls": []
        }


async def call_google_gemini(messages: List[Dict], tools: List[Dict]) -> Dict:
    """Chama Google Gemini API com tool calling"""

    if not GEMINI_API_KEY or not gemini_client:
        return {
            "role": "assistant",
            "content": "Configure GEMINI_API_KEY para usar Gemini",
            "tool_calls": []
        }

    try:
        # Extrai system message
        system_instruction = None
        conversation_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })

        # Chama Gemini
        if conversation_messages:
            response = await gemini_client.generate_with_conversation(
                messages=conversation_messages,
                system_instruction=system_instruction,
                tools=tools if tools else None
            )
        else:
            response = await gemini_client.generate_text(
                prompt=system_instruction or "Hello",
                tools=tools if tools else None
            )

        # Converte resposta para formato unificado
        tool_calls = []
        for tc in response.get("tool_calls", []):
            tool_calls.append({
                "id": f"call_{tc['name']}",
                "name": tc["name"],
                "input": tc.get("arguments", {})
            })

        return {
            "role": "assistant",
            "content": response.get("text", ""),
            "tool_calls": tool_calls,
            "stop_reason": response.get("finish_reason", "stop")
        }

    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Erro ao chamar Gemini: {str(e)}",
            "tool_calls": []
        }

async def call_anthropic_claude(messages: List[Dict], tools: List[Dict]) -> Dict:
    """Chama Anthropic Claude API com tool calling"""

    if not ANTHROPIC_API_KEY:
        return {
            "role": "assistant",
            "content": "Configure ANTHROPIC_API_KEY para usar Claude",
            "tool_calls": []
        }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Separar system message
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation_messages.append(msg)

            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "tools": tools,
                "messages": conversation_messages
            }

            if system_message:
                payload["system"] = system_message

            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                return {
                    "role": "assistant",
                    "content": f"Erro na API Anthropic: {response.text}",
                    "tool_calls": []
                }

            result = response.json()

            # Extrair tool calls se houver
            tool_calls = []
            content_text = ""

            for content_block in result.get("content", []):
                if content_block.get("type") == "text":
                    content_text += content_block.get("text", "")
                elif content_block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": content_block.get("id"),
                        "name": content_block.get("name"),
                        "input": content_block.get("input", {})
                    })

            return {
                "role": "assistant",
                "content": content_text,
                "tool_calls": tool_calls,
                "stop_reason": result.get("stop_reason")
            }

        except Exception as e:
            return {
                "role": "assistant",
                "content": f"Erro ao chamar Claude: {str(e)}",
                "tool_calls": []
            }

async def call_openai_gpt(messages: List[Dict], tools: List[Dict]) -> Dict:
    """Chama OpenAI GPT API com function calling"""

    if not OPENAI_API_KEY:
        return {
            "role": "assistant",
            "content": "Configure OPENAI_API_KEY para usar GPT",
            "tool_calls": []
        }

    # TODO: Implementar OpenAI function calling
    return {
        "role": "assistant",
        "content": "OpenAI integration coming soon",
        "tool_calls": []
    }

# ========================================
# ENDPOINTS
# ========================================

@app.get("/")
async def root():
    return {
        "service": "Vértice AI Agent - AI-FIRST Brain",
        "version": "2.0.0",  # Aurora 2.0 - World-Class
        "status": "online",
        "llm_provider": LLM_PROVIDER,
        "llm_configured": bool(ANTHROPIC_API_KEY or OPENAI_API_KEY),
        "legacy_tools": len(TOOLS),
        "world_class_tools": len(WORLD_CLASS_TOOLS),
        "total_tools": len(TOOLS) + len(WORLD_CLASS_TOOLS),
        "capabilities": {
            "conversational_ai": True,
            "tool_calling": True,
            "autonomous_investigation": True,
            "multi_service_orchestration": True,
            "chain_of_thought_reasoning": True,
            "multi_layer_memory": True,
            "parallel_tool_execution": True,
            "result_caching": True,
            "result_validation": True,
            "nsa_grade": True
        },
        "cognitive_systems": {
            "reasoning_engine": "online",
            "memory_system": "online",
            "tool_orchestrator": "online"
        }
    }

@app.get("/tools")
async def list_tools():
    """Lista todas as tools disponíveis para a AI"""
    return {
        "legacy_tools": len(TOOLS),
        "world_class_tools": len(WORLD_CLASS_TOOLS),
        "total_tools": len(TOOLS) + len(WORLD_CLASS_TOOLS),
        "legacy": TOOLS,
        "world_class": get_tool_catalog()
    }

@app.get("/tools/world-class")
async def list_world_class_tools():
    """
    Lista as World-Class Tools (NSA-grade).

    17 tools de nível mundial organizadas por categoria:
    - Cyber Security (6)
    - OSINT (2)
    - Analytics (5)
    - Advanced Tools (4)
    """
    catalog = get_tool_catalog()

    # Organize by category
    by_category = {}
    for name, info in catalog.items():
        category = info.get("category", "other")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append({
            "name": name,
            "description": info.get("description"),
            "complexity": info.get("complexity"),
            "avg_execution_time": info.get("avg_execution_time")
        })

    return {
        "total_tools": len(WORLD_CLASS_TOOLS),
        "categories": list(by_category.keys()),
        "tools_by_category": by_category,
        "standards": {
            "type_safety": "Pydantic models",
            "self_validating": True,
            "self_documenting": True,
            "graceful_failures": True,
            "performance_optimized": True,
            "intelligence_first": True
        },
        "catalog": catalog
    }

@app.post("/tools/world-class/execute")
async def execute_world_class_tool(
    tool_name: str,
    tool_input: Dict[str, Any]
):
    """
    Executa uma World-Class Tool diretamente.

    Args:
        tool_name: Nome da tool (ex: 'exploit_search')
        tool_input: Input parameters para a tool

    Returns:
        BaseToolResult com status, confidence, dados e metadata
    """
    if tool_name not in WORLD_CLASS_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(WORLD_CLASS_TOOLS.keys())}"
        )

    try:
        tool_func = WORLD_CLASS_TOOLS[tool_name]
        result = await tool_func(**tool_input)

        return {
            "tool_name": tool_name,
            "status": result.status,
            "confidence": result.confidence,
            "confidence_level": result.confidence_level,
            "is_actionable": result.is_actionable,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.timestamp,
            "result": result.dict(),
            "metadata": result.metadata,
            "errors": result.errors,
            "warnings": result.warnings
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )

@app.post("/tools/world-class/execute-parallel")
async def execute_parallel_tools(
    executions: List[Dict[str, Any]],
    fail_fast: bool = False
):
    """
    Executa múltiplas World-Class Tools em paralelo.

    Usa o ToolOrchestrator para:
    - Execução paralela (max 5 concurrent)
    - Caching automático (TTL 5 min)
    - Retry inteligente
    - Validação de resultados

    Args:
        executions: Lista de {tool_name, tool_input, priority?}
        fail_fast: Se True, para tudo no primeiro erro

    Returns:
        Lista de resultados com status, timing, confidence
    """
    tool_executions = []

    for exec_spec in executions:
        tool_name = exec_spec.get("tool_name")
        tool_input = exec_spec.get("tool_input", {})
        priority = exec_spec.get("priority", 5)

        if tool_name not in WORLD_CLASS_TOOLS:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )

        tool_func = WORLD_CLASS_TOOLS[tool_name]

        tool_executions.append(ToolExecution(
            tool_name=tool_name,
            tool_input=tool_input,
            executor=lambda inp, func=tool_func: func(**inp),
            priority=priority
        ))

    # Execute in parallel
    results = await tool_orchestrator.execute_parallel(
        executions=tool_executions,
        fail_fast=fail_fast
    )

    # Format results
    formatted_results = []
    for exec_result in results:
        formatted_results.append({
            "tool_name": exec_result.tool_name,
            "status": exec_result.status,
            "result": exec_result.result,
            "error": exec_result.error,
            "execution_time_ms": exec_result.execution_time_ms,
            "retry_count": exec_result.retry_count,
            "cached": exec_result.cached,
            "start_time": exec_result.start_time,
            "end_time": exec_result.end_time
        })

    # Get orchestrator stats
    orchestrator_stats = tool_orchestrator.get_stats()

    return {
        "executions": formatted_results,
        "summary": {
            "total": len(results),
            "successful": sum(1 for r in results if r.status == "success"),
            "failed": sum(1 for r in results if r.status == "failed"),
            "cached": sum(1 for r in results if r.cached),
            "total_time_ms": sum(r.execution_time_ms or 0 for r in results)
        },
        "orchestrator_stats": orchestrator_stats
    }

@app.get("/tools/orchestrator/stats")
async def get_orchestrator_stats():
    """
    Retorna estatísticas do Tool Orchestrator.

    Mostra:
    - Total de execuções
    - Taxa de sucesso
    - Cache hit rate
    - Performance metrics
    """
    return tool_orchestrator.get_stats()

@app.post("/test-gemini")
async def test_gemini(request: ChatRequest):
    """Simple test endpoint that bypasses reasoning engine"""
    user_query = request.messages[-1].content if request.messages else ""

    # Direct Gemini call
    response = await gemini_client.generate_text(prompt=user_query)

    return {
        "response": response.get("text", ""),
        "thought_chain": [],
        "tool_results": [],
        "metadata": {"test_mode": True}
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint conversacional principal com REASONING ENGINE + MEMORY.

    Aurora agora:
    - LEMBRA de conversas anteriores (working + episodic memory)
    - PENSA explicitamente (chain-of-thought)
    - APRENDE com investigações (semantic memory)
    - CONTEXTUALIZA baseado em histórico
    """

    # Generate session ID (or get from request metadata)
    import uuid
    session_id = str(uuid.uuid4())
    user_id = getattr(request, 'conversation_id', 'anonymous')  # If provided

    # Get last user message
    user_query = request.messages[-1].content if request.messages else ""

    # 🧠 REMEMBER: Try to recall conversation context
    conversation_context = await memory_system.remember_conversation(session_id, user_id)

    if not conversation_context:
        # Nova conversa - criar contexto
        conversation_context = ConversationContext(
            session_id=session_id,
            user_id=user_id
        )
        await memory_system.episodic.store_conversation(session_id, user_id)

    # Store user message in memory
    await memory_system.episodic.store_message(
        session_id=session_id,
        role="user",
        content=user_query
    )

    # Update working memory
    await memory_system.working.update_context(
        session_id=session_id,
        new_message={"role": "user", "content": user_query}
    )

    # Build context with memory
    context = {
        "conversation_history": [msg.dict() for msg in request.messages[:-1]],
        "episodic_memory": conversation_context.messages[-10:],  # Last 10 messages
        "available_tools": TOOLS,
        "tool_executor": execute_tool,
        "system_capabilities": {
            "threat_intelligence": True,
            "malware_analysis": True,
            "ssl_monitoring": True,
            "ip_intelligence": True,
            "port_scanning": True,
            "vulnerability_scanning": True,
            "osint": True,
            "crime_prediction": True,
            "comprehensive_investigation": True,
            "memory_enabled": True
        }
    }

    # 🧠 THINK: Cognitive processing with memory context
    thought_chain = await reasoning_engine.think_step_by_step(
        task=user_query,
        context=context,
        max_steps=10,
        confidence_threshold=80.0
    )

    # Extract tools used from execution phase
    tools_used = []
    for thought in thought_chain.thoughts:
        if thought.type == "execution" and "tool_name" in thought.metadata:
            tool_use = ToolUse(
                tool_name=thought.metadata["tool_name"],
                tool_input=thought.metadata.get("tool_input", {}),
                result=thought.metadata.get("tool_result", {})
            )
            tools_used.append(tool_use)

            # Store tool execution in memory
            execution_id = f"exec_{datetime.now().timestamp()}"
            await memory_system.episodic.store_tool_execution(
                execution_id=execution_id,
                session_id=session_id,
                tool_name=thought.metadata["tool_name"],
                tool_input=thought.metadata.get("tool_input", {}),
                tool_output=thought.metadata.get("tool_result", {}),
                success=True
            )

    # Store assistant response in memory
    assistant_response = thought_chain.final_answer or "Processing complete."
    await memory_system.episodic.store_message(
        session_id=session_id,
        role="assistant",
        content=assistant_response
    )

    # Update working memory with response
    await memory_system.working.update_context(
        session_id=session_id,
        new_message={"role": "assistant", "content": assistant_response},
        new_reasoning=thought_chain.__dict__
    )

    # 🧠 LEARN: If this was an investigation, store it
    if tools_used and thought_chain.overall_confidence > 70:
        investigation_id = f"inv_{session_id}_{datetime.now().timestamp()}"
        await memory_system.learn_from_investigation(
            investigation_id=investigation_id,
            session_id=session_id,
            target=user_query[:200],  # First 200 chars as target
            findings={"response": assistant_response},
            tools_used=[t.dict() for t in tools_used],
            reasoning_trace={
                "confidence": thought_chain.overall_confidence,
                "thoughts": len(thought_chain.thoughts)
            }
        )

    return ChatResponse(
        response=assistant_response,
        tools_used=tools_used,
        conversation_id=session_id,
        timestamp=datetime.now().isoformat(),
        reasoning_trace={
            "task": thought_chain.task,
            "total_thoughts": len(thought_chain.thoughts),
            "confidence": thought_chain.overall_confidence,
            "status": thought_chain.status,
            "duration": thought_chain.end_time,
            "memory_context_used": len(conversation_context.messages) if conversation_context else 0,
            "thought_summary": [
                {
                    "type": t.type,
                    "content": t.content[:200] + "..." if len(t.content) > 200 else t.content,
                    "confidence": t.confidence
                }
                for t in thought_chain.thoughts
            ]
        }
    )

@app.post("/chat/reasoning")
async def chat_with_full_reasoning(request: ChatRequest):
    """
    Endpoint que retorna o Chain-of-Thought COMPLETO.

    Use este endpoint para debugging, auditoria, ou quando precisar
    entender exatamente como Aurora chegou a uma conclusão.

    Retorna:
    - Todos os pensamentos (observations, analysis, planning, etc)
    - Confidence score de cada etapa
    - Metadados completos de execução
    - Tools chamadas com timestamps
    """

    user_query = request.messages[-1].content if request.messages else ""

    context = {
        "conversation_history": [msg.dict() for msg in request.messages[:-1]],
        "available_tools": TOOLS,
        "tool_executor": execute_tool,
        "system_capabilities": {
            "threat_intelligence": True,
            "malware_analysis": True,
            "ssl_monitoring": True,
            "ip_intelligence": True,
            "port_scanning": True,
            "vulnerability_scanning": True,
            "osint": True,
            "crime_prediction": True,
            "comprehensive_investigation": True
        }
    }

    # Get complete reasoning chain
    thought_chain = await reasoning_engine.think_step_by_step(
        task=user_query,
        context=context,
        max_steps=10,
        confidence_threshold=80.0
    )

    # Export full trace
    return {
        "task": thought_chain.task,
        "final_answer": thought_chain.final_answer,
        "overall_confidence": thought_chain.overall_confidence,
        "status": thought_chain.status,
        "start_time": thought_chain.start_time,
        "end_time": thought_chain.end_time,
        "complete_thought_chain": [
            {
                "thought_id": t.thought_id,
                "type": t.type,
                "content": t.content,
                "confidence": t.confidence,
                "timestamp": t.timestamp,
                "metadata": t.metadata,
                "parent_thought_id": t.parent_thought_id
            }
            for t in thought_chain.thoughts
        ],
        "metrics": {
            "total_thoughts": len(thought_chain.thoughts),
            "thoughts_by_type": {
                thought_type: sum(1 for t in thought_chain.thoughts if t.type == thought_type)
                for thought_type in set(t.type for t in thought_chain.thoughts)
            },
            "avg_confidence": sum(t.confidence for t in thought_chain.thoughts) / len(thought_chain.thoughts) if thought_chain.thoughts else 0
        }
    }

@app.get("/reasoning/capabilities")
async def reasoning_capabilities():
    """
    Retorna as capacidades cognitivas da Aurora.
    """
    return {
        "cognitive_engine": "Chain-of-Thought Reasoning Engine",
        "version": "2.0",
        "capabilities": {
            "explicit_reasoning": True,
            "self_reflection": True,
            "multi_step_planning": True,
            "dynamic_replanning": True,
            "confidence_scoring": True,
            "tool_orchestration": True,
            "autonomous_investigation": True
        },
        "thought_types": [
            "observation",
            "analysis",
            "hypothesis",
            "planning",
            "execution",
            "validation",
            "reflection",
            "decision",
            "correction"
        ],
        "max_reasoning_steps": 10,
        "confidence_threshold": 80.0,
        "nsa_grade": True
    }

@app.get("/memory/stats")
async def memory_stats():
    """
    Retorna estatísticas do sistema de memória.

    Mostra quantas conversas, mensagens, investigações
    foram armazenadas.
    """
    stats = await memory_system.get_memory_stats()
    return stats

@app.get("/memory/conversation/{session_id}")
async def get_conversation_memory(session_id: str):
    """
    Recupera memória de uma conversa específica.

    Útil para revisar conversas passadas ou continuar
    uma conversa anterior.
    """
    context = await memory_system.remember_conversation(session_id)

    if not context:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "session_id": context.session_id,
        "user_id": context.user_id,
        "message_count": len(context.messages),
        "messages": context.messages[-20:],  # Last 20 messages
        "tools_used_count": len(context.tools_used),
        "created_at": context.created_at,
        "last_activity": context.last_activity
    }

@app.get("/memory/investigations/similar/{target}")
async def get_similar_investigations(target: str, limit: int = 5):
    """
    Busca investigações similares ao target fornecido.

    Aurora pode aprender com investigações passadas.
    """
    investigations = await memory_system.episodic.get_similar_investigations(
        target=target,
        limit=limit
    )

    return {
        "target": target,
        "similar_investigations_found": len(investigations),
        "investigations": investigations
    }

@app.get("/memory/tool-stats/{tool_name}")
async def get_tool_stats(tool_name: str, last_n_days: int = 30):
    """
    Retorna estatísticas de uso de uma tool.

    Taxa de sucesso, tempo médio de execução, etc.
    """
    stats = await memory_system.episodic.get_tool_success_rate(
        tool_name=tool_name,
        last_n_days=last_n_days
    )

    return stats

@app.get("/health")
async def health():
    memory_stats = await memory_system.get_memory_stats()

    return {
        "status": "healthy",
        "llm_ready": bool(GEMINI_API_KEY or ANTHROPIC_API_KEY or OPENAI_API_KEY),
        "reasoning_engine": "online",
        "memory_system": memory_stats,
        "cognitive_capabilities": "NSA-grade"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)