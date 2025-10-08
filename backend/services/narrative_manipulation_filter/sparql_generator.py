"""
SPARQL Query Generator for Knowledge Graph Verification.

Automatically generates SPARQL queries from natural language claims:
1. Dependency parsing to extract subject-predicate-object
2. Entity linking for subject and object
3. Predicate mapping to Wikidata properties
4. SPARQL query construction
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import spacy
from spacy.tokens import Token

from config import get_settings
from entity_linker import Entity, entity_linker

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class TriplePattern:
    """Subject-Predicate-Object pattern extracted from claim."""

    subject: Optional[Entity]
    """Subject entity"""

    predicate: str
    """Predicate (verb/relation)"""

    predicate_wikidata_property: Optional[str]
    """Wikidata property ID (e.g., wdt:P19)"""

    object: Optional[Entity]
    """Object entity (or literal value)"""

    object_literal: Optional[str]
    """Object literal value (for dates, numbers, etc.)"""

    confidence: float = 0.0
    """Extraction confidence"""


@dataclass
class SPARQLQuery:
    """Generated SPARQL query with metadata."""

    query: str
    """SPARQL query string"""

    triple_pattern: TriplePattern
    """Extracted triple pattern"""

    original_claim: str
    """Original claim text"""

    query_type: str = "ask"
    """Query type: 'ask' (boolean) or 'select' (retrieve values)"""

    expected_result: Optional[Any] = None
    """Expected result for verification"""


class SPARQLQueryGenerator:
    """
    Generates SPARQL queries from natural language claims.

    Pipeline:
    1. Dependency parsing (spaCy) to extract syntactic structure
    2. Entity linking to identify subject and object
    3. Predicate mapping (verb → Wikidata property)
    4. SPARQL query construction
    """

    # Wikidata property mappings (Portuguese verbs → Wikidata properties)
    PROPERTY_MAPPINGS = {
        # Birth/Death
        "nascer": "wdt:P19",  # place of birth
        "nasceu": "wdt:P19",
        "nasce": "wdt:P19",
        "morrer": "wdt:P20",  # place of death
        "morreu": "wdt:P20",
        "morre": "wdt:P20",
        "falecer": "wdt:P20",
        "faleceu": "wdt:P20",
        # Dates
        "nascer_data": "wdt:P569",  # date of birth
        "morrer_data": "wdt:P570",  # date of death
        # Relations
        "casar": "wdt:P26",  # spouse
        "casou": "wdt:P26",
        "esposa": "wdt:P26",
        "esposo": "wdt:P26",
        "filho": "wdt:P40",  # child
        "filha": "wdt:P40",
        "pai": "wdt:P22",  # father
        "mãe": "wdt:P25",  # mother
        # Occupation/Position
        "ser": "wdt:P106",  # occupation
        "é": "wdt:P106",
        "foi": "wdt:P106",
        "trabalhar": "wdt:P106",
        "trabalhou": "wdt:P106",
        "presidente": "wdt:P39",  # position held
        "governador": "wdt:P39",
        "ministro": "wdt:P39",
        # Geographic
        "capital": "wdt:P36",  # capital
        "localizar": "wdt:P131",  # located in
        "localiza": "wdt:P131",
        "situar": "wdt:P131",
        "país": "wdt:P17",  # country
        "continente": "wdt:P30",  # continent
        # Attributes
        "população": "wdt:P1082",  # population
        "área": "wdt:P2046",  # area
        "altura": "wdt:P2048",  # height
        "fundação": "wdt:P571",  # inception
        "fundado": "wdt:P571",
        "fundar": "wdt:P571",
        # Education
        "estudar": "wdt:P69",  # educated at
        "estudou": "wdt:P69",
        "formar": "wdt:P69",
        "formou": "wdt:P69",
        # Authorship
        "escrever": "wdt:P50",  # author
        "escreveu": "wdt:P50",
        "autor": "wdt:P50",
        "criar": "wdt:P170",  # creator
        "criou": "wdt:P170",
        # Awards
        "ganhar": "wdt:P166",  # award received
        "ganhou": "wdt:P166",
        "receber": "wdt:P166",
        "recebeu": "wdt:P166",
        "prêmio": "wdt:P166",
        # Membership
        "membro": "wdt:P463",  # member of
        "pertencer": "wdt:P463",
        "pertence": "wdt:P463",
    }

    # Prepositions that indicate location predicates
    LOCATION_PREPOSITIONS = ["em", "no", "na", "de"]

    def __init__(self):
        """Initialize SPARQL generator."""
        self.nlp: Optional[spacy.language.Language] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize spaCy model and entity linker."""
        if self._initialized:
            return

        # Use entity_linker's spaCy model
        await entity_linker.initialize()
        self.nlp = entity_linker.nlp

        self._initialized = True
        logger.info("✅ SPARQL query generator initialized")

    async def generate_from_claim(self, claim: str, query_type: str = "ask") -> Optional[SPARQLQuery]:
        """
        Generate SPARQL query from natural language claim.

        Args:
            claim: Natural language claim (Portuguese)
            query_type: 'ask' (boolean check) or 'select' (retrieve values)

        Returns:
            SPARQLQuery object or None if extraction fails
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Generating SPARQL from claim: {claim}")

        # STEP 1: Extract triple pattern via dependency parsing
        triple = await self._extract_triple_pattern(claim)

        if not triple or not triple.subject or not triple.predicate_wikidata_property:
            logger.warning("Failed to extract triple pattern from claim")
            return None

        # STEP 2: Generate SPARQL query
        if query_type == "ask":
            query = self._build_ask_query(triple)
        else:
            query = self._build_select_query(triple)

        # STEP 3: Construct SPARQLQuery object
        sparql_query = SPARQLQuery(
            query=query,
            triple_pattern=triple,
            original_claim=claim,
            query_type=query_type,
            expected_result=triple.object,
        )

        logger.info(f"Generated SPARQL query:\n{query}")

        return sparql_query

    async def _extract_triple_pattern(self, claim: str) -> Optional[TriplePattern]:
        """
        Extract subject-predicate-object pattern from claim.

        Uses spaCy dependency parsing to identify:
        - Subject: nsubj dependency
        - Predicate: root verb
        - Object: dobj, attr, or pobj dependency

        Args:
            claim: Natural language claim

        Returns:
            TriplePattern or None
        """
        # Parse with spaCy
        doc = self.nlp(claim)

        # Extract entities from claim
        entities = await entity_linker.extract_and_link(
            text=claim, min_confidence=0.4, use_cache=True, enrich_with_metadata=False
        )

        # Build entity lookup by position
        entity_lookup = {}
        for entity in entities:
            for i in range(entity.start, entity.end):
                entity_lookup[i] = entity

        # Find syntactic elements
        subject_token: Optional[Token] = None
        predicate_token: Optional[Token] = None
        object_token: Optional[Token] = None

        # Find root verb (predicate)
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ in ["VERB", "AUX"]:
                predicate_token = token
                break

        if not predicate_token:
            logger.warning("No root verb found in claim")
            return None

        # Find subject (nominal subject)
        for token in doc:
            if token.dep_ == "nsubj" and token.head == predicate_token:
                subject_token = token
                break

        # Find object (direct object, attribute, or object of preposition)
        for token in doc:
            if token.head == predicate_token:
                if token.dep_ in ["dobj", "attr"]:
                    object_token = token
                    break
                elif token.dep_ == "prep":
                    # Check for prepositional object
                    for child in token.children:
                        if child.dep_ == "pobj":
                            object_token = child
                            break

        # Extract entities for subject and object
        subject_entity = None
        object_entity = None
        object_literal = None

        if subject_token:
            # Find entity covering subject token
            subject_entity = entity_lookup.get(subject_token.idx)

        if object_token:
            # Check if object is an entity
            object_entity = entity_lookup.get(object_token.idx)

            # If not an entity, treat as literal (e.g., date, number)
            if not object_entity:
                object_literal = object_token.text

        # Map predicate to Wikidata property
        predicate_lemma = predicate_token.lemma_.lower()

        # Check for location-based predicates (e.g., "nasceu em X")
        if any(prep in claim.lower() for prep in self.LOCATION_PREPOSITIONS):
            if "nasc" in predicate_lemma:
                predicate_property = "wdt:P19"  # place of birth
            elif "morr" in predicate_lemma or "falec" in predicate_lemma:
                predicate_property = "wdt:P20"  # place of death
            else:
                predicate_property = self.PROPERTY_MAPPINGS.get(predicate_lemma, "wdt:P31")
        else:
            predicate_property = self.PROPERTY_MAPPINGS.get(predicate_lemma, "wdt:P31")

        # Build triple pattern
        triple = TriplePattern(
            subject=subject_entity,
            predicate=predicate_token.text,
            predicate_wikidata_property=predicate_property,
            object=object_entity,
            object_literal=object_literal,
            confidence=min(
                subject_entity.confidence if subject_entity else 0.5,
                object_entity.confidence if object_entity else 0.5,
            ),
        )

        logger.debug(
            f"Triple: {subject_entity.text if subject_entity else '?'} "
            f"→ {predicate_property} → "
            f"{object_entity.text if object_entity else object_literal}"
        )

        return triple

    def _build_ask_query(self, triple: TriplePattern) -> str:
        """
        Build ASK query (boolean verification).

        Format:
        ASK {
            wd:Q76 wdt:P19 wd:Q1552 .
        }

        Args:
            triple: Triple pattern

        Returns:
            SPARQL ASK query
        """
        subject_id = triple.subject.wikidata_id if triple.subject else None
        object_id = triple.object.wikidata_id if triple.object else None

        if not subject_id:
            # Cannot build query without subject
            return ""

        if object_id:
            # Entity object
            query = f"""
ASK {{
    wd:{subject_id} {triple.predicate_wikidata_property} wd:{object_id} .
}}
""".strip()
        elif triple.object_literal:
            # Literal object
            query = f"""
ASK {{
    wd:{subject_id} {triple.predicate_wikidata_property} "{triple.object_literal}" .
}}
""".strip()
        else:
            # No object specified - just check if property exists
            query = f"""
ASK {{
    wd:{subject_id} {triple.predicate_wikidata_property} ?value .
}}
""".strip()

        return query

    def _build_select_query(self, triple: TriplePattern) -> str:
        """
        Build SELECT query (retrieve values).

        Format:
        SELECT ?value WHERE {
            wd:Q76 wdt:P19 ?value .
        }

        Args:
            triple: Triple pattern

        Returns:
            SPARQL SELECT query
        """
        subject_id = triple.subject.wikidata_id if triple.subject else None

        if not subject_id:
            return ""

        # Retrieve values for the property
        query = f"""
SELECT ?value ?valueLabel WHERE {{
    wd:{subject_id} {triple.predicate_wikidata_property} ?value .

    SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "pt,en" .
    }}
}}
LIMIT 10
""".strip()

        return query

    def get_property_label(self, property_id: str) -> str:
        """
        Get human-readable label for Wikidata property.

        Args:
            property_id: Property ID (e.g., "wdt:P19")

        Returns:
            Property label
        """
        # Extract P-ID
        p_id = property_id.replace("wdt:", "").replace("wd:", "")

        # Reverse lookup in mappings
        for verb, prop in self.PROPERTY_MAPPINGS.items():
            if prop == f"wdt:{p_id}":
                return verb

        return property_id


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

sparql_generator = SPARQLQueryGenerator()
