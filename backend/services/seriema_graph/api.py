"""Maximus Seriema Graph Service - Main Entry Point.

This service provides a REST API for managing knowledge graphs using Neo4j.
Inspired by the Seriema bird's ability to navigate complex terrains, this
service handles dynamic knowledge graph operations for the Maximus AI platform.

The service exposes endpoints for:
- Storing and retrieving argumentation frameworks
- Graph analysis (centrality, paths, neighborhoods)
- Pattern detection (circular arguments)
- Framework statistics and health monitoring
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import local SeriemaGraphClient
try:
    from seriema_graph_client import SeriemaGraphClient
    CLIENT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SeriemaGraphClient not available - running in limited mode: {e}")
    CLIENT_AVAILABLE = False
    SeriemaGraphClient = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global client instance
graph_client: Optional[SeriemaGraphClient] = None


class ArgumentNode(BaseModel):
    """Argument node model for API requests."""
    id: str = Field(..., description="Unique argument identifier")
    text: str = Field(..., description="Argument text content")
    role: str = Field(default="claim", description="Argument role (claim/premise/etc)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AttackRelation(BaseModel):
    """Attack relation model for API requests."""
    attacker_id: str = Field(..., description="ID of attacking argument")
    target_id: str = Field(..., description="ID of target argument")
    attack_type: str = Field(default="defeats", description="Type of attack")
    strength: float = Field(default=1.0, ge=0.0, le=1.0, description="Attack strength")


class FrameworkRequest(BaseModel):
    """Request model for storing argumentation framework."""
    framework_id: str = Field(..., description="Unique framework identifier")
    arguments: List[ArgumentNode] = Field(..., description="List of arguments")
    attacks: List[AttackRelation] = Field(default_factory=list, description="Attack relations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Framework metadata")


class PathQueryRequest(BaseModel):
    """Request model for path finding queries."""
    start_id: str = Field(..., description="Start argument ID")
    end_id: str = Field(..., description="End argument ID")
    max_depth: int = Field(default=5, ge=1, le=20, description="Maximum path depth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global graph_client

    logger.info("🕸️ Starting Maximus Seriema Graph Service...")

    if CLIENT_AVAILABLE and SeriemaGraphClient:
        try:
            # Initialize Neo4j client
            graph_client = SeriemaGraphClient(
                uri="bolt://neo4j:7687",
                user="neo4j",
                password="neo4j123",
                database="neo4j"
            )
            await graph_client.initialize()
            logger.info("✅ Seriema Graph Service started successfully")
        except Exception as e:
            logger.error(f"⚠️ Failed to initialize graph client: {e}")
            logger.warning("Running in limited mode without Neo4j connection")
            graph_client = None
    else:
        logger.warning("Running in limited mode - SeriemaGraphClient not available")

    yield

    # Shutdown
    logger.info("👋 Shutting down Seriema Graph Service...")
    if graph_client:
        try:
            await graph_client.close()
        except Exception as e:
            logger.error(f"Error closing graph client: {e}")
    logger.info("🛑 Seriema Graph Service shut down")


app = FastAPI(
    title="Maximus Seriema Graph Service",
    description="Knowledge Graph Management for Maximus AI Platform",
    version="1.0.0",
    lifespan=lifespan
)


def get_client() -> SeriemaGraphClient:
    """Dependency to get graph client instance."""
    if not graph_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph service not initialized or running in limited mode"
        )
    return graph_client


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns service health status and Neo4j connectivity.
    """
    health_status = {
        "status": "healthy",
        "service": "seriema_graph",
        "timestamp": datetime.utcnow().isoformat(),
        "client_available": CLIENT_AVAILABLE,
        "neo4j_connected": False
    }

    if graph_client:
        try:
            neo4j_health = await graph_client.health_check()
            health_status["neo4j_connected"] = neo4j_health.get("connected", False)
            health_status["neo4j_details"] = neo4j_health
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            health_status["neo4j_error"] = str(e)

    return health_status


@app.post("/framework/store")
async def store_framework(
    request: FrameworkRequest,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Store an argumentation framework in the graph database.

    Creates nodes for arguments and edges for attack relations.
    """
    try:
        # Convert API models to internal format
        # This is a simplified conversion - in production, would need proper mapping
        framework_data = {
            "id": request.framework_id,
            "arguments": [arg.dict() for arg in request.arguments],
            "attacks": [att.dict() for att in request.attacks],
            "metadata": request.metadata
        }

        # Note: The actual store_framework method expects ArgumentationFramework object
        # This is a simplified version - proper implementation would convert the data
        await client.store_framework(
            framework_id=request.framework_id,
            framework=framework_data  # In production, convert to proper type
        )

        return {
            "status": "success",
            "framework_id": request.framework_id,
            "arguments_stored": len(request.arguments),
            "attacks_stored": len(request.attacks),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error storing framework: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store framework: {str(e)}"
        )


@app.get("/framework/{framework_id}")
async def retrieve_framework(
    framework_id: str,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Retrieve an argumentation framework from the graph database.

    Returns all arguments and attack relations for the framework.
    """
    try:
        framework = await client.retrieve_framework(framework_id)

        if not framework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework {framework_id} not found"
            )

        return {
            "status": "success",
            "framework_id": framework_id,
            "framework": framework,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving framework: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve framework: {str(e)}"
        )


@app.get("/framework/{framework_id}/centrality")
async def get_argument_centrality(
    framework_id: str,
    algorithm: str = "betweenness",
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Calculate centrality measures for arguments in a framework.

    Supported algorithms: betweenness, closeness, pagerank
    """
    try:
        centrality = await client.get_argument_centrality(framework_id, algorithm)

        return {
            "status": "success",
            "framework_id": framework_id,
            "algorithm": algorithm,
            "centrality": centrality,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating centrality: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate centrality: {str(e)}"
        )


@app.post("/framework/{framework_id}/paths")
async def find_argument_paths(
    framework_id: str,
    query: PathQueryRequest,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Find all paths between two arguments in a framework.

    Useful for tracing argument chains and attack sequences.
    """
    try:
        paths = await client.find_argument_paths(
            framework_id=framework_id,
            start_id=query.start_id,
            end_id=query.end_id,
            max_depth=query.max_depth
        )

        return {
            "status": "success",
            "framework_id": framework_id,
            "start_id": query.start_id,
            "end_id": query.end_id,
            "paths": paths,
            "path_count": len(paths) if paths else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error finding paths: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find paths: {str(e)}"
        )


@app.get("/framework/{framework_id}/neighborhood/{argument_id}")
async def get_argument_neighborhood(
    framework_id: str,
    argument_id: str,
    depth: int = 2,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Get the neighborhood subgraph around an argument.

    Returns all arguments within specified depth.
    """
    try:
        neighborhood = await client.get_argument_neighborhoods(
            framework_id=framework_id,
            argument_ids=[argument_id],
            depth=depth
        )

        return {
            "status": "success",
            "framework_id": framework_id,
            "argument_id": argument_id,
            "depth": depth,
            "neighborhood": neighborhood,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting neighborhood: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get neighborhood: {str(e)}"
        )


@app.get("/framework/{framework_id}/circular-arguments")
async def detect_circular_arguments(
    framework_id: str,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Detect circular argument patterns (logical fallacies).

    Identifies cycles in the argument attack graph.
    """
    try:
        cycles = await client.detect_circular_arguments(framework_id)

        return {
            "status": "success",
            "framework_id": framework_id,
            "circular_arguments": cycles,
            "cycle_count": len(cycles) if cycles else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error detecting circular arguments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect circular arguments: {str(e)}"
        )


@app.get("/framework/{framework_id}/statistics")
async def get_framework_statistics(
    framework_id: str,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a framework.

    Returns node count, edge count, density, avg degree, etc.
    """
    try:
        stats = await client.get_framework_statistics(framework_id)

        return {
            "status": "success",
            "framework_id": framework_id,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.delete("/framework/{framework_id}")
async def delete_framework(
    framework_id: str,
    client: SeriemaGraphClient = Depends(get_client)
) -> Dict[str, Any]:
    """
    Delete an argumentation framework from the database.

    Removes all associated nodes and relationships.
    """
    try:
        await client.delete_framework(framework_id)

        return {
            "status": "success",
            "framework_id": framework_id,
            "message": "Framework deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting framework: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete framework: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8029,
        reload=True,
        log_level="info"
    )
