"""Maximus Domain Service - Main Application Entry Point.

This module serves as the main entry point for the Maximus Domain Service.
It initializes and configures the FastAPI application, sets up event handlers
for startup and shutdown, and defines the API endpoints for managing and
querying domain-specific information.

It handles the loading of domain ontologies, rules, and knowledge graphs,
and provides interfaces for other Maximus AI services to retrieve contextual
information and validate actions against domain constraints. This service is
crucial for enabling Maximus to operate effectively and intelligently across
diverse operational contexts.
"""

import asyncio
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from knowledge_base import KnowledgeBase, init_db

# Constitutional v3.0 imports
from shared.metrics_exporter import MetricsExporter, auto_update_sabbath_status
from shared.constitutional_tracing import create_constitutional_tracer
from shared.constitutional_logging import configure_constitutional_logging
from shared.health_checks import ConstitutionalHealthCheck


app = FastAPI(title="Maximus Domain Service", version="1.0.0")

# Global knowledge base instance
knowledge_base: Optional[KnowledgeBase] = None


class DomainQueryRequest(BaseModel):
    """Request model for querying domain-specific information.

    Attributes:
        domain_name (str): The name of the domain to query.
        query (str): A natural language query about the domain.
        context (Optional[Dict[str, Any]]): Additional context for the query.
    """

    domain_name: str
    query: str
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks for the Domain Service."""

    # Constitutional v3.0 Initialization
    global metrics_exporter, constitutional_tracer, health_checker
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    try:
        # Logging
        configure_constitutional_logging(
            service_name="domain_service",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            json_logs=True
        )

        # Metrics
        metrics_exporter = MetricsExporter(
            service_name="domain_service",
            version=service_version
        )
        auto_update_sabbath_status("domain_service")
        logger.info("✅ Constitutional Metrics initialized")

        # Tracing
        constitutional_tracer = create_constitutional_tracer(
            service_name="domain_service",
            version=service_version
        )
        constitutional_tracer.instrument_fastapi(app)
        logger.info("✅ Constitutional Tracing initialized")

        # Health
        health_checker = ConstitutionalHealthCheck(service_name="domain_service")
        logger.info("✅ Constitutional Health Checker initialized")

        # Routes
        if metrics_exporter:
            app.include_router(metrics_exporter.create_router())
            logger.info("✅ Constitutional metrics routes added")

    except Exception as e:
        logger.error(f"❌ Constitutional initialization failed: {e}", exc_info=True)

    # Mark startup complete
    if health_checker:
        health_checker.mark_startup_complete()

    global knowledge_base
    print("🧠 Starting Maximus Domain Service...")
    init_db()
    knowledge_base = KnowledgeBase()
    print("✅ Knowledge base initialized")
    print("✅ Maximus Domain Service started successfully.")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks for the Domain Service."""
    global knowledge_base
    print("👋 Shutting down Maximus Domain Service...")
    if knowledge_base:
        knowledge_base.close()
    print("🛑 Maximus Domain Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Performs a health check of the Domain Service.

    Returns:
        Dict[str, str]: A dictionary indicating the service status.
    """
    return {"status": "healthy", "message": "Domain Service is operational."}


@app.get("/domains")
async def list_domains() -> List[str]:
    """Lists all available domains.

    Returns:
        List[str]: A list of domain names.
    """
    return knowledge_base.list_domains()


@app.get("/domain/{domain_name}")
async def get_domain_info(domain_name: str) -> Dict[str, Any]:
    """Retrieves information about a specific domain.

    Args:
        domain_name (str): The name of the domain.

    Returns:
        Dict[str, Any]: A dictionary containing information about the domain.

    Raises:
        HTTPException: If the domain is not found.
    """
    result = knowledge_base.query_domain(domain_name, "")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/query_domain")
async def query_domain_endpoint(request: DomainQueryRequest) -> Dict[str, Any]:
    """Queries a specific domain for information based on a natural language query.

    Args:
        request (DomainQueryRequest): The request body containing the domain name and query.

    Returns:
        Dict[str, Any]: A dictionary containing the query results.

    Raises:
        HTTPException: If the domain is not found.
    """
    print(f"[API] Querying domain '{request.domain_name}' with: {request.query}")
    
    result = knowledge_base.query_domain(request.domain_name, request.query, request.context)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013)
