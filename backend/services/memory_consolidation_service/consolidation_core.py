"""FASE 9: Memory Consolidation Service - Core Logic

Long-term immunological memory and circadian rhythm consolidation.
Bio-inspired memory transfer from short-term to long-term storage.

Memory consolidation in biology:
1. Hippocampus (short-term) → Cortex (long-term) transfer during sleep
2. Replay of important experiences for learning
3. Pruning of irrelevant memories
4. Circadian rhythm regulation

In cyber defense:
1. Consolidate security events into long-term memory
2. Extract patterns and learnings from event sequences
3. Prune trivial/irrelevant events
4. Periodic consolidation cycles (circadian rhythm)

NO MOCKS - Production-ready memory consolidation algorithms.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict, deque
import json
import hashlib

import numpy as np
from scipy.spatial.distance import cosine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class MemoryImportance(Enum):
    """Memory importance levels."""
    TRIVIAL = "trivial"          # Discard
    LOW = "low"                  # Short-term only
    MEDIUM = "medium"            # Consider for consolidation
    HIGH = "high"                # Consolidate to long-term
    CRITICAL = "critical"        # Permanent long-term memory


class ConsolidationStatus(Enum):
    """Memory consolidation status."""
    PENDING = "pending"
    CONSOLIDATING = "consolidating"
    CONSOLIDATED = "consolidated"
    PRUNED = "pruned"


@dataclass
class SecurityEvent:
    """Security event for memory consolidation."""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: float  # 0-1
    source: str
    target: str
    indicators: List[str]
    outcome: Optional[str] = None  # "blocked", "allowed", "quarantined"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShortTermMemory:
    """Short-term memory buffer (hippocampus analogue)."""
    event: SecurityEvent
    importance_score: float  # 0-1
    access_count: int  # How many times accessed
    created_at: datetime
    status: ConsolidationStatus = ConsolidationStatus.PENDING


@dataclass
class LongTermMemory:
    """Long-term memory (cortex analogue)."""
    memory_id: str
    pattern_type: str  # "attack_sequence", "threat_actor", "vulnerability"
    description: str
    consolidated_events: List[str]  # Event IDs
    pattern_fingerprint: Dict[str, Any]  # Extracted pattern
    importance: MemoryImportance
    created_at: datetime
    last_accessed: datetime
    access_count: int
    strength: float  # 0-1 (stronger = less likely to be pruned)


@dataclass
class ConsolidationCycle:
    """Consolidation cycle execution record."""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime]
    events_processed: int
    memories_consolidated: int
    memories_pruned: int
    patterns_extracted: int
    status: str


# ============================================================================
# Importance Scorer
# ============================================================================

class ImportanceScorer:
    """Scores importance of security events for consolidation.

    Factors:
    1. Severity (high severity = high importance)
    2. Uniqueness (novel events = high importance)
    3. Recurrence (recurring patterns = high importance)
    4. Outcome (successful attacks = high importance)
    """

    def __init__(self):
        self.event_type_counts: Dict[str, int] = defaultdict(int)
        self.total_events: int = 0

    def score_importance(self, event: SecurityEvent) -> float:
        """Score importance of event.

        Args:
            event: Security event

        Returns:
            Importance score (0-1)
        """
        # Factor 1: Severity (30% weight)
        severity_score = event.severity

        # Factor 2: Uniqueness (30% weight)
        # Rare events are more important
        event_frequency = self.event_type_counts.get(event.event_type, 0)
        total = max(self.total_events, 1)
        uniqueness_score = 1.0 - (event_frequency / total)

        # Factor 3: Outcome (25% weight)
        # Successful attacks are more important
        outcome_score = self._score_outcome(event.outcome)

        # Factor 4: Indicator count (15% weight)
        # More indicators = more important
        indicator_score = min(len(event.indicators) / 10, 1.0)

        # Weighted combination
        importance = (
            0.30 * severity_score +
            0.30 * uniqueness_score +
            0.25 * outcome_score +
            0.15 * indicator_score
        )

        # Update statistics
        self.event_type_counts[event.event_type] += 1
        self.total_events += 1

        return float(np.clip(importance, 0.0, 1.0))

    def _score_outcome(self, outcome: Optional[str]) -> float:
        """Score outcome importance.

        Args:
            outcome: Event outcome

        Returns:
            Outcome score (0-1)
        """
        if outcome is None:
            return 0.5  # Unknown

        outcome_scores = {
            "blocked": 0.6,      # Threat prevented
            "allowed": 0.3,      # False positive or benign
            "quarantined": 0.7,  # Suspicious
            "compromised": 1.0,  # Successful attack
            "mitigated": 0.8     # Threat partially successful
        }

        return outcome_scores.get(outcome.lower(), 0.5)

    def get_status(self) -> Dict[str, Any]:
        """Get scorer status.

        Returns:
            Status dictionary
        """
        return {
            "component": "importance_scorer",
            "total_events": self.total_events,
            "unique_event_types": len(self.event_type_counts),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Pattern Extractor
# ============================================================================

class PatternExtractor:
    """Extracts patterns from event sequences for long-term memory.

    Patterns:
    1. Attack sequences (recon → exploit → lateral movement)
    2. Threat actor signatures (consistent TTPs)
    3. Vulnerability chains (exploit sequence)
    """

    def __init__(self):
        self.patterns_extracted: int = 0

    def extract_patterns(
        self,
        events: List[SecurityEvent],
        min_pattern_size: int = 2
    ) -> List[Dict[str, Any]]:
        """Extract patterns from event sequence.

        Args:
            events: List of security events
            min_pattern_size: Minimum events in pattern

        Returns:
            List of extracted patterns
        """
        patterns = []

        # Pattern 1: Time-based sequences (events close in time)
        temporal_patterns = self._extract_temporal_patterns(events, min_pattern_size)
        patterns.extend(temporal_patterns)

        # Pattern 2: Source-target patterns (same attacker/victim)
        relationship_patterns = self._extract_relationship_patterns(events, min_pattern_size)
        patterns.extend(relationship_patterns)

        # Pattern 3: Type-based sequences (attack kill chain)
        attack_chains = self._extract_attack_chains(events, min_pattern_size)
        patterns.extend(attack_chains)

        self.patterns_extracted += len(patterns)

        return patterns

    def _extract_temporal_patterns(
        self,
        events: List[SecurityEvent],
        min_size: int
    ) -> List[Dict[str, Any]]:
        """Extract patterns based on temporal proximity.

        Args:
            events: Security events
            min_size: Minimum pattern size

        Returns:
            Extracted patterns
        """
        patterns = []

        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Sliding window approach
        window_size_minutes = 60  # 1 hour window

        i = 0
        while i < len(sorted_events):
            window_start = sorted_events[i].timestamp
            window_end = window_start + timedelta(minutes=window_size_minutes)

            # Collect events in window
            window_events = []
            j = i
            while j < len(sorted_events) and sorted_events[j].timestamp <= window_end:
                window_events.append(sorted_events[j])
                j += 1

            # If window has enough events, create pattern
            if len(window_events) >= min_size:
                pattern = {
                    "pattern_type": "temporal_cluster",
                    "event_ids": [e.event_id for e in window_events],
                    "start_time": window_start.isoformat(),
                    "end_time": window_end.isoformat(),
                    "event_count": len(window_events),
                    "fingerprint": self._compute_pattern_fingerprint(window_events)
                }
                patterns.append(pattern)

            i = j if j > i else i + 1

        return patterns

    def _extract_relationship_patterns(
        self,
        events: List[SecurityEvent],
        min_size: int
    ) -> List[Dict[str, Any]]:
        """Extract patterns based on source-target relationships.

        Args:
            events: Security events
            min_size: Minimum pattern size

        Returns:
            Extracted patterns
        """
        patterns = []

        # Group by source
        by_source: Dict[str, List[SecurityEvent]] = defaultdict(list)
        for event in events:
            by_source[event.source].append(event)

        # Find sources with multiple events
        for source, source_events in by_source.items():
            if len(source_events) >= min_size:
                pattern = {
                    "pattern_type": "source_pattern",
                    "source": source,
                    "event_ids": [e.event_id for e in source_events],
                    "event_count": len(source_events),
                    "targets": list(set(e.target for e in source_events)),
                    "fingerprint": self._compute_pattern_fingerprint(source_events)
                }
                patterns.append(pattern)

        return patterns

    def _extract_attack_chains(
        self,
        events: List[SecurityEvent],
        min_size: int
    ) -> List[Dict[str, Any]]:
        """Extract attack kill chain patterns.

        Args:
            events: Security events
            min_size: Minimum pattern size

        Returns:
            Extracted patterns
        """
        patterns = []

        # Define kill chain stages
        kill_chain_stages = {
            "reconnaissance": ["port_scan", "network_scan", "enumeration"],
            "weaponization": ["exploit_dev", "payload_creation"],
            "delivery": ["phishing", "drive_by"],
            "exploitation": ["rce", "buffer_overflow", "sql_injection"],
            "installation": ["malware_install", "backdoor"],
            "command_control": ["c2_beacon", "c2_communication"],
            "actions": ["data_exfil", "lateral_movement", "privilege_escalation"]
        }

        # Map event types to stages
        event_stages = []
        for event in events:
            for stage, types in kill_chain_stages.items():
                if event.event_type in types:
                    event_stages.append((stage, event))
                    break

        # Look for sequential stages
        if len(event_stages) >= min_size:
            # Check if stages are in kill chain order
            stage_order = list(kill_chain_stages.keys())

            for i in range(len(event_stages) - min_size + 1):
                chain_events = event_stages[i:i + min_size]

                # Verify sequence
                current_stage_idx = stage_order.index(chain_events[0][0])
                is_valid_chain = True

                for j in range(1, len(chain_events)):
                    next_stage_idx = stage_order.index(chain_events[j][0])
                    if next_stage_idx <= current_stage_idx:
                        is_valid_chain = False
                        break
                    current_stage_idx = next_stage_idx

                if is_valid_chain:
                    chain_event_objs = [e[1] for e in chain_events]
                    pattern = {
                        "pattern_type": "attack_chain",
                        "event_ids": [e.event_id for e in chain_event_objs],
                        "stages": [e[0] for e in chain_events],
                        "event_count": len(chain_event_objs),
                        "fingerprint": self._compute_pattern_fingerprint(chain_event_objs)
                    }
                    patterns.append(pattern)

        return patterns

    def _compute_pattern_fingerprint(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Compute fingerprint of pattern.

        Args:
            events: Events in pattern

        Returns:
            Pattern fingerprint
        """
        # Aggregate statistics
        severities = [e.severity for e in events]
        sources = [e.source for e in events]
        targets = [e.target for e in events]
        types = [e.event_type for e in events]

        fingerprint = {
            "avg_severity": np.mean(severities),
            "max_severity": np.max(severities),
            "unique_sources": len(set(sources)),
            "unique_targets": len(set(targets)),
            "event_types": list(set(types)),
            "duration_minutes": (events[-1].timestamp - events[0].timestamp).total_seconds() / 60
        }

        return fingerprint

    def get_status(self) -> Dict[str, Any]:
        """Get extractor status.

        Returns:
            Status dictionary
        """
        return {
            "component": "pattern_extractor",
            "patterns_extracted": self.patterns_extracted,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Memory Consolidator
# ============================================================================

class MemoryConsolidator:
    """Main memory consolidation controller.

    Orchestrates:
    1. Short-term memory buffer (hippocampus)
    2. Long-term memory storage (cortex)
    3. Consolidation cycles (sleep)
    4. Memory pruning (forgetting)
    """

    def __init__(
        self,
        stm_capacity: int = 10000,
        consolidation_threshold: float = 0.6,
        pruning_threshold: float = 0.3
    ):
        self.short_term_memory: Dict[str, ShortTermMemory] = {}
        self.long_term_memory: Dict[str, LongTermMemory] = {}
        self.stm_capacity = stm_capacity
        self.consolidation_threshold = consolidation_threshold
        self.pruning_threshold = pruning_threshold

        self.importance_scorer = ImportanceScorer()
        self.pattern_extractor = PatternExtractor()

        self.consolidation_cycles: List[ConsolidationCycle] = []
        self.events_received: int = 0

    def ingest_event(self, event: SecurityEvent):
        """Ingest security event into short-term memory.

        Args:
            event: Security event
        """
        # Score importance
        importance = self.importance_scorer.score_importance(event)

        # Create STM entry
        stm_entry = ShortTermMemory(
            event=event,
            importance_score=importance,
            access_count=0,
            created_at=datetime.now()
        )

        # Add to STM
        self.short_term_memory[event.event_id] = stm_entry
        self.events_received += 1

        # Check capacity
        if len(self.short_term_memory) > self.stm_capacity:
            self._evict_least_important_stm()

        logger.debug(f"Ingested event {event.event_id} (importance: {importance:.2f})")

    def _evict_least_important_stm(self):
        """Evict least important STM entry."""
        # Find entry with lowest importance
        min_entry = min(
            self.short_term_memory.values(),
            key=lambda e: e.importance_score
        )

        # Mark as pruned and remove
        min_entry.status = ConsolidationStatus.PRUNED
        del self.short_term_memory[min_entry.event.event_id]

        logger.debug(f"Evicted STM entry {min_entry.event.event_id}")

    def run_consolidation_cycle(self) -> ConsolidationCycle:
        """Run consolidation cycle (sleep).

        Transfers important memories from STM to LTM.

        Returns:
            Consolidation cycle record
        """
        cycle_id = f"cycle_{int(datetime.now().timestamp())}"
        cycle = ConsolidationCycle(
            cycle_id=cycle_id,
            start_time=datetime.now(),
            end_time=None,
            events_processed=0,
            memories_consolidated=0,
            memories_pruned=0,
            patterns_extracted=0,
            status="running"
        )

        logger.info(f"Starting consolidation cycle: {cycle_id}")

        # Step 1: Identify events for consolidation
        events_to_consolidate = [
            stm.event
            for stm in self.short_term_memory.values()
            if stm.importance_score >= self.consolidation_threshold
        ]

        cycle.events_processed = len(events_to_consolidate)

        # Step 2: Extract patterns
        if len(events_to_consolidate) > 0:
            patterns = self.pattern_extractor.extract_patterns(events_to_consolidate)
            cycle.patterns_extracted = len(patterns)

            # Step 3: Create LTM entries for patterns
            for pattern in patterns:
                self._consolidate_pattern_to_ltm(pattern)
                cycle.memories_consolidated += 1

        # Step 4: Prune weak LTM memories
        pruned = self._prune_weak_memories()
        cycle.memories_pruned = pruned

        # Step 5: Clear consolidated STM entries
        for event_id in list(self.short_term_memory.keys()):
            stm = self.short_term_memory[event_id]
            if stm.importance_score >= self.consolidation_threshold:
                stm.status = ConsolidationStatus.CONSOLIDATED
                del self.short_term_memory[event_id]

        cycle.end_time = datetime.now()
        cycle.status = "completed"
        self.consolidation_cycles.append(cycle)

        logger.info(
            f"Consolidation cycle {cycle_id} complete: "
            f"{cycle.memories_consolidated} consolidated, {cycle.memories_pruned} pruned"
        )

        return cycle

    def _consolidate_pattern_to_ltm(self, pattern: Dict[str, Any]):
        """Consolidate pattern to long-term memory.

        Args:
            pattern: Extracted pattern
        """
        # Generate memory ID
        memory_id = hashlib.sha256(
            json.dumps(pattern, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Determine importance
        avg_severity = pattern["fingerprint"].get("avg_severity", 0.5)
        if avg_severity >= 0.8:
            importance = MemoryImportance.CRITICAL
        elif avg_severity >= 0.6:
            importance = MemoryImportance.HIGH
        else:
            importance = MemoryImportance.MEDIUM

        # Create LTM entry
        ltm_entry = LongTermMemory(
            memory_id=memory_id,
            pattern_type=pattern["pattern_type"],
            description=f"{pattern['pattern_type']} with {pattern['event_count']} events",
            consolidated_events=pattern["event_ids"],
            pattern_fingerprint=pattern,
            importance=importance,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            strength=1.0  # Start at full strength
        )

        self.long_term_memory[memory_id] = ltm_entry

        logger.debug(f"Consolidated pattern to LTM: {memory_id}")

    def _prune_weak_memories(self) -> int:
        """Prune weak long-term memories (forgetting).

        Returns:
            Number of memories pruned
        """
        pruned = 0

        for memory_id in list(self.long_term_memory.keys()):
            ltm = self.long_term_memory[memory_id]

            # Decay strength over time
            age_days = (datetime.now() - ltm.last_accessed).days
            decay_rate = 0.01  # 1% per day
            ltm.strength = max(0.0, ltm.strength - (decay_rate * age_days))

            # Prune if strength below threshold
            if ltm.strength < self.pruning_threshold:
                del self.long_term_memory[memory_id]
                pruned += 1

        return pruned

    def access_memory(self, memory_id: str) -> Optional[LongTermMemory]:
        """Access long-term memory (strengthens it).

        Args:
            memory_id: Memory identifier

        Returns:
            Long-term memory or None
        """
        if memory_id not in self.long_term_memory:
            return None

        ltm = self.long_term_memory[memory_id]
        ltm.access_count += 1
        ltm.last_accessed = datetime.now()
        ltm.strength = min(1.0, ltm.strength + 0.1)  # Strengthen on access

        return ltm

    def get_status(self) -> Dict[str, Any]:
        """Get consolidator status.

        Returns:
            Status dictionary
        """
        scorer_status = self.importance_scorer.get_status()
        extractor_status = self.pattern_extractor.get_status()

        return {
            "component": "memory_consolidator",
            "events_received": self.events_received,
            "stm_size": len(self.short_term_memory),
            "ltm_size": len(self.long_term_memory),
            "consolidation_cycles": len(self.consolidation_cycles),
            "importance_scorer": scorer_status,
            "pattern_extractor": extractor_status,
            "timestamp": datetime.now().isoformat()
        }
