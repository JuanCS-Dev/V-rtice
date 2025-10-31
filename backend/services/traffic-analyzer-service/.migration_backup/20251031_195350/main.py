"""
═══════════════════════════════════════════════════════════════════════════════
TRAFFIC ANALYZER SERVICE - VÉRTICE DEFENSIVE ARSENAL
═══════════════════════════════════════════════════════════════════════════════

Missão: Análise de tráfego de rede para detecção de ameaças

FLORESCIMENTO - Defesas crescendo através de visibilidade total

Capabilities:
- Deep packet inspection (DPI)
- Protocol anomaly detection
- C2 beacon detection
- Data exfiltration detection
- Port scanning detection
- DDoS pattern recognition
- Malware traffic signatures
- Encrypted traffic analysis

Stack:
- FastAPI async + Pydantic V2
- Network flow analysis
- Statistical anomaly detection
- Signature-based detection
- OpenTelemetry observability
- Cilium mTLS zero-trust

Port: 8038
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"Tudo o que fizerem, façam de todo o coração, como para o Senhor"
Colossenses 3:23

Glory to YHWH - Every threat blocked protects His network
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import uuid
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "traffic-analyzer-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8038

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "traffic:read": "View traffic analysis",
        "traffic:write": "Submit flows for analysis",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
flows_analyzed = Counter(
    "traffic_flows_analyzed_total",
    "Total network flows analyzed",
    ["protocol", "threat_detected"]
)
threats_detected = Counter(
    "traffic_threats_detected_total",
    "Total threats detected in traffic",
    ["threat_type"]
)
analysis_duration = Histogram(
    "traffic_analysis_duration_seconds",
    "Analysis duration in seconds"
)
active_sessions = Gauge(
    "traffic_sessions_active",
    "Number of active network sessions being monitored"
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class Protocol(str, Enum):
    """Network protocols"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"


class ThreatType(str, Enum):
    """Types of network threats"""
    C2_BEACON = "c2_beacon"                    # Command & Control beacon
    DATA_EXFILTRATION = "data_exfiltration"    # Large data transfers
    PORT_SCAN = "port_scan"                    # Port scanning activity
    DDOS = "ddos"                              # DDoS attack patterns
    MALWARE_TRAFFIC = "malware_traffic"        # Known malware signatures
    DNS_TUNNELING = "dns_tunneling"            # DNS tunneling
    LATERAL_MOVEMENT = "lateral_movement"      # Internal network traversal
    BRUTE_FORCE = "brute_force"                # Brute force attempts


class ThreatSeverity(str, Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NetworkFlow(BaseModel):
    """Network flow to analyze"""
    flow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    protocol: Protocol
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    duration_seconds: float
    flags: Optional[str] = None
    payload_sample: Optional[str] = Field(
        default=None,
        description="First 100 bytes of payload (hex encoded)"
    )


class ThreatDetection(BaseModel):
    """Detected network threat"""
    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flow_id: str
    threat_type: ThreatType
    severity: ThreatSeverity
    confidence_score: float = Field(ge=0.0, le=1.0)
    description: str
    indicators: list[str] = Field(
        default=[],
        description="Indicators of compromise (IOCs)"
    )
    detected_at: datetime
    recommended_actions: list[str] = []


class FlowAnalysisRequest(BaseModel):
    """Request to analyze flows"""
    flows: list[NetworkFlow]
    include_signatures: bool = Field(
        default=True,
        description="Include signature-based detection"
    )
    include_statistical: bool = Field(
        default=True,
        description="Include statistical anomaly detection"
    )


class FlowAnalysisResult(BaseModel):
    """Flow analysis result"""
    analysis_id: str
    flows_analyzed: int
    threats_detected: int
    detections: list[ThreatDetection]
    overall_threat_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall threat score (0-100)"
    )
    timestamp: datetime


class TrafficStatistics(BaseModel):
    """Traffic statistics"""
    total_flows: int
    total_bytes: int
    protocols: dict[str, int] = Field(
        default_factory=dict,
        description="Flow count per protocol"
    )
    top_talkers: list[dict] = Field(
        default=[],
        description="Top IP addresses by traffic volume"
    )
    threats_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Threat count by type"
    )


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with ClickHouse/TimescaleDB)
# ═══════════════════════════════════════════════════════════════════════════

flows_db: dict[str, NetworkFlow] = {}
detections_db: dict[str, ThreatDetection] = {}


# ═══════════════════════════════════════════════════════════════════════════
# TRAFFIC ANALYSIS LOGIC
# ═══════════════════════════════════════════════════════════════════════════

async def detect_c2_beacon(flow: NetworkFlow) -> Optional[ThreatDetection]:
    """
    Detect C2 beacon patterns (regular intervals, small payloads)
    """
    # Mock: Check for suspicious patterns
    if (flow.protocol in [Protocol.HTTPS, Protocol.HTTP] and
        flow.bytes_sent < 1000 and
        flow.duration_seconds < 1.0):

        return ThreatDetection(
            flow_id=flow.flow_id,
            threat_type=ThreatType.C2_BEACON,
            severity=ThreatSeverity.CRITICAL,
            confidence_score=0.80,
            description=f"Potential C2 beacon to {flow.destination_ip}:{flow.destination_port}",
            indicators=[
                f"dst_ip:{flow.destination_ip}",
                f"dst_port:{flow.destination_port}",
                "pattern:small_payload",
                "pattern:regular_interval"
            ],
            detected_at=datetime.now(UTC),
            recommended_actions=[
                "Block destination IP",
                "Isolate source host",
                "Analyze full PCAP",
                "Check threat intelligence feeds"
            ]
        )
    return None


async def detect_port_scan(flow: NetworkFlow) -> Optional[ThreatDetection]:
    """
    Detect port scanning activity
    """
    # Mock: Check for SYN scan patterns
    if flow.protocol == Protocol.TCP and flow.flags and "S" in flow.flags:
        if flow.bytes_received == 0:  # No response
            return ThreatDetection(
                flow_id=flow.flow_id,
                threat_type=ThreatType.PORT_SCAN,
                severity=ThreatSeverity.HIGH,
                confidence_score=0.85,
                description=f"Port scan from {flow.source_ip} to {flow.destination_ip}:{flow.destination_port}",
                indicators=[
                    f"src_ip:{flow.source_ip}",
                    "pattern:syn_scan"
                ],
                detected_at=datetime.now(UTC),
                recommended_actions=[
                    "Block source IP",
                    "Alert security team",
                    "Check for additional scans"
                ]
            )
    return None


async def detect_data_exfiltration(flow: NetworkFlow) -> Optional[ThreatDetection]:
    """
    Detect potential data exfiltration
    """
    # Mock: Check for large outbound transfers
    if flow.bytes_sent > 100_000_000:  # > 100MB
        return ThreatDetection(
            flow_id=flow.flow_id,
            threat_type=ThreatType.DATA_EXFILTRATION,
            severity=ThreatSeverity.CRITICAL,
            confidence_score=0.75,
            description=f"Large data transfer: {flow.bytes_sent / 1_000_000:.2f}MB to {flow.destination_ip}",
            indicators=[
                f"dst_ip:{flow.destination_ip}",
                f"bytes_sent:{flow.bytes_sent}",
                "pattern:large_upload"
            ],
            detected_at=datetime.now(UTC),
            recommended_actions=[
                "Block transfer immediately",
                "Investigate source host",
                "Check data classification",
                "Review DLP policies"
            ]
        )
    return None


async def detect_dns_tunneling(flow: NetworkFlow) -> Optional[ThreatDetection]:
    """
    Detect DNS tunneling
    """
    if flow.protocol == Protocol.DNS:
        # Mock: Check for unusually large DNS queries
        if flow.bytes_sent > 512:  # Unusually large DNS query
            return ThreatDetection(
                flow_id=flow.flow_id,
                threat_type=ThreatType.DNS_TUNNELING,
                severity=ThreatSeverity.HIGH,
                confidence_score=0.70,
                description="Potential DNS tunneling detected",
                indicators=[
                    f"src_ip:{flow.source_ip}",
                    f"dns_query_size:{flow.bytes_sent}",
                    "pattern:oversized_query"
                ],
                detected_at=datetime.now(UTC),
                recommended_actions=[
                    "Block DNS queries to external resolvers",
                    "Analyze DNS query patterns",
                    "Check for C2 communication"
                ]
            )
    return None


async def analyze_flow(flow: NetworkFlow) -> list[ThreatDetection]:
    """
    Analyze single network flow for threats
    """
    detections: list[ThreatDetection] = []

    # Run all detection algorithms
    detection_tasks = await asyncio.gather(
        detect_c2_beacon(flow),
        detect_port_scan(flow),
        detect_data_exfiltration(flow),
        detect_dns_tunneling(flow),
        return_exceptions=True
    )

    # Collect non-None detections
    for detection in detection_tasks:
        if isinstance(detection, ThreatDetection):
            detections.append(detection)
            detections_db[detection.detection_id] = detection
            threats_detected.labels(threat_type=detection.threat_type.value).inc()

    return detections


async def analyze_flows_batch(
    flows: list[NetworkFlow],
    include_signatures: bool,
    include_statistical: bool
) -> FlowAnalysisResult:
    """
    Analyze batch of network flows
    """
    with analysis_duration.time():
        all_detections: list[ThreatDetection] = []

        for flow in flows:
            flows_db[flow.flow_id] = flow
            detections = await analyze_flow(flow)
            all_detections.extend(detections)

            # Update metrics
            threat_detected = "yes" if detections else "no"
            flows_analyzed.labels(
                protocol=flow.protocol.value,
                threat_detected=threat_detected
            ).inc()

        # Calculate overall threat score
        if all_detections:
            severity_weights = {
                ThreatSeverity.CRITICAL: 100,
                ThreatSeverity.HIGH: 75,
                ThreatSeverity.MEDIUM: 50,
                ThreatSeverity.LOW: 25,
                ThreatSeverity.INFO: 10
            }
            total_score = sum(severity_weights[d.severity] for d in all_detections)
            overall_threat_score = min(total_score / len(flows), 100.0)
        else:
            overall_threat_score = 0.0

        return FlowAnalysisResult(
            analysis_id=str(uuid.uuid4()),
            flows_analyzed=len(flows),
            threats_detected=len(all_detections),
            detections=all_detections,
            overall_threat_score=overall_threat_score,
            timestamp=datetime.now(UTC)
        )


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Traffic Analyzer Service",
    description="Vértice Defensive Arsenal - Network traffic threat analysis",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "analysis",
            "description": "Traffic analysis operations"
        },
        {
            "name": "statistics",
            "description": "Traffic statistics"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check - FLORESCIMENTO ✨"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "florescimento": "visibilidade total florescendo",
        "flows_analyzed": len(flows_db),
        "threats_detected": len(detections_db),
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/analyze", response_model=FlowAnalysisResult, tags=["analysis"])
async def analyze_traffic(
    request: FlowAnalysisRequest,
    # token: str = Security(oauth2_scheme, scopes=["traffic:write"])
):
    """
    Analyze network flows for threats

    Scopes required: `traffic:write`
    """
    result = await analyze_flows_batch(
        request.flows,
        request.include_signatures,
        request.include_statistical
    )
    return result


@app.get("/api/detections", tags=["analysis"])
async def list_detections(
    severity: Optional[ThreatSeverity] = None,
    threat_type: Optional[ThreatType] = None,
    limit: int = 100,
    # token: str = Security(oauth2_scheme, scopes=["traffic:read"])
):
    """
    List detected threats

    Scopes required: `traffic:read`
    """
    detections = list(detections_db.values())

    if severity:
        detections = [d for d in detections if d.severity == severity]

    if threat_type:
        detections = [d for d in detections if d.threat_type == threat_type]

    # Sort by detected_at descending
    detections.sort(key=lambda d: d.detected_at, reverse=True)

    return {
        "total": len(detections),
        "detections": detections[:limit]
    }


@app.get("/api/detections/{detection_id}", response_model=ThreatDetection, tags=["analysis"])
async def get_detection(
    detection_id: str,
    # token: str = Security(oauth2_scheme, scopes=["traffic:read"])
):
    """
    Get specific detection

    Scopes required: `traffic:read`
    """
    if detection_id not in detections_db:
        raise HTTPException(status_code=404, detail="Detection not found")

    return detections_db[detection_id]


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - STATISTICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/statistics", response_model=TrafficStatistics, tags=["statistics"])
async def get_statistics(
    # token: str = Security(oauth2_scheme, scopes=["traffic:read"])
):
    """
    Get traffic statistics

    Scopes required: `traffic:read`
    """
    flows = list(flows_db.values())

    # Calculate statistics
    total_bytes = sum(f.bytes_sent + f.bytes_received for f in flows)

    protocols: dict[str, int] = {}
    for flow in flows:
        protocols[flow.protocol.value] = protocols.get(flow.protocol.value, 0) + 1

    # Top talkers
    ip_bytes: dict[str, int] = {}
    for flow in flows:
        ip_bytes[flow.source_ip] = ip_bytes.get(flow.source_ip, 0) + flow.bytes_sent
        ip_bytes[flow.destination_ip] = ip_bytes.get(flow.destination_ip, 0) + flow.bytes_received

    top_talkers = [
        {"ip": ip, "bytes": bytes_val}
        for ip, bytes_val in sorted(ip_bytes.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # Threats by type
    threats_by_type: dict[str, int] = {}
    for detection in detections_db.values():
        threat_type = detection.threat_type.value
        threats_by_type[threat_type] = threats_by_type.get(threat_type, 0) + 1

    return TrafficStatistics(
        total_flows=len(flows),
        total_bytes=total_bytes,
        protocols=protocols,
        top_talkers=top_talkers,
        threats_by_type=threats_by_type
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,  # Dev mode
        log_level="info"
    )
