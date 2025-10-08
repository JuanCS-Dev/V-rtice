"""
DBpedia Client for Cognitive Defense System.

Integrates:
1. DBpedia Spotlight - Entity linking and disambiguation
2. DBpedia SPARQL endpoint - Knowledge graph queries
3. Entity relationship extraction
4. Fact verification against DBpedia knowledge base
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import aiohttp
from SPARQLWrapper import JSON, SPARQLWrapper

from cache_manager import CacheCategory, cache_manager
from config import get_settings
from models import Entity, EntityType
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class DBpediaSpotlightClient:
    """
    DBpedia Spotlight client for entity linking.

    Extracts and disambiguates named entities using DBpedia resources.
    """

    def __init__(
        self,
        spotlight_endpoint: str = "https://api.dbpedia-spotlight.org/en/annotate",
        confidence: float = 0.4,
        support: int = 20,
    ):
        """
        Initialize DBpedia Spotlight client.

        Args:
            spotlight_endpoint: Spotlight API endpoint
            confidence: Minimum confidence threshold (0-1)
            support: Minimum support (prominence in Wikipedia)
        """
        self.spotlight_endpoint = spotlight_endpoint
        self.confidence = confidence
        self.support = support
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("DBpedia Spotlight client initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def extract_entities(self, text: str, use_cache: bool = True) -> List[Entity]:
        """
        Extract and disambiguate entities from text.

        Args:
            text: Input text
            use_cache: Use cache

        Returns:
            List of Entity objects
        """
        if not self.session:
            await self.initialize()

        # Check cache
        if use_cache:
            cache_key = f"dbpedia_entities:{hash_text(text)}"
            cached = await cache_manager.get(CacheCategory.EXTERNAL_API, cache_key)
            if cached:
                return [Entity(**e) for e in cached]

        try:
            # Call Spotlight API
            params = {
                "text": text,
                "confidence": self.confidence,
                "support": self.support,
            }
            headers = {"Accept": "application/json"}

            async with self.session.get(self.spotlight_endpoint, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    entities = self._parse_spotlight_response(data, text)
                elif response.status == 404:
                    # No entities found
                    entities = []
                else:
                    logger.warning(f"Spotlight API error: {response.status}")
                    entities = []

            # Cache result
            if use_cache:
                cache_key = f"dbpedia_entities:{hash_text(text)}"
                await cache_manager.set(
                    CacheCategory.EXTERNAL_API,
                    cache_key,
                    [e.model_dump() for e in entities],
                    ttl_override=3600,
                )

            logger.info(f"Extracted {len(entities)} entities from DBpedia Spotlight")
            return entities

        except asyncio.TimeoutError:
            logger.error("DBpedia Spotlight timeout")
            return []
        except Exception as e:
            logger.error(f"DBpedia Spotlight error: {e}", exc_info=True)
            return []

    @staticmethod
    def _parse_spotlight_response(data: Dict[str, Any], text: str) -> List[Entity]:
        """Parse Spotlight API response."""
        entities = []

        resources = data.get("Resources", [])

        for resource in resources:
            uri = resource.get("@URI", "")
            surface_form = resource.get("@surfaceForm", "")
            types = resource.get("@types", "").split(",")
            offset = int(resource.get("@offset", 0))
            similarity_score = float(resource.get("@similarityScore", 0.0))
            support = int(resource.get("@support", 0))

            # Map DBpedia types to EntityType
            entity_type = DBpediaSpotlightClient._map_dbpedia_type(types)

            entity = Entity(
                text=surface_form,
                entity_type=entity_type,
                uri=uri,
                confidence=similarity_score,
                start_char=offset,
                end_char=offset + len(surface_form),
                metadata={"dbpedia_types": types, "support": support},
            )
            entities.append(entity)

        return entities

    @staticmethod
    def _map_dbpedia_type(types: List[str]) -> EntityType:
        """Map DBpedia ontology types to EntityType enum."""
        type_str = ",".join(types).lower()

        if "person" in type_str or "agent" in type_str:
            return EntityType.PERSON
        elif "organisation" in type_str or "organization" in type_str or "company" in type_str:
            return EntityType.ORGANIZATION
        elif "place" in type_str or "location" in type_str:
            return EntityType.LOCATION
        elif "event" in type_str:
            return EntityType.EVENT
        elif "work" in type_str or "creativework" in type_str:
            return EntityType.WORK
        else:
            return EntityType.OTHER


class DBpediaSPARQLClient:
    """
    DBpedia SPARQL endpoint client.

    Queries DBpedia knowledge graph for fact verification.
    """

    def __init__(self, sparql_endpoint: str = "https://dbpedia.org/sparql"):
        """
        Initialize SPARQL client.

        Args:
            sparql_endpoint: SPARQL endpoint URL
        """
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(30)

    async def query(self, sparql_query: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Execute SPARQL query.

        Args:
            sparql_query: SPARQL query string
            use_cache: Use cache

        Returns:
            List of result bindings
        """
        # Check cache
        if use_cache:
            cache_key = f"dbpedia_sparql:{hash_text(sparql_query)}"
            cached = await cache_manager.get(CacheCategory.EXTERNAL_API, cache_key)
            if cached:
                return cached

        try:
            # Execute query in thread pool (SPARQLWrapper is synchronous)
            loop = asyncio.get_event_loop()
            self.sparql.setQuery(sparql_query)
            results = await loop.run_in_executor(None, self.sparql.query)
            results_dict = results.convert()

            bindings = results_dict.get("results", {}).get("bindings", [])

            # Cache result
            if use_cache:
                cache_key = f"dbpedia_sparql:{hash_text(sparql_query)}"
                await cache_manager.set(CacheCategory.EXTERNAL_API, cache_key, bindings, ttl_override=3600)

            logger.info(f"SPARQL query returned {len(bindings)} results")
            return bindings

        except Exception as e:
            logger.error(f"SPARQL query error: {e}", exc_info=True)
            return []

    async def get_entity_properties(self, entity_uri: str) -> Dict[str, List[str]]:
        """
        Get all properties for an entity.

        Args:
            entity_uri: DBpedia resource URI

        Returns:
            Dict mapping property URIs to values
        """
        query = f"""
        SELECT ?property ?value
        WHERE {{
            <{entity_uri}> ?property ?value .
        }}
        LIMIT 100
        """

        results = await self.query(query)

        properties = {}
        for binding in results:
            prop = binding.get("property", {}).get("value", "")
            val = binding.get("value", {}).get("value", "")

            if prop not in properties:
                properties[prop] = []
            properties[prop].append(val)

        return properties

    async def get_entity_abstract(self, entity_uri: str, language: str = "pt") -> Optional[str]:
        """
        Get entity abstract (summary).

        Args:
            entity_uri: DBpedia resource URI
            language: Language code (en, pt, etc.)

        Returns:
            Abstract text or None
        """
        query = f"""
        SELECT ?abstract
        WHERE {{
            <{entity_uri}> dbo:abstract ?abstract .
            FILTER (lang(?abstract) = "{language}")
        }}
        LIMIT 1
        """

        results = await self.query(query)

        if results:
            return results[0].get("abstract", {}).get("value")
        return None

    async def verify_relationship(self, subject_uri: str, predicate_uri: str, object_uri: str) -> bool:
        """
        Verify if relationship exists in DBpedia.

        Args:
            subject_uri: Subject entity URI
            predicate_uri: Predicate/property URI
            object_uri: Object entity URI

        Returns:
            True if relationship exists
        """
        query = f"""
        ASK {{
            <{subject_uri}> <{predicate_uri}> <{object_uri}> .
        }}
        """

        self.sparql.setQuery(query)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self.sparql.query)
        results_dict = results.convert()

        return results_dict.get("boolean", False)

    async def get_entity_type(self, entity_uri: str) -> List[str]:
        """
        Get RDF types for entity.

        Args:
            entity_uri: DBpedia resource URI

        Returns:
            List of type URIs
        """
        query = f"""
        SELECT ?type
        WHERE {{
            <{entity_uri}> rdf:type ?type .
        }}
        """

        results = await self.query(query)
        types = [r.get("type", {}).get("value", "") for r in results]
        return types

    async def find_related_entities(self, entity_uri: str, max_results: int = 10) -> List[Tuple[str, str, str]]:
        """
        Find entities related to given entity.

        Args:
            entity_uri: DBpedia resource URI
            max_results: Maximum results

        Returns:
            List of (predicate, related_entity_uri, label) tuples
        """
        query = f"""
        SELECT ?predicate ?related ?label
        WHERE {{
            <{entity_uri}> ?predicate ?related .
            FILTER (isURI(?related))
            OPTIONAL {{ ?related rdfs:label ?label . FILTER (lang(?label) = "en") }}
        }}
        LIMIT {max_results}
        """

        results = await self.query(query)

        related = []
        for binding in results:
            predicate = binding.get("predicate", {}).get("value", "")
            related_uri = binding.get("related", {}).get("value", "")
            label = binding.get("label", {}).get("value", related_uri)

            related.append((predicate, related_uri, label))

        return related

    async def get_temporal_facts(self, entity_uri: str) -> List[Dict[str, Any]]:
        """
        Get temporal facts about entity (birth/death dates, founding dates, etc.).

        Args:
            entity_uri: DBpedia resource URI

        Returns:
            List of temporal facts
        """
        query = f"""
        SELECT ?property ?date
        WHERE {{
            <{entity_uri}> ?property ?date .
            FILTER (
                ?property IN (
                    dbo:birthDate, dbo:deathDate,
                    dbo:foundingDate, dbo:dissolutionDate,
                    dbo:activeYearsStartYear, dbo:activeYearsEndYear,
                    dbo:releaseDate
                )
            )
        }}
        """

        results = await self.query(query)

        facts = []
        for binding in results:
            prop = binding.get("property", {}).get("value", "")
            date = binding.get("date", {}).get("value", "")

            facts.append(
                {"property": prop.split("/")[-1], "date": date}  # Extract property name
            )

        return facts


class DBpediaClient:
    """
    Unified DBpedia client combining Spotlight and SPARQL.
    """

    def __init__(self):
        """Initialize unified client."""
        self.spotlight = DBpediaSpotlightClient()
        self.sparql = DBpediaSPARQLClient()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize clients."""
        if self._initialized:
            return

        await self.spotlight.initialize()
        self._initialized = True
        logger.info("✅ DBpedia client initialized")

    async def close(self) -> None:
        """Close clients."""
        await self.spotlight.close()
        self._initialized = False

    async def extract_and_enrich_entities(self, text: str, include_abstracts: bool = False) -> List[Entity]:
        """
        Extract entities and enrich with DBpedia data.

        Args:
            text: Input text
            include_abstracts: Fetch entity abstracts

        Returns:
            List of enriched Entity objects
        """
        # Extract entities
        entities = await self.spotlight.extract_entities(text)

        # Enrich with DBpedia data
        for entity in entities:
            # Get types
            types = await self.sparql.get_entity_type(entity.uri)
            entity.metadata["rdf_types"] = types

            # Get abstract (optional)
            if include_abstracts:
                abstract = await self.sparql.get_entity_abstract(entity.uri, language="pt")
                if abstract:
                    entity.metadata["abstract"] = abstract

        return entities

    async def verify_fact(self, subject: str, predicate: str, object: str) -> Dict[str, Any]:
        """
        Verify factual statement against DBpedia.

        Args:
            subject: Subject entity (text or URI)
            predicate: Relationship/property
            object: Object entity (text or URI)

        Returns:
            Verification result dict
        """
        # If subject/object are text, try to resolve to URIs
        subject_uri = subject if subject.startswith("http") else f"http://dbpedia.org/resource/{quote(subject)}"
        object_uri = object if object.startswith("http") else f"http://dbpedia.org/resource/{quote(object)}"
        predicate_uri = predicate if predicate.startswith("http") else f"http://dbpedia.org/property/{quote(predicate)}"

        # Check relationship
        exists = await self.sparql.verify_relationship(
            subject_uri=subject_uri, predicate_uri=predicate_uri, object_uri=object_uri
        )

        # Get subject properties for additional context
        subject_props = await self.sparql.get_entity_properties(subject_uri)

        return {
            "verified": exists,
            "subject_uri": subject_uri,
            "predicate_uri": predicate_uri,
            "object_uri": object_uri,
            "subject_properties": subject_props,
        }

    async def check_temporal_consistency(
        self, entity_uri: str, claimed_date: str, event_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Check if claimed date is consistent with DBpedia temporal facts.

        Args:
            entity_uri: Entity URI
            claimed_date: Claimed date (ISO format or year)
            event_type: Event type (birth, death, founding, etc.)

        Returns:
            Consistency check result
        """
        temporal_facts = await self.sparql.get_temporal_facts(entity_uri)

        # Parse claimed date (simplified)
        try:
            claimed_year = int(claimed_date[:4])
        except (ValueError, IndexError):
            return {"consistent": None, "error": "Invalid date format"}

        # Check against temporal facts
        for fact in temporal_facts:
            fact_date = fact.get("date", "")
            try:
                fact_year = int(fact_date[:4])
            except (ValueError, IndexError):
                continue

            # Check consistency based on event type
            if event_type == "birth" and "birth" in fact["property"].lower():
                consistent = abs(fact_year - claimed_year) <= 1  # Allow 1 year tolerance
                return {
                    "consistent": consistent,
                    "dbpedia_date": fact_date,
                    "claimed_date": claimed_date,
                    "difference_years": abs(fact_year - claimed_year),
                }

        return {"consistent": None, "error": "No temporal facts found in DBpedia"}


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

dbpedia_client = DBpediaClient()
