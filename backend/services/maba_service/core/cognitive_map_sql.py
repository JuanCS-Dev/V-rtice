"""Cognitive Map Engine - SQL-Based Website Learning (Alternative to Neo4j).

This module implements a PostgreSQL-based cognitive map as an alternative to Neo4j.
Uses JSONB for flexible storage, GIN indexes for fast queries, and WITH RECURSIVE
for path finding.

Biblical Foundation:
- Ecclesiastes 7:12: "For the protection of wisdom is like the protection of money"
  (Wisdom in choosing the right tool for the job)

Key Features:
- SQL-based page and element storage
- Navigation path learning (WITH RECURSIVE)
- Element importance scoring
- JSONB for flexible attributes
- GIN indexes for fast queries
- Compatible interface with Neo4j version

Author: Vértice Platform Team
Created: 2025-11-01
"""

import asyncio
from datetime import datetime
import logging
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import asyncpg
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


class CognitiveMapSQL:
    """
    PostgreSQL-based cognitive map for website learning.

    Alternative to Neo4j implementation, uses PostgreSQL with JSONB
    and GIN indexes for comparable performance with lower ops complexity.

    Attributes:
        pool: AsyncPG connection pool
        _initialized: Initialization status
    """

    # Prometheus metrics
    pages_stored = Gauge(
        "maba_cognitive_map_sql_pages_total", "Total pages in cognitive map (SQL)"
    )

    elements_stored = Gauge(
        "maba_cognitive_map_sql_elements_total",
        "Total elements in cognitive map (SQL)",
    )

    queries_total = Counter(
        "maba_cognitive_map_sql_queries_total",
        "Total cognitive map queries (SQL)",
        ["query_type", "status"],
    )

    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_name: str,
        db_user: str,
        db_password: str,
    ):
        """
        Initialize SQL cognitive map engine.

        Args:
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: Database name
            db_user: Database user
            db_password: Database password
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password

        self.pool: asyncpg.Pool | None = None
        self._initialized = False

        logger.info(
            f"Cognitive map SQL engine initialized (PostgreSQL: {db_host}:{db_port}/{db_name})"
        )

    async def initialize(self) -> bool:
        """
        Initialize PostgreSQL connection and create schema.

        Returns:
            True if initialization succeeded, False otherwise
        """
        if self._initialized:
            logger.warning("Cognitive map SQL already initialized")
            return True

        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                min_size=2,
                max_size=10,
            )

            logger.debug("✅ PostgreSQL connection pool created")

            # Create schema
            await self._create_schema()

            self._initialized = True
            logger.info("✅ Cognitive map SQL engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize cognitive map SQL: {e}")
            return False

    async def _create_schema(self) -> None:
        """Create PostgreSQL schema for cognitive map."""
        async with self.pool.acquire() as conn:
            # Create pages table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cognitive_pages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    title TEXT,
                    visit_count INT DEFAULT 0,
                    first_seen TIMESTAMP DEFAULT NOW(),
                    last_seen TIMESTAMP DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'::jsonb
                );
                """
            )

            # Create elements table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cognitive_elements (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    page_id UUID REFERENCES cognitive_pages(id) ON DELETE CASCADE,
                    element_id TEXT UNIQUE NOT NULL,
                    selector TEXT NOT NULL,
                    tag TEXT,
                    text TEXT,
                    attributes JSONB DEFAULT '{}'::jsonb,
                    importance FLOAT DEFAULT 0.5,
                    interaction_count INT DEFAULT 0,
                    success_rate FLOAT DEFAULT 1.0,
                    last_interaction TIMESTAMP,
                    last_interaction_type TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )

            # Create navigation edges table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cognitive_navigation (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    from_page_id UUID REFERENCES cognitive_pages(id) ON DELETE CASCADE,
                    to_page_id UUID REFERENCES cognitive_pages(id) ON DELETE CASCADE,
                    action TEXT NOT NULL,
                    selector TEXT,
                    count INT DEFAULT 0,
                    last_used TIMESTAMP DEFAULT NOW(),
                    UNIQUE (from_page_id, to_page_id, action)
                );
                """
            )

            # Create indexes
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pages_domain ON cognitive_pages(domain);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pages_url_hash ON cognitive_pages(md5(url));"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_elements_page_id ON cognitive_elements(page_id);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_elements_selector ON cognitive_elements(selector);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_elements_importance ON cognitive_elements(importance DESC);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_elements_text_gin ON cognitive_elements USING GIN (to_tsvector('english', text));"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_navigation_from ON cognitive_navigation(from_page_id);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_navigation_to ON cognitive_navigation(to_page_id);"
            )

            logger.debug("✅ Cognitive map SQL schema created")

    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Cognitive map SQL connection pool closed")

    async def store_page(
        self,
        url: str,
        title: str | None = None,
        elements: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Store a page in the cognitive map.

        Args:
            url: Page URL
            title: Page title
            elements: List of page elements

        Returns:
            True if storage succeeded, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            async with self.pool.acquire() as conn:
                # Insert or update page
                page = await conn.fetchrow(
                    """
                    INSERT INTO cognitive_pages (url, domain, title, visit_count, last_seen)
                    VALUES ($1, $2, $3, 1, NOW())
                    ON CONFLICT (url) DO UPDATE
                    SET visit_count = cognitive_pages.visit_count + 1,
                        last_seen = NOW(),
                        title = COALESCE($3, cognitive_pages.title)
                    RETURNING id
                    """,
                    url,
                    domain,
                    title,
                )

                page_id = page["id"]

                # Store elements if provided
                if elements:
                    for element in elements:
                        selector = element.get("selector")
                        if not selector:
                            continue

                        element_id = f"{url}#{selector}"

                        await conn.execute(
                            """
                            INSERT INTO cognitive_elements (
                                page_id, element_id, selector, tag, text, attributes
                            )
                            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                            ON CONFLICT (element_id) DO UPDATE
                            SET tag = COALESCE($4, cognitive_elements.tag),
                                text = COALESCE($5, cognitive_elements.text),
                                attributes = $6::jsonb
                            """,
                            page_id,
                            element_id,
                            selector,
                            element.get("tag"),
                            element.get("text"),
                            element.get("attributes", {}),
                        )

                self.queries_total.labels(
                    query_type="store_page", status="success"
                ).inc()
                logger.debug(f"✅ Stored page (SQL): {url}")
                return True

        except Exception as e:
            self.queries_total.labels(query_type="store_page", status="failed").inc()
            logger.error(f"Failed to store page (SQL): {e}")
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
            async with self.pool.acquire() as conn:
                # Get page IDs
                from_page = await conn.fetchrow(
                    "SELECT id FROM cognitive_pages WHERE url = $1", from_url
                )
                to_page = await conn.fetchrow(
                    "SELECT id FROM cognitive_pages WHERE url = $1", to_url
                )

                if not from_page or not to_page:
                    logger.warning(
                        f"Cannot store navigation: pages not found ({from_url} -> {to_url})"
                    )
                    return False

                # Insert or update navigation edge
                await conn.execute(
                    """
                    INSERT INTO cognitive_navigation (from_page_id, to_page_id, action, selector, count, last_used)
                    VALUES ($1, $2, $3, $4, 1, NOW())
                    ON CONFLICT (from_page_id, to_page_id, action) DO UPDATE
                    SET count = cognitive_navigation.count + 1,
                        last_used = NOW(),
                        selector = COALESCE($4, cognitive_navigation.selector)
                    """,
                    from_page["id"],
                    to_page["id"],
                    action,
                    selector,
                )

                self.queries_total.labels(
                    query_type="store_navigation", status="success"
                ).inc()
                logger.debug(f"✅ Stored navigation (SQL): {from_url} -> {to_url}")
                return True

        except Exception as e:
            self.queries_total.labels(
                query_type="store_navigation", status="failed"
            ).inc()
            logger.error(f"Failed to store navigation (SQL): {e}")
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

            async with self.pool.acquire() as conn:
                # Update element stats
                await conn.execute(
                    """
                    UPDATE cognitive_elements
                    SET interaction_count = interaction_count + 1,
                        success_rate = (
                            (interaction_count * success_rate) + $1
                        ) / (interaction_count + 1),
                        importance = LEAST(importance + 0.01, 1.0),
                        last_interaction = NOW(),
                        last_interaction_type = $2
                    WHERE element_id = $3
                    """,
                    1.0 if success else 0.0,
                    interaction_type,
                    element_id,
                )

                logger.debug(f"✅ Recorded interaction (SQL): {selector} on {url}")
                return True

        except Exception as e:
            logger.error(f"Failed to record interaction (SQL): {e}")
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
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT e.selector
                    FROM cognitive_elements e
                    JOIN cognitive_pages p ON e.page_id = p.id
                    WHERE p.url = $1
                        AND e.text ILIKE '%' || $2 || '%'
                        AND e.importance >= $3
                    ORDER BY e.importance DESC
                    LIMIT 1
                    """,
                    url,
                    description,
                    min_importance,
                )

                if row:
                    self.queries_total.labels(
                        query_type="find_element", status="success"
                    ).inc()
                    return row["selector"]
                else:
                    self.queries_total.labels(
                        query_type="find_element", status="not_found"
                    ).inc()
                    return None

        except Exception as e:
            self.queries_total.labels(query_type="find_element", status="failed").inc()
            logger.error(f"Failed to find element (SQL): {e}")
            return None

    async def get_navigation_path(
        self, from_url: str, to_url: str, max_depth: int = 10
    ) -> list[tuple[str, str]] | None:
        """
        Find navigation path between two URLs using WITH RECURSIVE.

        Args:
            from_url: Starting URL
            to_url: Target URL
            max_depth: Maximum path depth

        Returns:
            List of (url, action) tuples representing the path, or None if not found
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    WITH RECURSIVE path AS (
                        -- Base case: start page
                        SELECT
                            p1.url as from_url,
                            p2.url as to_url,
                            cn.action,
                            ARRAY[p1.url, p2.url] as path_urls,
                            ARRAY[cn.action] as actions,
                            1 as depth
                        FROM cognitive_pages p1
                        JOIN cognitive_navigation cn ON p1.id = cn.from_page_id
                        JOIN cognitive_pages p2 ON cn.to_page_id = p2.id
                        WHERE p1.url = $1

                        UNION ALL

                        -- Recursive case: extend path
                        SELECT
                            path.to_url,
                            p3.url,
                            cn2.action,
                            path.path_urls || p3.url,
                            path.actions || cn2.action,
                            path.depth + 1
                        FROM path
                        JOIN cognitive_pages p2 ON p2.url = path.to_url
                        JOIN cognitive_navigation cn2 ON p2.id = cn2.from_page_id
                        JOIN cognitive_pages p3 ON cn2.to_page_id = p3.id
                        WHERE p3.url != ALL(path.path_urls)  -- Prevent cycles
                            AND path.depth < $3  -- Max depth
                    )
                    SELECT path_urls, actions
                    FROM path
                    WHERE path_urls[array_upper(path_urls, 1)] = $2
                    ORDER BY depth
                    LIMIT 1
                    """,
                    from_url,
                    to_url,
                    max_depth,
                )

                if not rows:
                    self.queries_total.labels(
                        query_type="get_path", status="not_found"
                    ).inc()
                    return None

                row = rows[0]
                urls = row["path_urls"]
                actions = row["actions"]

                # Return list of (url, action) tuples (excluding first URL)
                path = list(zip(urls[1:], actions))

                self.queries_total.labels(query_type="get_path", status="success").inc()
                return path

        except Exception as e:
            self.queries_total.labels(query_type="get_path", status="failed").inc()
            logger.error(f"Failed to get navigation path (SQL): {e}")
            return None

    async def get_similar_pages(self, url: str, limit: int = 5) -> list[str]:
        """
        Find pages similar to the given URL (same domain).

        Args:
            url: Reference URL
            limit: Maximum number of results

        Returns:
            List of similar page URLs
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT url
                    FROM cognitive_pages
                    WHERE domain = $1
                        AND url != $2
                    ORDER BY visit_count DESC
                    LIMIT $3
                    """,
                    domain,
                    url,
                    limit,
                )

                self.queries_total.labels(
                    query_type="get_similar", status="success"
                ).inc()
                return [row["url"] for row in rows]

        except Exception as e:
            self.queries_total.labels(query_type="get_similar", status="failed").inc()
            logger.error(f"Failed to get similar pages (SQL): {e}")
            return []

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cognitive map statistics.

        Returns:
            Dictionary with stats (pages, elements, navigations)
        """
        try:
            async with self.pool.acquire() as conn:
                pages_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM cognitive_pages"
                )
                elements_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM cognitive_elements"
                )
                navigation_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM cognitive_navigation"
                )

                # Update Prometheus metrics
                self.pages_stored.set(pages_count)
                self.elements_stored.set(elements_count)

                return {
                    "pages": pages_count,
                    "elements": elements_count,
                    "navigations": navigation_count,
                    "storage_backend": "postgresql",
                }

        except Exception as e:
            logger.error(f"Failed to get stats (SQL): {e}")
            return {}
