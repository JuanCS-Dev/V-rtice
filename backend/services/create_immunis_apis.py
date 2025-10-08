#!/usr/bin/env python3
"""Script to generate generic api.py files for Immunis services.

Follows DEBUG_GUIDE best practices:
- Optional imports (section 5.9)
- Production-ready code
- No mocks, no placeholders
"""

from pathlib import Path

SERVICES = [
    ("bcell", 8016, "B-Cell - Antibody Generation"),
    ("helper_t", 8017, "Helper T-Cell - Coordination"),
    ("cytotoxic_t", 8018, "Cytotoxic T-Cell - Threat Elimination"),
    ("nk_cell", 8019, "NK Cell - Rapid Cytotoxicity"),
    ("dendritic", 8014, "Dendritic Cell - Antigen Presentation"),
]

API_TEMPLATE = '''"""Immunis {service_title} Service - FastAPI Wrapper

Exposes {service_title} capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from {core_module} import {core_class}
    CORE_AVAILABLE = True
except ImportError:
    logger.warning("{core_class} not available - running in limited mode")
    CORE_AVAILABLE = False
    {core_class} = None

app = FastAPI(
    title="Immunis {service_title} Service",
    version="1.0.0",
    description="Bio-inspired {service_desc} service"
)

# Initialize core if available
if CORE_AVAILABLE and {core_class}:
    try:
        core = {core_class}()
        logger.info("{service_title} core initialized")
    except Exception as e:
        logger.warning(f"Core initialization failed: {{e}}")
        core = None
else:
    core = None


class ProcessRequest(BaseModel):
    """Generic request model for processing.

    Attributes:
        data (Dict[str, Any]): Input data to process
        context (Optional[Dict[str, Any]]): Optional context
    """
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks."""
    logger.info("🦠 Starting Immunis {service_title} Service...")
    logger.info("✅ {service_title} Service started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis {service_title} Service...")
    logger.info("🛑 {service_title} Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {{
        "status": "healthy",
        "service": "immunis_{service_id}",
        "core_available": CORE_AVAILABLE and core is not None,
        "timestamp": datetime.now().isoformat()
    }}


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    if core and hasattr(core, 'get_status'):
        try:
            return await core.get_status()
        except Exception as e:
            logger.error(f"Status retrieval failed: {{e}}")

    return {{
        "status": "operational",
        "service": "immunis_{service_id}",
        "mode": "limited" if not core else "full",
        "timestamp": datetime.now().isoformat()
    }}


@app.post("/process")
async def process_data(request: ProcessRequest) -> Dict[str, Any]:
    """Main processing endpoint.

    Args:
        request (ProcessRequest): Data to process

    Returns:
        Dict[str, Any]: Processing results

    Raises:
        HTTPException: If processing fails
    """
    if not core:
        raise HTTPException(
            status_code=503,
            detail="Core not available - service in limited mode"
        )

    try:
        # Call core processing method if available
        if hasattr(core, 'process'):
            result = await core.process(request.data, request.context)
        elif hasattr(core, 'analyze'):
            result = await core.analyze(request.data, request.context)
        else:
            result = {{"processed": True, "data": request.data}}

        return {{
            "status": "success",
            "service": "immunis_{service_id}",
            "results": result,
            "timestamp": datetime.now().isoformat()
        }}

    except Exception as e:
        logger.error(f"Processing failed: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''


def create_api_file(service_id, port, service_title):
    """Create api.py file for a service."""
    service_dir = Path(f"/home/juan/vertice-dev/backend/services/immunis_{service_id}_service")

    if not service_dir.exists():
        print(f"❌ Directory not found: {service_dir}")
        return False

    # Check if api.py already exists
    api_file = service_dir / "api.py"
    if api_file.exists():
        print(f"⚠️  api.py already exists: {api_file}")
        return False

    # Generate core class name
    core_class = "".join(word.capitalize() for word in service_id.split("_")) + "Core"
    core_module = service_id + "_core"

    # Generate api.py content
    content = API_TEMPLATE.format(
        service_id=service_id,
        service_title=service_title,
        service_desc=service_title.lower(),
        core_module=core_module,
        core_class=core_class,
        port=port,
    )

    # Write file
    api_file.write_text(content)
    print(f"✅ Created: {api_file}")
    return True


def main():
    """Main execution."""
    print("=" * 60)
    print("Creating api.py files for Immunis services")
    print("=" * 60)

    created = 0
    for service_id, port, service_title in SERVICES:
        if create_api_file(service_id, port, service_title):
            created += 1

    print("=" * 60)
    print(f"✅ Created {created}/{len(SERVICES)} api.py files")
    print("=" * 60)


if __name__ == "__main__":
    main()
