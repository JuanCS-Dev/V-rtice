"""
Offensive Tools API Routes.

FastAPI routes para ferramentas offensive: Network Scanner, DNS Enum, Payload Gen.
Integração com MAXIMUS Tool Registry e ethical boundaries.

Philosophy: Powerful tools with ethical guardrails.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, validator, IPvAnyAddress
import structlog

from ..core.tool_registry import registry, ToolCategory
from ..core.base import ToolResult, OperationMode
from ..core.maximus_adapter import MAXIMUSToolContext

log = structlog.get_logger()

# Prometheus Metrics
OFFENSIVE_REQUESTS = Counter(
    "offensive_tools_requests_total",
    "Total offensive tool requests",
    ["tool", "operation", "mode"]
)
OFFENSIVE_LATENCY = Histogram(
    "offensive_tools_latency_seconds",
    "Offensive tool operation latency",
    ["tool", "operation"]
)
ETHICAL_BLOCKS = Counter(
    "offensive_ethical_blocks_total",
    "Requests blocked by ethical boundaries",
    ["tool", "reason"]
)

# Router
router = APIRouter(
    prefix="/offensive",
    tags=["Offensive Tools"],
    responses={404: {"description": "Not found"}}
)


# ============================================================================
# Pydantic Models
# ============================================================================

class ToolExecutionContext(BaseModel):
    """Execution context for tool operations."""
    operation_mode: str = Field(
        default="defensive",
        description="Operation mode: defensive, research, red_team"
    )
    authorization_token: Optional[str] = Field(
        default=None,
        description="Authorization token for high-risk operations"
    )
    target_justification: Optional[str] = Field(
        default=None,
        description="Justification for targeting"
    )

    @validator('operation_mode')
    def validate_mode(cls, v):
        valid_modes = ["defensive", "research", "red_team"]
        if v not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        return v


class NetworkScanRequest(BaseModel):
    """Network scan request."""
    target: str = Field(..., description="Target IP or hostname")
    ports: Optional[List[int]] = Field(
        default=None,
        description="Specific ports to scan. None = common ports"
    )
    timeout: float = Field(default=5.0, ge=0.1, le=60.0)
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)

    @validator('target')
    def validate_target(cls, v):
        # Basic validation - não escanear localhost/private sem justificativa
        if v in ['localhost', '127.0.0.1', '::1']:
            raise ValueError("Localhost scanning requires explicit authorization")
        return v


class DNSEnumerationRequest(BaseModel):
    """DNS enumeration request."""
    domain: str = Field(..., description="Target domain")
    subdomain_wordlist: Optional[List[str]] = Field(
        default=None,
        description="Custom subdomain wordlist"
    )
    dns_servers: Optional[List[str]] = Field(
        default=None,
        description="Custom DNS servers"
    )
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)

    @validator('domain')
    def validate_domain(cls, v):
        if not v or '/' in v or ':' in v:
            raise ValueError("Invalid domain format")
        return v.lower()


class PayloadGenerationRequest(BaseModel):
    """Payload generation request."""
    payload_type: str = Field(
        ...,
        description="Payload type: reverse_shell, bind_shell, etc"
    )
    target_platform: str = Field(
        ...,
        description="Target platform: linux, windows, etc"
    )
    lhost: Optional[str] = Field(default=None, description="Listener host")
    lport: Optional[int] = Field(default=None, ge=1, le=65535)
    obfuscation_level: int = Field(default=1, ge=0, le=3)
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)

    @validator('payload_type')
    def validate_payload_type(cls, v):
        valid_types = ['reverse_shell', 'bind_shell', 'meterpreter', 'custom']
        if v not in valid_types:
            raise ValueError(f"Invalid payload type. Must be one of: {valid_types}")
        return v

    @validator('target_platform')
    def validate_platform(cls, v):
        valid_platforms = ['linux', 'windows', 'macos', 'cross_platform']
        if v not in valid_platforms:
            raise ValueError(f"Invalid platform. Must be one of: {valid_platforms}")
        return v


class ToolResultResponse(BaseModel):
    """Generic tool result response."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    timestamp: datetime
    tool_name: str
    operation_mode: str
    execution_time_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"open_ports": [22, 80, 443]},
                "error": None,
                "timestamp": "2025-10-12T22:00:00Z",
                "tool_name": "network_scanner",
                "operation_mode": "defensive",
                "execution_time_ms": 1234.56
            }
        }


class ToolListResponse(BaseModel):
    """Available tools list."""
    tools: List[Dict[str, Any]]
    total: int
    categories: Dict[str, int]


# ============================================================================
# Helper Functions
# ============================================================================

def create_maximus_context(
    context: ToolExecutionContext,
    user_agent: Optional[str] = None
) -> MAXIMUSToolContext:
    """Create MAXIMUS context from request context."""
    return MAXIMUSToolContext(
        operation_mode=OperationMode(context.operation_mode),
        authorization_token=context.authorization_token,
        user_id=user_agent or "api",
        session_id=f"api_{datetime.utcnow().timestamp()}",
        target_justification=context.target_justification
    )


def convert_tool_result(
    result: ToolResult,
    tool_name: str,
    operation_mode: str
) -> ToolResultResponse:
    """Convert internal ToolResult to API response."""
    return ToolResultResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        timestamp=result.timestamp,
        tool_name=tool_name,
        operation_mode=operation_mode,
        execution_time_ms=result.execution_time * 1000  # Convert to ms
    )


# ============================================================================
# Tool Discovery Endpoints
# ============================================================================

@router.get(
    "/tools",
    response_model=ToolListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available offensive tools"
)
async def list_offensive_tools(
    category: Optional[str] = None
) -> ToolListResponse:
    """
    List all registered offensive tools.
    
    Optionally filter by category: reconnaissance, exploitation, etc.
    """
    try:
        # Get tools from registry
        cat_filter = ToolCategory(category) if category else None
        tools = registry.list_tools(category=cat_filter)
        
        # Convert to API format
        tools_data = [
            {
                "name": t.name,
                "category": t.category.value,
                "description": t.description,
                "requires_auth": t.requires_auth,
                "risk_level": t.risk_level
            }
            for t in tools
        ]
        
        # Count by category
        categories = {}
        for t in tools:
            cat = t.category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        return ToolListResponse(
            tools=tools_data,
            total=len(tools_data),
            categories=categories
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {category}"
        )


@router.get(
    "/tools/{tool_name}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get tool information"
)
async def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get detailed information about specific tool."""
    try:
        info = registry.get_tool_info(tool_name)
        
        return {
            "name": info.name,
            "category": info.category.value,
            "description": info.description,
            "requires_auth": info.requires_auth,
            "risk_level": info.risk_level,
            "status": "available"
        }
        
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_name}"
        )


@router.get(
    "/registry/stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get registry statistics"
)
async def get_registry_stats() -> Dict[str, Any]:
    """Get tool registry statistics."""
    stats = registry.get_stats()
    return {
        **stats,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Network Scanner Endpoints
# ============================================================================

@router.post(
    "/scan/network",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan network target"
)
async def scan_network(
    request: NetworkScanRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Execute network scan.
    
    AI-enhanced port scanner with service detection.
    Defensive mode: common ports only.
    Research/RedTeam: full range with authorization.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="network_scanner",
        operation="scan",
        mode=request.context.operation_mode
    ).inc()
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="network_scanner", operation="scan").time():
            # Get tool with MAXIMUS wrapper
            tool = registry.get_tool("network_scanner", with_maximus=True)
            
            # Create context
            context = create_maximus_context(request.context, user_agent)
            
            # Execute scan
            result = await tool.execute(
                target=request.target,
                ports=request.ports,
                timeout=request.timeout,
                context=context
            )
            
            log.info(
                "network_scan_completed",
                target=request.target,
                success=result.success,
                mode=request.context.operation_mode
            )
            
            return convert_tool_result(
                result,
                "network_scanner",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="network_scanner", reason="unauthorized").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        log.error("network_scan_failed", error=str(e), target=request.target)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


# ============================================================================
# DNS Enumeration Endpoints
# ============================================================================

@router.post(
    "/recon/dns-enum",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Enumerate DNS records"
)
async def enumerate_dns(
    request: DNSEnumerationRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Execute DNS enumeration.
    
    Discovers subdomains, DNS records, and infrastructure.
    Low risk OSINT operation.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="dns_enumerator",
        operation="enumerate",
        mode=request.context.operation_mode
    ).inc()
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="dns_enumerator", operation="enumerate").time():
            # Get tool
            tool = registry.get_tool("dns_enumerator", with_maximus=True)
            
            # Create context
            context = create_maximus_context(request.context, user_agent)
            
            # Execute enumeration
            result = await tool.execute(
                domain=request.domain,
                subdomain_wordlist=request.subdomain_wordlist,
                dns_servers=request.dns_servers,
                context=context
            )
            
            log.info(
                "dns_enum_completed",
                domain=request.domain,
                success=result.success
            )
            
            return convert_tool_result(
                result,
                "dns_enumerator",
                request.context.operation_mode
            )
            
    except Exception as e:
        log.error("dns_enum_failed", error=str(e), domain=request.domain)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DNS enumeration failed: {str(e)}"
        )


# ============================================================================
# Payload Generation Endpoints
# ============================================================================

@router.post(
    "/exploit/generate-payload",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate exploitation payload"
)
async def generate_payload(
    request: PayloadGenerationRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Generate exploitation payload.
    
    HIGH RISK: Requires authorization token.
    Only for authorized red team operations.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="payload_generator",
        operation="generate",
        mode=request.context.operation_mode
    ).inc()
    
    # Verify high-risk authorization
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="payload_generator", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization token required for payload generation"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="payload_generator", operation="generate").time():
            # Get tool
            tool = registry.get_tool("payload_generator", with_maximus=True)
            
            # Create context
            context = create_maximus_context(request.context, user_agent)
            
            # Generate payload
            result = await tool.execute(
                payload_type=request.payload_type,
                target_platform=request.target_platform,
                lhost=request.lhost,
                lport=request.lport,
                obfuscation_level=request.obfuscation_level,
                context=context
            )
            
            log.warning(
                "payload_generated",
                payload_type=request.payload_type,
                platform=request.target_platform,
                mode=request.context.operation_mode,
                user=user_agent
            )
            
            return convert_tool_result(
                result,
                "payload_generator",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="payload_generator", reason="unauthorized").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        log.error("payload_generation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payload generation failed: {str(e)}"
        )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check() -> Dict:
    """Health check for offensive tools."""
    stats = registry.get_stats()
    
    return {
        "status": "operational",
        "registry": {
            "tools_registered": stats["total_tools"],
            "tools_instantiated": stats["instantiated"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }
