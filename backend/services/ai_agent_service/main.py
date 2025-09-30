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
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic, openai, local
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

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

# ========================================
# LLM INTEGRATION
# ========================================

async def call_llm_with_tools(messages: List[Dict], tools: List[Dict]) -> Dict:
    """
    Chama o LLM (Anthropic Claude) com tool calling support
    """
    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
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
        "version": "1.0.0",
        "status": "online",
        "llm_provider": LLM_PROVIDER,
        "llm_configured": bool(ANTHROPIC_API_KEY or OPENAI_API_KEY),
        "available_tools": len(TOOLS),
        "capabilities": {
            "conversational_ai": True,
            "tool_calling": True,
            "autonomous_investigation": True,
            "multi_service_orchestration": True
        }
    }

@app.get("/tools")
async def list_tools():
    """Lista todas as tools disponíveis para a AI"""
    return {
        "total_tools": len(TOOLS),
        "tools": TOOLS
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint conversacional principal. A AI pode:
    - Responder perguntas
    - Chamar tools para executar ações
    - Fazer investigações autônomas
    - Orquestrar múltiplos serviços
    """

    # System prompt
    system_prompt = """Você é o VÉRTICE AI, um agente de inteligência cibernética avançado.

Você tem acesso maestro a múltiplos serviços de segurança através de tools (function calling).

Suas capacidades:
- Análise de threat intelligence (offline-first, sem depender de APIs externas)
- Detecção de malware e análise de hashes
- Verificação de certificados SSL/TLS
- Intelligence de IPs (geolocalização, ASN, ISP)
- Scanning de portas e vulnerabilidades
- OSINT (Open Source Intelligence)
- Predição de criminalidade com IA
- Investigações completas automatizadas

Você é proativo, preciso, e sempre usa as tools disponíveis para fornecer informações REAIS e VERIFICADAS.
Nunca invente dados - sempre use as tools para obter informações reais dos serviços.

Quando o usuário pedir para analisar algo, USE AS TOOLS automaticamente.
Seja conciso mas completo. Priorize informações críticas primeiro."""

    messages_with_system = [
        {"role": "system", "content": system_prompt}
    ] + [msg.dict() for msg in request.messages]

    tools_used = []
    max_iterations = 5  # Prevenir loops infinitos

    for iteration in range(max_iterations):
        # Chamar LLM
        llm_response = await call_llm_with_tools(messages_with_system, TOOLS)

        # Se não há tool calls, retornar resposta
        if not llm_response.get("tool_calls"):
            return ChatResponse(
                response=llm_response["content"],
                tools_used=tools_used,
                timestamp=datetime.now().isoformat()
            )

        # Executar tools
        tool_results = []
        for tool_call in llm_response["tool_calls"]:
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]

            # Executar tool
            result = await execute_tool(tool_name, tool_input)

            tools_used.append(ToolUse(
                tool_name=tool_name,
                tool_input=tool_input,
                result=result
            ))

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call["id"],
                "content": json.dumps(result)
            })

        # Adicionar tool results à conversa
        messages_with_system.append({
            "role": "assistant",
            "content": llm_response.get("content", "") or tool_results
        })

        messages_with_system.append({
            "role": "user",
            "content": tool_results
        })

        # Se o LLM disse que terminou, sair do loop
        if llm_response.get("stop_reason") == "end_turn":
            break

    # Resposta final após executar tools
    final_response = await call_llm_with_tools(messages_with_system, TOOLS)

    return ChatResponse(
        response=final_response["content"],
        tools_used=tools_used,
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "llm_ready": bool(ANTHROPIC_API_KEY or OPENAI_API_KEY)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)