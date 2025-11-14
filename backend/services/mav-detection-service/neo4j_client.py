"""
Neo4j client for MAV Detection Service.

Constitutional: Lei Zero - network analysis respects user privacy.

This module provides graph database operations for MAV (Militância em Ambientes Virtuais)
campaign detection, replacing in-memory dictionaries with persistent graph storage.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

# Global driver
_driver: Optional[AsyncDriver] = None


async def init_neo4j_driver() -> AsyncDriver:
    """
    Initialize Neo4j driver.

    Constitutional: P2 (Validação Preventiva) - validates connection before use.

    Returns:
        Neo4j AsyncDriver

    Raises:
        ConnectionError: If Neo4j is unavailable
    """
    global _driver

    if _driver is not None:
        return _driver

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        _driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

        # Verify connectivity
        await _driver.verify_connectivity()

        logger.info(
            "✅ Neo4j driver initialized",
            extra={"uri": neo4j_uri}
        )
        return _driver

    except Exception as e:
        logger.error(f"❌ Failed to initialize Neo4j driver: {e}", exc_info=True)
        raise ConnectionError(f"Neo4j unavailable: {e}") from e


async def close_neo4j_driver():
    """Close Neo4j driver gracefully."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("✅ Neo4j driver closed")


async def health_check() -> Dict[str, Any]:
    """
    Check Neo4j health.

    Returns:
        Health status dict
    """
    if _driver is None:
        return {"healthy": False, "error": "Driver not initialized"}

    try:
        async with _driver.session() as session:
            result = await session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            record = await result.single()

            return {
                "healthy": True,
                "component": record["name"],
                "version": record["versions"][0]
            }
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        return {"healthy": False, "error": str(e)}


# ============================================================================
# CAMPAIGN OPERATIONS
# ============================================================================


async def create_campaign(
    campaign_id: str,
    campaign_type: str,
    target_entity: str,
    start_time: str,
    confidence_score: float,
    metadata: Dict[str, Any]
) -> None:
    """
    Create MAV campaign node.

    Args:
        campaign_id: Unique campaign identifier
        campaign_type: Type of campaign (coordinated_harassment, disinformation, etc.)
        target_entity: Target of the campaign
        start_time: Campaign start timestamp
        confidence_score: Detection confidence
        metadata: Additional campaign data
    """
    async with _driver.session() as session:
        await session.run(
            """
            MERGE (c:Campaign {id: $campaign_id})
            SET c.type = $campaign_type,
                c.target = $target_entity,
                c.start_time = datetime($start_time),
                c.confidence_score = $confidence_score,
                c.metadata = $metadata,
                c.updated_at = datetime()
            """,
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            target_entity=target_entity,
            start_time=start_time,
            confidence_score=confidence_score,
            metadata=metadata
        )
        logger.info(f"✅ Campaign created: {campaign_id}")


async def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    """Get campaign by ID."""
    async with _driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            RETURN c.id as id, c.type as type, c.target as target,
                   toString(c.start_time) as start_time,
                   c.confidence_score as confidence_score,
                   c.metadata as metadata
            """,
            campaign_id=campaign_id
        )
        record = await result.single()

        if not record:
            return None

        return dict(record)


async def list_campaigns(limit: int = 100) -> List[Dict[str, Any]]:
    """List all campaigns."""
    async with _driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign)
            RETURN c.id as id, c.type as type, c.target as target,
                   toString(c.start_time) as start_time,
                   c.confidence_score as confidence_score
            ORDER BY c.start_time DESC
            LIMIT $limit
            """,
            limit=limit
        )
        records = await result.values()

        return [
            {
                "id": r[0],
                "type": r[1],
                "target": r[2],
                "start_time": r[3],
                "confidence_score": r[4]
            }
            for r in records
        ]


# ============================================================================
# ACCOUNT OPERATIONS
# ============================================================================


async def create_account(
    account_id: str,
    username: str,
    platform: str,
    creation_date: str,
    metadata: Dict[str, Any]
) -> None:
    """Create social media account node."""
    async with _driver.session() as session:
        await session.run(
            """
            MERGE (a:Account {id: $account_id})
            SET a.username = $username,
                a.platform = $platform,
                a.creation_date = datetime($creation_date),
                a.metadata = $metadata,
                a.updated_at = datetime()
            """,
            account_id=account_id,
            username=username,
            platform=platform,
            creation_date=creation_date,
            metadata=metadata
        )


async def link_account_to_campaign(account_id: str, campaign_id: str, role: str) -> None:
    """Link account to campaign with role."""
    async with _driver.session() as session:
        await session.run(
            """
            MATCH (a:Account {id: $account_id})
            MATCH (c:Campaign {id: $campaign_id})
            MERGE (a)-[r:PARTICIPATES_IN {role: $role}]->(c)
            SET r.detected_at = datetime()
            """,
            account_id=account_id,
            campaign_id=campaign_id,
            role=role
        )


# ============================================================================
# POST OPERATIONS
# ============================================================================


async def create_post(
    post_id: str,
    account_id: str,
    campaign_id: Optional[str],
    content: str,
    timestamp: str,
    metadata: Dict[str, Any]
) -> None:
    """Create social media post node."""
    async with _driver.session() as session:
        # Create post
        await session.run(
            """
            MERGE (p:Post {id: $post_id})
            SET p.content = $content,
                p.timestamp = datetime($timestamp),
                p.metadata = $metadata,
                p.updated_at = datetime()
            """,
            post_id=post_id,
            content=content,
            timestamp=timestamp,
            metadata=metadata
        )

        # Link to account
        await session.run(
            """
            MATCH (p:Post {id: $post_id})
            MATCH (a:Account {id: $account_id})
            MERGE (a)-[:POSTED]->(p)
            """,
            post_id=post_id,
            account_id=account_id
        )

        # Link to campaign if provided
        if campaign_id:
            await session.run(
                """
                MATCH (p:Post {id: $post_id})
                MATCH (c:Campaign {id: $campaign_id})
                MERGE (p)-[:PART_OF]->(c)
                """,
                post_id=post_id,
                campaign_id=campaign_id
            )


# ============================================================================
# GRAPH ANALYSIS
# ============================================================================


async def detect_coordinated_accounts(campaign_id: str) -> List[Dict[str, Any]]:
    """
    Detect coordinated accounts in a campaign using graph analysis.

    Returns accounts that show coordination patterns (posting at similar times,
    similar content, etc.)
    """
    async with _driver.session() as session:
        result = await session.run(
            """
            MATCH (a:Account)-[:PARTICIPATES_IN]->(c:Campaign {id: $campaign_id})
            MATCH (a)-[:POSTED]->(p:Post)-[:PART_OF]->(c)
            WITH a, count(p) as post_count
            WHERE post_count > 3
            RETURN a.id as account_id, a.username as username,
                   a.platform as platform, post_count
            ORDER BY post_count DESC
            """,
            campaign_id=campaign_id
        )
        records = await result.values()

        return [
            {
                "account_id": r[0],
                "username": r[1],
                "platform": r[2],
                "post_count": r[3]
            }
            for r in records
        ]


async def find_campaign_network(campaign_id: str) -> Dict[str, Any]:
    """
    Get complete network for a campaign.

    Returns:
        Dict with nodes and edges for visualization
    """
    async with _driver.session() as session:
        # Get campaign nodes
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            OPTIONAL MATCH (a:Account)-[:PARTICIPATES_IN]->(c)
            OPTIONAL MATCH (a)-[:POSTED]->(p:Post)-[:PART_OF]->(c)
            RETURN c, collect(DISTINCT a) as accounts, collect(DISTINCT p) as posts
            """,
            campaign_id=campaign_id
        )
        record = await result.single()

        if not record:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        # Add campaign node
        campaign = record["c"]
        nodes.append({
            "id": campaign["id"],
            "type": "campaign",
            "label": campaign.get("target", "Unknown")
        })

        # Add account nodes and edges
        for account in record["accounts"]:
            if account:
                nodes.append({
                    "id": account["id"],
                    "type": "account",
                    "label": account.get("username", "Unknown")
                })
                edges.append({
                    "source": account["id"],
                    "target": campaign["id"],
                    "type": "PARTICIPATES_IN"
                })

        # Add post nodes
        for post in record["posts"]:
            if post:
                nodes.append({
                    "id": post["id"],
                    "type": "post",
                    "label": post.get("content", "")[:50]
                })
                edges.append({
                    "source": post["id"],
                    "target": campaign["id"],
                    "type": "PART_OF"
                })

        return {"nodes": nodes, "edges": edges}


async def get_statistics() -> Dict[str, Any]:
    """Get system-wide statistics."""
    async with _driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign) WITH count(c) as campaigns
            MATCH (a:Account) WITH campaigns, count(a) as accounts
            MATCH (p:Post) WITH campaigns, accounts, count(p) as posts
            RETURN campaigns, accounts, posts
            """
        )
        record = await result.single()

        return {
            "total_campaigns": record["campaigns"],
            "total_accounts": record["accounts"],
            "total_posts": record["posts"]
        }
