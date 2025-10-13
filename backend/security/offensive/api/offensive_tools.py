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
from ..core.base import ToolResult
from ..core.maximus_adapter import MAXIMUSToolContext, OperationMode

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


class PrivilegeEscalationRequest(BaseModel):
    """Privilege escalation request."""
    target_system: str = Field(..., description="Target system info")
    scan_type: str = Field(
        default="comprehensive",
        description="Scan type: quick, comprehensive"
    )
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


class PersistenceRequest(BaseModel):
    """Persistence mechanism request."""
    target_platform: str = Field(..., description="Target platform")
    persistence_type: str = Field(
        ...,
        description="Type: registry, service, scheduled_task, etc"
    )
    stealth_level: int = Field(default=2, ge=1, le=3)
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


class LateralMovementRequest(BaseModel):
    """Lateral movement request."""
    source_host: str = Field(..., description="Source host")
    target_hosts: List[str] = Field(..., description="Target hosts")
    method: str = Field(
        default="smb",
        description="Movement method: smb, wmi, ssh, rdp"
    )
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


class CredentialHarvestRequest(BaseModel):
    """Credential harvesting request."""
    target_system: str = Field(..., description="Target system")
    harvest_types: List[str] = Field(
        default=["memory", "registry", "files"],
        description="Types to harvest"
    )
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


class DataExfiltrationRequest(BaseModel):
    """Data exfiltration request."""
    source_path: str = Field(..., description="Source data path")
    exfil_method: str = Field(
        default="https",
        description="Exfiltration method: https, dns, smb"
    )
    encryption: bool = Field(default=True)
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


class PayloadExecutionRequest(BaseModel):
    """Payload execution request."""
    payload: str = Field(..., description="Payload to execute")
    execution_method: str = Field(
        default="direct",
        description="Execution method: direct, reflective, process_injection"
    )
    target_process: Optional[str] = Field(
        default=None,
        description="Target process for injection"
    )
    context: ToolExecutionContext = Field(default_factory=ToolExecutionContext)


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
# Post-Exploitation: Privilege Escalation
# ============================================================================

@router.post(
    "/post-exploit/privilege-escalation",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Identify privilege escalation vectors"
)
async def privilege_escalation(
    request: PrivilegeEscalationRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Identify privilege escalation opportunities.
    
    HIGH RISK: Requires authorization.
    Scans for misconfigurations, vulnerable services, etc.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="privilege_escalation",
        operation="scan",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="privilege_escalation", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for privilege escalation"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="privilege_escalation", operation="scan").time():
            tool = registry.get_tool("privilege_escalation", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                target_system=request.target_system,
                scan_type=request.scan_type,
                context=context
            )
            
            log.warning(
                "privilege_escalation_scan",
                target=request.target_system,
                mode=request.context.operation_mode
            )
            
            return convert_tool_result(
                result,
                "privilege_escalation",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="privilege_escalation", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("privilege_escalation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Privilege escalation scan failed: {str(e)}"
        )


# ============================================================================
# Post-Exploitation: Persistence
# ============================================================================

@router.post(
    "/post-exploit/persistence",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Establish persistence mechanism"
)
async def establish_persistence(
    request: PersistenceRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Establish persistence on compromised system.
    
    HIGH RISK: Requires authorization.
    Creates mechanisms for maintaining access.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="persistence",
        operation="establish",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="persistence", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for persistence"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="persistence", operation="establish").time():
            tool = registry.get_tool("persistence", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                target_platform=request.target_platform,
                persistence_type=request.persistence_type,
                stealth_level=request.stealth_level,
                context=context
            )
            
            log.warning(
                "persistence_established",
                platform=request.target_platform,
                type=request.persistence_type
            )
            
            return convert_tool_result(
                result,
                "persistence",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="persistence", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("persistence_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Persistence establishment failed: {str(e)}"
        )


# ============================================================================
# Post-Exploitation: Lateral Movement
# ============================================================================

@router.post(
    "/post-exploit/lateral-movement",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute lateral movement"
)
async def lateral_movement(
    request: LateralMovementRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Execute lateral movement to other systems.
    
    HIGH RISK: Requires authorization.
    Moves across network using various methods.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="lateral_movement",
        operation="move",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="lateral_movement", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for lateral movement"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="lateral_movement", operation="move").time():
            tool = registry.get_tool("lateral_movement", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                source_host=request.source_host,
                target_hosts=request.target_hosts,
                method=request.method,
                context=context
            )
            
            log.warning(
                "lateral_movement_executed",
                source=request.source_host,
                targets=request.target_hosts,
                method=request.method
            )
            
            return convert_tool_result(
                result,
                "lateral_movement",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="lateral_movement", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("lateral_movement_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lateral movement failed: {str(e)}"
        )


# ============================================================================
# Post-Exploitation: Credential Harvesting
# ============================================================================

@router.post(
    "/post-exploit/credential-harvest",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Harvest credentials"
)
async def credential_harvest(
    request: CredentialHarvestRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Harvest credentials from compromised system.
    
    HIGH RISK: Requires authorization.
    Extracts passwords, tokens, keys from various sources.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="credential_harvesting",
        operation="harvest",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="credential_harvesting", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for credential harvesting"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="credential_harvesting", operation="harvest").time():
            tool = registry.get_tool("credential_harvesting", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                target_system=request.target_system,
                harvest_types=request.harvest_types,
                context=context
            )
            
            log.warning(
                "credentials_harvested",
                target=request.target_system,
                types=request.harvest_types
            )
            
            return convert_tool_result(
                result,
                "credential_harvesting",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="credential_harvesting", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("credential_harvest_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Credential harvesting failed: {str(e)}"
        )


# ============================================================================
# Post-Exploitation: Data Exfiltration
# ============================================================================

@router.post(
    "/post-exploit/data-exfiltration",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Exfiltrate data"
)
async def data_exfiltration(
    request: DataExfiltrationRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Exfiltrate data from compromised system.
    
    HIGH RISK: Requires authorization.
    Transfers data using covert channels.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="data_exfiltration",
        operation="exfiltrate",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="data_exfiltration", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for data exfiltration"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="data_exfiltration", operation="exfiltrate").time():
            tool = registry.get_tool("data_exfiltration", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                source_path=request.source_path,
                exfil_method=request.exfil_method,
                encryption=request.encryption,
                context=context
            )
            
            log.warning(
                "data_exfiltrated",
                source=request.source_path,
                method=request.exfil_method
            )
            
            return convert_tool_result(
                result,
                "data_exfiltration",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="data_exfiltration", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("data_exfiltration_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data exfiltration failed: {str(e)}"
        )


# ============================================================================
# Exploitation: Payload Execution
# ============================================================================

@router.post(
    "/exploit/execute-payload",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute payload"
)
async def execute_payload(
    request: PayloadExecutionRequest,
    user_agent: Optional[str] = Header(None)
) -> ToolResultResponse:
    """
    Execute exploitation payload.
    
    HIGH RISK: Requires authorization.
    Executes payload with specified method.
    """
    OFFENSIVE_REQUESTS.labels(
        tool="payload_executor",
        operation="execute",
        mode=request.context.operation_mode
    ).inc()
    
    if not request.context.authorization_token:
        ETHICAL_BLOCKS.labels(tool="payload_executor", reason="no_auth_token").inc()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required for payload execution"
        )
    
    try:
        with OFFENSIVE_LATENCY.labels(tool="payload_executor", operation="execute").time():
            tool = registry.get_tool("payload_executor", with_maximus=True)
            context = create_maximus_context(request.context, user_agent)
            
            result = await tool.execute(
                payload=request.payload,
                execution_method=request.execution_method,
                target_process=request.target_process,
                context=context
            )
            
            log.warning(
                "payload_executed",
                method=request.execution_method,
                target_process=request.target_process
            )
            
            return convert_tool_result(
                result,
                "payload_executor",
                request.context.operation_mode
            )
            
    except PermissionError as e:
        ETHICAL_BLOCKS.labels(tool="payload_executor", reason="unauthorized").inc()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        log.error("payload_execution_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payload execution failed: {str(e)}"
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
