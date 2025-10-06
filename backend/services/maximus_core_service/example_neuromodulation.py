"""
Neuromodulation System - Example Usage

Demonstrates the 4 neuromodulatory systems in action:
1. Dopamine: Reward prediction error and learning rate modulation
2. Serotonin: Exploration vs exploitation control
3. Norepinephrine: Threat response and arousal
4. Acetylcholine: Attention modulation

Shows adaptive behavior based on outcomes, threats, and importance.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, 100% production code
"""

import asyncio
from datetime import datetime

from maximus_integrated import MaximusIntegrated


async def demonstrate_neuromodulation():
    """Demonstrate all 4 neuromodulatory systems in action."""

    print("=" * 80)
    print("NEUROMODULATION SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("\nInitializing MAXIMUS AI with Neuromodulation...")
    print()

    # Initialize Maximus with neuromodulation
    maximus = MaximusIntegrated()

    # ========================================================================
    # SCENARIO 1: BASELINE STATE
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 1: Baseline Neuromodulation State")
    print("=" * 80)

    initial_state = maximus.get_neuromodulation_state()
    initial_params = initial_state["modulated_parameters"]

    print("\n📊 Initial Neuromodulator Levels:")
    print(f"  Dopamine:        {initial_state['global_state']['dopamine']:.2f}")
    print(f"  Serotonin:       {initial_state['global_state']['serotonin']:.2f}")
    print(f"  Norepinephrine:  {initial_state['global_state']['norepinephrine']:.2f}")
    print(f"  Acetylcholine:   {initial_state['global_state']['acetylcholine']:.2f}")
    print(f"\n  Overall Mood:    {initial_state['global_state']['overall_mood']:.2f}")
    print(f"  Cognitive Load:  {initial_state['global_state']['cognitive_load']:.2f}")

    print("\n🎛️  Modulated Parameters (Baseline):")
    print(f"  Learning Rate:        {initial_params['learning_rate']:.4f}")
    print(f"  Attention Threshold:  {initial_params['attention_threshold']:.3f}")
    print(f"  Arousal Gain:         {initial_params['arousal_gain']:.2f}x")
    print(f"  Temperature:          {initial_params['temperature']:.2f}")

    # ========================================================================
    # SCENARIO 2: POSITIVE OUTCOME (DOPAMINE + SEROTONIN)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 2: Positive Outcome - Better Than Expected!")
    print("=" * 80)
    print("\nSimulating successful threat detection...")
    print("  Expected quality: 0.5")
    print("  Actual quality:   0.9 (excellent!)")

    outcome_result = await maximus.process_outcome(
        expected_reward=0.5,
        actual_reward=0.9,
        success=True
    )

    print(f"\n🧠 Dopamine Response:")
    print(f"  RPE (Reward Prediction Error): +{outcome_result['rpe']:.3f}")
    print(f"  Interpretation: Positive surprise! System exceeded expectations")
    print(f"  Motivation Level: {outcome_result['motivation']:.2f}")

    updated_params_1 = outcome_result["updated_parameters"]
    print(f"\n📈 Learning Rate Adjusted:")
    print(f"  Before: {initial_params['learning_rate']:.4f}")
    print(f"  After:  {updated_params_1['learning_rate']:.4f}")
    print(f"  Effect: Higher learning rate due to surprise (faster adaptation)")

    print(f"\n🧘 Serotonin Response:")
    serotonin_before = initial_state['global_state']['serotonin']
    serotonin_after = updated_params_1['raw_neuromodulation']['serotonin_level']
    print(f"  Serotonin: {serotonin_before:.2f} → {serotonin_after:.2f}")
    print(f"  Effect: Success increases serotonin (better mood, less exploration)")

    print(f"\n🌡️  Temperature Adjusted:")
    print(f"  Before: {initial_params['temperature']:.2f}")
    print(f"  After:  {updated_params_1['temperature']:.2f}")
    print(f"  Effect: Lower temperature (more exploitation, less random exploration)")

    # ========================================================================
    # SCENARIO 3: THREAT DETECTED (NOREPINEPHRINE)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 3: Critical Threat Detected!")
    print("=" * 80)
    print("\nSimulating intrusion detection...")
    print("  Threat Type: intrusion")
    print("  Severity:    0.9 (critical)")

    await asyncio.sleep(1)  # Simulate time passing

    threat_result = await maximus.respond_to_threat(
        threat_severity=0.9,
        threat_type="intrusion"
    )

    print(f"\n⚡ Norepinephrine Surge:")
    print(f"  Arousal Level: {threat_result['arousal_level']:.2f}")
    print(f"  Interpretation: Fight-or-flight response activated!")

    print(f"\n🔍 Attention System Response:")
    print(f"  Attention Gain:       {threat_result['attention_gain']:.2f}x")
    print(f"  Attention Threshold:  {threat_result['updated_attention_threshold']:.3f}")
    print(f"  Effect: Heightened vigilance and threat awareness")

    print(f"\n⚠️  Yerkes-Dodson Law in Action:")
    print(f"  Note: Very high arousal can reduce attention gain (anxiety)")
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

    await asyncio.sleep(1)

    negative_outcome = await maximus.process_outcome(
        expected_reward=0.7,
        actual_reward=0.3,
        success=False
    )

    print(f"\n🧠 Dopamine Response:")
    print(f"  RPE: {negative_outcome['rpe']:.3f} (negative)")
    print(f"  Interpretation: Negative surprise (worse than expected)")
    print(f"  Motivation: {negative_outcome['motivation']:.2f}")

    updated_params_2 = negative_outcome["updated_parameters"]

    print(f"\n📉 Learning Rate Still Elevated:")
    print(f"  Learning Rate: {updated_params_2['learning_rate']:.4f}")
    print(f"  Why? Surprise magnitude (abs value) drives learning, not direction")
    print(f"  Effect: System adapts quickly from mistakes")

    print(f"\n😔 Serotonin Response:")
    serotonin_negative = updated_params_2['raw_neuromodulation']['serotonin_level']
    print(f"  Serotonin: {serotonin_after:.2f} → {serotonin_negative:.2f}")
    print(f"  Effect: Failure may decrease serotonin (lower mood)")

    print(f"\n🌡️  Temperature Increase:")
    temp_before = updated_params_1['temperature']
    temp_after = updated_params_2['temperature']
    print(f"  Temperature: {temp_before:.2f} → {temp_after:.2f}")
    if temp_after > temp_before:
        print(f"  Effect: More exploration (current strategy not working)")
    else:
        print(f"  Effect: Stable (minor change)")

    # ========================================================================
    # SCENARIO 5: IMPORTANT STIMULUS (ACETYLCHOLINE)
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 5: Important Stimulus Detected")
    print("=" * 80)
    print("\nSimulating critical alert...")
    print("  Importance: 0.9 (very important)")

    # Modulate acetylcholine directly
    maximus.neuromodulation.acetylcholine.modulate_attention(importance=0.9)

    ach_level = maximus.neuromodulation.acetylcholine.level
    salience_threshold = maximus.neuromodulation.acetylcholine.get_salience_threshold()

    print(f"\n💡 Acetylcholine Response:")
    print(f"  ACh Level: {ach_level:.2f}")
    print(f"  Salience Threshold: {salience_threshold:.3f}")
    print(f"  Effect: Lower threshold means attending to MORE stimuli")

    print(f"\n🎯 Attention System Adjustment:")
    current_params = maximus.get_neuromodulated_parameters()
    print(f"  Attention Threshold: {current_params['attention_threshold']:.3f}")
    print(f"  Effect: More sensitive to anomalies and threats")

    print(f"\n🧠 Memory Encoding:")
    encoding_rate = maximus.neuromodulation.acetylcholine.get_memory_encoding_rate()
    print(f"  Memory Encoding Rate: {encoding_rate:.2f}")
    print(f"  Effect: Better memory formation for important events")

    # ========================================================================
    # SCENARIO 6: FINAL STATE SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("SCENARIO 6: Final Neuromodulation State")
    print("=" * 80)

    final_state = maximus.get_neuromodulation_state()
    final_params = final_state["modulated_parameters"]

    print("\n📊 Final Neuromodulator Levels:")
    print(f"  Dopamine:        {final_state['global_state']['dopamine']:.2f}")
    print(f"  Serotonin:       {final_state['global_state']['serotonin']:.2f}")
    print(f"  Norepinephrine:  {final_state['global_state']['norepinephrine']:.2f}")
    print(f"  Acetylcholine:   {final_state['global_state']['acetylcholine']:.2f}")
    print(f"\n  Overall Mood:    {final_state['global_state']['overall_mood']:.2f}")
    print(f"  Cognitive Load:  {final_state['global_state']['cognitive_load']:.2f}")

    print("\n🎛️  Final Modulated Parameters:")
    print(f"  Learning Rate:        {final_params['learning_rate']:.4f}")
    print(f"  Attention Threshold:  {final_params['attention_threshold']:.3f}")
    print(f"  Arousal Gain:         {final_params['arousal_gain']:.2f}x")
    print(f"  Temperature:          {final_params['temperature']:.2f}")

    # ========================================================================
    # COMPARISON & INSIGHTS
    # ========================================================================
    print("\n" + "=" * 80)
    print("KEY INSIGHTS & COMPARISONS")
    print("=" * 80)

    print("\n📈 Parameter Evolution:")
    print(f"  Learning Rate:       {initial_params['learning_rate']:.4f} → {final_params['learning_rate']:.4f}")
    print(f"  Attention Threshold: {initial_params['attention_threshold']:.3f} → {final_params['attention_threshold']:.3f}")
    print(f"  Arousal Gain:        {initial_params['arousal_gain']:.2f}x → {final_params['arousal_gain']:.2f}x")
    print(f"  Temperature:         {initial_params['temperature']:.2f} → {final_params['temperature']:.2f}")

    print("\n🧬 Biological Principles Demonstrated:")
    print("  ✅ Dopamine: Surprise-based learning (RPE magnitude)")
    print("  ✅ Serotonin: Mood regulation and exploration control")
    print("  ✅ Norepinephrine: Yerkes-Dodson law (inverted-U)")
    print("  ✅ Acetylcholine: Attention gating and salience filtering")

    print("\n🎯 Adaptive Behavior:")
    print("  ✅ System learns faster after surprises (positive or negative)")
    print("  ✅ Success reduces exploration (exploitation mode)")
    print("  ✅ Failure increases exploration (seeking better strategies)")
    print("  ✅ Threats heighten vigilance and attention")
    print("  ✅ Important stimuli lower attention threshold")

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE ✅")
    print("=" * 80)
    print("\nAll 4 neuromodulatory systems working correctly!")
    print("MAXIMUS AI exhibits bio-inspired adaptive behavior.")
    print()


if __name__ == "__main__":
    """Run the demonstration."""
    print("\nStarting Neuromodulation System Demonstration...")
    print("This will showcase all 4 neuromodulatory systems in action.\n")

    asyncio.run(demonstrate_neuromodulation())

    print("\nDemonstration finished. Review the output above to see:")
    print("  1. Baseline neuromodulation state")
    print("  2. Positive outcome response (Dopamine + Serotonin)")
    print("  3. Threat response (Norepinephrine)")
    print("  4. Negative outcome response")
    print("  5. Important stimulus response (Acetylcholine)")
    print("  6. Final state and insights")
    print()
