"""
Wikidata Client for Cognitive Defense System.

Integrates Wikidata knowledge graph for fact verification:
1. Entity search and resolution
2. SPARQL queries for claims and statements
3. Temporal fact verification with qualifiers
4. Cross-referencing with external databases
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from SPARQLWrapper import JSON, SPARQLWrapper

from cache_manager import CacheCategory, cache_manager
from config import get_settings
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class WikidataSearchClient:
    """
    Wikidata search API client.

    Searches and resolves entities to Wikidata QIDs.
    """

    def __init__(self, search_endpoint: str = "https://www.wikidata.org/w/api.php"):
        """
        Initialize Wikidata search client.

        Args:
            search_endpoint: Wikidata API endpoint
        """
        self.search_endpoint = search_endpoint
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Wikidata search client initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def search_entity(
        self, query: str, language: str = "pt", limit: int = 5, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in Wikidata.

        Args:
            query: Search query
            language: Language code
            limit: Maximum results
            use_cache: Use cache

        Returns:
            List of entity candidates
        """
        if not self.session:
            await self.initialize()

        # Check cache
        if use_cache:
            cache_key = f"wikidata_search:{hash_text(query)}:{language}"
            cached = await cache_manager.get(CacheCategory.EXTERNAL_API, cache_key)
            if cached:
                return cached

        try:
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": language,
                "search": query,
                "limit": limit,
            }

            async with self.session.get(self.search_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("search", [])
                else:
                    logger.warning(f"Wikidata search error: {response.status}")
                    results = []

            # Cache result
            if use_cache:
                cache_key = f"wikidata_search:{hash_text(query)}:{language}"
                await cache_manager.set(CacheCategory.EXTERNAL_API, cache_key, results, ttl_override=3600)

            logger.info(f"Found {len(results)} Wikidata entities for '{query}'")
            return results

        except asyncio.TimeoutError:
            logger.error("Wikidata search timeout")
            return []
        except Exception as e:
            logger.error(f"Wikidata search error: {e}", exc_info=True)
            return []

    async def get_entity_by_id(
        self, entity_id: str, language: str = "pt", use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get entity data by Wikidata ID.

        Args:
            entity_id: Wikidata entity ID (e.g., Q42)
            language: Language code
            use_cache: Use cache

        Returns:
            Entity data dict or None
        """
        if not self.session:
            await self.initialize()

        # Check cache
        if use_cache:
            cache_key = f"wikidata_entity:{entity_id}:{language}"
            cached = await cache_manager.get(CacheCategory.EXTERNAL_API, cache_key)
            if cached:
                return cached

        try:
            params = {
                "action": "wbgetentities",
                "format": "json",
                "ids": entity_id,
                "languages": language,
            }

            async with self.session.get(self.search_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    entity_data = data.get("entities", {}).get(entity_id, {})
                else:
                    logger.warning(f"Wikidata get entity error: {response.status}")
                    entity_data = None

            # Cache result
            if use_cache and entity_data:
                cache_key = f"wikidata_entity:{entity_id}:{language}"
                await cache_manager.set(
                    CacheCategory.EXTERNAL_API,
                    cache_key,
                    entity_data,
                    ttl_override=3600,
                )

            return entity_data

        except asyncio.TimeoutError:
            logger.error("Wikidata get entity timeout")
            return None
        except Exception as e:
            logger.error(f"Wikidata get entity error: {e}", exc_info=True)
            return None


class WikidataSPARQLClient:
    """
    Wikidata SPARQL endpoint client.

    Queries Wikidata knowledge graph using SPARQL.
    """

    def __init__(self, sparql_endpoint: str = "https://query.wikidata.org/sparql"):
        """
        Initialize SPARQL client.

        Args:
            sparql_endpoint: SPARQL endpoint URL
        """
        self.sparql_endpoint = sparql_endpoint
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(30)
        # Set user agent (required by Wikidata)
        self.sparql.addCustomHttpHeader("User-Agent", "VerticeCognitiveDefense/2.0")

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
            cache_key = f"wikidata_sparql:{hash_text(sparql_query)}"
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
                cache_key = f"wikidata_sparql:{hash_text(sparql_query)}"
                await cache_manager.set(CacheCategory.EXTERNAL_API, cache_key, bindings, ttl_override=3600)

            logger.info(f"Wikidata SPARQL query returned {len(bindings)} results")
            return bindings

        except Exception as e:
            logger.error(f"Wikidata SPARQL query error: {e}", exc_info=True)
            return []

    async def get_entity_claims(self, entity_id: str, property_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get claims/statements for an entity.

        Args:
            entity_id: Wikidata entity ID (e.g., Q42)
            property_id: Optional property ID to filter (e.g., P31 for instance of)

        Returns:
            List of claims
        """
        if property_id:
            query = f"""
            SELECT ?property ?value ?valueLabel
            WHERE {{
                wd:{entity_id} wdt:{property_id} ?value .
                BIND(wdt:{property_id} AS ?property)
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
            }}
            LIMIT 100
            """
        else:
            query = f"""
            SELECT ?property ?propertyLabel ?value ?valueLabel
            WHERE {{
                wd:{entity_id} ?property ?value .
                ?prop wikibase:directClaim ?property .
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
            }}
            LIMIT 100
            """

        results = await self.query(query)
        return results

    async def verify_claim(self, entity_id: str, property_id: str, expected_value: str) -> Dict[str, Any]:
        """
        Verify if entity has specific claim.

        Args:
            entity_id: Wikidata entity ID
            property_id: Property ID (e.g., P31)
            expected_value: Expected value (entity ID or literal)

        Returns:
            Verification result
        """
        query = f"""
        ASK {{
            wd:{entity_id} wdt:{property_id} wd:{expected_value} .
        }}
        """

        self.sparql.setQuery(query)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self.sparql.query)
        results_dict = results.convert()

        verified = results_dict.get("boolean", False)

        # Get actual values for context
        actual_values_query = f"""
        SELECT ?value ?valueLabel
        WHERE {{
            wd:{entity_id} wdt:{property_id} ?value .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
        }}
        """

        actual_values = await self.query(actual_values_query)

        return {
            "verified": verified,
            "entity_id": entity_id,
            "property_id": property_id,
            "expected_value": expected_value,
            "actual_values": [v.get("valueLabel", {}).get("value", "") for v in actual_values],
        }

    async def get_birth_death_dates(self, entity_id: str) -> Dict[str, Optional[str]]:
        """
        Get birth and death dates for person.

        Args:
            entity_id: Wikidata entity ID

        Returns:
            Dict with birth_date and death_date
        """
        query = f"""
        SELECT ?birthDate ?deathDate
        WHERE {{
            OPTIONAL {{ wd:{entity_id} wdt:P569 ?birthDate . }}
            OPTIONAL {{ wd:{entity_id} wdt:P570 ?deathDate . }}
        }}
        LIMIT 1
        """

        results = await self.query(query)

        if results:
            binding = results[0]
            return {
                "birth_date": binding.get("birthDate", {}).get("value"),
                "death_date": binding.get("deathDate", {}).get("value"),
            }

        return {"birth_date": None, "death_date": None}

    async def get_occupation(self, entity_id: str) -> List[str]:
        """
        Get occupations for person/organization.

        Args:
            entity_id: Wikidata entity ID

        Returns:
            List of occupation labels
        """
        query = f"""
        SELECT ?occupationLabel
        WHERE {{
            wd:{entity_id} wdt:P106 ?occupation .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
        }}
        """

        results = await self.query(query)
        occupations = [r.get("occupationLabel", {}).get("value", "") for r in results]

        return occupations

    async def get_instance_of(self, entity_id: str) -> List[str]:
        """
        Get 'instance of' (P31) types for entity.

        Args:
            entity_id: Wikidata entity ID

        Returns:
            List of type labels
        """
        query = f"""
        SELECT ?typeLabel
        WHERE {{
            wd:{entity_id} wdt:P31 ?type .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
        }}
        """

        results = await self.query(query)
        types = [r.get("typeLabel", {}).get("value", "") for r in results]

        return types

    async def check_temporal_overlap(self, entity1_id: str, entity2_id: str) -> Dict[str, Any]:
        """
        Check if two entities have temporal overlap (e.g., lived at same time).

        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID

        Returns:
            Temporal overlap analysis
        """
        # Get dates for both entities
        dates1 = await self.get_birth_death_dates(entity1_id)
        dates2 = await self.get_birth_death_dates(entity2_id)

        birth1 = dates1.get("birth_date")
        death1 = dates1.get("death_date")
        birth2 = dates2.get("birth_date")
        death2 = dates2.get("death_date")

        # Simple overlap check (can be enhanced)
        overlap = False
        if birth1 and birth2:
            try:
                year1_birth = int(birth1[:4])
                year1_death = int(death1[:4]) if death1 else 9999
                year2_birth = int(birth2[:4])
                year2_death = int(death2[:4]) if death2 else 9999

                # Check if lifespans overlap
                overlap = not (year1_death < year2_birth or year2_death < year1_birth)

            except (ValueError, IndexError):
                overlap = None

        return {
            "entity1_id": entity1_id,
            "entity2_id": entity2_id,
            "entity1_dates": dates1,
            "entity2_dates": dates2,
            "temporal_overlap": overlap,
        }

    async def find_common_properties(
        self, entity1_id: str, entity2_id: str, max_properties: int = 10
    ) -> List[Dict[str, str]]:
        """
        Find common properties between two entities.

        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID
            max_properties: Maximum properties to return

        Returns:
            List of common properties
        """
        query = f"""
        SELECT ?property ?propertyLabel ?value1Label ?value2Label
        WHERE {{
            wd:{entity1_id} ?property ?value1 .
            wd:{entity2_id} ?property ?value2 .
            ?prop wikibase:directClaim ?property .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,pt". }}
        }}
        LIMIT {max_properties}
        """

        results = await self.query(query)

        common_props = []
        for r in results:
            common_props.append(
                {
                    "property": r.get("propertyLabel", {}).get("value", ""),
                    "entity1_value": r.get("value1Label", {}).get("value", ""),
                    "entity2_value": r.get("value2Label", {}).get("value", ""),
                }
            )

        return common_props


class WikidataClient:
    """
    Unified Wikidata client combining search and SPARQL.
    """

    def __init__(self):
        """Initialize unified client."""
        self.search = WikidataSearchClient()
        self.sparql = WikidataSPARQLClient()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize clients."""
        if self._initialized:
            return

        await self.search.initialize()
        self._initialized = True
        logger.info("✅ Wikidata client initialized")

    async def close(self) -> None:
        """Close clients."""
        await self.search.close()
        self._initialized = False

    async def resolve_entity(self, entity_text: str, language: str = "pt") -> Optional[str]:
        """
        Resolve entity text to Wikidata ID.

        Args:
            entity_text: Entity text
            language: Language code

        Returns:
            Wikidata entity ID (e.g., Q42) or None
        """
        results = await self.search.search_entity(query=entity_text, language=language, limit=1)

        if results:
            return results[0].get("id")
        return None

    async def get_entity_summary(self, entity_id: str, language: str = "pt") -> Dict[str, Any]:
        """
        Get comprehensive entity summary.

        Args:
            entity_id: Wikidata entity ID
            language: Language code

        Returns:
            Entity summary dict
        """
        # Get entity data
        entity_data = await self.search.get_entity_by_id(entity_id, language)

        if not entity_data:
            return {}

        # Get labels and descriptions
        labels = entity_data.get("labels", {})
        descriptions = entity_data.get("descriptions", {})

        label = labels.get(language, {}).get("value", "")
        description = descriptions.get(language, {}).get("value", "")

        # Get types
        types = await self.sparql.get_instance_of(entity_id)

        # Get additional info based on type
        additional_info = {}

        if "human" in " ".join(types).lower() or "person" in " ".join(types).lower():
            dates = await self.sparql.get_birth_death_dates(entity_id)
            occupations = await self.sparql.get_occupation(entity_id)
            additional_info["birth_date"] = dates.get("birth_date")
            additional_info["death_date"] = dates.get("death_date")
            additional_info["occupations"] = occupations

        return {
            "entity_id": entity_id,
            "label": label,
            "description": description,
            "types": types,
            "additional_info": additional_info,
        }

    async def verify_factual_statement(
        self, subject: str, predicate: str, object_value: str, language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Verify factual statement.

        Args:
            subject: Subject entity (text)
            predicate: Property (text or P-ID)
            object_value: Expected value (text)
            language: Language code

        Returns:
            Verification result
        """
        # Resolve subject to Wikidata ID
        subject_id = await self.resolve_entity(subject, language)

        if not subject_id:
            return {"verified": False, "error": "Subject entity not found in Wikidata"}

        # Resolve object to Wikidata ID (if applicable)
        object_id = await self.resolve_entity(object_value, language)

        # Get property ID (simplified - in production, use property search)
        # For now, assume predicate is already a P-ID or we have a mapping
        property_id = predicate if predicate.startswith("P") else "P31"  # Default to instance of

        if object_id:
            # Verify entity-to-entity claim
            result = await self.sparql.verify_claim(subject_id, property_id, object_id)
        else:
            # Get all claims for property and check if object_value matches
            claims = await self.sparql.get_entity_claims(subject_id, property_id)
            verified = any(object_value.lower() in str(c).lower() for c in claims)
            result = {
                "verified": verified,
                "entity_id": subject_id,
                "property_id": property_id,
                "expected_value": object_value,
                "actual_values": [str(c) for c in claims[:5]],
            }

        return result


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

wikidata_client = WikidataClient()
