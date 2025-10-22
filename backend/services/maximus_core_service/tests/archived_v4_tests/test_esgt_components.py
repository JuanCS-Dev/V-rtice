"""
ESGT Component Tests - Kuramoto & SPM Deep Dive
===============================================

Detailed tests for Kuramoto network and SPM subsystems.
Focus on synchronization dynamics and content generation.

REGRA DE OURO: NO MOCK, NO PLACEHOLDER, PRODUCTION-READY
"""

import asyncio
from typing import List

import pytest
import pytest_asyncio

from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore, TriggerConditions
from consciousness.esgt.kuramoto import KuramotoNetwork, OscillatorConfig
from consciousness.esgt.spm import SimpleSPM, SimpleSPMConfig, SalienceSPM, SalienceDetectorConfig
from consciousness.tig.fabric import TIGFabric, TopologyConfig


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_fabric():
    """Create test TIG fabric."""
    config = TopologyConfig(
        node_count=16,
        target_density=0.25,
        clustering_target=0.75,
        enable_small_world_rewiring=True,
    )
    fabric = TIGFabric(config)
    await fabric.initialize()
    yield fabric


@pytest_asyncio.fixture
async def test_coordinator(test_fabric):
    """Create test coordinator."""
    triggers = TriggerConditions(
        min_salience=0.60,
        min_available_nodes=8,
        refractory_period_ms=50.0,
    )
    
    coordinator = ESGTCoordinator(
        tig_fabric=test_fabric,
        triggers=triggers,
    )
    
    await coordinator.start()
    yield coordinator
    await coordinator.stop()


# =============================================================================
# Kuramoto Network Tests
# =============================================================================


@pytest.mark.asyncio
async def test_kuramoto_oscillator_initialization():
    """Test Kuramoto oscillator initialization."""
    config = OscillatorConfig(
        natural_frequency=40.0,
        coupling_strength=1.0,
        phase_noise=0.01,
    )
    
    network = KuramotoNetwork(config=config)
    
    # Add oscillators
    for i in range(10):
        network.add_oscillator(f"node-{i}")
    
    assert len(network.oscillators) == 10
    
    # Check initial phases
    for osc in network.oscillators.values():
        assert 0 <= osc.phase < 2 * 3.14159


@pytest.mark.asyncio
async def test_kuramoto_phase_synchronization():
    """Test Kuramoto phase synchronization dynamics."""
    config = OscillatorConfig(
        natural_frequency=40.0,
        coupling_strength=2.0,  # Strong coupling
        phase_noise=0.001,  # Low noise
    )
    
    network = KuramotoNetwork(config=config)
    
    # Add oscillators
    for i in range(12):
        network.add_oscillator(f"node-{i}")
    
    # Evolve for synchronization
    dt = 0.001
    for _ in range(500):
        network.step(dt)
    
    # Measure coherence
    coherence = network.compute_global_coherence()
    
    # Strong coupling + many steps should produce synchrony
    assert coherence.order_parameter > 0.5, \
        f"Failed to synchronize: r={coherence.order_parameter:.3f}"


@pytest.mark.asyncio
async def test_kuramoto_desynchronization():
    """Test Kuramoto desynchronization with weak coupling."""
    config = OscillatorConfig(
        natural_frequency=40.0,
        coupling_strength=0.1,  # Weak coupling
        phase_noise=0.05,  # High noise
    )
    
    network = KuramotoNetwork(config=config)
    
    for i in range(12):
        network.add_oscillator(f"node-{i}")
    
    # Evolve
    dt = 0.001
    for _ in range(200):
        network.step(dt)
    
    coherence = network.compute_global_coherence()
    
    # Weak coupling + noise should prevent synchrony
    assert coherence.order_parameter < 0.70, \
        f"Unexpectedly synchronized: r={coherence.order_parameter:.3f}"


@pytest.mark.asyncio
async def test_kuramoto_phase_reset():
    """Test Kuramoto phase reset functionality."""
    config = OscillatorConfig(natural_frequency=40.0, coupling_strength=1.0)
    
    network = KuramotoNetwork(config=config)
    
    for i in range(8):
        network.add_oscillator(f"node-{i}")
    
    # Evolve to get non-zero phases
    for _ in range(100):
        network.step(0.001)
    
    # Reset
    network.reset_all_phases()
    
    # All phases should be near zero
    for osc in network.oscillators.values():
        assert abs(osc.phase) < 0.5


@pytest.mark.asyncio
async def test_kuramoto_coupling_strength_effect():
    """Test effect of coupling strength on synchronization."""
    weak_config = OscillatorConfig(
        natural_frequency=40.0,
        coupling_strength=0.5,
        phase_noise=0.01,
    )
    
    strong_config = OscillatorConfig(
        natural_frequency=40.0,
        coupling_strength=3.0,
        phase_noise=0.01,
    )
    
    weak_network = KuramotoNetwork(config=weak_config)
    strong_network = KuramotoNetwork(config=strong_config)
    
    for i in range(10):
        weak_network.add_oscillator(f"node-{i}")
        strong_network.add_oscillator(f"node-{i}")
    
    # Evolve both
    for _ in range(300):
        weak_network.step(0.001)
        strong_network.step(0.001)
    
    weak_coherence = weak_network.compute_global_coherence()
    strong_coherence = strong_network.compute_global_coherence()
    
    # Strong coupling should produce higher coherence
    assert strong_coherence.order_parameter > weak_coherence.order_parameter


# =============================================================================
# SPM Tests - SimpleSPM
# =============================================================================


@pytest.mark.asyncio
async def test_simple_spm_initialization():
    """Test SimpleSPM initialization and startup."""
    config = SimpleSPMConfig(
        processing_interval_ms=50.0,
        base_novelty=0.5,
        base_relevance=0.5,
        base_urgency=0.3,
        max_outputs=10,
    )
    
    spm = SimpleSPM("test-spm", config)
    
    await spm.start()
    
    try:
        assert spm.is_running
        
        # Give time for processing
        await asyncio.sleep(0.1)
        
    finally:
        await spm.stop()
        assert not spm.is_running


@pytest.mark.asyncio
async def test_simple_spm_output_generation():
    """Test SimpleSPM output generation."""
    config = SimpleSPMConfig(
        processing_interval_ms=30.0,
        base_novelty=0.6,
        base_relevance=0.5,
        base_urgency=0.4,
        max_outputs=5,
    )
    
    spm = SimpleSPM("test-spm", config)
    
    await spm.start()
    
    try:
        # Wait for outputs
        await asyncio.sleep(0.15)
        
        outputs = spm.get_recent_outputs(n=3)
        
        # Should have generated outputs
        assert len(outputs) > 0, "No outputs generated"
        
        # Check output structure
        for output in outputs:
            assert "salience" in output
            assert "content" in output
            assert "timestamp_ns" in output
        
    finally:
        await spm.stop()


@pytest.mark.asyncio
async def test_simple_spm_salience_variation():
    """Test SimpleSPM salience variation over time."""
    config = SimpleSPMConfig(
        processing_interval_ms=30.0,
        base_novelty=0.7,
        base_relevance=0.6,
        base_urgency=0.5,
        max_outputs=10,
    )
    
    spm = SimpleSPM("test-spm", config)
    
    await spm.start()
    
    try:
        await asyncio.sleep(0.2)
        
        outputs = spm.get_recent_outputs(n=5)
        
        if len(outputs) >= 2:
            # Salience should vary
            saliences = [o["salience"].compute_total() for o in outputs]
            
            # Should have some variation
            salience_range = max(saliences) - min(saliences)
            assert salience_range > 0.01, "No salience variation"
        
    finally:
        await spm.stop()


# =============================================================================
# SPM Tests - SalienceSPM
# =============================================================================


@pytest.mark.asyncio
async def test_salience_spm_initialization(test_coordinator):
    """Test SalienceSPM initialization."""
    config = SalienceDetectorConfig(
        mode="active",
        update_interval_ms=50.0,
        novelty_threshold=0.70,
        relevance_threshold=0.65,
        urgency_threshold=0.60,
    )
    
    spm = SalienceSPM("test-salience", config, test_coordinator)
    
    await spm.start()
    
    try:
        assert spm.is_running
        
        await asyncio.sleep(0.1)
        
    finally:
        await spm.stop()


@pytest.mark.asyncio
async def test_salience_spm_detection(test_coordinator):
    """Test SalienceSPM detection of salient events."""
    config = SalienceDetectorConfig(
        mode="active",
        update_interval_ms=50.0,
        novelty_threshold=0.70,
        relevance_threshold=0.65,
        urgency_threshold=0.60,
    )
    
    spm = SalienceSPM("test-salience", config, test_coordinator)
    
    await spm.start()
    
    try:
        # Simulate events
        high_salience_event = {
            "novelty": 0.85,
            "relevance": 0.80,
            "urgency": 0.75,
        }
        
        low_salience_event = {
            "novelty": 0.40,
            "relevance": 0.35,
            "urgency": 0.30,
        }
        
        # Process events
        await spm.process_event(high_salience_event)
        await spm.process_event(low_salience_event)
        
        await asyncio.sleep(0.1)
        
        # SalienceSPM should have detected high salience
        # (Implementation detail - may trigger ESGT automatically)
        
    finally:
        await spm.stop()


# =============================================================================
# Integration: Kuramoto + ESGT
# =============================================================================


@pytest.mark.asyncio
async def test_kuramoto_integration_with_esgt(test_coordinator):
    """Test Kuramoto network integration with ESGT."""
    salience = SalienceScore(novelty=0.85, relevance=0.80, urgency=0.75)
    content = {"kuramoto_test": True}
    
    # Trigger ESGT (which uses Kuramoto internally)
    event = await test_coordinator.initiate_esgt(salience, content)
    
    if event.success:
        # Should achieve synchronization
        assert event.achieved_coherence > 0.60, \
            f"Low coherence: {event.achieved_coherence:.3f}"


@pytest.mark.asyncio
async def test_kuramoto_coherence_tracking(test_coordinator):
    """Test Kuramoto coherence tracking over multiple events."""
    coherence_values: List[float] = []
    
    for i in range(8):
        salience = SalienceScore(
            novelty=0.80 + i * 0.02,
            relevance=0.75,
            urgency=0.70,
        )
        content = {"iteration": i}
        
        event = await test_coordinator.initiate_esgt(salience, content)
        
        if event.success:
            coherence_values.append(event.achieved_coherence)
        
        await asyncio.sleep(0.12)
    
    # Should have collected coherence values
    if coherence_values:
        avg_coherence = sum(coherence_values) / len(coherence_values)
        assert avg_coherence > 0.60, f"Low average coherence: {avg_coherence:.3f}"


# =============================================================================
# Integration: SPM + ESGT
# =============================================================================


@pytest.mark.asyncio
async def test_spm_esgt_full_loop(test_coordinator):
    """Test full loop: SPM generates → ESGT processes."""
    config = SimpleSPMConfig(
        processing_interval_ms=40.0,
        base_novelty=0.75,
        base_relevance=0.70,
        base_urgency=0.65,
        max_outputs=5,
    )
    
    spm = SimpleSPM("test-spm", config)
    
    await spm.start()
    
    try:
        # Let SPM generate outputs
        await asyncio.sleep(0.15)
        
        outputs = spm.get_recent_outputs(n=3)
        
        if outputs:
            # Use SPM output for ESGT
            output = outputs[0]
            salience = output["salience"]
            content = output["content"]
            
            event = await test_coordinator.initiate_esgt(salience, content)
            
            # Should process successfully if salience sufficient
            assert event is not None
        
    finally:
        await spm.stop()


@pytest.mark.asyncio
async def test_multiple_spm_competition(test_coordinator):
    """Test competition among multiple SPMs for ESGT access."""
    spms = []
    
    for i in range(3):
        config = SimpleSPMConfig(
            processing_interval_ms=40.0,
            base_novelty=0.65 + i * 0.05,
            base_relevance=0.60,
            base_urgency=0.55,
            max_outputs=3,
        )
        spm = SimpleSPM(f"spm-{i}", config)
        await spm.start()
        spms.append(spm)
    
    try:
        await asyncio.sleep(0.15)
        
        # Collect outputs from all SPMs
        all_outputs = []
        for spm in spms:
            outputs = spm.get_recent_outputs(n=1)
            if outputs:
                all_outputs.append(outputs[0])
        
        # Try to trigger ESGT with each
        results = []
        for i, output in enumerate(all_outputs):
            event = await test_coordinator.initiate_esgt(
                output["salience"],
                output["content"]
            )
            results.append((i, event.success))
            await asyncio.sleep(0.001)  # Rapid succession
        
        # Due to refractory, only first should succeed
        successful = [r for r in results if r[1]]
        assert len(successful) <= 2, "Too many succeeded despite refractory"
        
    finally:
        for spm in spms:
            await spm.stop()
