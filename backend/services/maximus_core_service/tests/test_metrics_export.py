"""
Test Suite for Prometheus Metrics Export

Validates metrics collection, export, and accuracy for MAXIMUS AI 3.0.

Tests:
1. Metrics exporter initialization
2. Predictive Coding metrics recording
3. Neuromodulation metrics recording
4. Skill Learning metrics recording

REGRA DE OURO: Zero mocks, real metrics validation
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_metrics_exporter_initialization():
    """Test that MaximusMetricsExporter initializes correctly with all metric types."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Validate Predictive Coding metrics
    assert hasattr(exporter, 'free_energy'), "Missing free_energy metric"
    assert hasattr(exporter, 'pc_latency'), "Missing pc_latency metric"
    assert hasattr(exporter, 'prediction_errors'), "Missing prediction_errors metric"

    # Validate Neuromodulation metrics
    assert hasattr(exporter, 'dopamine_level'), "Missing dopamine_level metric"
    assert hasattr(exporter, 'acetylcholine_level'), "Missing acetylcholine_level metric"
    assert hasattr(exporter, 'norepinephrine_level'), "Missing norepinephrine_level metric"
    assert hasattr(exporter, 'serotonin_level'), "Missing serotonin_level metric"
    assert hasattr(exporter, 'learning_rate'), "Missing learning_rate metric"

    # Validate Skill Learning metrics
    assert hasattr(exporter, 'skill_executions'), "Missing skill_executions metric"
    assert hasattr(exporter, 'skill_reward'), "Missing skill_reward metric"
    assert hasattr(exporter, 'skill_latency'), "Missing skill_latency metric"

    # Validate Attention metrics
    assert hasattr(exporter, 'attention_salience'), "Missing attention_salience metric"
    assert hasattr(exporter, 'attention_threshold'), "Missing attention_threshold metric"

    # Validate Ethical AI metrics
    assert hasattr(exporter, 'ethical_decisions'), "Missing ethical_decisions metric"
    assert hasattr(exporter, 'ethical_approval_rate'), "Missing ethical_approval_rate metric"

    # Validate System metrics
    assert hasattr(exporter, 'events_processed'), "Missing events_processed metric"
    assert hasattr(exporter, 'pipeline_latency'), "Missing pipeline_latency metric"
    assert hasattr(exporter, 'threat_detection_accuracy'), "Missing threat_detection_accuracy metric"

    # Validate system info
    assert hasattr(exporter, 'system_info'), "Missing system_info metric"

    # Test metrics export
    metrics_output = exporter.get_metrics()
    assert isinstance(metrics_output, bytes), "Metrics output should be bytes"
    assert len(metrics_output) > 0, "Metrics output should not be empty"

    # Validate content type
    content_type = exporter.get_content_type()
    assert content_type == 'text/plain; version=0.0.4; charset=utf-8', f"Unexpected content type: {content_type}"

    print("✅ test_metrics_exporter_initialization passed")


def test_predictive_coding_metrics():
    """Test Predictive Coding metrics recording and export."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Record metrics for all 5 layers
    layers = ['l1', 'l2', 'l3', 'l4', 'l5']
    for i, layer in enumerate(layers):
        free_energy = 0.5 + (i * 0.1)
        latency = 0.01 + (i * 0.01)
        exporter.record_predictive_coding(layer, free_energy, latency)

    # Get metrics
    metrics_output = exporter.get_metrics().decode('utf-8')

    # Validate Predictive Coding metrics present
    assert 'maximus_free_energy' in metrics_output, "free_energy metric not in output"
    assert 'maximus_predictive_coding_latency_seconds' in metrics_output, "pc_latency metric not in output"

    # Validate all layers present
    for layer in layers:
        assert f'layer="{layer}"' in metrics_output, f"Layer {layer} not in metrics output"

    # Validate prediction errors counter (should increment for high free energy)
    assert 'maximus_prediction_errors_total' in metrics_output, "prediction_errors metric not in output"

    # Check that high free energy layers (>0.5) triggered prediction errors
    # l1=0.5 (not counted), l2=0.6 (counted), l3=0.7 (counted), l4=0.8 (counted), l5=0.9 (counted)
    # So we should have 4 prediction errors total
    assert 'maximus_prediction_errors_total{layer="l2"} 1.0' in metrics_output
    assert 'maximus_prediction_errors_total{layer="l3"} 1.0' in metrics_output

    print("✅ test_predictive_coding_metrics passed")


def test_neuromodulation_metrics():
    """Test Neuromodulation metrics recording and export."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Record neuromodulation state
    state = {
        'dopamine': 0.75,
        'acetylcholine': 0.6,
        'norepinephrine': 0.8,
        'serotonin': 0.5,
        'learning_rate': 0.015
    }
    exporter.record_neuromodulation(state)

    # Get metrics
    metrics_output = exporter.get_metrics().decode('utf-8')

    # Validate all neuromodulators present with correct values
    assert 'maximus_dopamine_level 0.75' in metrics_output, "dopamine level incorrect"
    assert 'maximus_acetylcholine_level 0.6' in metrics_output, "acetylcholine level incorrect"
    assert 'maximus_norepinephrine_level 0.8' in metrics_output, "norepinephrine level incorrect"
    assert 'maximus_serotonin_level 0.5' in metrics_output, "serotonin level incorrect"
    assert 'maximus_learning_rate 0.015' in metrics_output, "learning rate incorrect"

    # Test partial state update
    partial_state = {'dopamine': 0.9}
    exporter.record_neuromodulation(partial_state)

    metrics_output = exporter.get_metrics().decode('utf-8')
    assert 'maximus_dopamine_level 0.9' in metrics_output, "dopamine update failed"

    print("✅ test_neuromodulation_metrics passed")


def test_skill_learning_metrics():
    """Test Skill Learning metrics recording and export."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Record skill executions
    exporter.record_skill_execution(
        skill_name='detect_malware',
        mode='hybrid',
        success=True,
        reward=0.85,
        latency=0.05
    )

    exporter.record_skill_execution(
        skill_name='block_c2',
        mode='model_free',
        success=False,
        reward=-0.3,
        latency=0.02
    )

    exporter.record_skill_execution(
        skill_name='detect_malware',
        mode='hybrid',
        success=True,
        reward=0.9,
        latency=0.04
    )

    # Update success rate
    exporter.update_skill_success_rate('detect_malware', 0.95)

    # Get metrics
    metrics_output = exporter.get_metrics().decode('utf-8')

    # Validate skill execution counters
    assert 'maximus_skill_executions_total' in metrics_output, "skill_executions metric missing"
    assert 'skill_name="detect_malware"' in metrics_output, "detect_malware skill missing"
    assert 'skill_name="block_c2"' in metrics_output, "block_c2 skill missing"
    assert 'mode="hybrid"' in metrics_output, "hybrid mode missing"
    assert 'mode="model_free"' in metrics_output, "model_free mode missing"
    assert 'status="success"' in metrics_output, "success status missing"
    assert 'status="failure"' in metrics_output, "failure status missing"

    # Validate skill rewards histogram
    assert 'maximus_skill_reward' in metrics_output, "skill_reward metric missing"

    # Validate skill latency histogram
    assert 'maximus_skill_execution_latency_seconds' in metrics_output, "skill_latency metric missing"

    # Validate success rate gauge
    assert 'maximus_skill_success_rate{skill_name="detect_malware"} 0.95' in metrics_output, "success rate incorrect"

    print("✅ test_skill_learning_metrics passed")


def test_attention_and_ethical_metrics():
    """Test Attention System and Ethical AI metrics recording."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Record attention metrics
    exporter.record_attention(salience=0.85, threshold=0.7)
    exporter.record_attention(salience=0.95, threshold=0.6)
    exporter.record_attention_update(reason='high_surprise')

    # Record ethical decisions
    exporter.record_ethical_decision(approved=True)
    exporter.record_ethical_decision(approved=True)
    exporter.record_ethical_decision(approved=False)
    exporter.update_ethical_approval_rate(0.67)
    exporter.record_ethical_violation(category='bias')

    # Get metrics
    metrics_output = exporter.get_metrics().decode('utf-8')

    # Validate attention metrics
    assert 'maximus_attention_salience' in metrics_output, "attention_salience metric missing"
    assert 'maximus_attention_threshold 0.6' in metrics_output, "attention_threshold incorrect"
    assert 'maximus_attention_updates_total{reason="high_surprise"} 1.0' in metrics_output

    # Validate ethical metrics
    assert 'maximus_ethical_decisions_total{result="approved"} 2.0' in metrics_output
    assert 'maximus_ethical_decisions_total{result="rejected"} 1.0' in metrics_output
    assert 'maximus_ethical_approval_rate 0.67' in metrics_output
    assert 'maximus_ethical_violations_total{category="bias"} 1.0' in metrics_output

    print("✅ test_attention_and_ethical_metrics passed")


def test_system_metrics():
    """Test System-level metrics recording."""
    from monitoring import MaximusMetricsExporter

    exporter = MaximusMetricsExporter()

    # Record event processing
    exporter.record_event_processed('malware', detected_as_threat=True, latency=0.05)
    exporter.record_event_processed('normal', detected_as_threat=False, latency=0.01)
    exporter.record_event_processed('c2_communication', detected_as_threat=True, latency=0.08)

    # Update detection metrics
    exporter.update_detection_metrics(accuracy=0.95, fp_rate=0.03, fn_rate=0.02)

    # Get metrics
    metrics_output = exporter.get_metrics().decode('utf-8')

    # Validate event processing
    assert 'maximus_events_processed_total' in metrics_output
    assert 'event_type="malware"' in metrics_output
    assert 'detected_as_threat="true"' in metrics_output
    assert 'detected_as_threat="false"' in metrics_output

    # Validate pipeline latency
    assert 'maximus_pipeline_latency_seconds' in metrics_output

    # Validate detection quality metrics
    assert 'maximus_threat_detection_accuracy 0.95' in metrics_output
    assert 'maximus_false_positive_rate 0.03' in metrics_output
    assert 'maximus_false_negative_rate 0.02' in metrics_output

    # Validate system info
    assert 'maximus_system_info' in metrics_output
    assert 'version="3.0.0"' in metrics_output
    assert 'regra_de_ouro_compliant="true"' in metrics_output

    print("✅ test_system_metrics passed")


# Test runner
def run_all_tests():
    """Run all metrics tests."""
    print("\n" + "="*80)
    print("MAXIMUS AI 3.0 - Prometheus Metrics Test Suite")
    print("="*80 + "\n")

    tests = [
        ("Metrics Exporter Initialization", test_metrics_exporter_initialization),
        ("Predictive Coding Metrics", test_predictive_coding_metrics),
        ("Neuromodulation Metrics", test_neuromodulation_metrics),
        ("Skill Learning Metrics", test_skill_learning_metrics),
        ("Attention & Ethical Metrics", test_attention_and_ethical_metrics),
        ("System Metrics", test_system_metrics),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"[{passed + failed + 1}/{len(tests)}] Testing: {test_name}")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
        print()

    # Summary
    print("="*80)
    print(f"Test Results: {passed}/{passed + failed} passed")
    if failed == 0:
        print("✅ ALL METRICS TESTS PASSED")
    else:
        print(f"❌ {failed} tests failed")
    print("="*80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
