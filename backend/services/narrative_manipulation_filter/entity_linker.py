"""
Entity Linker for Knowledge Graph Verification.

Integrates:
- spaCy NER (Portuguese) for entity extraction
- DBpedia Spotlight for entity disambiguation
- Wikidata ID resolution for canonical identifiers
"""

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Set

from cache_manager import cache_manager, CacheCategory
from config import get_settings
from dbpedia_client import dbpedia_client
import spacy
from spacy.language import Language
from utils import hash_text
from wikidata_client import wikidata_client

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class Entity:
    """Linked entity with canonical identifiers."""

    text: str
    """Original text mention"""

    label: str
    """Entity type (PERSON, ORG, LOC, etc.)"""

    start: int
    """Start character position"""

    end: int
    """End character position"""

    dbpedia_uri: Optional[str] = None
    """DBpedia resource URI"""

    wikidata_id: Optional[str] = None
    """Wikidata Q-ID"""

    confidence: float = 0.0
    """Disambiguation confidence (0-1)"""

    description: Optional[str] = None
    """Entity description from Wikidata"""

    aliases: List[str] = None
    """Alternative names/labels"""

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.aliases is None:
            self.aliases = []


class EntityLinker:
    """
    Entity linking pipeline: NER → Disambiguation → ID Resolution.

    Pipeline:
    1. spaCy NER extracts entity mentions
    2. DBpedia Spotlight disambiguates mentions to DBpedia URIs
    3. Resolve DBpedia URIs to Wikidata IDs via owl:sameAs
    4. Enrich with Wikidata metadata (description, aliases)
    """

    def __init__(self):
        """Initialize entity linker."""
        self.nlp: Optional[Language] = None
        self._initialized = False

        # Entity type mapping (spaCy → Wikidata)
        self.entity_type_map = {
            "PER": "Q5",  # Human
            "PERSON": "Q5",
            "ORG": "Q43229",  # Organization
            "LOC": "Q17334923",  # Location
            "GPE": "Q6256",  # Country
            "DATE": "Q573",  # Date
            "EVENT": "Q1656682",  # Event
        }

    async def initialize(self) -> None:
        """Load spaCy Portuguese model."""
        if self._initialized:
            logger.warning("Entity linker already initialized")
            return

        try:
            logger.info("🚀 Loading spaCy Portuguese NER model...")

            # Load Portuguese model (pt_core_news_lg)
            # Note: Run `python -m spacy download pt_core_news_lg` first
            try:
                self.nlp = spacy.load("pt_core_news_lg")
            except OSError:
                logger.warning("pt_core_news_lg not found, trying pt_core_news_sm...")
                try:
                    self.nlp = spacy.load("pt_core_news_sm")
                except OSError:
                    logger.error(
                        "No Portuguese spaCy model found. Please install: python -m spacy download pt_core_news_lg"
                    )
                    raise

            # Optimize pipeline (disable unnecessary components)
            disabled = ["lemmatizer", "textcat"]
            for component in disabled:
                if self.nlp.has_pipe(component):
                    self.nlp.disable_pipe(component)

            logger.info(f"✅ spaCy model loaded: {self.nlp.meta['name']}")

            # Initialize external clients
            await dbpedia_client.initialize()
            await wikidata_client.initialize()

            self._initialized = True
            logger.info("✅ Entity linker initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize entity linker: {e}", exc_info=True)
            raise

    async def extract_and_link(
        self,
        text: str,
        min_confidence: float = 0.5,
        use_cache: bool = True,
        enrich_with_metadata: bool = True,
    ) -> List[Entity]:
        """
        Extract and link entities from text.

        Args:
            text: Input text
            min_confidence: Minimum disambiguation confidence
            use_cache: Whether to use cache
            enrich_with_metadata: Fetch Wikidata descriptions/aliases

        Returns:
            List of linked entities
        """
        if not self._initialized:
            await self.initialize()

        # Check cache
        if use_cache:
            cache_key = f"entities:{hash_text(text)}"
            cached = await cache_manager.get(CacheCategory.ANALYSIS, cache_key)
            if cached:
                logger.debug("Entity cache hit")
                return [Entity(**e) for e in cached]

        # STEP 1: spaCy NER extraction
        entities = await self._extract_entities_spacy(text)

        if not entities:
            logger.debug("No entities detected by spaCy NER")
            return []

        logger.info(f"Extracted {len(entities)} entities via spaCy NER")

        # STEP 2: DBpedia Spotlight disambiguation (parallel)
        tasks = [self._disambiguate_entity(entity, text) for entity in entities]

        disambiguated = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful disambiguations above confidence threshold
        linked_entities = []
        for entity in disambiguated:
            if isinstance(entity, Exception):
                logger.warning(f"Disambiguation error: {entity}")
                continue

            if entity.confidence >= min_confidence:
                linked_entities.append(entity)

        logger.info(
            f"Linked {len(linked_entities)}/{len(entities)} entities "
            f"(threshold={min_confidence})"
        )

        # STEP 3: Enrich with Wikidata metadata (optional)
        if enrich_with_metadata and linked_entities:
            enriched = await self._enrich_entities(linked_entities)
            linked_entities = enriched

        # Cache results for 7 days
        if use_cache and linked_entities:
            cache_key = f"entities:{hash_text(text)}"
            serialized = [
                {
                    "text": e.text,
                    "label": e.label,
                    "start": e.start,
                    "end": e.end,
                    "dbpedia_uri": e.dbpedia_uri,
                    "wikidata_id": e.wikidata_id,
                    "confidence": e.confidence,
                    "description": e.description,
                    "aliases": e.aliases,
                }
                for e in linked_entities
            ]
            await cache_manager.set(CacheCategory.ANALYSIS, cache_key, serialized)

        return linked_entities

    async def _extract_entities_spacy(self, text: str) -> List[Entity]:
        """Extract entity mentions using spaCy NER."""
        # Run NER in thread pool (CPU-bound)
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)

        entities = []

        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.0,  # Will be updated after disambiguation
            )
            entities.append(entity)

        return entities

    async def _disambiguate_entity(self, entity: Entity, full_text: str) -> Entity:
        """
        Disambiguate entity using DBpedia Spotlight.

        Args:
            entity: Entity from spaCy NER
            full_text: Full text context for disambiguation

        Returns:
            Entity with DBpedia URI, Wikidata ID, confidence
        """
        try:
            # DBpedia Spotlight annotation
            annotations = await dbpedia_client.spotlight_annotate(
                text=full_text,
                confidence=0.3,  # Lower threshold, we filter later
                support=20,
            )

            # Find annotation matching our entity
            best_match = None
            best_overlap = 0.0

            for annotation in annotations:
                # Calculate overlap with entity span
                anno_start = annotation.get("offset", 0)
                anno_end = anno_start + len(annotation.get("surfaceForm", ""))

                overlap_start = max(entity.start, anno_start)
                overlap_end = min(entity.end, anno_end)
                overlap_length = max(0, overlap_end - overlap_start)

                entity_length = entity.end - entity.start

                if entity_length > 0:
                    overlap_ratio = overlap_length / entity_length

                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_match = annotation

            if best_match and best_overlap >= 0.5:
                dbpedia_uri = best_match.get("URI", "")
                confidence = float(best_match.get("similarityScore", 0))

                # Resolve to Wikidata ID
                wikidata_id = await self._resolve_wikidata_id(dbpedia_uri)

                entity.dbpedia_uri = dbpedia_uri
                entity.wikidata_id = wikidata_id
                entity.confidence = confidence

                logger.debug(
                    f"Linked '{entity.text}' → {wikidata_id} "
                    f"(confidence={confidence:.3f})"
                )
            else:
                # Fallback: search Wikidata directly
                wikidata_id = await self._search_wikidata(entity.text, entity.label)

                if wikidata_id:
                    entity.wikidata_id = wikidata_id
                    entity.confidence = 0.6  # Lower confidence for search-based
                    logger.debug(
                        f"Linked '{entity.text}' → {wikidata_id} via Wikidata search"
                    )

        except Exception as e:
            logger.warning(f"Disambiguation failed for '{entity.text}': {e}")

        return entity

    async def _resolve_wikidata_id(self, dbpedia_uri: str) -> Optional[str]:
        """
        Resolve DBpedia URI to Wikidata ID.

        Uses owl:sameAs property in DBpedia SPARQL endpoint.

        Args:
            dbpedia_uri: DBpedia resource URI

        Returns:
            Wikidata Q-ID or None
        """
        if not dbpedia_uri:
            return None

        try:
            # Query DBpedia for owl:sameAs links
            query = f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>

            SELECT ?wikidata WHERE {{
                <{dbpedia_uri}> owl:sameAs ?wikidata .
                FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
            }}
            LIMIT 1
            """

            results = await dbpedia_client.sparql_query(query)

            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                wikidata_uri = bindings[0].get("wikidata", {}).get("value", "")
                # Extract Q-ID from URI
                if "/entity/Q" in wikidata_uri:
                    wikidata_id = wikidata_uri.split("/entity/")[-1]
                    return wikidata_id

            return None

        except Exception as e:
            logger.warning(f"Wikidata ID resolution failed for {dbpedia_uri}: {e}")
            return None

    async def _search_wikidata(
        self, entity_text: str, entity_type: str
    ) -> Optional[str]:
        """
        Search Wikidata for entity (fallback when Spotlight fails).

        Args:
            entity_text: Entity mention text
            entity_type: Entity type label

        Returns:
            Wikidata Q-ID or None
        """
        try:
            results = await wikidata_client.search(
                query=entity_text, language="pt", limit=5
            )

            if not results:
                return None

            # Get best match (first result)
            best = results[0]

            return best.get("id")

        except Exception as e:
            logger.warning(f"Wikidata search failed for '{entity_text}': {e}")
            return None

    async def _enrich_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Enrich entities with Wikidata metadata.

        Fetches:
        - rdfs:label (description)
        - skos:altLabel (aliases)

        Args:
            entities: List of entities with Wikidata IDs

        Returns:
            Enriched entities
        """
        tasks = []

        for entity in entities:
            if entity.wikidata_id:
                tasks.append(self._fetch_wikidata_metadata(entity))
            else:
                tasks.append(asyncio.sleep(0, result=entity))

        enriched = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter exceptions
        result = []
        for entity in enriched:
            if isinstance(entity, Exception):
                logger.warning(f"Metadata fetch error: {entity}")
                continue
            result.append(entity)

        return result

    async def _fetch_wikidata_metadata(self, entity: Entity) -> Entity:
        """Fetch description and aliases from Wikidata."""
        if not entity.wikidata_id:
            return entity

        try:
            # SPARQL query for label and aliases
            query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?label (GROUP_CONCAT(DISTINCT ?alias; separator="|") AS ?aliases) WHERE {{
                OPTIONAL {{ wd:{entity.wikidata_id} rdfs:label ?label . FILTER(LANG(?label) = "pt") }}
                OPTIONAL {{ wd:{entity.wikidata_id} skos:altLabel ?alias . FILTER(LANG(?alias) = "pt") }}
            }}
            GROUP BY ?label
            LIMIT 1
            """

            results = await wikidata_client.sparql_query(query)

            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                binding = bindings[0]

                label = binding.get("label", {}).get("value")
                if label:
                    entity.description = label

                aliases_str = binding.get("aliases", {}).get("value", "")
                if aliases_str:
                    entity.aliases = [
                        a.strip() for a in aliases_str.split("|") if a.strip()
                    ]

        except Exception as e:
            logger.warning(f"Metadata fetch failed for {entity.wikidata_id}: {e}")

        return entity

    def get_entities_by_type(
        self, entities: List[Entity], entity_types: List[str]
    ) -> List[Entity]:
        """
        Filter entities by type.

        Args:
            entities: List of entities
            entity_types: List of entity type labels (e.g., ["PERSON", "ORG"])

        Returns:
            Filtered entities
        """
        return [e for e in entities if e.label in entity_types]

    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Remove duplicate entities based on Wikidata ID.

        Args:
            entities: List of entities (may contain duplicates)

        Returns:
            Deduplicated entities
        """
        seen: Set[str] = set()
        unique = []

        for entity in entities:
            key = entity.wikidata_id or f"{entity.text}_{entity.start}"

            if key not in seen:
                seen.add(key)
                unique.append(entity)

        return unique


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

entity_linker = EntityLinker()
