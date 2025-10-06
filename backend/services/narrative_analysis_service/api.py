"""FASE 8: Advanced Narrative Analysis Service - FastAPI

REST API for narrative intelligence: social graph analysis, bot detection,
propaganda attribution, and meme tracking.

NO MOCKS - Production-ready HTTP interface.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from narrative_core import (
    BotDetector,
    MemeTracker,
    NarrativeEntity,
    PropagandaAttributor,
    SocialGraphAnalyzer,
)
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global service instances
social_graph: Optional[SocialGraphAnalyzer] = None
bot_detector: Optional[BotDetector] = None
propaganda_attributor: Optional[PropagandaAttributor] = None
meme_tracker: Optional[MemeTracker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global social_graph, bot_detector, propaganda_attributor, meme_tracker

    logger.info("Initializing Narrative Analysis Service...")

    # Initialize all components
    social_graph = SocialGraphAnalyzer()
    bot_detector = BotDetector()
    propaganda_attributor = PropagandaAttributor()
    meme_tracker = MemeTracker()

    logger.info("All narrative analysis components initialized")

    yield

    logger.info("Shutting down Narrative Analysis Service...")


app = FastAPI(
    title="VÉRTICE Narrative Analysis Service",
    description="Advanced narrative intelligence for information warfare detection",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Request/Response Models
# ============================================================================


class SocialRelationRequest(BaseModel):
    """Request to add social relationship."""

    source_id: str = Field(..., description="Source account ID")
    target_id: str = Field(..., description="Target account ID")
    relation_type: str = Field(
        ..., description="Relationship type (follows, retweets, mentions)"
    )
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class InfluenceScoresResponse(BaseModel):
    """Response with influence scores."""

    scores: Dict[str, float] = Field(..., description="Account ID -> influence score")
    algorithm: str = Field("pagerank", description="Algorithm used")
    timestamp: str = Field(..., description="Analysis timestamp")


class CoordinationDetectionRequest(BaseModel):
    """Request for coordinated behavior detection."""

    min_cluster_size: int = Field(3, description="Minimum accounts in cluster")
    time_window_hours: int = Field(24, description="Time window for coordination")


class BotAnalysisRequest(BaseModel):
    """Request for bot detection analysis."""

    account_id: str = Field(..., description="Account ID to analyze")
    posts: List[Dict[str, Any]] = Field(..., description="Recent posts from account")
    account_metadata: Dict[str, Any] = Field(
        ..., description="Account metadata (created_at, followers, etc)"
    )


class BotScoreResponse(BaseModel):
    """Response with bot detection score."""

    entity_id: str
    bot_probability: float
    indicators: Dict[str, float]
    confidence: float
    timestamp: str


class PropagandaAnalysisRequest(BaseModel):
    """Request for propaganda attribution."""

    narrative_id: str = Field(..., description="Narrative/post ID")
    text: str = Field(..., description="Text content to analyze")


class PropagandaAttributionResponse(BaseModel):
    """Response with propaganda attribution."""

    narrative_id: str
    attributed_source_id: Optional[str]
    similarity_score: float
    matching_features: List[str]
    confidence: float
    timestamp: str


class MemeTrackingRequest(BaseModel):
    """Request for meme tracking."""

    meme_id: str = Field(..., description="Meme ID")
    image_data: str = Field(..., description="Base64-encoded image data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MemeLineageResponse(BaseModel):
    """Response with meme lineage."""

    meme_id: str
    parent_meme_id: Optional[str]
    generation: int
    mutation_distance: int
    perceptual_hash: str
    first_seen: str
    propagation_count: int


class StatusResponse(BaseModel):
    """Service status response."""

    service: str
    status: str
    components: Dict[str, Dict[str, Any]]
    timestamp: str


# ============================================================================
# Social Graph Endpoints
# ============================================================================


@app.post("/graph/add_relation")
async def add_social_relation(request: SocialRelationRequest):
    """Add social relationship to graph.

    Args:
        request: Relationship details

    Returns:
        Success confirmation
    """
    if social_graph is None:
        raise HTTPException(
            status_code=503, detail="Social graph analyzer not initialized"
        )

    try:
        # Parse timestamp if provided
        timestamp = None
        if request.timestamp:
            timestamp = datetime.fromisoformat(request.timestamp)

        # Add relation to graph
        social_graph.add_relation(
            source=request.source_id,
            target=request.target_id,
            relation_type=request.relation_type,
            timestamp=timestamp,
        )

        return {
            "status": "success",
            "source": request.source_id,
            "target": request.target_id,
            "relation_type": request.relation_type,
        }

    except Exception as e:
        logger.error(f"Error adding relation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/influence_scores", response_model=InfluenceScoresResponse)
async def get_influence_scores():
    """Compute influence scores using PageRank.

    Returns:
        Influence scores for all accounts
    """
    if social_graph is None:
        raise HTTPException(
            status_code=503, detail="Social graph analyzer not initialized"
        )

    try:
        scores = social_graph.compute_influence_scores()

        return InfluenceScoresResponse(
            scores=scores, algorithm="pagerank", timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error computing influence scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/detect_coordination")
async def detect_coordinated_behavior(request: CoordinationDetectionRequest):
    """Detect coordinated inauthentic behavior.

    Args:
        request: Detection parameters

    Returns:
        Detected coordination clusters
    """
    if social_graph is None:
        raise HTTPException(
            status_code=503, detail="Social graph analyzer not initialized"
        )

    try:
        clusters = social_graph.detect_coordinated_behavior(
            min_cluster_size=request.min_cluster_size,
            time_window_hours=request.time_window_hours,
        )

        # Convert sets to lists for JSON serialization
        clusters_list = [
            {"cluster_id": idx, "accounts": list(cluster), "size": len(cluster)}
            for idx, cluster in enumerate(clusters)
        ]

        return {
            "clusters": clusters_list,
            "total_clusters": len(clusters_list),
            "min_cluster_size": request.min_cluster_size,
            "time_window_hours": request.time_window_hours,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error detecting coordination: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/communities")
async def detect_communities(resolution: float = 1.0):
    """Detect communities using Louvain method.

    Args:
        resolution: Resolution parameter for community detection

    Returns:
        Detected communities
    """
    if social_graph is None:
        raise HTTPException(
            status_code=503, detail="Social graph analyzer not initialized"
        )

    try:
        communities = social_graph.detect_communities(resolution=resolution)

        # Convert to serializable format
        communities_list = [
            {"community_id": comm_id, "members": list(members), "size": len(members)}
            for comm_id, members in communities.items()
        ]

        return {
            "communities": communities_list,
            "total_communities": len(communities_list),
            "resolution": resolution,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error detecting communities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Bot Detection Endpoints
# ============================================================================


@app.post("/bot/analyze", response_model=BotScoreResponse)
async def analyze_account_for_bots(request: BotAnalysisRequest):
    """Analyze account for bot characteristics.

    Args:
        request: Account data for analysis

    Returns:
        Bot detection score and indicators
    """
    if bot_detector is None:
        raise HTTPException(status_code=503, detail="Bot detector not initialized")

    try:
        # Analyze account
        bot_score = bot_detector.analyze_account(
            account_id=request.account_id,
            posts=request.posts,
            account_metadata=request.account_metadata,
        )

        return BotScoreResponse(
            entity_id=bot_score.entity_id,
            bot_probability=bot_score.bot_probability,
            indicators=bot_score.indicators,
            confidence=bot_score.confidence,
            timestamp=bot_score.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error analyzing account for bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bot/batch_analyze")
async def batch_analyze_accounts(
    accounts: List[BotAnalysisRequest], background_tasks: BackgroundTasks
):
    """Batch analyze multiple accounts.

    Args:
        accounts: List of accounts to analyze
        background_tasks: FastAPI background tasks

    Returns:
        Analysis results for all accounts
    """
    if bot_detector is None:
        raise HTTPException(status_code=503, detail="Bot detector not initialized")

    try:
        results = []

        for request in accounts:
            bot_score = bot_detector.analyze_account(
                account_id=request.account_id,
                posts=request.posts,
                account_metadata=request.account_metadata,
            )

            results.append(
                {
                    "entity_id": bot_score.entity_id,
                    "bot_probability": bot_score.bot_probability,
                    "indicators": bot_score.indicators,
                    "confidence": bot_score.confidence,
                    "timestamp": bot_score.timestamp.isoformat(),
                }
            )

        return {
            "results": results,
            "total_analyzed": len(results),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Propaganda Attribution Endpoints
# ============================================================================


@app.post("/propaganda/analyze", response_model=PropagandaAttributionResponse)
async def analyze_propaganda(request: PropagandaAnalysisRequest):
    """Analyze text for propaganda attribution.

    Args:
        request: Text content to analyze

    Returns:
        Attribution result with source and confidence
    """
    if propaganda_attributor is None:
        raise HTTPException(
            status_code=503, detail="Propaganda attributor not initialized"
        )

    try:
        # Analyze narrative
        attribution = propaganda_attributor.attribute_narrative(
            narrative_id=request.narrative_id, text=request.text
        )

        return PropagandaAttributionResponse(
            narrative_id=attribution.narrative_id,
            attributed_source_id=attribution.attributed_source_id,
            similarity_score=attribution.similarity_score,
            matching_features=attribution.matching_features,
            confidence=attribution.confidence,
            timestamp=attribution.timestamp.isoformat(),
        )

    except Exception as e:
        logger.error(f"Error analyzing propaganda: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/propaganda/register_source")
async def register_propaganda_source(source_id: str, texts: List[str]):
    """Register known propaganda source with sample texts.

    Args:
        source_id: Source identifier
        texts: Sample texts from source

    Returns:
        Registration confirmation
    """
    if propaganda_attributor is None:
        raise HTTPException(
            status_code=503, detail="Propaganda attributor not initialized"
        )

    try:
        # Register source
        propaganda_attributor.register_source(source_id=source_id, sample_texts=texts)

        return {
            "status": "success",
            "source_id": source_id,
            "samples_registered": len(texts),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error registering source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Meme Tracking Endpoints
# ============================================================================


@app.post("/meme/track", response_model=MemeLineageResponse)
async def track_meme(request: MemeTrackingRequest):
    """Track meme and identify lineage.

    Args:
        request: Meme data

    Returns:
        Meme lineage information
    """
    if meme_tracker is None:
        raise HTTPException(status_code=503, detail="Meme tracker not initialized")

    try:
        # Decode base64 image data
        import base64

        image_data = base64.b64decode(request.image_data)

        # Track meme
        lineage = meme_tracker.track_meme(
            meme_id=request.meme_id, image_data=image_data, metadata=request.metadata
        )

        return MemeLineageResponse(
            meme_id=lineage.meme_id,
            parent_meme_id=lineage.parent_meme_id,
            generation=lineage.generation,
            mutation_distance=lineage.mutation_distance,
            perceptual_hash=lineage.perceptual_hash,
            first_seen=lineage.first_seen.isoformat(),
            propagation_count=lineage.propagation_count,
        )

    except Exception as e:
        logger.error(f"Error tracking meme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meme/lineage/{meme_id}")
async def get_meme_lineage(meme_id: str):
    """Get complete lineage for a meme.

    Args:
        meme_id: Meme identifier

    Returns:
        Complete meme family tree
    """
    if meme_tracker is None:
        raise HTTPException(status_code=503, detail="Meme tracker not initialized")

    try:
        # Get lineage from database
        if meme_id not in meme_tracker.meme_database:
            raise HTTPException(status_code=404, detail=f"Meme {meme_id} not found")

        lineage = meme_tracker.meme_database[meme_id]

        # Find all descendants
        descendants = []
        for mid, lin in meme_tracker.meme_database.items():
            if lin.parent_meme_id == meme_id:
                descendants.append(
                    {
                        "meme_id": mid,
                        "generation": lin.generation,
                        "mutation_distance": lin.mutation_distance,
                        "first_seen": lin.first_seen.isoformat(),
                    }
                )

        return {
            "meme_id": meme_id,
            "parent_meme_id": lineage.parent_meme_id,
            "generation": lineage.generation,
            "mutation_distance": lineage.mutation_distance,
            "perceptual_hash": lineage.perceptual_hash,
            "first_seen": lineage.first_seen.isoformat(),
            "propagation_count": lineage.propagation_count,
            "descendants": descendants,
            "descendants_count": len(descendants),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meme lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "narrative_analysis",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get comprehensive service status.

    Returns:
        Status of all components
    """
    components = {}

    # Social graph status
    if social_graph is not None:
        components["social_graph"] = social_graph.get_status()

    # Bot detector status
    if bot_detector is not None:
        components["bot_detector"] = bot_detector.get_status()

    # Propaganda attributor status
    if propaganda_attributor is not None:
        components["propaganda_attributor"] = propaganda_attributor.get_status()

    # Meme tracker status
    if meme_tracker is not None:
        components["meme_tracker"] = meme_tracker.get_status()

    return StatusResponse(
        service="narrative_analysis",
        status="operational",
        components=components,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics.

    Returns:
        Combined statistics from all components
    """
    stats = {
        "service": "narrative_analysis",
        "timestamp": datetime.now().isoformat(),
        "components": {},
    }

    # Gather stats from all components
    if social_graph is not None:
        status = social_graph.get_status()
        stats["components"]["social_graph"] = {
            "nodes": status["nodes"],
            "edges": status["edges"],
            "density": status["density"],
        }

    if bot_detector is not None:
        status = bot_detector.get_status()
        stats["components"]["bot_detector"] = {
            "accounts_analyzed": status["accounts_analyzed"],
            "bots_detected": status["bots_detected"],
            "detection_rate": status["detection_rate"],
        }

    if propaganda_attributor is not None:
        status = propaganda_attributor.get_status()
        stats["components"]["propaganda_attributor"] = {
            "registered_sources": status["registered_sources"],
            "narratives_analyzed": status["narratives_analyzed"],
            "attributions_made": status["attributions_made"],
        }

    if meme_tracker is not None:
        status = meme_tracker.get_status()
        stats["components"]["meme_tracker"] = {
            "memes_tracked": status["memes_tracked"],
            "unique_lineages": status["unique_lineages"],
            "avg_generation": status["avg_generation"],
        }

    return stats


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8015, log_level="info", access_log=True)
