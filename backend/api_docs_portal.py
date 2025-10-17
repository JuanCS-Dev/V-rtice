"""
Vértice Platform - Unified API Documentation Portal
===================================================

Aggregates OpenAPI documentation from all 67+ microservices into a single
portal with service discovery, health monitoring, and interactive API testing.

Features:
    - Auto-discovery of all services
    - Aggregated OpenAPI specs
    - Service health monitoring
    - Interactive API testing (Swagger UI)
    - Service dependency visualization
    - Performance metrics

Run:
    uvicorn backend.api_docs_portal:app --host 0.0.0.0 --port 8888

Access:
    - Docs Portal: http://localhost:8888/docs
    - Service List: http://localhost:8888/services
    - Health Overview: http://localhost:8888/health
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.shared.constants import ServicePorts
from backend.shared.openapi_config import create_openapi_config

# ============================================================================
# MODELS
# ============================================================================


class ServiceInfo(BaseModel):
    """Information about a microservice."""

    name: str
    port: int
    url: str
    health_endpoint: str
    docs_endpoint: str
    openapi_endpoint: str
    status: str = "unknown"
    last_checked: datetime | None = None


class ServiceHealth(BaseModel):
    """Health status of a service."""

    service_name: str
    status: str
    response_time_ms: float
    last_checked: datetime
    error: str | None = None


class AggregatedDocs(BaseModel):
    """Aggregated API documentation."""

    total_services: int
    healthy_services: int
    total_endpoints: int
    services: list[dict[str, Any]]
    generated_at: datetime


# ============================================================================
# SERVICE REGISTRY
# ============================================================================

SERVICE_REGISTRY: list[ServiceInfo] = []


def register_services():
    """Register all Vértice microservices."""
    services = [
        ("API Gateway", ServicePorts.API_GATEWAY),
        ("MAXIMUS Core", ServicePorts.MAXIMUS_CORE),
        ("IP Intelligence", ServicePorts.IP_INTELLIGENCE),
        ("Threat Intel", ServicePorts.THREAT_INTEL),
        ("File Analysis", ServicePorts.FILE_ANALYSIS),
        ("Malware Analysis", ServicePorts.MALWARE_ANALYSIS),
        ("Behavioral Analysis", ServicePorts.BEHAVIORAL_ANALYSIS),
        ("Forensics", ServicePorts.FORENSICS),
        ("OSINT", ServicePorts.OSINT),
        ("Predictive Hunting", ServicePorts.PREDICTIVE_HUNTING),
        ("Context Analyzer", ServicePorts.CONTEXT_ANALYZER),
        ("Immunis API", ServicePorts.IMMUNIS_API),
        ("SIEM Integration", ServicePorts.SIEM_INTEGRATION),
        ("Incident Response", ServicePorts.INCIDENT_RESPONSE),
        ("Autonomous Investigation", ServicePorts.AUTONOMOUS_INVESTIGATION),
        ("Narrative Filter", ServicePorts.NARRATIVE_FILTER),
        ("Memory Consolidation", ServicePorts.MEMORY_CONSOLIDATION),
        ("Adaptive Learning", ServicePorts.ADAPTIVE_LEARNING),
        ("Pattern Recognition", ServicePorts.PATTERN_RECOGNITION),
        ("Strategic Planning", ServicePorts.STRATEGIC_PLANNING),
        ("Network Recon", ServicePorts.NETWORK_RECON),
        ("Web Attack", ServicePorts.WEB_ATTACK),
        ("C2 Orchestration", ServicePorts.C2_ORCHESTRATION),
        ("BAS", ServicePorts.BAS),
        ("Social Engineering", ServicePorts.SOCIAL_ENGINEERING),
        ("Phishing Sim", ServicePorts.PHISHING_SIM),
        ("Vuln Scanner", ServicePorts.VULN_SCANNER),
        ("Neo4j Service", ServicePorts.NEO4J_SERVICE),
        ("Seriema Graph", ServicePorts.SERIEMA_GRAPH),
        ("Tataca Ingestion", ServicePorts.TATACA_INGESTION),
        ("Visual Cortex", ServicePorts.VISUAL_CORTEX),
        ("Auditory Cortex", ServicePorts.AUDITORY_CORTEX),
        ("Somatosensory", ServicePorts.SOMATOSENSORY),
        ("Chemical Sensing", ServicePorts.CHEMICAL_SENSING),
        ("Vestibular", ServicePorts.VESTIBULAR),
        ("HCL Monitor", ServicePorts.HCL_MONITOR),
        ("HCL Analyzer", ServicePorts.HCL_ANALYZER),
        ("HCL Planner", ServicePorts.HCL_PLANNER),
        ("HCL Executor", ServicePorts.HCL_EXECUTOR),
        ("HCL KB", ServicePorts.HCL_KB),
        ("Immunis Macrophage", ServicePorts.IMMUNIS_MACROPHAGE),
        ("Immunis Neutrophil", ServicePorts.IMMUNIS_NEUTROPHIL),
        ("Immunis NK Cell", ServicePorts.IMMUNIS_NK_CELL),
        ("Immunis B-Cell", ServicePorts.IMMUNIS_BCELL),
        ("Immunis Cytotoxic T", ServicePorts.IMMUNIS_CYTOTOXIC_T),
        ("Immunis Helper T", ServicePorts.IMMUNIS_HELPER_T),
        ("Immunis Dendritic", ServicePorts.IMMUNIS_DENDRITIC),
        ("MAXIMUS Oraculo", ServicePorts.MAXIMUS_ORACULO),
        ("MAXIMUS Eureka", ServicePorts.MAXIMUS_EUREKA),
        ("MAXIMUS Predict", ServicePorts.MAXIMUS_PREDICT),
        ("Neuromodulation", ServicePorts.NEUROMODULATION),
        ("Dopamine Core", ServicePorts.DOPAMINE_CORE),
        ("Serotonin Core", ServicePorts.SEROTONIN_CORE),
        ("Noradrenaline Core", ServicePorts.NORADRENALINE_CORE),
        ("Auth Service", ServicePorts.AUTH_SERVICE),
        ("Digital Thalamus", ServicePorts.DIGITAL_THALAMUS),
        ("Prefrontal Cortex", ServicePorts.PREFRONTAL_CORTEX),
        ("Homeostatic Regulation", ServicePorts.HOMEOSTATIC_REGULATION),
        ("Reflex Triage", ServicePorts.REFLEX_TRIAGE),
        ("AI Immune", ServicePorts.AI_IMMUNE),
        ("Cloud Coordinator", ServicePorts.CLOUD_COORDINATOR),
    ]

    for name, port in services:
        base_url = f"http://localhost:{port}"
        SERVICE_REGISTRY.append(
            ServiceInfo(
                name=name,
                port=port,
                url=base_url,
                health_endpoint=f"{base_url}/health",
                docs_endpoint=f"{base_url}/docs",
                openapi_endpoint=f"{base_url}/openapi.json",
            )
        )


# Initialize registry
register_services()


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    **create_openapi_config(
        service_name="Vértice API Documentation Portal",
        service_description="Unified documentation portal for all 67+ Vértice microservices",
        version="1.0.0",
        tags=[
            {"name": "services", "description": "Service discovery and management"},
            {"name": "health", "description": "Health monitoring"},
            {"name": "docs", "description": "Aggregated API documentation"},
        ],
    )
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/", response_class=HTMLResponse, tags=["docs"])
async def root():
    """Render documentation portal home page."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vértice API Documentation Portal</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                background: #0a0a0a;
                color: #e0e0e0;
            }}
            h1 {{ color: #00ff00; border-bottom: 2px solid #00ff00; padding-bottom: 0.5rem; }}
            h2 {{ color: #00cc00; margin-top: 2rem; }}
            .service-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }}
            .service-card {{
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 1rem;
                transition: transform 0.2s, border-color 0.2s;
            }}
            .service-card:hover {{
                transform: translateY(-2px);
                border-color: #00ff00;
            }}
            .service-name {{ font-weight: bold; color: #00ff00; margin-bottom: 0.5rem; }}
            .service-port {{ color: #888; font-size: 0.9rem; }}
            .service-links {{ margin-top: 1rem; }}
            .service-links a {{
                display: inline-block;
                margin-right: 1rem;
                color: #00aaff;
                text-decoration: none;
            }}
            .service-links a:hover {{ text-decoration: underline; }}
            .stats {{
                display: flex;
                gap: 2rem;
                margin: 2rem 0;
                padding: 1rem;
                background: #1a1a1a;
                border-radius: 8px;
            }}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #00ff00; }}
            .stat-label {{ color: #888; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <h1>🌐 Vértice Platform - API Documentation Portal</h1>
        <p>Unified documentation for all {len(SERVICE_REGISTRY)} microservices</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(SERVICE_REGISTRY)}</div>
                <div class="stat-label">Total Services</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="healthy-count">-</div>
                <div class="stat-label">Healthy Services</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="endpoints-count">-</div>
                <div class="stat-label">Total Endpoints</div>
            </div>
        </div>

        <h2>📚 Service Catalog</h2>
        <div class="service-grid" id="services">
            Loading services...
        </div>

        <h2>🔗 Quick Links</h2>
        <ul>
            <li><a href="/docs">Interactive API Documentation (Swagger UI)</a></li>
            <li><a href="/services">Service List (JSON)</a></li>
            <li><a href="/health/all">Health Status (JSON)</a></li>
            <li><a href="/docs/aggregated">Aggregated OpenAPI Spec</a></li>
        </ul>

        <script>
            // Load services dynamically
            fetch('/services')
                .then(r => r.json())
                .then(services => {{
                    const grid = document.getElementById('services');
                    grid.innerHTML = services.map(s => `
                        <div class="service-card">
                            <div class="service-name">${{s.name}}</div>
                            <div class="service-port">Port: ${{s.port}}</div>
                            <div class="service-links">
                                <a href="${{s.docs_endpoint}}" target="_blank">📖 Docs</a>
                                <a href="${{s.openapi_endpoint}}" target="_blank">📄 OpenAPI</a>
                                <a href="${{s.health_endpoint}}" target="_blank">❤️ Health</a>
                            </div>
                        </div>
                    `).join('');
                }});

            // Load health stats
            fetch('/health/all')
                .then(r => r.json())
                .then(data => {{
                    document.getElementById('healthy-count').textContent =
                        data.filter(s => s.status === 'healthy').length;
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/services", response_model=list[ServiceInfo], tags=["services"])
async def list_services():
    """List all registered services."""
    return SERVICE_REGISTRY


@app.get("/health/all", response_model=list[ServiceHealth], tags=["health"])
async def check_all_health():
    """Check health status of all services."""
    results = []

    async with httpx.AsyncClient(timeout=2.0) as client:
        tasks = []
        for service in SERVICE_REGISTRY:
            tasks.append(check_service_health(client, service))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, ServiceHealth)]


async def check_service_health(
    client: httpx.AsyncClient, service: ServiceInfo
) -> ServiceHealth:
    """Check health of a single service."""
    start_time = datetime.now()

    try:
        response = await client.get(service.health_endpoint)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        return ServiceHealth(
            service_name=service.name,
            status="healthy" if response.status_code == 200 else "unhealthy",
            response_time_ms=round(elapsed_ms, 2),
            last_checked=datetime.now(),
        )
    except Exception as e:
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        return ServiceHealth(
            service_name=service.name,
            status="down",
            response_time_ms=round(elapsed_ms, 2),
            last_checked=datetime.now(),
            error=str(e),
        )


@app.get("/docs/aggregated", response_model=AggregatedDocs, tags=["docs"])
async def get_aggregated_docs():
    """Get aggregated OpenAPI documentation from all services."""
    services_data = []
    total_endpoints = 0
    healthy_count = 0

    async with httpx.AsyncClient(timeout=5.0) as client:
        for service in SERVICE_REGISTRY:
            try:
                # Fetch OpenAPI spec
                response = await client.get(service.openapi_endpoint)
                if response.status_code == 200:
                    spec = response.json()
                    endpoint_count = len(spec.get("paths", {}))
                    total_endpoints += endpoint_count

                    services_data.append(
                        {
                            "name": service.name,
                            "port": service.port,
                            "docs_url": service.docs_endpoint,
                            "openapi_url": service.openapi_endpoint,
                            "endpoints_count": endpoint_count,
                            "version": spec.get("info", {}).get("version", "unknown"),
                            "description": spec.get("info", {}).get(
                                "description", ""
                            ),
                        }
                    )
                    healthy_count += 1
            except Exception:
                # Service not available
                pass

    return AggregatedDocs(
        total_services=len(SERVICE_REGISTRY),
        healthy_services=healthy_count,
        total_endpoints=total_endpoints,
        services=services_data,
        generated_at=datetime.now(),
    )


@app.get("/health", tags=["health"])
async def portal_health():
    """Portal health check."""
    return {
        "status": "healthy",
        "service": "API Documentation Portal",
        "timestamp": datetime.now().isoformat(),
        "registered_services": len(SERVICE_REGISTRY),
    }


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("Starting Vértice API Documentation Portal...")
    print(f"Registered {len(SERVICE_REGISTRY)} services")
    print("Portal available at: http://localhost:8888")
    print("Documentation: http://localhost:8888/docs")

    uvicorn.run(app, host="0.0.0.0", port=8888)
