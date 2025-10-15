"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - CBR Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/cbr_engine.py
Purpose: Case-Based Reasoning cycle (Retrieve → Reuse → Revise → Retain)

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-15)

DOUTRINA:
├─ Lei Zero: Precedentes aumentam florescimento (consistência)
├─ Lei I: Precedentes minoritários não são descartados
└─ Padrão Pagani: Real precedents, tested retrieval

SCIENTIFIC BASIS:
└─ Aamodt & Plaza (1994) - Case-Based Reasoning: Foundational Issues
    Artificial Intelligence Review 8: 395-416
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from justice.precedent_database import PrecedentDB, CasePrecedent


@dataclass
class CBRResult:
    """Result from CBR reasoning process."""
    suggested_action: str
    precedent_id: int
    confidence: float
    rationale: str


class CBREngine:
    """Case-Based Reasoning engine for ethical decision-making.

    Implements the 4-step CBR cycle:
    1. Retrieve: Find similar past cases
    2. Reuse: Adapt past solution to current case
    3. Revise: Validate with constitutional rules
    4. Retain: Store new case as precedent
    """

    def __init__(self, db: PrecedentDB):
        """Initialize CBR engine.

        Args:
            db: PrecedentDB instance for precedent storage/retrieval
        """
        self.db = db

    async def retrieve(self, current_case: Dict[str, Any]) -> List[CasePrecedent]:
        """Retrieve similar past cases (Step 1: Retrieve).

        Args:
            current_case: Current case to find precedents for

        Returns:
            List of similar CasePrecedent objects
        """
        # Generate embedding for current case
        embedding = self.db.embedder.embed_case(current_case)

        # Find similar cases via vector similarity
        similar = await self.db.find_similar(embedding, limit=5)

        return similar

    async def reuse(
        self, similar_cases: List[CasePrecedent], current: Dict[str, Any]
    ) -> Optional[CBRResult]:
        """Adapt past solution to current case (Step 2: Reuse).

        Args:
            similar_cases: List of similar precedents
            current: Current case details

        Returns:
            CBRResult with suggested action, or None if confidence too low
        """
        if not similar_cases:
            return None

        # Use most similar case (first in list from find_similar)
        # Cases are already ordered by similarity from retrieve step
        best = similar_cases[0]

        # Calculate confidence
        confidence = self._calculate_confidence(best, current)

        # Require high confidence (0.7) to use precedent
        if confidence < 0.7:
            return None

        return CBRResult(
            suggested_action=best.action_taken,
            precedent_id=best.id,
            confidence=confidence,
            rationale=f"Following precedent #{best.id} (success: {best.success:.2f})"
        )

    def _calculate_confidence(
        self, precedent: CasePrecedent, current: Dict[str, Any]
    ) -> float:
        """Calculate confidence in using a precedent.

        Confidence = success_rate * 0.9 (conservative)

        Args:
            precedent: Past case precedent
            current: Current case

        Returns:
            Confidence score (0.0-1.0)
        """
        success = precedent.success if precedent.success is not None else 0.5
        return success * 0.9  # Conservative multiplier

    async def revise(
        self, suggestion: CBRResult, validators: List[Any]
    ) -> Dict[str, Any]:
        """Validate suggestion against constitutional rules (Step 3: Revise).

        Args:
            suggestion: CBRResult to validate
            validators: List of validator objects (e.g., DDL engine)

        Returns:
            {"valid": bool, "reason": str} validation result
        """
        # Validate with each validator
        for validator in validators:
            result = await validator.validate({"action_type": suggestion.suggested_action})

            if not result["valid"]:
                return {
                    "valid": False,
                    "reason": result.get("violations", "Validation failed")
                }

        return {"valid": True}

    async def retain(self, case: CasePrecedent):
        """Store new case as precedent (Step 4: Retain).

        Args:
            case: CasePrecedent to store
        """
        await self.db.store(case)

    async def full_cycle(
        self, current_case: Dict[str, Any], validators: List[Any]
    ) -> Optional[CBRResult]:
        """Execute complete CBR cycle: Retrieve → Reuse → Revise → (Retain).

        Args:
            current_case: Current case to reason about
            validators: List of validators for revise step

        Returns:
            CBRResult if successful, None otherwise
        """
        # 1. Retrieve
        similar = await self.retrieve(current_case)

        # 2. Reuse
        suggestion = await self.reuse(similar, current_case)

        if not suggestion:
            return None

        # 3. Revise (validate)
        validation = await self.revise(suggestion, validators)

        if not validation["valid"]:
            return None

        # 4. Retain happens externally (after execution + feedback)

        return suggestion
