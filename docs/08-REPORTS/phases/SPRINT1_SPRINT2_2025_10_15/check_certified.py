# Known certified modules based on git commits
certified = {
    "safety.py": "test_safety_refactored.py",
    "tig/fabric.py": "test_fabric_hardening.py (99.12%)",
    "esgt/coordinator.py": "test_coordinator_hardening.py (98.80%)", 
    "esgt/kuramoto.py": "test_kuramoto_100pct.py (100%)",
    "mcea/stress.py": "test_stress.py (100%)",
    "mcea/controller.py": "test_controller_100pct.py (100%)",
    "mmei/goals.py": "test_goals.py (100%)",
    "mmei/monitor.py": "test_mmei_coverage_100pct.py (100%)",
    "prefrontal_cortex.py": "test_prefrontal_cortex_100pct.py (100%)",
}

print("✅ CERTIFIED MODULES (exclude from audit):")
for mod, test in certified.items():
    print(f"  - consciousness/{mod} → {test}")

print("\n🎯 TRUE TARGETS (uncertified primitives):")
targets = [
    "api.py",
    "system.py", 
    "autobiographical_narrative.py",
    "temporal_binding.py",
    "biomimetic_safety_bridge.py",
    "prometheus_metrics.py",
    "validate_tig_metrics.py",
    "integration_example.py",
    "episodic_memory/core.py",
    "episodic_memory/event.py", 
    "episodic_memory/memory_buffer.py",
    "lrr/recursive_reasoner.py",
    "lrr/contradiction_detector.py",
    "lrr/introspection_engine.py",
    "lrr/meta_monitor.py",
    "mea/attention_schema.py",
    "mea/boundary_detector.py",
    "mea/prediction_validator.py",
    "mea/self_model.py",
    "metacognition/monitor.py",
    "neuromodulation/coordinator_hardened.py",
    "neuromodulation/modulator_base.py",
    "neuromodulation/dopamine_hardened.py",
    "neuromodulation/acetylcholine_hardened.py",
    "neuromodulation/norepinephrine_hardened.py",
    "neuromodulation/serotonin_hardened.py",
    "predictive_coding/hierarchy_hardened.py",
    "predictive_coding/layer_base_hardened.py",
    "predictive_coding/layer1_sensory_hardened.py",
    "predictive_coding/layer2_behavioral_hardened.py",
    "predictive_coding/layer3_operational_hardened.py",
    "predictive_coding/layer4_tactical_hardened.py",
    "predictive_coding/layer5_strategic_hardened.py",
    "reactive_fabric/orchestration/data_orchestrator.py",
    "reactive_fabric/collectors/event_collector.py",
    "reactive_fabric/collectors/metrics_collector.py",
    "sandboxing/__init__.py",
    "sandboxing/kill_switch.py",
    "sandboxing/resource_limiter.py",
    "validation/coherence.py",
    "validation/phi_proxies.py",
    "validation/metacognition.py",
    "integration/esgt_subscriber.py",
    "integration/mcea_client.py",
    "integration/mmei_client.py",
    "integration/mea_bridge.py",
    "integration/sensory_esgt_bridge.py",
    "esgt/spm/base.py",
    "esgt/spm/simple.py",
    "esgt/spm/metrics_monitor.py",
    "esgt/spm/salience_detector.py",
    "esgt/arousal_integration.py",
    "tig/sync.py",
]

# Exclude old/deprecated files
deprecated = ["_old.py", "integration_example.py", "validate_tig_metrics.py"]

clean_targets = [t for t in targets if not any(d in t for d in deprecated)]

print(f"\n📊 SCOPE: {len(clean_targets)} modules to certify")
for i, t in enumerate(clean_targets, 1):
    print(f"  {i:2d}. consciousness/{t}")
