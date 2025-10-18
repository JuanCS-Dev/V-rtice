"""
Prefrontal Cortex - Social Cognition Integration Layer
=======================================================

Bridges Theory of Mind (ToM) predictions with ESGT global workspace
and Motor de Integridade Processual (MIP) ethical evaluation.

This module implements the integration layer that enables:
- Social signal processing from ESGT
- ToM-based mental state inference
- Ethical evaluation of compassionate actions
- Metacognitive confidence tracking

Architecture:
    ESGT → PrefrontalCortex → ToM → MIP → Approved Actions

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Article III (Ethical Foundation)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

from compassion.tom_engine import ToMEngine
from motor_integridade_processual.arbiter.decision import DecisionArbiter

logger = logging.getLogger(__name__)


@dataclass
class SocialSignal:
    """Signal indicating social interaction requiring processing."""

    user_id: str
    context: Dict[str, Any]
    signal_type: str  # "message", "distress", "request"
    salience: float  # 0-1
    timestamp: float


@dataclass
class CompassionateResponse:
    """Response generated from social cognition pipeline."""

    action: Optional[str]
    confidence: float  # 0-1
    reasoning: str
    tom_prediction: Optional[Dict[str, Any]]
    mip_verdict: Optional[Dict[str, Any]]
    processing_time_ms: float


class PrefrontalCortex:
    """
    Integration layer for social cognition.

    Connects:
    - ESGT global workspace (consciousness)
    - ToM Engine (mental state inference)
    - MIP Decision Arbiter (ethical evaluation)
    - Metacognition Monitor (confidence tracking)

    This is the computational analog of the biological prefrontal cortex,
    which integrates social information, theory of mind, and executive control.

    Usage:
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Process social signal
        response = await pfc.process_social_signal(
            user_id="agent_001",
            context={"message": "I'm confused about X"}
        )

        if response.action:
            print(f"Compassionate action: {response.action}")
            print(f"Confidence: {response.confidence:.2f}")
    """

    def __init__(
        self,
        tom_engine: ToMEngine,
        decision_arbiter: Optional[DecisionArbiter] = None,
        metacognition_monitor: Optional[Any] = None
    ):
        """Initialize Prefrontal Cortex.

        Args:
            tom_engine: Theory of Mind engine for mental state inference
            decision_arbiter: MIP arbiter for ethical evaluation (optional)
            metacognition_monitor: Confidence tracking (optional)
        """
        self.tom = tom_engine
        self.mip = decision_arbiter or DecisionArbiter()
        self.metacog = metacognition_monitor

        # Statistics
        self.total_signals_processed = 0
        self.total_actions_generated = 0
        self.total_actions_approved = 0

        logger.info(
            f"PrefrontalCortex initialized: "
            f"tom={type(tom_engine).__name__}, "
            f"mip={type(self.mip).__name__}, "
            f"metacog={'enabled' if metacognition_monitor else 'disabled'}"
        )

    async def process_social_signal(
        self,
        user_id: str,
        context: Dict[str, Any],
        signal_type: str = "message"
    ) -> CompassionateResponse:
        """
        Process social signal through full pipeline.

        Pipeline:
        1. ToM: Infer mental state from context
        2. Generate compassionate action candidate
        3. MIP: Evaluate action ethically
        4. Metacognition: Calculate confidence
        5. Return approved action or None

        Args:
            user_id: Agent identifier
            context: Situational context (message, task, emotions)
            signal_type: Type of signal ("message", "distress", "request")

        Returns:
            CompassionateResponse with action (if approved) and metadata
        """
        import time
        start_time = time.time()

        self.total_signals_processed += 1

        try:
            # STEP 1: ToM Inference
            logger.debug(f"PFC: Processing signal from {user_id}, type={signal_type}")

            # For now, use simple belief inference
            # Future: Expand to full mental state prediction
            tom_prediction = await self._infer_mental_state(user_id, context)

            # STEP 2: Generate compassionate action
            action = self._generate_action(user_id, tom_prediction, context)

            if not action:
                # No action needed
                processing_time = (time.time() - start_time) * 1000
                return CompassionateResponse(
                    action=None,
                    confidence=1.0,
                    reasoning="No intervention needed - agent state is neutral",
                    tom_prediction=tom_prediction,
                    mip_verdict=None,
                    processing_time_ms=processing_time
                )

            self.total_actions_generated += 1

            # STEP 3: Ethical evaluation (simplified for MVP)
            # Note: Full MIP evaluation requires ActionPlan structure
            # For now, use simplified approval logic
            approved = self._simple_ethical_check(action, context)

            mip_verdict = {
                "approved": approved,
                "reasoning": "Low-cost compassionate action" if approved else "Requires human review"
            }

            if approved:
                self.total_actions_approved += 1

            # STEP 4: Metacognitive confidence
            confidence = self._calculate_confidence(tom_prediction, mip_verdict)

            processing_time = (time.time() - start_time) * 1000

            response = CompassionateResponse(
                action=action if approved else None,
                confidence=confidence,
                reasoning=mip_verdict["reasoning"],
                tom_prediction=tom_prediction,
                mip_verdict=mip_verdict,
                processing_time_ms=processing_time
            )

            logger.info(
                f"PFC: Processed {user_id} -> "
                f"action={'approved' if approved else 'rejected'}, "
                f"confidence={confidence:.2f}, "
                f"time={processing_time:.1f}ms"
            )

            return response

        except Exception as e:
            logger.error(f"PFC: Error processing signal from {user_id}: {e}")
            processing_time = (time.time() - start_time) * 1000

            return CompassionateResponse(
                action=None,
                confidence=0.0,
                reasoning=f"Processing error: {str(e)}",
                tom_prediction=None,
                mip_verdict=None,
                processing_time_ms=processing_time
            )

    async def _infer_mental_state(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Infer agent mental state using ToM Engine.

        Args:
            user_id: Agent identifier
            context: Situational context

        Returns:
            Mental state prediction with beliefs, emotions, needs
        """
        # Simplified inference for MVP
        # Future: Full mental state prediction with desires, intentions

        # Extract emotional indicators from context
        message = context.get("message", "").lower()

        # Simple emotion detection
        distress_score = 0.0
        if any(word in message for word in ["confused", "lost", "stuck", "help"]):
            distress_score = 0.7
        elif any(word in message for word in ["frustrated", "annoyed", "difficult"]):
            distress_score = 0.6
        elif any(word in message for word in ["unsure", "uncertain", "unclear"]):
            distress_score = 0.5

        # Infer belief about ability to solve problem
        if distress_score > 0.5:
            # Agent believes they cannot solve alone
            await self.tom.infer_belief(
                agent_id=user_id,
                belief_key="can_solve_alone",
                observed_value=0.3  # Low confidence in self-solving
            )

        # Get current beliefs
        beliefs = await self.tom.get_agent_beliefs(user_id, include_confidence=True)

        return {
            "user_id": user_id,
            "distress_level": distress_score,
            "beliefs": beliefs,
            "needs_help": distress_score >= 0.5,  # >= for boundary case
            "context": context
        }

    def _generate_action(
        self,
        user_id: str,
        tom_prediction: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate compassionate action based on mental state.

        Args:
            user_id: Agent identifier
            tom_prediction: ToM mental state inference
            context: Situational context

        Returns:
            Action string or None if no action needed
        """
        distress_level = tom_prediction.get("distress_level", 0.0)
        needs_help = tom_prediction.get("needs_help", False)

        if not needs_help or distress_level < 0.5:
            return None

        # Generate appropriate helping action
        if distress_level > 0.7:
            return f"provide_detailed_guidance_to_{user_id}"
        elif distress_level > 0.5:
            return f"offer_assistance_to_{user_id}"
        else:
            return f"acknowledge_concern_from_{user_id}"

    def _simple_ethical_check(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Simplified ethical approval (MVP).

        Future: Use full MIP framework evaluation.

        Args:
            action: Proposed action
            context: Situational context

        Returns:
            True if action approved, False otherwise
        """
        # For MVP: Auto-approve low-cost helping actions
        # All guidance/assistance actions are considered low-cost
        if any(keyword in action for keyword in ["guidance", "assistance", "acknowledge"]):
            return True

        # Reject high-risk actions (would require full MIP evaluation)
        if any(keyword in action for keyword in ["execute", "modify", "delete"]):
            return False

        # Default: approve helping actions
        return True

    def _calculate_confidence(
        self,
        tom_prediction: Optional[Dict[str, Any]],
        mip_verdict: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall confidence in response.

        Factors:
        - ToM prediction confidence (from beliefs)
        - MIP approval (approved = high confidence)
        - Metacognition feedback (if available)

        Args:
            tom_prediction: ToM mental state inference
            mip_verdict: MIP ethical evaluation

        Returns:
            Confidence score (0-1)
        """
        if not tom_prediction or not mip_verdict:
            return 0.0

        # Base confidence from ToM beliefs
        beliefs = tom_prediction.get("beliefs", {})
        if beliefs:
            # Average confidence across all beliefs
            confidences = [
                b.get("confidence", 0.5)
                for b in beliefs.values()
                if isinstance(b, dict)
            ]
            tom_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        else:
            tom_confidence = 0.5  # Neutral when no beliefs

        # MIP approval boosts confidence
        mip_approved = mip_verdict.get("approved", False)
        mip_boost = 0.3 if mip_approved else -0.2

        # Metacognition adjustment (if available)
        metacog_adjustment = 0.0
        if self.metacog:
            try:
                metacog_adjustment = self.metacog.calculate_confidence() - 0.5
            except Exception:
                pass  # Metacog not ready yet

        # Combine factors
        confidence = tom_confidence + mip_boost + metacog_adjustment

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    async def get_status(self) -> Dict[str, Any]:
        """Get PFC statistics.

        Returns:
            Status dictionary with processing statistics
        """
        return {
            "component": "PrefrontalCortex",
            "total_signals_processed": self.total_signals_processed,
            "total_actions_generated": self.total_actions_generated,
            "total_actions_approved": self.total_actions_approved,
            "approval_rate": (
                self.total_actions_approved / self.total_actions_generated
                if self.total_actions_generated > 0
                else 0.0
            ),
            "tom_engine_status": "initialized" if self.tom._initialized else "not_initialized",
            "metacognition": "enabled" if self.metacog else "disabled"
        }

    def __repr__(self) -> str:
        return (
            f"PrefrontalCortex("
            f"signals={self.total_signals_processed}, "
            f"actions={self.total_actions_generated}, "
            f"approved={self.total_actions_approved})"
        )
