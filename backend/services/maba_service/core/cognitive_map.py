"""Cognitive Map Engine - Graph-Based Website Learning.

This module implements a graph database (Neo4j) based cognitive map that learns
website structures over time. It stores pages, elements, navigation paths, and
interaction patterns for intelligent automation.

Key Features:
- Graph-based page and element storage
- Navigation path learning
- Element importance scoring
- Similar page detection
- Pattern recognition

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from typing import Any
from urllib.parse import urlparse

from neo4j import AsyncDriver, AsyncGraphDatabase
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


class CognitiveMapEngine:
    """
    Graph-based cognitive map for website learning.

    Uses Neo4j to store and query learned website structures, enabling
    intelligent navigation and automation based on past interactions.

    Attributes:
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        _driver: Neo4j async driver
        _initialized: Initialization status
    """

    # Prometheus metrics
    pages_stored = Gauge(
        "maba_cognitive_map_pages_total", "Total pages in cognitive map"
    )

    elements_stored = Gauge(
        "maba_cognitive_map_elements_total", "Total elements in cognitive map"
    )

    queries_total = Counter(
        "maba_cognitive_map_queries_total",
        "Total cognitive map queries",
        ["query_type", "status"],
    )

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """
        Initialize cognitive map engine.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        self._driver: AsyncDriver | None = None
        self._initialized = False

        logger.info(f"Cognitive map engine initialized (Neo4j: {neo4j_uri})")

    async def initialize(self) -> bool:
        """
        Initialize Neo4j connection and create indexes.

        Returns:
            True if initialization succeeded, False otherwise
        """
        if self._initialized:
            logger.warning("Cognitive map already initialized")
            return True

        try:
            # Create Neo4j driver
            self._driver = AsyncGraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
            )

            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.debug("✅ Neo4j connection verified")

            # Create indexes and constraints
            await self._create_schema()

            self._initialized = True
            logger.info("✅ Cognitive map engine initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize cognitive map: {e}", exc_info=True)
            return False

    async def shutdown(self) -> None:
        """Shutdown cognitive map engine."""
        if self._driver:
            await self._driver.close()
            self._initialized = False
            logger.info("✅ Cognitive map engine shut down")

    async def _create_schema(self) -> None:
        """Create Neo4j indexes and constraints."""
        async with self._driver.session() as session:
            # Create constraints
            await session.run(
                "CREATE CONSTRAINT page_url IF NOT EXISTS "
                "FOR (p:Page) REQUIRE p.url IS UNIQUE"
            )

            await session.run(
                "CREATE CONSTRAINT element_id IF NOT EXISTS "
                "FOR (e:Element) REQUIRE e.element_id IS UNIQUE"
            )

            # Create indexes
            await session.run(
                "CREATE INDEX page_domain IF NOT EXISTS " "FOR (p:Page) ON (p.domain)"
            )

            await session.run(
                "CREATE INDEX element_selector IF NOT EXISTS "
                "FOR (e:Element) ON (e.selector)"
            )

            logger.debug("✅ Neo4j schema created")

    async def store_page(
        self,
        url: str,
        title: str,
        elements: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Store a page in the cognitive map.

        Args:
            url: Page URL
            title: Page title
            elements: List of extracted elements
            metadata: Additional page metadata

        Returns:
            True if storage succeeded, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            async with self._driver.session() as session:
                # Create or update page node
                await session.run(
                    """
                    MERGE (p:Page {url: $url})
                    SET p.title = $title,
                        p.domain = $domain,
                        p.updated_at = datetime(),
                        p.visit_count = COALESCE(p.visit_count, 0) + 1,
                        p.metadata = $metadata
                    """,
                    url=url,
                    title=title,
                    domain=domain,
                    metadata=metadata or {},
                )

                # Store elements
                for element in elements:
                    element_id = (
                        f"{url}#{element.get('selector', element.get('id', 'unknown'))}"
                    )

                    await session.run(
                        """
                        MERGE (e:Element {element_id: $element_id})
                        SET e.selector = $selector,
                            e.tag = $tag,
                            e.text = $text,
                            e.attributes = $attributes,
                            e.importance = COALESCE(e.importance, 0.5),
                            e.interaction_count = COALESCE(e.interaction_count, 0)
                        WITH e
                        MATCH (p:Page {url: $url})
                        MERGE (p)-[:CONTAINS]->(e)
                        """,
                        element_id=element_id,
                        selector=element.get("selector"),
                        tag=element.get("tag"),
                        text=element.get("text"),
                        attributes=element.get("attributes", {}),
                        url=url,
                    )

                self.queries_total.labels(
                    query_type="store_page", status="success"
                ).inc()
                logger.debug(f"✅ Stored page: {url}")
                return True

        except Exception as e:
            self.queries_total.labels(query_type="store_page", status="failed").inc()
            logger.error(f"Failed to store page: {e}")
            return False

    async def store_navigation(
        self, from_url: str, to_url: str, action: str, selector: str | None = None
    ) -> bool:
        """
        Store a navigation action in the cognitive map.

        Args:
            from_url: Source page URL
            to_url: Destination page URL
            action: Navigation action (click, link, etc.)
            selector: Element selector that triggered navigation

        Returns:
            True if storage succeeded, False otherwise
        """
        try:
            async with self._driver.session() as session:
                await session.run(
                    """
                    MATCH (from:Page {url: $from_url})
                    MATCH (to:Page {url: $to_url})
                    MERGE (from)-[nav:NAVIGATES_TO]->(to)
                    SET nav.action = $action,
                        nav.selector = $selector,
                        nav.count = COALESCE(nav.count, 0) + 1,
                        nav.last_used = datetime()
                    """,
                    from_url=from_url,
                    to_url=to_url,
                    action=action,
                    selector=selector,
                )

                self.queries_total.labels(
                    query_type="store_navigation", status="success"
                ).inc()
                logger.debug(f"✅ Stored navigation: {from_url} -> {to_url}")
                return True

        except Exception as e:
            self.queries_total.labels(
                query_type="store_navigation", status="failed"
            ).inc()
            logger.error(f"Failed to store navigation: {e}")
            return False

    async def record_interaction(
        self, url: str, selector: str, interaction_type: str, success: bool = True
    ) -> bool:
        """
        Record an element interaction to update importance scores.

        Args:
            url: Page URL
            selector: Element selector
            interaction_type: Type of interaction (click, type, etc.)
            success: Whether interaction succeeded

        Returns:
            True if recording succeeded, False otherwise
        """
        try:
            element_id = f"{url}#{selector}"

            async with self._driver.session() as session:
                await session.run(
                    """
                    MATCH (e:Element {element_id: $element_id})
                    SET e.interaction_count = COALESCE(e.interaction_count, 0) + 1,
                        e.success_rate = (
                            COALESCE(e.interaction_count, 0) * COALESCE(e.success_rate, 1.0) + $success
                        ) / (COALESCE(e.interaction_count, 0) + 1),
                        e.importance = e.importance + 0.01,
                        e.last_interaction = datetime(),
                        e.last_interaction_type = $interaction_type
                    """,
                    element_id=element_id,
                    success=1.0 if success else 0.0,
                    interaction_type=interaction_type,
                )

                logger.debug(f"✅ Recorded interaction: {selector} on {url}")
                return True

        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
            return False

    async def find_element(
        self, url: str, description: str, min_importance: float = 0.3
    ) -> str | None:
        """
        Find an element by natural language description.

        Args:
            url: Page URL
            description: Natural language description
            min_importance: Minimum importance score

        Returns:
            Element selector if found, None otherwise
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    """
                    MATCH (p:Page {url: $url})-[:CONTAINS]->(e:Element)
                    WHERE e.text CONTAINS $description
                        AND e.importance >= $min_importance
                    RETURN e.selector AS selector
                    ORDER BY e.importance DESC
                    LIMIT 1
                    """,
                    url=url,
                    description=description,
                    min_importance=min_importance,
                )

                record = await result.single()
                if record:
                    self.queries_total.labels(
                        query_type="find_element", status="success"
                    ).inc()
                    return record["selector"]
                else:
                    self.queries_total.labels(
                        query_type="find_element", status="not_found"
                    ).inc()
                    return None

        except Exception as e:
            self.queries_total.labels(query_type="find_element", status="failed").inc()
            logger.error(f"Failed to find element: {e}")
            return None

    async def get_navigation_path(
        self, from_url: str, to_url: str
    ) -> list[tuple[str, str]] | None:
        """
        Find the best navigation path between two pages.

        Args:
            from_url: Source page URL
            to_url: Destination page URL

        Returns:
            List of (url, action) tuples representing the path, or None if no path found
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    """
                    MATCH path = shortestPath(
                        (from:Page {url: $from_url})-[:NAVIGATES_TO*]->(to:Page {url: $to_url})
                    )
                    UNWIND relationships(path) as rel
                    RETURN startNode(rel).url AS from_url,
                           endNode(rel).url AS to_url,
                           rel.action AS action,
                           rel.selector AS selector
                    """,
                    from_url=from_url,
                    to_url=to_url,
                )

                path = []
                async for record in result:
                    path.append((record["to_url"], record["action"]))

                if path:
                    self.queries_total.labels(
                        query_type="get_path", status="success"
                    ).inc()
                    return path
                else:
                    self.queries_total.labels(
                        query_type="get_path", status="not_found"
                    ).inc()
                    return None

        except Exception as e:
            self.queries_total.labels(query_type="get_path", status="failed").inc()
            logger.error(f"Failed to get navigation path: {e}")
            return None

    async def get_similar_pages(self, url: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Find similar pages based on structure and elements.

        Args:
            url: Reference page URL
            limit: Maximum number of results

        Returns:
            List of similar page dicts
        """
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    """
                    MATCH (ref:Page {url: $url})-[:CONTAINS]->(e:Element)
                    WITH ref, collect(e.tag) AS ref_tags
                    MATCH (other:Page)-[:CONTAINS]->(oe:Element)
                    WHERE ref <> other AND ref.domain = other.domain
                    WITH other, collect(oe.tag) AS other_tags, ref_tags
                    WITH other,
                         size([tag IN ref_tags WHERE tag IN other_tags]) * 1.0 / size(ref_tags) AS similarity
                    WHERE similarity > 0.5
                    RETURN other.url AS url,
                           other.title AS title,
                           similarity
                    ORDER BY similarity DESC
                    LIMIT $limit
                    """,
                    url=url,
                    limit=limit,
                )

                similar_pages = []
                async for record in result:
                    similar_pages.append(
                        {
                            "url": record["url"],
                            "title": record["title"],
                            "similarity": record["similarity"],
                        }
                    )

                self.queries_total.labels(
                    query_type="find_similar", status="success"
                ).inc()
                return similar_pages

        except Exception as e:
            self.queries_total.labels(query_type="find_similar", status="failed").inc()
            logger.error(f"Failed to find similar pages: {e}")
            return []

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cognitive map statistics.

        Returns:
            Dict with statistics
        """
        try:
            async with self._driver.session() as session:
                # Count pages
                result = await session.run(
                    "MATCH (p:Page) RETURN count(p) AS page_count"
                )
                record = await result.single()
                page_count = record["page_count"] if record else 0

                # Count elements
                result = await session.run(
                    "MATCH (e:Element) RETURN count(e) AS element_count"
                )
                record = await result.single()
                element_count = record["element_count"] if record else 0

                # Count navigation edges
                result = await session.run(
                    "MATCH ()-[nav:NAVIGATES_TO]->() RETURN count(nav) AS nav_count"
                )
                record = await result.single()
                nav_count = record["nav_count"] if record else 0

                self.pages_stored.set(page_count)
                self.elements_stored.set(element_count)

                return {
                    "pages": page_count,
                    "elements": element_count,
                    "navigation_edges": nav_count,
                }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"pages": 0, "elements": 0, "navigation_edges": 0}

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health status dict
        """
        if not self._initialized or not self._driver:
            return {"status": "not_initialized"}

        try:
            # Verify connectivity
            await self._driver.verify_connectivity()

            # Get stats
            stats = await self.get_stats()

            return {"status": "healthy", "neo4j_uri": self.neo4j_uri, "stats": stats}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
