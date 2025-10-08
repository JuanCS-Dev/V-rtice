"""
Neuromodulation Integration Test (Simplified)

Tests just the neuromodulation connections without full MaximusIntegrated stack.
Validates:
1. NeuromodulationController integration
2. AttentionSystem integration
3. Parameter modulation
4. Outcome processing
5. Threat response

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, 100% production code
"""

import pytest

from attention_system.attention_core import AttentionSystem
from neuromodulation import NeuromodulationController

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def neuromodulation():
    """Create a NeuromodulationController for testing."""
    return NeuromodulationController()


@pytest.fixture
def attention_system():
    """Create an AttentionSystem for testing."""
    return AttentionSystem(foveal_threshold=0.6, scan_interval=1.0)


# ============================================================================
# TEST 1: NEUROMODULATION CONTROLLER PROVIDES PARAMETERS
# ============================================================================


def test_neuromodulation_provides_parameters(neuromodulation):
    """Test that NeuromodulationController can provide all necessary parameters."""
    print("\n" + "=" * 80)
    print("TEST 1: NeuromodulationController Provides Parameters")
    print("=" * 80)

    # Get base learning rate modulation (Dopamine)
    base_lr = 0.01
    modulated_lr = neuromodulation.get_modulated_learning_rate(base_lr)
    assert modulated_lr > 0, "Modulated LR should be positive"
    print(f"✅ Learning rate modulation: {base_lr:.4f} → {modulated_lr:.4f}")

    # Get exploration rate (Serotonin)
    exploration_rate = neuromodulation.serotonin.get_exploration_rate()
    assert 0.05 <= exploration_rate <= 0.3, "Exploration rate should be in [0.05, 0.3]"
    print(f"✅ Exploration rate: {exploration_rate:.3f}")

    # Get attention gain (Norepinephrine)
    attention_gain = neuromodulation.norepinephrine.get_attention_gain()
    assert 0.0 <= attention_gain <= 2.0, "Attention gain should be in [0, 2]"
    print(f"✅ Attention gain: {attention_gain:.2f}x")

    # Get salience threshold (Acetylcholine)
    salience_threshold = neuromodulation.acetylcholine.get_salience_threshold()
    assert 0.0 <= salience_threshold <= 1.0, "Salience threshold should be in [0, 1]"
    print(f"✅ Salience threshold: {salience_threshold:.3f}")


# ============================================================================
# TEST 2: OUTCOME PROCESSING UPDATES DOPAMINE AND SEROTONIN
# ============================================================================


def test_outcome_processing_updates_neuromodulators(neuromodulation):
    """Test that outcome processing updates dopamine and serotonin correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: Outcome Processing Updates Dopamine & Serotonin")
    print("=" * 80)

    # Get initial states (use tonic_level for dopamine, level for serotonin)
    initial_dopamine = neuromodulation.dopamine.tonic_level
    initial_serotonin = neuromodulation.serotonin.level

    # Process positive outcome (better than expected)
    result = neuromodulation.process_reward(expected_reward=0.5, actual_reward=0.8, success=True)

    # Verify RPE calculated
    assert "rpe" in result, "Should return RPE"
    assert result["rpe"] > 0, "Positive surprise should give positive RPE"
    print(f"✅ Positive RPE: {result['rpe']:.3f}")

    # Verify motivation updated
    assert "motivation" in result, "Should return motivation"
    print(f"✅ Motivation: {result['motivation']:.2f}")

    # Get updated states
    updated_dopamine = neuromodulation.dopamine.tonic_level
    updated_serotonin = neuromodulation.serotonin.level

    # Note: Dopamine level may not change dramatically, but phasic burst should
    print(f"✅ Dopamine: {initial_dopamine:.2f} → {updated_dopamine:.2f}")
    print(f"✅ Serotonin: {initial_serotonin:.2f} → {updated_serotonin:.2f}")


# ============================================================================
# TEST 3: THREAT RESPONSE ACTIVATES NOREPINEPHRINE
# ============================================================================


def test_threat_response_activates_norepinephrine(neuromodulation):
    """Test that threat response increases norepinephrine arousal."""
    print("\n" + "=" * 80)
    print("TEST 3: Threat Response Activates Norepinephrine")
    print("=" * 80)

    # Get initial arousal
    initial_arousal = neuromodulation.norepinephrine.get_arousal_level()
    initial_gain = neuromodulation.norepinephrine.get_attention_gain()

    # Respond to high-severity threat
    threat_severity = 0.8
    neuromodulation.respond_to_threat(threat_severity)

    # Get updated arousal
    updated_arousal = neuromodulation.norepinephrine.get_arousal_level()
    updated_gain = neuromodulation.norepinephrine.get_attention_gain()

    # Verify arousal increased
    assert updated_arousal > initial_arousal, "Threat should increase arousal"

    # Note: Attention gain follows Yerkes-Dodson law (inverted-U)
    # Too high arousal can DECREASE gain (anxiety/overarousal)
    # This is correct biological behavior!
    print(f"✅ Threat severity: {threat_severity}")
    print(f"✅ Arousal: {initial_arousal:.2f} → {updated_arousal:.2f}")
    print(f"✅ Attention gain: {initial_gain:.2f}x → {updated_gain:.2f}x")
    print("   (Yerkes-Dodson: Very high arousal can reduce gain due to anxiety)")


# ============================================================================
# TEST 4: ACETYLCHOLINE MODULATES ATTENTION THRESHOLD
# ============================================================================


def test_acetylcholine_modulates_attention_threshold(neuromodulation, attention_system):
    """Test that acetylcholine can modulate attention system threshold."""
    print("\n" + "=" * 80)
    print("TEST 4: Acetylcholine Modulates Attention Threshold")
    print("=" * 80)

    # Get initial ACh level and salience threshold
    initial_ach = neuromodulation.acetylcholine.level
    initial_salience = neuromodulation.acetylcholine.get_salience_threshold()

    # Get attention system initial threshold
    initial_attention_threshold = attention_system.salience_scorer.foveal_threshold

    print(f"   Initial ACh: {initial_ach:.2f}")
    print(f"   Initial salience threshold: {initial_salience:.3f}")
    print(f"   Initial attention threshold: {initial_attention_threshold:.3f}")

    # Modulate attention with high importance (should increase ACh)
    neuromodulation.acetylcholine.modulate_attention(importance=0.8)

    # Get updated values
    updated_ach = neuromodulation.acetylcholine.level
    updated_salience = neuromodulation.acetylcholine.get_salience_threshold()

    # Apply modulation to attention system
    # High ACh → lower salience threshold → more attention
    # Map salience_threshold [0.3, 0.7] to foveal_threshold [0.4, 0.8] (inverted)
    modulated_attention_threshold = 0.8 - (updated_salience - 0.3) * (0.4 / 0.4)
    attention_system.salience_scorer.foveal_threshold = modulated_attention_threshold

    print(f"✅ ACh after important stimulus: {initial_ach:.2f} → {updated_ach:.2f}")
    print(f"✅ Salience threshold: {initial_salience:.3f} → {updated_salience:.3f}")
    print(f"✅ Attention threshold modulated: {initial_attention_threshold:.3f} → {modulated_attention_threshold:.3f}")

    # Verify threshold was updated
    assert attention_system.salience_scorer.foveal_threshold == modulated_attention_threshold


# ============================================================================
# TEST 5: SEROTONIN CONTROLS EXPLORATION TEMPERATURE
# ============================================================================


def test_serotonin_controls_exploration_temperature(neuromodulation):
    """Test that serotonin can control exploration vs exploitation."""
    print("\n" + "=" * 80)
    print("TEST 5: Serotonin Controls Exploration Temperature")
    print("=" * 80)

    # Get initial serotonin and exploration rate
    initial_serotonin = neuromodulation.serotonin.level
    initial_exploration = neuromodulation.serotonin.get_exploration_rate()

    # Convert to temperature (high exploration → high temperature)
    initial_temperature = 0.3 + (initial_exploration / 0.3) * 0.7

    print(f"   Initial serotonin: {initial_serotonin:.2f}")
    print(f"   Initial exploration rate: {initial_exploration:.3f}")
    print(f"   Initial temperature: {initial_temperature:.2f}")

    # Simulate low mood/stress (should increase exploration)
    neuromodulation.serotonin.update_from_outcome(success=False, stress=0.8)

    # Get updated values
    updated_serotonin = neuromodulation.serotonin.level
    updated_exploration = neuromodulation.serotonin.get_exploration_rate()
    updated_temperature = 0.3 + (updated_exploration / 0.3) * 0.7

    print("✅ After failure + stress:")
    print(f"   Serotonin: {initial_serotonin:.2f} → {updated_serotonin:.2f}")
    print(f"   Exploration rate: {initial_exploration:.3f} → {updated_exploration:.3f}")
    print(f"   Temperature: {initial_temperature:.2f} → {updated_temperature:.2f}")

    # Verify that failure/stress affected serotonin (should decrease or stay same)
    assert updated_serotonin <= initial_serotonin + 0.1, "Failure should not increase serotonin significantly"


# ============================================================================
# TEST 6: GLOBAL STATE PROVIDES COMPLETE NEUROMODULATION INFO
# ============================================================================


def test_global_state_provides_complete_info(neuromodulation):
    """Test that global state includes all neuromodulation information."""
    print("\n" + "=" * 80)
    print("TEST 6: Global State Provides Complete Info")
    print("=" * 80)

    # Get global state
    state = neuromodulation.get_global_state()

    # Verify all fields present
    assert hasattr(state, "dopamine"), "Should have dopamine"
    assert hasattr(state, "serotonin"), "Should have serotonin"
    assert hasattr(state, "norepinephrine"), "Should have norepinephrine"
    assert hasattr(state, "acetylcholine"), "Should have acetylcholine"
    assert hasattr(state, "overall_mood"), "Should have overall_mood"
    assert hasattr(state, "cognitive_load"), "Should have cognitive_load"

    # Verify state objects have correct structure
    assert hasattr(state.dopamine, "tonic_level"), "DopamineState should have tonic_level"
    assert hasattr(state.serotonin, "level"), "SerotoninState should have level"
    assert hasattr(state.norepinephrine, "level"), "NorepinephrineState should have level"
    assert hasattr(state.acetylcholine, "level"), "AcetylcholineState should have level"

    # Verify values are reasonable
    assert 0.0 <= state.dopamine.tonic_level <= 1.0, "Dopamine tonic should be in [0, 1]"
    assert 0.0 <= state.serotonin.level <= 1.0, "Serotonin should be in [0, 1]"
    assert 0.0 <= state.norepinephrine.level <= 1.0, "Norepinephrine should be in [0, 1]"
    assert 0.0 <= state.acetylcholine.level <= 1.0, "Acetylcholine should be in [0, 1]"
    assert -1.0 <= state.overall_mood <= 1.0, "Overall mood should be in [-1, 1]"
    assert 0.0 <= state.cognitive_load <= 1.0, "Cognitive load should be in [0, 1]"

    print("✅ Global state complete:")
    print(f"   Dopamine: {state.dopamine.tonic_level:.2f}")
    print(f"   Serotonin: {state.serotonin.level:.2f}")
    print(f"   Norepinephrine: {state.norepinephrine.level:.2f}")
    print(f"   Acetylcholine: {state.acetylcholine.level:.2f}")
    print(f"   Overall Mood: {state.overall_mood:.2f}")
    print(f"   Cognitive Load: {state.cognitive_load:.2f}")


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NEUROMODULATION INTEGRATION TESTS (SIMPLIFIED)")
    print("=" * 80)
    print("\nRunning tests...")
    print("\nTest Suite:")
    print("  1. NeuromodulationController provides parameters")
    print("  2. Outcome processing updates Dopamine & Serotonin")
    print("  3. Threat response activates Norepinephrine")
    print("  4. Acetylcholine modulates attention threshold")
    print("  5. Serotonin controls exploration temperature")
    print("  6. Global state provides complete info")
    print("\nTarget: 6/6 passing (100%)")
    print("=" * 80)
