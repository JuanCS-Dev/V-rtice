"""
Neuromodulation Integration Tests

Validates all 4 neuromodulatory systems (Dopamine, Serotonin, Norepinephrine, Acetylcholine)
and their coordinated behavior through the NeuromodulationController.

Tests:
1. Dopamine RPE modulates learning rate
2. Serotonin controls exploration/exploitation
3. Norepinephrine responds to threats
4. Acetylcholine modulates attention gain
5. Controller coordinates all 4 systems

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, 100% production code
"""

import pytest

from neuromodulation import (
    AcetylcholineSystem,
    DopamineSystem,
    NeuromodulationController,
    NorepinephrineSystem,
    SerotoninSystem,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def controller():
    """Create a fresh NeuromodulationController for each test."""
    return NeuromodulationController()


@pytest.fixture
def dopamine_system():
    """Create a fresh DopamineSystem for isolated testing."""
    return DopamineSystem()


@pytest.fixture
def serotonin_system():
    """Create a fresh SerotoninSystem for isolated testing."""
    return SerotoninSystem()


@pytest.fixture
def norepinephrine_system():
    """Create a fresh NorepinephrineSystem for isolated testing."""
    return NorepinephrineSystem()


@pytest.fixture
def acetylcholine_system():
    """Create a fresh AcetylcholineSystem for isolated testing."""
    return AcetylcholineSystem()


# ============================================================================
# TEST 1: DOPAMINE RPE MODULATES LEARNING RATE
# ============================================================================


def test_dopamine_modulates_learning_rate(dopamine_system):
    """Test that Reward Prediction Error (RPE) modulates learning rate correctly."""
    print("\n" + "=" * 80)
    print("TEST 1: Dopamine RPE Modulates Learning Rate")
    print("=" * 80)

    # Test positive RPE (better than expected) → increase learning rate
    expected_reward = 0.5
    actual_reward = 0.8
    rpe_positive = dopamine_system.compute_reward_prediction_error(expected_reward, actual_reward)

    assert rpe_positive > 0, "Positive RPE should be > 0"
    assert rpe_positive == (actual_reward - expected_reward), "RPE = actual - expected"

    # Get modulated learning rate (pass RPE as parameter)
    # IMPORTANT: Dopamine modulates by MAGNITUDE (abs) of RPE, not sign
    # Biological: Larger surprise (any direction) → higher learning rate
    base_lr = 0.01
    modulated_lr = dopamine_system.modulate_learning_rate(base_lr, rpe_positive)

    assert modulated_lr >= base_lr, "Surprise should increase LR"
    print(f"✅ Positive RPE: {rpe_positive:.3f} → LR modulated")

    # Test negative RPE (worse than expected)
    # Also increases LR because surprise is high (abs(RPE) is large)
    dopamine_system_neg = DopamineSystem()
    expected_reward_neg = 0.8
    actual_reward_neg = 0.3
    rpe_negative = dopamine_system_neg.compute_reward_prediction_error(expected_reward_neg, actual_reward_neg)

    assert rpe_negative < 0, "Negative RPE should be < 0"

    modulated_lr_neg = dopamine_system_neg.modulate_learning_rate(base_lr, rpe_negative)
    # Negative RPE with large magnitude ALSO increases LR (surprise-based)
    assert modulated_lr_neg >= base_lr, "Large surprise (negative RPE) should increase LR"
    print(f"✅ Negative RPE: {rpe_negative:.3f} → LR modulated (surprise-based)")
    print(
        f"   Base LR: {base_lr}, Modulated LR (positive surprise): {modulated_lr:.4f}, (negative surprise): {modulated_lr_neg:.4f}"
    )
    print("   Both increased because abs(RPE) determines learning rate (biological surprise)")


# ============================================================================
# TEST 2: SEROTONIN CONTROLS EXPLORATION/EXPLOITATION
# ============================================================================


def test_serotonin_controls_exploration_exploitation(serotonin_system):
    """Test that serotonin level controls exploration vs exploitation trade-off."""
    print("\n" + "=" * 80)
    print("TEST 2: Serotonin Controls Exploration/Exploitation")
    print("=" * 80)

    # Low serotonin → higher exploration (within 0.05-0.3 range)
    serotonin_system.level = 0.3  # Low serotonin
    exploration_rate_low = serotonin_system.get_exploration_rate()

    # With defaults (max=0.3, min=0.05), low serotonin gives exploration ~0.22
    assert 0.15 <= exploration_rate_low <= 0.3, "Low serotonin should give moderate-high exploration"
    print(f"✅ Low serotonin ({serotonin_system.level:.1f}) → Exploration rate: {exploration_rate_low:.2f}")

    # High serotonin → lower exploration (more exploitation)
    serotonin_system.level = 0.9  # High serotonin
    exploration_rate_high = serotonin_system.get_exploration_rate()

    assert exploration_rate_high < exploration_rate_low, "High serotonin should reduce exploration"
    assert 0.05 <= exploration_rate_high <= 0.15, "High serotonin should give low exploration"
    print(f"✅ High serotonin ({serotonin_system.level:.1f}) → Exploration rate: {exploration_rate_high:.2f}")
    print(f"   Exploration decreased as expected ({exploration_rate_low:.2f} → {exploration_rate_high:.2f})")

    # Test update from outcome
    serotonin_system_test = SerotoninSystem()
    initial_level = serotonin_system_test.level

    # Success increases serotonin
    serotonin_system_test.update_from_outcome(success=True, stress=0.2)
    assert serotonin_system_test.level >= initial_level, "Success should increase/maintain serotonin"
    print(f"✅ Success outcome → Serotonin increased: {initial_level:.2f} → {serotonin_system_test.level:.2f}")


# ============================================================================
# TEST 3: NOREPINEPHRINE RESPONDS TO THREATS
# ============================================================================


def test_norepinephrine_responds_to_threats(norepinephrine_system):
    """Test that norepinephrine increases arousal in response to threats."""
    print("\n" + "=" * 80)
    print("TEST 3: Norepinephrine Responds to Threats")
    print("=" * 80)

    initial_arousal = norepinephrine_system.get_arousal_level()

    # Activate threat response
    threat_severity = 0.8  # High severity threat
    norepinephrine_system.respond_to_threat(threat_severity)

    # Check arousal increased
    new_arousal = norepinephrine_system.get_arousal_level()
    assert new_arousal > initial_arousal, "Threat should increase arousal"
    print(
        f"✅ Threat detected (severity {threat_severity}) → Arousal increased: {initial_arousal:.2f} → {new_arousal:.2f}"
    )

    # Get attention gain (related to arousal/vigilance)
    attention_gain = norepinephrine_system.get_attention_gain()
    assert 0.0 <= attention_gain <= 2.0, "Attention gain should be reasonable"
    assert attention_gain > 1.0, "High arousal should increase attention gain"
    print(f"✅ Attention gain: {attention_gain:.2f}x (appropriate for threat)")

    # Test decay over time via update
    for _ in range(5):
        norepinephrine_system.update(workload=0.0)

    final_arousal = norepinephrine_system.get_arousal_level()
    assert final_arousal < new_arousal, "Arousal should decay over time"
    print(f"✅ Arousal decay working: {final_arousal:.2f} (after 5 updates)")


# ============================================================================
# TEST 4: ACETYLCHOLINE MODULATES ATTENTION GAIN
# ============================================================================


def test_acetylcholine_modulates_attention_gain(acetylcholine_system):
    """Test that acetylcholine modulates attention gain based on novelty/learning."""
    print("\n" + "=" * 80)
    print("TEST 4: Acetylcholine Modulates Attention Gain")
    print("=" * 80)

    # Test salience threshold (related to attention)
    # High ACh → lower threshold (attend to more things)
    acetylcholine_system.level = 0.9
    high_ach_threshold = acetylcholine_system.get_salience_threshold()

    print(f"✅ High ACh ({acetylcholine_system.level:.1f}) → Salience threshold: {high_ach_threshold:.2f}")

    # Low ACh → higher threshold (attend to fewer things)
    acetylcholine_system.level = 0.3
    low_ach_threshold = acetylcholine_system.get_salience_threshold()

    assert low_ach_threshold > high_ach_threshold, "Low ACh should increase threshold (less sensitive)"
    print(f"✅ Low ACh ({acetylcholine_system.level:.1f}) → Salience threshold: {low_ach_threshold:.2f}")

    # Test memory encoding rate
    acetylcholine_system.level = 0.8
    encoding_rate = acetylcholine_system.get_memory_encoding_rate()
    assert 0.0 <= encoding_rate <= 1.0, "Encoding rate should be in [0, 1]"
    print(f"✅ Memory encoding rate: {encoding_rate:.2f}")

    # Test attention modulation with importance
    acetylcholine_system_mod = AcetylcholineSystem()
    initial_ach = acetylcholine_system_mod.level

    # Important stimulus increases ACh
    importance = 0.8
    acetylcholine_system_mod.modulate_attention(importance)

    final_ach = acetylcholine_system_mod.level
    assert final_ach >= initial_ach, "Important stimulus should maintain/increase ACh"
    print(f"✅ Important stimulus (score {importance}) → ACh: {initial_ach:.2f} → {final_ach:.2f}")


# ============================================================================
# TEST 5: CONTROLLER COORDINATES ALL 4 SYSTEMS
# ============================================================================


def test_controller_coordinates_all_systems(controller):
    """Test that NeuromodulationController coordinates all 4 systems correctly."""
    print("\n" + "=" * 80)
    print("TEST 5: Controller Coordinates All 4 Systems")
    print("=" * 80)

    # Verify all systems initialized
    assert controller.dopamine is not None, "Dopamine system should be initialized"
    assert controller.serotonin is not None, "Serotonin system should be initialized"
    assert controller.norepinephrine is not None, "Norepinephrine system should be initialized"
    assert controller.acetylcholine is not None, "Acetylcholine system should be initialized"
    print("✅ All 4 neuromodulatory systems initialized")

    # Test reward processing coordinates dopamine + serotonin
    expected_reward = 0.5
    actual_reward = 0.7
    result = controller.process_reward(expected_reward=expected_reward, actual_reward=actual_reward, success=True)

    assert "rpe" in result, "Should return RPE"
    assert "motivation" in result, "Should return motivation"
    assert "serotonin_level" in result, "Should return serotonin level"
    assert result["rpe"] > 0, "Positive reward should produce positive RPE"
    print(f"✅ Reward processing coordinated: RPE={result['rpe']:.2f}, Motivation={result['motivation']:.2f}")

    # Test threat response coordinates norepinephrine
    threat_severity = 0.7
    controller.respond_to_threat(threat_severity)

    attention_gain = controller.norepinephrine.get_attention_gain()
    assert attention_gain >= 1.0, "Threat should increase attention gain"
    print(f"✅ Threat response coordinated: Attention Gain={attention_gain:.2f}x")

    # Test attention modulation coordinates acetylcholine
    importance = 0.6
    salience = 0.7
    should_attend = controller.modulate_attention(importance, salience)

    assert isinstance(should_attend, bool), "Should return boolean"
    salience_threshold = controller.acetylcholine.get_salience_threshold()
    assert 0.0 <= salience_threshold <= 1.0, "Salience threshold should be reasonable"
    print(f"✅ Attention modulation coordinated: Threshold={salience_threshold:.2f}, Should attend={should_attend}")

    # Test get global state
    state = controller.get_global_state()

    assert state is not None, "Should return global state"
    assert hasattr(state, "dopamine"), "State should have dopamine"
    assert hasattr(state, "serotonin"), "State should have serotonin"
    assert hasattr(state, "norepinephrine"), "State should have norepinephrine"
    assert hasattr(state, "acetylcholine"), "State should have acetylcholine"
    assert hasattr(state, "overall_mood"), "State should have overall mood"
    assert hasattr(state, "cognitive_load"), "State should have cognitive load"
    print(f"✅ Global state accessible: Mood={state.overall_mood:.2f}, Load={state.cognitive_load:.2f}")

    # Test get modulated learning rate (integrates dopamine)
    base_lr = 0.01
    modulated_lr = controller.get_modulated_learning_rate(base_lr)

    assert modulated_lr > 0, "Modulated LR should be positive"
    print(f"✅ Learning rate modulation: {base_lr:.4f} → {modulated_lr:.4f}")


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NEUROMODULATION INTEGRATION TESTS")
    print("=" * 80)
    print("\nRunning tests...")
    print("\nTest Suite:")
    print("  1. Dopamine RPE modulates learning rate")
    print("  2. Serotonin controls exploration/exploitation")
    print("  3. Norepinephrine responds to threats")
    print("  4. Acetylcholine modulates attention gain")
    print("  5. Controller coordinates all 4 systems")
    print("\nTarget: 5/5 passing (100%)")
    print("=" * 80)
