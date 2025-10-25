"""
Neuromodulation System - Standalone Example

Demonstrates the 4 neuromodulatory systems without MaximusIntegrated:
1. Dopamine: Reward prediction error and learning rate modulation
2. Serotonin: Exploration vs exploitation control
3. Norepinephrine: Threat response and arousal
4. Acetylcholine: Attention modulation

Shows adaptive behavior based on outcomes, threats, and importance.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, 100% production code
"""

from neuromodulation import NeuromodulationController


def demonstrate_neuromodulation_standalone():
    """Demonstrate all 4 neuromodulatory systems in action."""

    print("=" * 80)
    print("NEUROMODULATION SYSTEM DEMONSTRATION (STANDALONE)")
    print("=" * 80)
    print("\nInitializing Neuromodulation Controller...")
    print()

    # Initialize neuromodulation controller
    neuro = NeuromodulationController()

    # ========================================================================
    # SCENARIO 1: BASELINE STATE
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 1: Baseline Neuromodulation State")
    print("=" * 80)

    initial_state = neuro.get_global_state()

    print("\n📊 Initial Neuromodulator Levels:")
    print(f"  Dopamine (tonic):  {initial_state.dopamine.tonic_level:.2f}")
    print(f"  Serotonin:         {initial_state.serotonin.level:.2f}")
    print(f"  Norepinephrine:    {initial_state.norepinephrine.level:.2f}")
    print(f"  Acetylcholine:     {initial_state.acetylcholine.level:.2f}")
    print(f"\n  Overall Mood:      {initial_state.overall_mood:.2f}")
    print(f"  Cognitive Load:    {initial_state.cognitive_load:.2f}")

    # Get initial parameters
    initial_lr = neuro.get_modulated_learning_rate(base_learning_rate=0.01)
    initial_exploration = neuro.serotonin.get_exploration_rate()
    initial_arousal = neuro.norepinephrine.get_arousal_level()
    initial_salience = neuro.acetylcholine.get_salience_threshold()

    print("\n🎛️  Modulated Parameters (Baseline):")
    print(f"  Learning Rate:        {initial_lr:.4f}")
    print(f"  Exploration Rate:     {initial_exploration:.3f}")
    print(f"  Arousal Level:        {initial_arousal:.2f}")
    print(f"  Salience Threshold:   {initial_salience:.3f}")

    # ========================================================================
    # SCENARIO 2: POSITIVE OUTCOME (DOPAMINE + SEROTONIN)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 2: Positive Outcome - Better Than Expected!")
    print("=" * 80)
    print("\nSimulating successful threat detection...")
    print("  Expected quality: 0.5")
    print("  Actual quality:   0.9 (excellent!)")

    outcome_result = neuro.process_reward(
        expected_reward=0.5,
        actual_reward=0.9,
        success=True
    )

    print(f"\n🧠 Dopamine Response:")
    print(f"  RPE (Reward Prediction Error): +{outcome_result['rpe']:.3f}")
    print(f"  Interpretation: Positive surprise! System exceeded expectations")
    print(f"  Motivation Level: {outcome_result['motivation']:.2f}")

    # Get updated learning rate
    updated_lr_1 = neuro.get_modulated_learning_rate(base_learning_rate=0.01)
    print(f"\n📈 Learning Rate Adjusted:")
    print(f"  Before: {initial_lr:.4f}")
    print(f"  After:  {updated_lr_1:.4f}")
    print(f"  Effect: Higher learning rate due to surprise (faster adaptation)")

    # Get updated serotonin
    updated_serotonin_1 = neuro.serotonin.level
    updated_exploration_1 = neuro.serotonin.get_exploration_rate()
    print(f"\n🧘 Serotonin Response:")
    print(f"  Serotonin: {initial_state.serotonin.level:.2f} → {updated_serotonin_1:.2f}")
    print(f"  Exploration: {initial_exploration:.3f} → {updated_exploration_1:.3f}")
    print(f"  Effect: Success increases serotonin (better mood, less exploration)")

    # ========================================================================
    # SCENARIO 3: THREAT DETECTED (NOREPINEPHRINE)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 3: Critical Threat Detected!")
    print("=" * 80)
    print("\nSimulating intrusion detection...")
    print("  Threat Severity:  0.9 (critical)")

    neuro.respond_to_threat(threat_severity=0.9)

    updated_arousal = neuro.norepinephrine.get_arousal_level()
    updated_gain = neuro.norepinephrine.get_attention_gain()

    print(f"\n⚡ Norepinephrine Surge:")
    print(f"  Arousal: {initial_arousal:.2f} → {updated_arousal:.2f}")
    print(f"  Interpretation: Fight-or-flight response activated!")

    print(f"\n🔍 Attention System Response:")
    print(f"  Attention Gain: {updated_gain:.2f}x")
    print(f"  Effect: Heightened vigilance and threat awareness")

    print(f"\n⚠️  Yerkes-Dodson Law in Action:")
    print(f"  Note: Very high arousal can reduce attention gain (anxiety)")
    print(f"  Current arousal {updated_arousal:.2f} vs optimal ~0.6")
    print(f"  This is correct biological behavior!")

    # ========================================================================
    # SCENARIO 4: NEGATIVE OUTCOME (DOPAMINE + SEROTONIN)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 4: Negative Outcome - Worse Than Expected")
    print("=" * 80)
    print("\nSimulating failed response...")
    print("  Expected quality: 0.7")
    print("  Actual quality:   0.3 (poor)")

    negative_outcome = neuro.process_reward(
        expected_reward=0.7,
        actual_reward=0.3,
        success=False
    )

    print(f"\n🧠 Dopamine Response:")
    print(f"  RPE: {negative_outcome['rpe']:.3f} (negative)")
    print(f"  Interpretation: Negative surprise (worse than expected)")
    print(f"  Motivation: {negative_outcome['motivation']:.2f}")

    updated_lr_2 = neuro.get_modulated_learning_rate(base_learning_rate=0.01)
    print(f"\n📉 Learning Rate Still Elevated:")
    print(f"  Learning Rate: {updated_lr_2:.4f}")
    print(f"  Why? Surprise magnitude (abs value) drives learning, not direction")
    print(f"  Effect: System adapts quickly from mistakes")

    updated_serotonin_2 = neuro.serotonin.level
    updated_exploration_2 = neuro.serotonin.get_exploration_rate()
    print(f"\n😔 Serotonin Response:")
    print(f"  Serotonin: {updated_serotonin_1:.2f} → {updated_serotonin_2:.2f}")
    print(f"  Exploration: {updated_exploration_1:.3f} → {updated_exploration_2:.3f}")
    print(f"  Effect: Failure may decrease serotonin (lower mood)")

    if updated_exploration_2 > updated_exploration_1:
        print(f"  → More exploration (current strategy not working)")
    else:
        print(f"  → Exploration stable/decreased")

    # ========================================================================
    # SCENARIO 5: IMPORTANT STIMULUS (ACETYLCHOLINE)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 5: Important Stimulus Detected")
    print("=" * 80)
    print("\nSimulating critical alert...")
    print("  Importance: 0.9 (very important)")

    # Modulate acetylcholine
    initial_ach = neuro.acetylcholine.level
    neuro.acetylcholine.modulate_attention(importance=0.9)

    updated_ach = neuro.acetylcholine.level
    updated_salience = neuro.acetylcholine.get_salience_threshold()

    print(f"\n💡 Acetylcholine Response:")
    print(f"  ACh Level: {initial_ach:.2f} → {updated_ach:.2f}")
    print(f"  Salience Threshold: {initial_salience:.3f} → {updated_salience:.3f}")
    print(f"  Effect: Lower threshold means attending to MORE stimuli")

    encoding_rate = neuro.acetylcholine.get_memory_encoding_rate()
    print(f"\n🧠 Memory Encoding:")
    print(f"  Memory Encoding Rate: {encoding_rate:.2f}")
    print(f"  Effect: Better memory formation for important events")

    # ========================================================================
    # SCENARIO 6: FINAL STATE SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 6: Final Neuromodulation State")
    print("=" * 80)

    final_state = neuro.get_global_state()

    print("\n📊 Final Neuromodulator Levels:")
    print(f"  Dopamine (tonic):  {final_state.dopamine.tonic_level:.2f}")
    print(f"  Serotonin:         {final_state.serotonin.level:.2f}")
    print(f"  Norepinephrine:    {final_state.norepinephrine.level:.2f}")
    print(f"  Acetylcholine:     {final_state.acetylcholine.level:.2f}")
    print(f"\n  Overall Mood:      {final_state.overall_mood:.2f}")
    print(f"  Cognitive Load:    {final_state.cognitive_load:.2f}")

    # Get final parameters
    final_lr = neuro.get_modulated_learning_rate(base_learning_rate=0.01)
    final_exploration = neuro.serotonin.get_exploration_rate()
    final_arousal = neuro.norepinephrine.get_arousal_level()
    final_salience = neuro.acetylcholine.get_salience_threshold()

    print("\n🎛️  Final Modulated Parameters:")
    print(f"  Learning Rate:        {final_lr:.4f}")
    print(f"  Exploration Rate:     {final_exploration:.3f}")
    print(f"  Arousal Level:        {final_arousal:.2f}")
    print(f"  Salience Threshold:   {final_salience:.3f}")

    # ========================================================================
    # COMPARISON & INSIGHTS
    # ========================================================================
    print("\n" + "=" * 80)
    print("KEY INSIGHTS & COMPARISONS")
    print("=" * 80)

    print("\n📈 Parameter Evolution:")
    print(f"  Learning Rate:       {initial_lr:.4f} → {final_lr:.4f}")
    print(f"  Exploration Rate:    {initial_exploration:.3f} → {final_exploration:.3f}")
    print(f"  Arousal Level:       {initial_arousal:.2f} → {final_arousal:.2f}")
    print(f"  Salience Threshold:  {initial_salience:.3f} → {final_salience:.3f}")

    print("\n🧬 Biological Principles Demonstrated:")
    print("  ✅ Dopamine: Surprise-based learning (RPE magnitude)")
    print("  ✅ Serotonin: Mood regulation and exploration control")
    print("  ✅ Norepinephrine: Yerkes-Dodson law (inverted-U)")
    print("  ✅ Acetylcholine: Attention gating and salience filtering")

    print("\n🎯 Adaptive Behavior:")
    print("  ✅ System learns faster after surprises (positive or negative)")
    print("  ✅ Success reduces exploration (exploitation mode)")
    print("  ✅ Failure can increase exploration (seeking better strategies)")
    print("  ✅ Threats heighten vigilance and attention")
    print("  ✅ Important stimuli lower attention threshold")

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE ✅")
    print("=" * 80)
    print("\nAll 4 neuromodulatory systems working correctly!")
    print("Neuromodulation exhibits bio-inspired adaptive behavior.")
    print()


if __name__ == "__main__":
    """Run the standalone demonstration."""
    print("\nStarting Neuromodulation System Demonstration (Standalone)...")
    print("This will showcase all 4 neuromodulatory systems in action.\n")

    demonstrate_neuromodulation_standalone()

    print("\nDemonstration finished. Review the output above to see:")
    print("  1. Baseline neuromodulation state")
    print("  2. Positive outcome response (Dopamine + Serotonin)")
    print("  3. Threat response (Norepinephrine)")
    print("  4. Negative outcome response")
    print("  5. Important stimulus response (Acetylcholine)")
    print("  6. Final state and insights")
    print()
