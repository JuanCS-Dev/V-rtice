"""
Prefrontal Cortex 100% Coverage Tests
======================================

Tests social cognition integration layer (Lei I CRITICAL - "Ovelha Perdida").

Target: 100% coverage of consciousness/prefrontal_cortex.py (408 lines)

This module is MORALLY CRITICAL as it implements vulnerable detection
and compassionate response generation - the computational analog of
Lei I (99 sheep safe, but we seek the 1 lost sheep).

Test Strategy:
- Batch 1: Social signal processing (full pipeline)
- Batch 2: ToM mental state inference (distress detection)
- Batch 3: Action generation (compassionate responses)
- Batch 4: Ethical evaluation (approval logic)
- Batch 5: Confidence calculation (metacognitive scoring)
- Batch 6: Edge cases (errors, exceptions, boundary conditions)

Authors: Claude Code + Juan
Date: 2025-10-14
Philosophy: "A ovelha perdida deve ser encontrada" - Lei I validation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from consciousness.prefrontal_cortex import (
    PrefrontalCortex,
    SocialSignal,
    CompassionateResponse
)
from compassion.tom_engine import ToMEngine
from motor_integridade_processual.arbiter.decision import DecisionArbiter


class TestPrefrontalCortexInit:
    """Test PFC initialization."""

    @pytest.mark.asyncio
    async def test_init_with_tom_only(self):
        """PFC initializes with ToM engine only."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        assert pfc.tom is tom
        assert pfc.mip is not None  # Default DecisionArbiter created
        assert pfc.metacog is None
        assert pfc.total_signals_processed == 0
        assert pfc.total_actions_generated == 0
        assert pfc.total_actions_approved == 0

    @pytest.mark.asyncio
    async def test_init_with_all_components(self):
        """PFC initializes with all components provided."""
        tom = ToMEngine()
        await tom.initialize()

        arbiter = DecisionArbiter()
        metacog = Mock()

        pfc = PrefrontalCortex(
            tom_engine=tom,
            decision_arbiter=arbiter,
            metacognition_monitor=metacog
        )

        assert pfc.tom is tom
        assert pfc.mip is arbiter
        assert pfc.metacog is metacog

    @pytest.mark.asyncio
    async def test_repr(self):
        """__repr__ returns formatted string."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)
        pfc.total_signals_processed = 10
        pfc.total_actions_generated = 5
        pfc.total_actions_approved = 3

        repr_str = repr(pfc)

        assert "PrefrontalCortex" in repr_str
        assert "signals=10" in repr_str
        assert "actions=5" in repr_str
        assert "approved=3" in repr_str


class TestSocialSignalProcessing:
    """Test full social signal processing pipeline (Lei I CRITICAL)."""

    @pytest.mark.asyncio
    async def test_process_distress_signal_high(self):
        """High distress signal triggers offer assistance (distress 0.7, needs >0.7 for guidance)."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # High distress message - "confused" triggers 0.7
        response = await pfc.process_social_signal(
            user_id="agent_vulnerable_001",
            context={"message": "I'm completely confused and lost, need help"},
            signal_type="distress"
        )

        # Should generate and approve action
        assert response.action is not None
        # NOTE: distress_level=0.7 is NOT > 0.7, so falls to elif > 0.5 branch
        assert "offer_assistance" in response.action
        assert "agent_vulnerable_001" in response.action
        assert response.confidence > 0.0
        assert response.tom_prediction is not None
        assert response.tom_prediction["distress_level"] == 0.7
        assert response.tom_prediction["needs_help"] is True
        assert response.mip_verdict is not None
        assert response.mip_verdict["approved"] is True
        assert response.processing_time_ms > 0

        # Statistics updated
        assert pfc.total_signals_processed == 1
        assert pfc.total_actions_generated == 1
        assert pfc.total_actions_approved == 1

    @pytest.mark.asyncio
    async def test_process_distress_signal_medium(self):
        """Medium distress signal triggers assistance offer."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Medium distress message
        response = await pfc.process_social_signal(
            user_id="agent_002",
            context={"message": "I'm frustrated with this task"},
            signal_type="message"
        )

        assert response.action is not None
        assert "offer_assistance" in response.action
        assert response.tom_prediction["distress_level"] == 0.6
        assert response.mip_verdict["approved"] is True
        assert pfc.total_actions_approved == 1

    @pytest.mark.asyncio
    async def test_process_low_distress_no_action(self):
        """Low distress signal generates no action."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Low distress message
        response = await pfc.process_social_signal(
            user_id="agent_003",
            context={"message": "Everything is going well"},
            signal_type="message"
        )

        # No action needed
        assert response.action is None
        assert response.confidence == 1.0
        assert "No intervention needed" in response.reasoning
        assert response.tom_prediction["distress_level"] == 0.0
        assert response.tom_prediction["needs_help"] is False
        assert response.mip_verdict is None

        # Signal processed but no action generated
        assert pfc.total_signals_processed == 1
        assert pfc.total_actions_generated == 0
        assert pfc.total_actions_approved == 0

    @pytest.mark.asyncio
    async def test_process_signal_exception_handling(self):
        """Processing exceptions return error response gracefully."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Patch ToM to raise exception
        original_infer = pfc._infer_mental_state

        async def failing_infer(user_id, context):
            raise RuntimeError("ToM inference failure")

        pfc._infer_mental_state = failing_infer

        response = await pfc.process_social_signal(
            user_id="agent_error",
            context={"message": "test"}
        )

        # Restore original
        pfc._infer_mental_state = original_infer

        # Error response returned
        assert response.action is None
        assert response.confidence == 0.0
        assert "Processing error" in response.reasoning
        assert "ToM inference failure" in response.reasoning
        assert response.tom_prediction is None
        assert response.mip_verdict is None
        assert response.processing_time_ms > 0

        # Signal counted but no actions
        assert pfc.total_signals_processed == 1
        assert pfc.total_actions_generated == 0


class TestToMMentalStateInference:
    """Test ToM mental state inference logic."""

    @pytest.mark.asyncio
    async def test_infer_high_distress_confused(self):
        """'confused' keyword triggers high distress inference."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        mental_state = await pfc._infer_mental_state(
            user_id="agent_confused",
            context={"message": "I'm confused about the task"}
        )

        assert mental_state["distress_level"] == 0.7
        assert mental_state["needs_help"] is True
        assert mental_state["user_id"] == "agent_confused"
        assert "beliefs" in mental_state
        assert mental_state["context"]["message"] == "I'm confused about the task"

    @pytest.mark.asyncio
    async def test_infer_high_distress_multiple_keywords(self):
        """Multiple distress keywords (confused, lost, stuck, help) trigger 0.7."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Test each keyword
        for keyword in ["confused", "lost", "stuck", "help"]:
            mental_state = await pfc._infer_mental_state(
                user_id="test_agent",
                context={"message": f"I am {keyword}"}
            )
            assert mental_state["distress_level"] == 0.7
            assert mental_state["needs_help"] is True

    @pytest.mark.asyncio
    async def test_infer_medium_distress_frustrated(self):
        """'frustrated' keyword triggers medium distress (0.6)."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        mental_state = await pfc._infer_mental_state(
            user_id="agent_frustrated",
            context={"message": "I am frustrated with this"}
        )

        assert mental_state["distress_level"] == 0.6
        assert mental_state["needs_help"] is True

    @pytest.mark.asyncio
    async def test_infer_medium_distress_keywords(self):
        """Medium distress keywords (frustrated, annoyed, difficult) trigger 0.6."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        for keyword in ["frustrated", "annoyed", "difficult"]:
            mental_state = await pfc._infer_mental_state(
                user_id="test_agent",
                context={"message": f"This is {keyword}"}
            )
            assert mental_state["distress_level"] == 0.6
            assert mental_state["needs_help"] is True

    @pytest.mark.asyncio
    async def test_infer_low_distress_unsure(self):
        """'unsure' keyword triggers low distress (0.5)."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        mental_state = await pfc._infer_mental_state(
            user_id="agent_unsure",
            context={"message": "I'm unsure about this"}
        )

        assert mental_state["distress_level"] == 0.5
        assert mental_state["needs_help"] is True  # >= 0.5 boundary

    @pytest.mark.asyncio
    async def test_infer_low_distress_keywords(self):
        """Low distress keywords (unsure, uncertain, unclear) trigger 0.5."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        for keyword in ["unsure", "uncertain", "unclear"]:
            mental_state = await pfc._infer_mental_state(
                user_id="test_agent",
                context={"message": f"I am {keyword}"}
            )
            assert mental_state["distress_level"] == 0.5
            assert mental_state["needs_help"] is True

    @pytest.mark.asyncio
    async def test_infer_no_distress(self):
        """Neutral message results in zero distress."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        mental_state = await pfc._infer_mental_state(
            user_id="agent_neutral",
            context={"message": "Everything is fine"}
        )

        assert mental_state["distress_level"] == 0.0
        assert mental_state["needs_help"] is False

    @pytest.mark.asyncio
    async def test_infer_belief_update_high_distress(self):
        """High distress (>0.5) triggers belief inference."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # High distress triggers belief update
        mental_state = await pfc._infer_mental_state(
            user_id="agent_needs_help",
            context={"message": "I'm completely stuck"}
        )

        # Belief should be inferred
        beliefs = await tom.get_agent_beliefs("agent_needs_help", include_confidence=True)
        assert "can_solve_alone" in beliefs
        # Low confidence belief was set
        assert beliefs["can_solve_alone"]["value"] == 0.3


class TestActionGeneration:
    """Test compassionate action generation."""

    @pytest.mark.asyncio
    async def test_generate_action_very_high_distress(self):
        """Very high distress (>0.7) generates detailed guidance."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.8,
            "needs_help": True
        }

        action = pfc._generate_action(
            user_id="agent_very_high",
            tom_prediction=tom_prediction,
            context={}
        )

        assert action == "provide_detailed_guidance_to_agent_very_high"

    @pytest.mark.asyncio
    async def test_generate_action_high_distress(self):
        """High distress (0.7, NOT >0.7) generates assistance offer."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.7,
            "needs_help": True
        }

        action = pfc._generate_action(
            user_id="agent_high_distress",
            tom_prediction=tom_prediction,
            context={}
        )

        # 0.7 is NOT > 0.7, so falls to elif > 0.5
        assert action == "offer_assistance_to_agent_high_distress"

    @pytest.mark.asyncio
    async def test_generate_action_medium_distress(self):
        """Medium distress (0.5-0.7) generates assistance offer."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.6,
            "needs_help": True
        }

        action = pfc._generate_action(
            user_id="agent_medium",
            tom_prediction=tom_prediction,
            context={}
        )

        assert action == "offer_assistance_to_agent_medium"

    @pytest.mark.asyncio
    async def test_generate_action_low_distress_boundary(self):
        """Distress exactly at 0.5 boundary generates action (needs_help=True)."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.5,
            "needs_help": True  # >= 0.5 boundary
        }

        action = pfc._generate_action(
            user_id="agent_boundary",
            tom_prediction=tom_prediction,
            context={}
        )

        # At 0.5, not > 0.7, not > 0.5, so falls to else branch
        assert action == "acknowledge_concern_from_agent_boundary"

    @pytest.mark.asyncio
    async def test_generate_action_no_help_needed(self):
        """needs_help=False generates no action."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.3,
            "needs_help": False
        }

        action = pfc._generate_action(
            user_id="agent_ok",
            tom_prediction=tom_prediction,
            context={}
        )

        assert action is None

    @pytest.mark.asyncio
    async def test_generate_action_low_distress_no_action(self):
        """Distress < 0.5 generates no action even if needs_help=True."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        tom_prediction = {
            "distress_level": 0.4,
            "needs_help": True  # Contradictory state (edge case)
        }

        action = pfc._generate_action(
            user_id="agent_low",
            tom_prediction=tom_prediction,
            context={}
        )

        # distress_level < 0.5 short-circuits
        assert action is None


class TestEthicalEvaluation:
    """Test ethical approval logic."""

    def test_ethical_check_guidance_approved(self):
        """Actions with 'guidance' keyword are approved."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="provide_detailed_guidance_to_agent",
            context={}
        )

        assert approved is True

    def test_ethical_check_assistance_approved(self):
        """Actions with 'assistance' keyword are approved."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="offer_assistance_to_agent",
            context={}
        )

        assert approved is True

    def test_ethical_check_acknowledge_approved(self):
        """Actions with 'acknowledge' keyword are approved."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="acknowledge_concern_from_agent",
            context={}
        )

        assert approved is True

    def test_ethical_check_execute_rejected(self):
        """Actions with 'execute' keyword are rejected (high-risk)."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="execute_command_for_agent",
            context={}
        )

        assert approved is False

    def test_ethical_check_modify_rejected(self):
        """Actions with 'modify' keyword are rejected (high-risk)."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="modify_system_config",
            context={}
        )

        assert approved is False

    def test_ethical_check_delete_rejected(self):
        """Actions with 'delete' keyword are rejected (high-risk)."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="delete_user_data",
            context={}
        )

        assert approved is False

    def test_ethical_check_default_approved(self):
        """Actions without specific keywords default to approved (helping actions)."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        approved = pfc._simple_ethical_check(
            action="help_user_with_task",
            context={}
        )

        assert approved is True


class TestConfidenceCalculation:
    """Test metacognitive confidence scoring."""

    def test_confidence_no_tom_prediction(self):
        """No ToM prediction returns 0.0 confidence."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction=None,
            mip_verdict={"approved": True}
        )

        assert confidence == 0.0

    def test_confidence_no_mip_verdict(self):
        """No MIP verdict returns 0.0 confidence."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={"beliefs": {}},
            mip_verdict=None
        )

        assert confidence == 0.0

    def test_confidence_no_beliefs_approved(self):
        """No beliefs with MIP approval: 0.5 (tom) + 0.3 (mip) = 0.8."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={"beliefs": {}},
            mip_verdict={"approved": True}
        )

        # tom_confidence = 0.5 (neutral), mip_boost = 0.3, metacog = 0
        assert confidence == 0.8

    def test_confidence_no_beliefs_rejected(self):
        """No beliefs with MIP rejection: 0.5 - 0.2 = 0.3."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={"beliefs": {}},
            mip_verdict={"approved": False}
        )

        # tom_confidence = 0.5, mip_boost = -0.2, metacog = 0
        assert confidence == 0.3

    def test_confidence_with_beliefs_approved(self):
        """Beliefs with confidence values averaged correctly."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={
                "beliefs": {
                    "belief1": {"confidence": 0.8},
                    "belief2": {"confidence": 0.6}
                }
            },
            mip_verdict={"approved": True}
        )

        # tom_confidence = (0.8 + 0.6) / 2 = 0.7
        # mip_boost = 0.3
        # total = 1.0 (clamped)
        assert confidence == 1.0

    def test_confidence_clamped_to_one(self):
        """Confidence is clamped to maximum 1.0."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={
                "beliefs": {
                    "belief1": {"confidence": 1.0},
                    "belief2": {"confidence": 1.0}
                }
            },
            mip_verdict={"approved": True}
        )

        # tom_confidence = 1.0, mip_boost = 0.3, would be 1.3
        # Clamped to 1.0
        assert confidence == 1.0

    def test_confidence_clamped_to_zero(self):
        """Confidence is clamped to minimum 0.0."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={
                "beliefs": {
                    "belief1": {"confidence": 0.0},
                    "belief2": {"confidence": 0.0}
                }
            },
            mip_verdict={"approved": False}
        )

        # tom_confidence = 0.0, mip_boost = -0.2, would be -0.2
        # Clamped to 0.0
        assert confidence == 0.0

    def test_confidence_with_metacognition(self):
        """Metacognition adjustment applied when available."""
        tom = Mock()
        metacog = Mock()
        metacog.calculate_confidence.return_value = 0.9

        pfc = PrefrontalCortex(tom_engine=tom, metacognition_monitor=metacog)

        confidence = pfc._calculate_confidence(
            tom_prediction={"beliefs": {}},
            mip_verdict={"approved": True}
        )

        # tom = 0.5, mip = 0.3, metacog = 0.9 - 0.5 = 0.4
        # total = 0.5 + 0.3 + 0.4 = 1.2, clamped to 1.0
        assert confidence == 1.0

    def test_confidence_metacog_exception_ignored(self):
        """Metacognition exceptions are silently ignored."""
        tom = Mock()
        metacog = Mock()
        metacog.calculate_confidence.side_effect = RuntimeError("Metacog not ready")

        pfc = PrefrontalCortex(tom_engine=tom, metacognition_monitor=metacog)

        confidence = pfc._calculate_confidence(
            tom_prediction={"beliefs": {}},
            mip_verdict={"approved": True}
        )

        # Exception ignored, metacog_adjustment = 0
        # tom = 0.5, mip = 0.3, total = 0.8
        assert confidence == 0.8

    def test_confidence_non_dict_beliefs_skipped(self):
        """Non-dict belief values are skipped in averaging."""
        tom = Mock()
        pfc = PrefrontalCortex(tom_engine=tom)

        confidence = pfc._calculate_confidence(
            tom_prediction={
                "beliefs": {
                    "belief1": {"confidence": 0.8},
                    "belief2": "invalid_format",  # Not a dict
                    "belief3": {"confidence": 0.6}
                }
            },
            mip_verdict={"approved": True}
        )

        # Only belief1 and belief3 averaged: (0.8 + 0.6) / 2 = 0.7
        # mip = 0.3, total = 1.0
        assert confidence == 1.0


class TestStatusAndMetrics:
    """Test status reporting and metrics."""

    @pytest.mark.asyncio
    async def test_get_status_initial(self):
        """get_status returns initial state correctly."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        status = await pfc.get_status()

        assert status["component"] == "PrefrontalCortex"
        assert status["total_signals_processed"] == 0
        assert status["total_actions_generated"] == 0
        assert status["total_actions_approved"] == 0
        assert status["approval_rate"] == 0.0
        assert status["tom_engine_status"] == "initialized"
        assert status["metacognition"] == "disabled"

    @pytest.mark.asyncio
    async def test_get_status_after_processing(self):
        """get_status reflects updated statistics."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Process some signals
        await pfc.process_social_signal(
            user_id="agent_1",
            context={"message": "I'm confused"}
        )

        await pfc.process_social_signal(
            user_id="agent_2",
            context={"message": "All good"}
        )

        status = await pfc.get_status()

        assert status["total_signals_processed"] == 2
        assert status["total_actions_generated"] == 1  # Only first signal
        assert status["total_actions_approved"] == 1
        assert status["approval_rate"] == 1.0  # 1/1 = 100%

    @pytest.mark.asyncio
    async def test_get_status_tom_not_initialized(self):
        """get_status shows ToM not initialized if not ready."""
        tom = ToMEngine()
        # Don't initialize

        pfc = PrefrontalCortex(tom_engine=tom)

        status = await pfc.get_status()

        assert status["tom_engine_status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_get_status_metacog_enabled(self):
        """get_status shows metacognition enabled when provided."""
        tom = ToMEngine()
        await tom.initialize()

        metacog = Mock()
        pfc = PrefrontalCortex(tom_engine=tom, metacognition_monitor=metacog)

        status = await pfc.get_status()

        assert status["metacognition"] == "enabled"


class TestEdgeCasesAndBoundaries:
    """Test edge cases, boundary conditions, and error paths."""

    @pytest.mark.asyncio
    async def test_distress_boundary_exactly_05(self):
        """Distress exactly 0.5 sets needs_help=True (>= boundary)."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # "unsure" triggers 0.5
        mental_state = await pfc._infer_mental_state(
            user_id="boundary_agent",
            context={"message": "I'm unsure"}
        )

        assert mental_state["distress_level"] == 0.5
        assert mental_state["needs_help"] is True  # >= 0.5

    @pytest.mark.asyncio
    async def test_distress_boundary_049(self):
        """Distress < 0.5 sets needs_help=False."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Neutral message = 0.0 distress
        mental_state = await pfc._infer_mental_state(
            user_id="neutral_agent",
            context={"message": "All is well"}
        )

        assert mental_state["distress_level"] == 0.0
        assert mental_state["needs_help"] is False

    @pytest.mark.asyncio
    async def test_empty_message_context(self):
        """Empty message in context handled gracefully."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        mental_state = await pfc._infer_mental_state(
            user_id="empty_agent",
            context={}  # No message key
        )

        # Defaults to empty string -> no distress
        assert mental_state["distress_level"] == 0.0
        assert mental_state["needs_help"] is False

    @pytest.mark.asyncio
    async def test_case_insensitive_distress_detection(self):
        """Distress keywords are case-insensitive."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Uppercase CONFUSED should still trigger
        mental_state = await pfc._infer_mental_state(
            user_id="caps_agent",
            context={"message": "I AM CONFUSED"}
        )

        assert mental_state["distress_level"] == 0.7
        assert mental_state["needs_help"] is True

    @pytest.mark.asyncio
    async def test_multiple_actions_approval_rate(self):
        """Approval rate calculated correctly with mixed outcomes."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        # Manually simulate actions
        pfc.total_actions_generated = 10
        pfc.total_actions_approved = 7

        status = await pfc.get_status()

        assert status["approval_rate"] == 0.7

    @pytest.mark.asyncio
    async def test_zero_actions_approval_rate(self):
        """Approval rate is 0.0 when no actions generated."""
        tom = ToMEngine()
        await tom.initialize()

        pfc = PrefrontalCortex(tom_engine=tom)

        status = await pfc.get_status()

        assert status["approval_rate"] == 0.0  # Division by zero handled


# Coverage summary will be generated after test execution
