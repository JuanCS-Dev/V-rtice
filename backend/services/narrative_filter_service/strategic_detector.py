"""Strategic Pattern Detector - Camada 2 do Filtro de Narrativas.

Responsável por:
- Detectar padrões estratégicos em comunicações de agentes (ALLIANCE, DECEPTION, INCONSISTENCY, COLLUSION)
- Construir grafo de alianças (NetworkX)
- Calcular mutual information entre agentes
- Scoring de deception e inconsistency
"""

from collections import defaultdict
from datetime import datetime, timedelta

import networkx as nx
from scipy.stats import entropy

from config import settings
from models import Alliance, PatternType, SemanticRepresentation, StrategicPattern


class StrategicPatternDetector:
    """Detector de padrões estratégicos usando Game Theory."""

    def __init__(self) -> None:
        """Initialize strategic pattern detector."""
        self.alliance_graph = nx.Graph()
        self.interaction_history: dict[tuple[str, str], list[datetime]] = defaultdict(list)

    def detect_alliance(
        self, agent_a: str, agent_b: str, recent_interactions: list[SemanticRepresentation]
    ) -> Alliance | None:
        """Detect alliance between two agents.

        Args:
            agent_a: First agent ID
            agent_b: Second agent ID
            recent_interactions: Recent semantic representations

        Returns:
            Alliance object if detected, None otherwise
        """
        # Filter interactions between these two agents
        pair_interactions = [
            rep
            for rep in recent_interactions
            if rep.source_agent_id in [agent_a, agent_b]
            and any(other_agent in rep.raw_content.lower() for other_agent in [agent_a.lower(), agent_b.lower()])
        ]

        if len(pair_interactions) < 3:
            return None

        # Calculate cooperative intent ratio
        cooperative_count = sum(1 for rep in pair_interactions if rep.intent_classification.value == "COOPERATIVE")
        strength = cooperative_count / len(pair_interactions)

        if strength >= settings.alliance_threshold:
            # Update graph
            if self.alliance_graph.has_edge(agent_a, agent_b):
                self.alliance_graph[agent_a][agent_b]["weight"] = strength
            else:
                self.alliance_graph.add_edge(agent_a, agent_b, weight=strength)

            return Alliance(
                agent_a=agent_a,
                agent_b=agent_b,
                strength=strength,
                interaction_count=len(pair_interactions),
                status="ACTIVE",
            )

        return None

    def calculate_mutual_information(
        self, agent_a: str, agent_b: str, interactions: list[SemanticRepresentation]
    ) -> float:
        """Calculate mutual information between two agents.

        Args:
            agent_a: First agent ID
            agent_b: Second agent ID
            interactions: All semantic representations

        Returns:
            Mutual information score (0.0 to 1.0)
        """
        # Get messages from each agent
        a_messages = [rep for rep in interactions if rep.source_agent_id == agent_a]
        b_messages = [rep for rep in interactions if rep.source_agent_id == agent_b]

        if not a_messages or not b_messages:
            return 0.0

        # Calculate intent distributions
        a_intents = [rep.intent_classification.value for rep in a_messages]
        b_intents = [rep.intent_classification.value for rep in b_messages]

        # Create probability distributions
        intent_types = ["COOPERATIVE", "COMPETITIVE", "NEUTRAL", "AMBIGUOUS"]
        a_dist = [a_intents.count(intent) / len(a_intents) for intent in intent_types]
        b_dist = [b_intents.count(intent) / len(b_intents) for intent in intent_types]

        # Avoid division by zero
        a_dist = [max(p, 1e-10) for p in a_dist]
        b_dist = [max(p, 1e-10) for p in b_dist]

        # Calculate KL divergence as proxy for mutual information
        kl_div = entropy(a_dist, b_dist)

        # Normalize to 0-1 range (lower KL = higher MI)
        normalized_mi = 1.0 / (1.0 + kl_div)

        return float(min(normalized_mi, 1.0))

    def detect_deception(self, agent_id: str, interactions: list[SemanticRepresentation]) -> float:
        """Calculate deception score for an agent.

        Args:
            agent_id: Agent ID to analyze
            interactions: Recent semantic representations

        Returns:
            Deception score (0.0 to 1.0)
        """
        agent_messages = [rep for rep in interactions if rep.source_agent_id == agent_id]

        if len(agent_messages) < 2:
            return 0.0

        # Deception indicators:
        # 1. High variation in intent classification
        intents = [rep.intent_classification.value for rep in agent_messages]
        unique_intents = len(set(intents))
        intent_variation = unique_intents / 4.0  # 4 possible intents

        # 2. Low average confidence
        avg_confidence = sum(rep.intent_confidence for rep in agent_messages) / len(agent_messages)
        confidence_indicator = 1.0 - avg_confidence

        # 3. Rapid switches between cooperative and competitive
        switches = sum(
            1
            for i in range(len(intents) - 1)
            if (intents[i] == "COOPERATIVE" and intents[i + 1] == "COMPETITIVE")
            or (intents[i] == "COMPETITIVE" and intents[i + 1] == "COOPERATIVE")
        )
        switch_rate = min(switches / max(len(intents) - 1, 1), 1.0)

        # Weighted deception score
        deception_score = (intent_variation * 0.3 + confidence_indicator * 0.4 + switch_rate * 0.3)

        return min(deception_score, 1.0)

    def detect_inconsistency(
        self, agent_id: str, interactions: list[SemanticRepresentation], time_window_hours: int = 24
    ) -> float:
        """Calculate inconsistency score for an agent.

        Args:
            agent_id: Agent ID to analyze
            interactions: Semantic representations
            time_window_hours: Time window to analyze

        Returns:
            Inconsistency score (0.0 to 1.0)
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_messages = [
            rep for rep in interactions if rep.source_agent_id == agent_id and rep.timestamp >= cutoff_time
        ]

        if len(recent_messages) < 3:
            return 0.0

        # Check for contradictory statements
        cooperative_messages = [rep for rep in recent_messages if rep.intent_classification.value == "COOPERATIVE"]
        competitive_messages = [rep for rep in recent_messages if rep.intent_classification.value == "COMPETITIVE"]

        if not cooperative_messages or not competitive_messages:
            return 0.0

        # Inconsistency = having both strong cooperative and competitive signals
        coop_ratio = len(cooperative_messages) / len(recent_messages)
        comp_ratio = len(competitive_messages) / len(recent_messages)

        # High inconsistency when both ratios are significant (not clearly one or the other)
        inconsistency = min(coop_ratio, comp_ratio) * 2.0

        return min(inconsistency, 1.0)

    async def detect_patterns(
        self, interactions: list[SemanticRepresentation], time_window_hours: int = 24
    ) -> list[StrategicPattern]:
        """Detect all strategic patterns in interactions.

        Args:
            interactions: Semantic representations to analyze
            time_window_hours: Time window for analysis

        Returns:
            List of detected strategic patterns
        """
        patterns: list[StrategicPattern] = []
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent = [rep for rep in interactions if rep.timestamp >= cutoff_time]

        # Get unique agents
        agents = list({rep.source_agent_id for rep in recent})

        # Detect alliances (pairwise)
        for i, agent_a in enumerate(agents):
            for agent_b in agents[i + 1 :]:
                alliance = self.detect_alliance(agent_a, agent_b, recent)
                if alliance:
                    mi = self.calculate_mutual_information(agent_a, agent_b, recent)
                    evidence = [rep.message_id for rep in recent if rep.source_agent_id in [agent_a, agent_b]][:10]

                    patterns.append(
                        StrategicPattern(
                            pattern_type=PatternType.ALLIANCE,
                            agents_involved=[agent_a, agent_b],
                            evidence_messages=evidence,
                            mutual_information=mi,
                            metadata={"alliance_strength": alliance.strength},
                        )
                    )

        # Detect deception (per agent)
        for agent in agents:
            deception_score = self.detect_deception(agent, recent)
            if deception_score >= settings.deception_threshold:
                evidence = [rep.message_id for rep in recent if rep.source_agent_id == agent][:10]

                patterns.append(
                    StrategicPattern(
                        pattern_type=PatternType.DECEPTION,
                        agents_involved=[agent],
                        evidence_messages=evidence,
                        deception_score=deception_score,
                        metadata={"agent_id": agent, "score": deception_score},
                    )
                )

        # Detect inconsistency (per agent)
        for agent in agents:
            inconsistency_score = self.detect_inconsistency(agent, recent, time_window_hours)
            if inconsistency_score >= settings.inconsistency_threshold:
                evidence = [rep.message_id for rep in recent if rep.source_agent_id == agent][:10]

                patterns.append(
                    StrategicPattern(
                        pattern_type=PatternType.INCONSISTENCY,
                        agents_involved=[agent],
                        evidence_messages=evidence,
                        inconsistency_score=inconsistency_score,
                        metadata={"agent_id": agent, "score": inconsistency_score},
                    )
                )

        return patterns

    def get_alliance_clusters(self) -> list[list[str]]:
        """Get clusters of allied agents using graph community detection.

        Returns:
            List of agent clusters (communities)
        """
        if self.alliance_graph.number_of_nodes() == 0:
            return []

        # Use greedy modularity maximization
        from networkx.algorithms import community

        communities = community.greedy_modularity_communities(self.alliance_graph, weight="weight")

        return [list(comm) for comm in communities]
