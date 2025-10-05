"""
Dung's Abstract Argumentation Framework for Cognitive Defense System.

Implements formal argumentation analysis:
- Argument attack relations
- Extension semantics (grounded, preferred, stable)
- Coherence calculation
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import json

from .models import Argument, Fallacy, ArgumentRole
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ArgumentationFramework:
    """
    Dung's Abstract Argumentation Framework implementation.

    Models arguments and attack relations for formal analysis.
    """

    def __init__(self):
        """Initialize argumentation framework."""
        self.arguments: Dict[str, Argument] = {}
        self.attacks: Set[Tuple[str, str]] = set()  # (attacker_id, attacked_id)

    def add_argument(self, argument: Argument) -> None:
        """
        Add argument to framework.

        Args:
            argument: Argument to add
        """
        self.arguments[argument.id] = argument

    def add_arguments(self, arguments: List[Argument]) -> None:
        """Add multiple arguments."""
        for arg in arguments:
            self.add_argument(arg)

    def add_attack(self, attacker_id: str, attacked_id: str) -> None:
        """
        Add attack relation.

        Args:
            attacker_id: Attacking argument ID
            attacked_id: Attacked argument ID
        """
        if attacker_id in self.arguments and attacked_id in self.arguments:
            self.attacks.add((attacker_id, attacked_id))
        else:
            logger.warning(f"Cannot add attack: argument IDs not found")

    def infer_attacks_from_fallacies(
        self,
        fallacies: List[Fallacy]
    ) -> None:
        """
        Infer attack relations from detected fallacies.

        A fallacious argument attacks itself (undermines its own credibility).

        Args:
            fallacies: List of detected fallacies
        """
        for fallacy in fallacies:
            # Fallacious argument attacks itself
            self.add_attack(fallacy.argument_id, fallacy.argument_id)

            logger.debug(
                f"Added self-attack for fallacious argument {fallacy.argument_id} "
                f"({fallacy.fallacy_type.value})"
            )

    def infer_attacks_from_structure(self) -> None:
        """
        Infer attack relations from argument structure.

        Rules:
        - Premises attack opposing claims
        - Counter-premises attack supporting premises
        """
        # Group by parent
        children: Dict[str, List[Argument]] = defaultdict(list)
        for arg in self.arguments.values():
            if arg.parent_id:
                children[arg.parent_id].append(arg)

        # Find opposing arguments (simplified heuristic)
        for arg1_id, arg1 in self.arguments.items():
            for arg2_id, arg2 in self.arguments.items():
                if arg1_id == arg2_id:
                    continue

                # Claims attack opposing claims
                if (arg1.role == ArgumentRole.CLAIM and
                    arg2.role == ArgumentRole.CLAIM):

                    # Simple opposition detection (production should use semantics)
                    if self._are_opposing(arg1.text, arg2.text):
                        self.add_attack(arg1_id, arg2_id)

    @staticmethod
    def _are_opposing(text1: str, text2: str) -> bool:
        """
        Simple opposition detection.

        Args:
            text1: First text
            text2: Second text

        Returns:
            True if texts are opposing
        """
        # Negation indicators
        negations = ["não", "nunca", "nenhum", "sem", "jamais"]

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # Check if one contains negation and other doesn't
        text1_has_neg = any(neg in text1_lower for neg in negations)
        text2_has_neg = any(neg in text2_lower for neg in negations)

        # Simple heuristic: if one has negation and other doesn't, might be opposing
        if text1_has_neg != text2_has_neg:
            # Check if they share keywords (topic similarity)
            words1 = set(text1_lower.split())
            words2 = set(text2_lower.split())
            overlap = len(words1 & words2)

            if overlap >= 2:  # Share at least 2 words
                return True

        return False

    def get_attackers(self, argument_id: str) -> Set[str]:
        """
        Get arguments that attack given argument.

        Args:
            argument_id: Target argument ID

        Returns:
            Set of attacker IDs
        """
        return {
            attacker for attacker, attacked in self.attacks
            if attacked == argument_id
        }

    def get_attacked(self, argument_id: str) -> Set[str]:
        """
        Get arguments attacked by given argument.

        Args:
            argument_id: Attacker argument ID

        Returns:
            Set of attacked IDs
        """
        return {
            attacked for attacker, attacked in self.attacks
            if attacker == argument_id
        }

    def is_defended(self, argument_id: str, extension: Set[str]) -> bool:
        """
        Check if argument is defended by extension.

        An argument is defended if all its attackers are attacked by extension.

        Args:
            argument_id: Argument ID to check
            extension: Set of argument IDs in extension

        Returns:
            True if defended
        """
        attackers = self.get_attackers(argument_id)

        for attacker in attackers:
            # Check if attacker is attacked by extension
            attacker_attackers = self.get_attackers(attacker)

            if not (attacker_attackers & extension):
                # Attacker is not attacked by extension
                return False

        return True

    def compute_grounded_extension(self) -> Set[str]:
        """
        Compute grounded extension (smallest admissible set).

        Returns:
            Set of argument IDs in grounded extension
        """
        extension = set()
        changed = True

        while changed:
            changed = False

            for arg_id in self.arguments.keys():
                if arg_id in extension:
                    continue

                # Check if arg is defended by current extension
                attackers = self.get_attackers(arg_id)

                if all(self.get_attackers(att) & extension for att in attackers):
                    # All attackers are attacked by extension
                    # Check if arg doesn't attack extension
                    if not (self.get_attacked(arg_id) & extension):
                        extension.add(arg_id)
                        changed = True

        return extension

    def compute_preferred_extensions(self, max_iterations: int = 100) -> List[Set[str]]:
        """
        Compute preferred extensions (maximal admissible sets).

        Simplified algorithm - production should use complete semantics.

        Args:
            max_iterations: Maximum iterations

        Returns:
            List of preferred extensions
        """
        # Start with grounded
        grounded = self.compute_grounded_extension()

        extensions = [grounded]

        # Try to expand
        for _ in range(max_iterations):
            expanded = False

            for ext in list(extensions):
                for arg_id in self.arguments.keys():
                    if arg_id in ext:
                        continue

                    # Check if adding arg_id maintains admissibility
                    new_ext = ext | {arg_id}

                    if self._is_conflict_free(new_ext) and self._is_admissible(new_ext):
                        extensions.append(new_ext)
                        expanded = True

            if not expanded:
                break

        # Return maximal extensions
        maximal = []
        for ext in extensions:
            is_maximal = True
            for other in extensions:
                if ext < other:  # ext is proper subset of other
                    is_maximal = False
                    break
            if is_maximal and ext not in maximal:
                maximal.append(ext)

        return maximal[:10]  # Limit to 10 for performance

    def _is_conflict_free(self, extension: Set[str]) -> bool:
        """Check if extension is conflict-free (no internal attacks)."""
        for arg_id in extension:
            attacked = self.get_attacked(arg_id)
            if attacked & extension:
                return False
        return True

    def _is_admissible(self, extension: Set[str]) -> bool:
        """Check if extension is admissible (conflict-free + defends all members)."""
        if not self._is_conflict_free(extension):
            return False

        for arg_id in extension:
            if not self.is_defended(arg_id, extension):
                return False

        return True

    def calculate_coherence(self) -> float:
        """
        Calculate argumentation coherence.

        Coherence is high when:
        - Few internal conflicts
        - Many well-supported arguments
        - Strong grounded extension

        Returns:
            Coherence score (0-1)
        """
        if not self.arguments:
            return 1.0  # Empty is coherent

        # Factor 1: Conflict density
        total_possible_attacks = len(self.arguments) * (len(self.arguments) - 1)
        conflict_density = len(self.attacks) / total_possible_attacks if total_possible_attacks > 0 else 0
        conflict_score = 1.0 - min(1.0, conflict_density * 2)  # Penalize conflicts

        # Factor 2: Grounded extension size
        grounded = self.compute_grounded_extension()
        grounded_ratio = len(grounded) / len(self.arguments)

        # Factor 3: Average argument confidence
        avg_confidence = sum(arg.confidence for arg in self.arguments.values()) / len(self.arguments)

        # Weighted combination
        coherence = (
            conflict_score * 0.4 +
            grounded_ratio * 0.3 +
            avg_confidence * 0.3
        )

        return coherence

    def get_winning_arguments(self) -> List[str]:
        """
        Get winning arguments (in grounded extension).

        Returns:
            List of winning argument IDs
        """
        grounded = self.compute_grounded_extension()
        return list(grounded)

    def to_dict(self) -> Dict[str, any]:
        """
        Export framework to dict.

        Returns:
            Dict representation
        """
        return {
            "arguments": {
                arg_id: {
                    "text": arg.text,
                    "role": arg.role.value,
                    "confidence": arg.confidence,
                    "start_char": arg.start_char,
                    "end_char": arg.end_char,
                    "parent_id": arg.parent_id
                }
                for arg_id, arg in self.arguments.items()
            },
            "attacks": [
                {"from": attacker, "to": attacked}
                for attacker, attacked in self.attacks
            ],
            "grounded_extension": list(self.compute_grounded_extension()),
            "coherence": self.calculate_coherence()
        }

    def to_json(self) -> str:
        """Export framework to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'ArgumentationFramework':
        """
        Create framework from dict.

        Args:
            data: Dict representation

        Returns:
            ArgumentationFramework
        """
        framework = cls()

        # Reconstruct arguments
        for arg_id, arg_data in data.get("arguments", {}).items():
            arg = Argument(
                id=arg_id,
                text=arg_data["text"],
                role=ArgumentRole(arg_data["role"]),
                start_char=arg_data["start_char"],
                end_char=arg_data["end_char"],
                confidence=arg_data["confidence"],
                parent_id=arg_data.get("parent_id")
            )
            framework.add_argument(arg)

        # Reconstruct attacks
        for attack in data.get("attacks", []):
            framework.add_attack(attack["from"], attack["to"])

        return framework

    def visualize_dot(self) -> str:
        """
        Generate Graphviz DOT representation.

        Returns:
            DOT format string
        """
        lines = ["digraph ArgumentationFramework {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        # Grounded extension (highlighted)
        grounded = self.compute_grounded_extension()

        # Nodes
        for arg_id, arg in self.arguments.items():
            label = f"{arg.role.value}\\n{arg.text[:30]}..."
            color = "green" if arg_id in grounded else "lightgray"
            lines.append(f'  "{arg_id}" [label="{label}", fillcolor="{color}", style=filled];')

        # Edges (attacks)
        for attacker, attacked in self.attacks:
            lines.append(f'  "{attacker}" -> "{attacked}" [color=red];')

        lines.append("}")

        return "\n".join(lines)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_framework_from_arguments(
    arguments: List[Argument],
    fallacies: List[Fallacy]
) -> ArgumentationFramework:
    """
    Build argumentation framework from arguments and fallacies.

    Args:
        arguments: List of arguments
        fallacies: List of fallacies

    Returns:
        ArgumentationFramework
    """
    framework = ArgumentationFramework()

    # Add arguments
    framework.add_arguments(arguments)

    # Infer attacks from fallacies
    framework.infer_attacks_from_fallacies(fallacies)

    # Infer attacks from structure
    framework.infer_attacks_from_structure()

    logger.info(
        f"Built argumentation framework: {len(arguments)} arguments, "
        f"{len(framework.attacks)} attacks, coherence={framework.calculate_coherence():.3f}"
    )

    return framework
