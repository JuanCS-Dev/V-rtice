"""
Seriema Graph Client for Cognitive Defense System.

Neo4j integration for storing and analyzing argumentation frameworks:
- Argument and attack relation persistence
- Graph-based argument analysis
- Centrality measures, community detection
- Path finding, subgraph extraction
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from datetime import datetime, timedelta
import asyncio

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, Neo4jError

from .models import Argument, ArgumentRole, Fallacy
from .argumentation_framework import ArgumentationFramework
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class SeriemaGraphClient:
    """
    Neo4j client for Seriema Graph service.

    Stores argumentation frameworks as property graphs:
    - Nodes: Arguments (with properties: text, role, confidence, etc.)
    - Edges: ATTACKS relationships
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "neo4j",
        database: str = "neo4j",
        max_connection_pool_size: int = 50
    ):
        """
        Initialize Seriema Graph client.

        Args:
            uri: Neo4j URI
            user: Username
            password: Password
            database: Database name
            max_connection_pool_size: Connection pool size
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database

        self.driver: Optional[AsyncDriver] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Neo4j driver."""
        if self._initialized:
            logger.warning("Seriema Graph client already initialized")
            return

        try:
            logger.info(f"Connecting to Seriema Graph: {self.uri}")

            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=50,
                connection_timeout=30.0
            )

            # Verify connectivity
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 AS test")
                record = await result.single()
                if record["test"] != 1:
                    raise RuntimeError("Neo4j health check failed")

            # Create indexes and constraints
            await self._create_schema()

            self._initialized = True
            logger.info("✅ Seriema Graph client initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Seriema Graph client: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close Neo4j driver."""
        if self.driver:
            await self.driver.close()
            self._initialized = False
            logger.info("Seriema Graph client closed")

    async def _create_schema(self) -> None:
        """Create indexes and constraints."""
        async with self.driver.session(database=self.database) as session:
            # Constraint on Argument ID
            try:
                await session.run(
                    "CREATE CONSTRAINT argument_id_unique IF NOT EXISTS "
                    "FOR (a:Argument) REQUIRE a.id IS UNIQUE"
                )
            except Neo4jError:
                pass  # Already exists

            # Index on framework_id for fast filtering
            try:
                await session.run(
                    "CREATE INDEX argument_framework_idx IF NOT EXISTS "
                    "FOR (a:Argument) ON (a.framework_id)"
                )
            except Neo4jError:
                pass

            # Index on role
            try:
                await session.run(
                    "CREATE INDEX argument_role_idx IF NOT EXISTS "
                    "FOR (a:Argument) ON (a.role)"
                )
            except Neo4jError:
                pass

            logger.info("Schema constraints and indexes created")

    async def store_framework(
        self,
        framework: ArgumentationFramework,
        framework_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store argumentation framework in Neo4j.

        Args:
            framework: ArgumentationFramework to store
            framework_id: Unique framework identifier
            metadata: Additional metadata (text_id, timestamp, etc.)

        Returns:
            True if successful
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        try:
            async with self.driver.session(database=self.database) as session:
                # Use transaction for atomicity
                await session.execute_write(
                    self._store_framework_tx,
                    framework,
                    framework_id,
                    metadata or {}
                )

            logger.info(
                f"Stored framework {framework_id}: {len(framework.arguments)} arguments, "
                f"{len(framework.attacks)} attacks"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store framework {framework_id}: {e}", exc_info=True)
            return False

    @staticmethod
    async def _store_framework_tx(
        tx,
        framework: ArgumentationFramework,
        framework_id: str,
        metadata: Dict[str, Any]
    ):
        """Transaction function for storing framework."""
        timestamp = datetime.utcnow().isoformat()

        # Delete existing framework (if any)
        await tx.run(
            "MATCH (a:Argument {framework_id: $framework_id}) DETACH DELETE a",
            framework_id=framework_id
        )

        # Create argument nodes
        for arg_id, arg in framework.arguments.items():
            await tx.run(
                """
                CREATE (a:Argument {
                    id: $id,
                    framework_id: $framework_id,
                    text: $text,
                    role: $role,
                    start_char: $start_char,
                    end_char: $end_char,
                    confidence: $confidence,
                    parent_id: $parent_id,
                    created_at: $created_at
                })
                """,
                id=arg_id,
                framework_id=framework_id,
                text=arg.text,
                role=arg.role.value,
                start_char=arg.start_char,
                end_char=arg.end_char,
                confidence=arg.confidence,
                parent_id=arg.parent_id,
                created_at=timestamp
            )

        # Create attack relationships
        for attacker_id, attacked_id in framework.attacks:
            await tx.run(
                """
                MATCH (attacker:Argument {id: $attacker_id, framework_id: $framework_id})
                MATCH (attacked:Argument {id: $attacked_id, framework_id: $framework_id})
                CREATE (attacker)-[:ATTACKS {created_at: $created_at}]->(attacked)
                """,
                attacker_id=attacker_id,
                attacked_id=attacked_id,
                framework_id=framework_id,
                created_at=timestamp
            )

        # Store metadata as FrameworkMetadata node
        await tx.run(
            """
            CREATE (m:FrameworkMetadata {
                framework_id: $framework_id,
                coherence: $coherence,
                num_arguments: $num_arguments,
                num_attacks: $num_attacks,
                grounded_extension_size: $grounded_size,
                created_at: $created_at,
                metadata: $metadata
            })
            """,
            framework_id=framework_id,
            coherence=framework.calculate_coherence(),
            num_arguments=len(framework.arguments),
            num_attacks=len(framework.attacks),
            grounded_size=len(framework.compute_grounded_extension()),
            created_at=timestamp,
            metadata=metadata
        )

    async def retrieve_framework(
        self,
        framework_id: str
    ) -> Optional[ArgumentationFramework]:
        """
        Retrieve argumentation framework from Neo4j.

        Args:
            framework_id: Framework identifier

        Returns:
            ArgumentationFramework or None
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        try:
            async with self.driver.session(database=self.database) as session:
                # Fetch arguments
                result = await session.run(
                    """
                    MATCH (a:Argument {framework_id: $framework_id})
                    RETURN a.id AS id, a.text AS text, a.role AS role,
                           a.start_char AS start_char, a.end_char AS end_char,
                           a.confidence AS confidence, a.parent_id AS parent_id
                    """,
                    framework_id=framework_id
                )

                arguments = []
                async for record in result:
                    arg = Argument(
                        id=record["id"],
                        text=record["text"],
                        role=ArgumentRole(record["role"]),
                        start_char=record["start_char"],
                        end_char=record["end_char"],
                        confidence=record["confidence"],
                        parent_id=record["parent_id"]
                    )
                    arguments.append(arg)

                if not arguments:
                    return None

                # Fetch attacks
                result = await session.run(
                    """
                    MATCH (attacker:Argument {framework_id: $framework_id})-[:ATTACKS]->(attacked:Argument)
                    RETURN attacker.id AS attacker_id, attacked.id AS attacked_id
                    """,
                    framework_id=framework_id
                )

                attacks = []
                async for record in result:
                    attacks.append((record["attacker_id"], record["attacked_id"]))

                # Rebuild framework
                framework = ArgumentationFramework()
                framework.add_arguments(arguments)

                for attacker_id, attacked_id in attacks:
                    framework.add_attack(attacker_id, attacked_id)

                logger.info(f"Retrieved framework {framework_id}")
                return framework

        except Exception as e:
            logger.error(f"Failed to retrieve framework {framework_id}: {e}", exc_info=True)
            return None

    async def get_argument_centrality(
        self,
        framework_id: str,
        algorithm: str = "pagerank"
    ) -> Dict[str, float]:
        """
        Calculate argument centrality scores.

        Args:
            framework_id: Framework identifier
            algorithm: 'pagerank', 'betweenness', or 'degree'

        Returns:
            Dict mapping argument_id -> centrality score
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        async with self.driver.session(database=self.database) as session:
            if algorithm == "pagerank":
                # PageRank centrality
                result = await session.run(
                    """
                    CALL gds.pageRank.stream({
                        nodeQuery: 'MATCH (a:Argument {framework_id: $framework_id}) RETURN id(a) AS id',
                        relationshipQuery: 'MATCH (a1:Argument {framework_id: $framework_id})-[:ATTACKS]->(a2:Argument) RETURN id(a1) AS source, id(a2) AS target',
                        dampingFactor: 0.85
                    })
                    YIELD nodeId, score
                    MATCH (a:Argument) WHERE id(a) = nodeId
                    RETURN a.id AS argument_id, score
                    """,
                    framework_id=framework_id
                )
            elif algorithm == "degree":
                # Degree centrality (in-degree + out-degree)
                result = await session.run(
                    """
                    MATCH (a:Argument {framework_id: $framework_id})
                    OPTIONAL MATCH (a)-[r_out:ATTACKS]->()
                    OPTIONAL MATCH ()-[r_in:ATTACKS]->(a)
                    RETURN a.id AS argument_id,
                           (COUNT(DISTINCT r_out) + COUNT(DISTINCT r_in)) AS score
                    """,
                    framework_id=framework_id
                )
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            centrality = {}
            async for record in result:
                centrality[record["argument_id"]] = float(record["score"])

            return centrality

    async def find_argument_paths(
        self,
        framework_id: str,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Find all attack paths from source to target.

        Args:
            framework_id: Framework identifier
            source_id: Source argument ID
            target_id: Target argument ID
            max_depth: Maximum path length

        Returns:
            List of paths (each path is list of argument IDs)
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH path = (source:Argument {id: $source_id, framework_id: $framework_id})
                             -[:ATTACKS*1..5]->(target:Argument {id: $target_id, framework_id: $framework_id})
                WHERE LENGTH(path) <= $max_depth
                RETURN [node IN nodes(path) | node.id] AS path
                LIMIT 10
                """,
                framework_id=framework_id,
                source_id=source_id,
                target_id=target_id,
                max_depth=max_depth
            )

            paths = []
            async for record in result:
                paths.append(record["path"])

            return paths

    async def get_argument_neighborhoods(
        self,
        framework_id: str,
        argument_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get k-hop neighborhood of argument.

        Args:
            framework_id: Framework identifier
            argument_id: Argument ID
            depth: Neighborhood depth

        Returns:
            Dict with attackers, attacked, and indirect relationships
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        async with self.driver.session(database=self.database) as session:
            # Direct attackers
            result = await session.run(
                """
                MATCH (attacker:Argument {framework_id: $framework_id})-[:ATTACKS]->(arg:Argument {id: $argument_id})
                RETURN attacker.id AS id, attacker.text AS text, attacker.role AS role
                """,
                framework_id=framework_id,
                argument_id=argument_id
            )

            attackers = []
            async for record in result:
                attackers.append({
                    "id": record["id"],
                    "text": record["text"],
                    "role": record["role"]
                })

            # Direct attacked
            result = await session.run(
                """
                MATCH (arg:Argument {id: $argument_id, framework_id: $framework_id})-[:ATTACKS]->(attacked:Argument)
                RETURN attacked.id AS id, attacked.text AS text, attacked.role AS role
                """,
                framework_id=framework_id,
                argument_id=argument_id
            )

            attacked = []
            async for record in result:
                attacked.append({
                    "id": record["id"],
                    "text": record["text"],
                    "role": record["role"]
                })

            # Indirect (k-hop)
            result = await session.run(
                """
                MATCH path = (arg:Argument {id: $argument_id, framework_id: $framework_id})
                             -[:ATTACKS*1..3]-(neighbor:Argument)
                WHERE LENGTH(path) <= $depth AND neighbor.id <> $argument_id
                RETURN DISTINCT neighbor.id AS id, neighbor.text AS text,
                       neighbor.role AS role, LENGTH(path) AS distance
                ORDER BY distance
                LIMIT 20
                """,
                framework_id=framework_id,
                argument_id=argument_id,
                depth=depth
            )

            indirect = []
            async for record in result:
                indirect.append({
                    "id": record["id"],
                    "text": record["text"],
                    "role": record["role"],
                    "distance": record["distance"]
                })

            return {
                "argument_id": argument_id,
                "direct_attackers": attackers,
                "direct_attacked": attacked,
                "indirect_neighbors": indirect
            }

    async def detect_circular_arguments(
        self,
        framework_id: str
    ) -> List[List[str]]:
        """
        Detect circular attack patterns (cycles).

        Args:
            framework_id: Framework identifier

        Returns:
            List of cycles (each cycle is list of argument IDs)
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH path = (a:Argument {framework_id: $framework_id})-[:ATTACKS*2..10]->(a)
                WHERE ALL(node IN nodes(path)[1..-1] WHERE node.framework_id = $framework_id)
                RETURN [node IN nodes(path) | node.id] AS cycle
                LIMIT 20
                """,
                framework_id=framework_id
            )

            cycles = []
            async for record in result:
                cycles.append(record["cycle"])

            return cycles

    async def get_framework_statistics(
        self,
        framework_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive framework statistics.

        Args:
            framework_id: Framework identifier

        Returns:
            Statistics dict
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                """
                MATCH (a:Argument {framework_id: $framework_id})
                OPTIONAL MATCH (a)-[attack:ATTACKS]->()
                WITH a, COUNT(DISTINCT attack) AS out_degree
                OPTIONAL MATCH ()-[attacked:ATTACKS]->(a)
                WITH a, out_degree, COUNT(DISTINCT attacked) AS in_degree
                RETURN
                    COUNT(DISTINCT a) AS num_arguments,
                    SUM(out_degree) AS num_attacks,
                    AVG(out_degree) AS avg_out_degree,
                    AVG(in_degree) AS avg_in_degree,
                    MAX(out_degree) AS max_out_degree,
                    MAX(in_degree) AS max_in_degree,
                    COLLECT(DISTINCT a.role) AS roles
                """,
                framework_id=framework_id
            )

            record = await result.single()

            if not record:
                return {}

            return {
                "framework_id": framework_id,
                "num_arguments": record["num_arguments"],
                "num_attacks": record["num_attacks"],
                "avg_out_degree": float(record["avg_out_degree"] or 0),
                "avg_in_degree": float(record["avg_in_degree"] or 0),
                "max_out_degree": record["max_out_degree"],
                "max_in_degree": record["max_in_degree"],
                "roles": record["roles"]
            }

    async def delete_framework(
        self,
        framework_id: str
    ) -> bool:
        """
        Delete framework from Neo4j.

        Args:
            framework_id: Framework identifier

        Returns:
            True if deleted
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")

        try:
            async with self.driver.session(database=self.database) as session:
                # Delete arguments and metadata
                await session.run(
                    """
                    MATCH (a:Argument {framework_id: $framework_id})
                    DETACH DELETE a
                    """,
                    framework_id=framework_id
                )

                await session.run(
                    """
                    MATCH (m:FrameworkMetadata {framework_id: $framework_id})
                    DELETE m
                    """,
                    framework_id=framework_id
                )

            logger.info(f"Deleted framework {framework_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete framework {framework_id}: {e}", exc_info=True)
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Neo4j connection health.

        Returns:
            Health status dict
        """
        try:
            if not self.driver:
                return {"status": "unhealthy", "error": "Driver not initialized"}

            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 AS health")
                record = await result.single()

                if record["health"] == 1:
                    return {"status": "healthy"}
                else:
                    return {"status": "unhealthy", "error": "Unexpected response"}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

seriema_graph_client = SeriemaGraphClient(
    uri=getattr(settings, "SERIEMA_GRAPH_URI", "bolt://localhost:7687"),
    user=getattr(settings, "SERIEMA_GRAPH_USER", "neo4j"),
    password=getattr(settings, "SERIEMA_GRAPH_PASSWORD", "neo4j"),
    database=getattr(settings, "SERIEMA_GRAPH_DATABASE", "neo4j")
)
