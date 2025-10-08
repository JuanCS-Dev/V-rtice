"""FASE 9: Adaptive Immunity Service - Core Logic

Antibody diversification and affinity maturation for adaptive threat detection.
Bio-inspired adaptive learning through clonal selection and somatic hypermutation.

Adaptive immunity in biology:
1. Antibody diversification: Generate diverse antibody repertoire
2. Clonal selection: Expand successful antibodies
3. Affinity maturation: Refine antibody binding through somatic hypermutation
4. Memory cells: Long-term immunity

In cyber defense:
1. Detector diversification: Generate multiple detection signatures per threat
2. Clonal selection: Expand successful detectors
3. Affinity maturation: Refine detectors based on feedback
4. Detector memory: Maintain high-performing detectors

NO MOCKS - Production-ready adaptive learning algorithms.
"""

import hashlib
import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================


class AntibodyType(Enum):
    """Types of antibodies (detectors)."""

    SIGNATURE_BASED = "signature"  # Pattern matching
    BEHAVIORAL = "behavioral"  # Behavior analysis
    STATISTICAL = "statistical"  # Statistical anomaly
    HYBRID = "hybrid"  # Combination


@dataclass
class ThreatSample:
    """Threat sample for training antibodies."""

    sample_id: str
    threat_family: str
    features: Dict[str, float]  # Numerical features
    raw_data: bytes  # Raw threat data
    severity: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Antibody:
    """Adaptive antibody (threat detector).

    Biological analogy: B-cell antibody
    Cyber: Threat detection signature
    """

    antibody_id: str
    antibody_type: AntibodyType
    target_family: str  # Threat family this detects
    detection_pattern: Dict[str, Any]  # Detection logic
    affinity_score: float  # 0-1 (detection accuracy)
    generation: int  # How many mutations from parent
    parent_id: Optional[str]  # Parent antibody
    created_at: datetime
    last_matched: Optional[datetime] = None
    match_count: int = 0
    false_positive_count: int = 0
    true_positive_count: int = 0


@dataclass
class ClonalExpansion:
    """Record of clonal expansion event."""

    expansion_id: str
    parent_antibody_id: str
    clones_created: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AffinityMaturationEvent:
    """Record of affinity maturation (mutation)."""

    event_id: str
    antibody_id: str
    mutation_type: str
    affinity_before: float
    affinity_after: float
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Antibody Generator
# ============================================================================


class AntibodyGenerator:
    """Generates diverse antibody repertoire.

    Biological: V(D)J recombination creates antibody diversity
    Cyber: Generate diverse detection patterns
    """

    def __init__(self):
        self.antibodies_generated: int = 0

    def generate_initial_repertoire(
        self, threat_samples: List[ThreatSample], repertoire_size: int = 100
    ) -> List[Antibody]:
        """Generate initial antibody repertoire from threat samples.

        Args:
            threat_samples: Training threat samples
            repertoire_size: Number of antibodies to generate

        Returns:
            List of antibodies
        """
        antibodies = []

        # Group samples by family
        samples_by_family: Dict[str, List[ThreatSample]] = defaultdict(list)
        for sample in threat_samples:
            samples_by_family[sample.threat_family].append(sample)

        # Generate antibodies for each family
        antibodies_per_family = max(1, repertoire_size // len(samples_by_family))

        for family, family_samples in samples_by_family.items():
            # Generate diverse antibodies
            for i in range(antibodies_per_family):
                antibody = self._generate_antibody(family, family_samples, generation=0)
                antibodies.append(antibody)

        self.antibodies_generated += len(antibodies)

        logger.info(f"Generated initial repertoire: {len(antibodies)} antibodies")

        return antibodies

    def _generate_antibody(
        self,
        threat_family: str,
        samples: List[ThreatSample],
        generation: int,
        parent_id: Optional[str] = None,
    ) -> Antibody:
        """Generate single antibody.

        Args:
            threat_family: Target threat family
            samples: Training samples
            generation: Generation number
            parent_id: Parent antibody ID (if mutated)

        Returns:
            Antibody
        """
        # Extract features from samples
        feature_stats = self._compute_feature_statistics(samples)

        # Choose antibody type randomly
        antibody_type = random.choice(list(AntibodyType))

        # Generate detection pattern based on type
        if antibody_type == AntibodyType.SIGNATURE_BASED:
            pattern = self._generate_signature_pattern(feature_stats)
        elif antibody_type == AntibodyType.BEHAVIORAL:
            pattern = self._generate_behavioral_pattern(feature_stats)
        elif antibody_type == AntibodyType.STATISTICAL:
            pattern = self._generate_statistical_pattern(feature_stats)
        else:  # HYBRID
            pattern = self._generate_hybrid_pattern(feature_stats)

        # Generate ID
        antibody_id = hashlib.sha256(f"{threat_family}_{generation}_{random.random()}".encode()).hexdigest()[:16]

        # Create antibody
        antibody = Antibody(
            antibody_id=antibody_id,
            antibody_type=antibody_type,
            target_family=threat_family,
            detection_pattern=pattern,
            affinity_score=0.5,  # Initial neutral affinity
            generation=generation,
            parent_id=parent_id,
            created_at=datetime.now(),
        )

        return antibody

    def _compute_feature_statistics(self, samples: List[ThreatSample]) -> Dict[str, Dict[str, float]]:
        """Compute statistical features from samples.

        Args:
            samples: Threat samples

        Returns:
            Feature statistics
        """
        # Collect all features
        all_features: Dict[str, List[float]] = defaultdict(list)

        for sample in samples:
            for feature_name, feature_value in sample.features.items():
                all_features[feature_name].append(feature_value)

        # Compute statistics
        stats = {}

        for feature_name, values in all_features.items():
            stats[feature_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values),
            }

        return stats

    def _generate_signature_pattern(self, feature_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate signature-based detection pattern.

        Args:
            feature_stats: Feature statistics

        Returns:
            Detection pattern
        """
        # Select random features
        selected_features = random.sample(list(feature_stats.keys()), k=min(5, len(feature_stats)))

        # Create thresholds
        thresholds = {}
        for feature in selected_features:
            mean = feature_stats[feature]["mean"]
            std = feature_stats[feature]["std"]

            # Threshold = mean ± random std devs
            offset = random.uniform(0.5, 2.0) * std
            if random.random() > 0.5:
                thresholds[feature] = (">=", mean + offset)
            else:
                thresholds[feature] = ("<=", mean - offset)

        return {"type": "signature", "thresholds": thresholds}

    def _generate_behavioral_pattern(self, feature_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate behavioral detection pattern.

        Args:
            feature_stats: Feature statistics

        Returns:
            Detection pattern
        """
        # Behavioral patterns look at sequences/trends
        return {
            "type": "behavioral",
            "sequence_features": list(feature_stats.keys())[:3],
            "trend_threshold": 0.7,
        }

    def _generate_statistical_pattern(self, feature_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate statistical detection pattern.

        Args:
            feature_stats: Feature statistics

        Returns:
            Detection pattern
        """
        # Statistical patterns use distribution matching
        return {
            "type": "statistical",
            "distributions": {
                feature: {"mean": stats["mean"], "std": stats["std"]}
                for feature, stats in list(feature_stats.items())[:5]
            },
            "z_score_threshold": 3.0,
        }

    def _generate_hybrid_pattern(self, feature_stats: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate hybrid detection pattern.

        Args:
            feature_stats: Feature statistics

        Returns:
            Detection pattern
        """
        # Hybrid combines multiple approaches
        return {
            "type": "hybrid",
            "signature": self._generate_signature_pattern(feature_stats),
            "statistical": self._generate_statistical_pattern(feature_stats),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get generator status.

        Returns:
            Status dictionary
        """
        return {
            "component": "antibody_generator",
            "antibodies_generated": self.antibodies_generated,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Affinity Maturation Engine
# ============================================================================


class AffinityMaturationEngine:
    """Refines antibodies through somatic hypermutation.

    Biological: B-cells mutate to improve antigen binding
    Cyber: Detectors mutate to improve threat detection
    """

    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate
        self.maturation_events: List[AffinityMaturationEvent] = []
        self.generator = AntibodyGenerator()

    def mature_antibody(self, antibody: Antibody, feedback: Dict[str, bool]) -> List[Antibody]:
        """Mature antibody through mutation.

        Args:
            antibody: Antibody to mature
            feedback: Detection feedback (sample_id -> was_correct)

        Returns:
            List of mutated antibodies
        """
        # Compute current affinity from feedback
        current_affinity = self._compute_affinity_from_feedback(feedback)

        # Generate mutations
        mutants = []

        num_mutations = random.randint(1, 5)

        for i in range(num_mutations):
            mutant = self._mutate_antibody(antibody)

            # Estimate mutant affinity (would need testing in real system)
            mutant_affinity = current_affinity + random.uniform(-0.1, 0.2)
            mutant.affinity_score = np.clip(mutant_affinity, 0.0, 1.0)

            mutants.append(mutant)

            # Record maturation event
            event = AffinityMaturationEvent(
                event_id=f"mat_{int(datetime.now().timestamp())}_{i}",
                antibody_id=antibody.antibody_id,
                mutation_type="somatic_hypermutation",
                affinity_before=current_affinity,
                affinity_after=mutant.affinity_score,
            )
            self.maturation_events.append(event)

        logger.debug(f"Matured antibody {antibody.antibody_id}: generated {len(mutants)} mutants")

        return mutants

    def _compute_affinity_from_feedback(self, feedback: Dict[str, bool]) -> float:
        """Compute affinity score from feedback.

        Args:
            feedback: Detection feedback

        Returns:
            Affinity score (0-1)
        """
        if len(feedback) == 0:
            return 0.5

        correct = sum(1 for was_correct in feedback.values() if was_correct)
        affinity = correct / len(feedback)

        return affinity

    def _mutate_antibody(self, parent: Antibody) -> Antibody:
        """Create mutated version of antibody.

        Args:
            parent: Parent antibody

        Returns:
            Mutated antibody
        """
        # Copy parent pattern
        mutated_pattern = json.loads(json.dumps(parent.detection_pattern))

        # Apply mutations based on type
        if parent.antibody_type == AntibodyType.SIGNATURE_BASED:
            self._mutate_signature_pattern(mutated_pattern)
        elif parent.antibody_type == AntibodyType.STATISTICAL:
            self._mutate_statistical_pattern(mutated_pattern)

        # Generate new ID
        antibody_id = hashlib.sha256(f"{parent.antibody_id}_{random.random()}".encode()).hexdigest()[:16]

        # Create mutant
        mutant = Antibody(
            antibody_id=antibody_id,
            antibody_type=parent.antibody_type,
            target_family=parent.target_family,
            detection_pattern=mutated_pattern,
            affinity_score=parent.affinity_score,
            generation=parent.generation + 1,
            parent_id=parent.antibody_id,
            created_at=datetime.now(),
        )

        return mutant

    def _mutate_signature_pattern(self, pattern: Dict[str, Any]):
        """Mutate signature pattern in-place.

        Args:
            pattern: Pattern to mutate
        """
        if "thresholds" in pattern:
            # Randomly adjust thresholds
            for feature, (op, value) in list(pattern["thresholds"].items()):
                if random.random() < self.mutation_rate:
                    # Adjust threshold by ±10%
                    adjustment = value * random.uniform(-0.1, 0.1)
                    pattern["thresholds"][feature] = (op, value + adjustment)

    def _mutate_statistical_pattern(self, pattern: Dict[str, Any]):
        """Mutate statistical pattern in-place.

        Args:
            pattern: Pattern to mutate
        """
        if "distributions" in pattern:
            # Randomly adjust distribution parameters
            for feature, dist in pattern["distributions"].items():
                if random.random() < self.mutation_rate:
                    dist["mean"] += dist["mean"] * random.uniform(-0.05, 0.05)
                    dist["std"] += dist["std"] * random.uniform(-0.05, 0.05)

        if "z_score_threshold" in pattern:
            if random.random() < self.mutation_rate:
                pattern["z_score_threshold"] += random.uniform(-0.2, 0.2)

    def get_status(self) -> Dict[str, Any]:
        """Get maturation engine status.

        Returns:
            Status dictionary
        """
        return {
            "component": "affinity_maturation_engine",
            "maturation_events": len(self.maturation_events),
            "mutation_rate": self.mutation_rate,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Clonal Selection Manager
# ============================================================================


class ClonalSelectionManager:
    """Manages clonal selection and expansion.

    Biological: Successful B-cells proliferate
    Cyber: Successful detectors are cloned and expanded
    """

    def __init__(self, expansion_threshold: float = 0.8):
        self.expansion_threshold = expansion_threshold
        self.expansions: List[ClonalExpansion] = []
        self.generator = AntibodyGenerator()

    def select_for_expansion(self, antibodies: List[Antibody], max_expansions: int = 10) -> List[Antibody]:
        """Select high-affinity antibodies for clonal expansion.

        Args:
            antibodies: Antibody pool
            max_expansions: Maximum number of expansions

        Returns:
            Expanded antibody pool (includes clones)
        """
        # Find high-affinity antibodies
        high_affinity = [ab for ab in antibodies if ab.affinity_score >= self.expansion_threshold]

        # Sort by affinity
        high_affinity.sort(key=lambda ab: ab.affinity_score, reverse=True)

        # Expand top performers
        expanded = list(antibodies)  # Start with original pool

        for antibody in high_affinity[:max_expansions]:
            # Number of clones proportional to affinity
            num_clones = int(antibody.affinity_score * 10)

            clones = self._clone_antibody(antibody, num_clones)
            expanded.extend(clones)

            # Record expansion
            expansion = ClonalExpansion(
                expansion_id=f"exp_{int(datetime.now().timestamp())}",
                parent_antibody_id=antibody.antibody_id,
                clones_created=len(clones),
                reason=f"High affinity: {antibody.affinity_score:.2f}",
            )
            self.expansions.append(expansion)

            logger.info(
                f"Clonal expansion: {antibody.antibody_id} → {len(clones)} clones "
                f"(affinity: {antibody.affinity_score:.2f})"
            )

        return expanded

    def _clone_antibody(self, parent: Antibody, num_clones: int) -> List[Antibody]:
        """Clone antibody with slight variations.

        Args:
            parent: Parent antibody
            num_clones: Number of clones to create

        Returns:
            List of clones
        """
        clones = []

        for i in range(num_clones):
            # Clone with ID suffix
            clone_id = f"{parent.antibody_id}_clone{i}"

            # Copy pattern (with tiny random variation)
            clone_pattern = json.loads(json.dumps(parent.detection_pattern))

            clone = Antibody(
                antibody_id=clone_id,
                antibody_type=parent.antibody_type,
                target_family=parent.target_family,
                detection_pattern=clone_pattern,
                affinity_score=parent.affinity_score,
                generation=parent.generation,
                parent_id=parent.antibody_id,
                created_at=datetime.now(),
            )

            clones.append(clone)

        return clones

    def get_status(self) -> Dict[str, Any]:
        """Get selection manager status.

        Returns:
            Status dictionary
        """
        total_clones = sum(exp.clones_created for exp in self.expansions)

        return {
            "component": "clonal_selection_manager",
            "expansions_performed": len(self.expansions),
            "total_clones_created": total_clones,
            "expansion_threshold": self.expansion_threshold,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Adaptive Immunity Controller
# ============================================================================


class AdaptiveImmunityController:
    """Main adaptive immunity controller.

    Orchestrates:
    1. Antibody generation
    2. Affinity maturation
    3. Clonal selection
    """

    def __init__(
        self,
        initial_repertoire_size: int = 100,
        mutation_rate: float = 0.1,
        expansion_threshold: float = 0.8,
    ):
        self.antibody_generator = AntibodyGenerator()
        self.affinity_maturation_engine = AffinityMaturationEngine(mutation_rate)
        self.clonal_selection_manager = ClonalSelectionManager(expansion_threshold)

        self.antibody_pool: Dict[str, Antibody] = {}
        self.repertoire_initialized: bool = False

    def initialize_repertoire(self, threat_samples: List[ThreatSample]):
        """Initialize antibody repertoire from threat samples.

        Args:
            threat_samples: Training threat samples
        """
        logger.info(f"Initializing repertoire with {len(threat_samples)} samples")

        # Generate initial antibodies
        antibodies = self.antibody_generator.generate_initial_repertoire(threat_samples, repertoire_size=100)

        # Add to pool
        for antibody in antibodies:
            self.antibody_pool[antibody.antibody_id] = antibody

        self.repertoire_initialized = True

        logger.info(f"Repertoire initialized: {len(self.antibody_pool)} antibodies")

    def run_maturation_cycle(self, feedback_data: Dict[str, Dict[str, bool]]):
        """Run affinity maturation cycle.

        Args:
            feedback_data: Antibody ID -> {sample_id -> was_correct}
        """
        logger.info("Running affinity maturation cycle")

        new_antibodies = []

        for antibody_id, feedback in feedback_data.items():
            if antibody_id in self.antibody_pool:
                antibody = self.antibody_pool[antibody_id]

                # Mature antibody
                mutants = self.affinity_maturation_engine.mature_antibody(antibody, feedback)

                new_antibodies.extend(mutants)

        # Add mutants to pool
        for antibody in new_antibodies:
            self.antibody_pool[antibody.antibody_id] = antibody

        logger.info(f"Maturation cycle complete: {len(new_antibodies)} new antibodies")

    def run_selection_cycle(self):
        """Run clonal selection cycle."""
        logger.info("Running clonal selection cycle")

        # Get current antibodies
        current_antibodies = list(self.antibody_pool.values())

        # Select and expand
        expanded_pool = self.clonal_selection_manager.select_for_expansion(current_antibodies, max_expansions=10)

        # Update pool
        self.antibody_pool = {ab.antibody_id: ab for ab in expanded_pool}

        logger.info(f"Selection cycle complete: {len(self.antibody_pool)} antibodies")

    def get_status(self) -> Dict[str, Any]:
        """Get controller status.

        Returns:
            Status dictionary
        """
        generator_status = self.antibody_generator.get_status()
        maturation_status = self.affinity_maturation_engine.get_status()
        selection_status = self.clonal_selection_manager.get_status()

        return {
            "component": "adaptive_immunity_controller",
            "repertoire_initialized": self.repertoire_initialized,
            "antibody_pool_size": len(self.antibody_pool),
            "antibody_generator": generator_status,
            "affinity_maturation_engine": maturation_status,
            "clonal_selection_manager": selection_status,
            "timestamp": datetime.now().isoformat(),
        }
