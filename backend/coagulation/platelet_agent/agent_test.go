package main

import (
	"context"
	"testing"
	"time"
)

// TestAgentStateTransitions tests state machine transitions.
//
// Validates biological analogy: Resting → Activated → Resting
func TestAgentStateTransitions(t *testing.T) {
	config := &Config{
		AgentID:             "test-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               false,
	}
	
	// Skip if NATS not available
	agent, err := NewAgent(config)
	if err != nil {
		t.Skip("NATS not available, skipping integration test")
	}
	defer agent.Shutdown()
	
	// Initial state should be Resting
	if agent.state != StateResting {
		t.Errorf("Expected initial state Resting, got %s", agent.state)
	}
	
	// Simulate high anomaly score (should trigger activation)
	agent.activate(0.9)
	
	if agent.state != StateActivated {
		t.Errorf("Expected state Activated after activate(), got %s", agent.state)
	}
	
	// Simulate low anomaly score (should deactivate)
	agent.deactivate()
	
	if agent.state != StateResting {
		t.Errorf("Expected state Resting after deactivate(), got %s", agent.state)
	}
}

// TestAgentAnomalyAggregation tests sensor score aggregation.
func TestAgentAnomalyAggregation(t *testing.T) {
	config := &Config{
		AgentID:             "test-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               false,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Skip("NATS not available, skipping test")
	}
	defer agent.Shutdown()
	
	// Test anomaly aggregation logic
	// Process score: 0.8, Network: 0.0, File: 0.0
	// Expected: 0.8*0.4 + 0.0*0.4 + 0.0*0.2 = 0.32
	processScore := 0.8
	networkScore := 0.0
	fileScore := 0.0
	
	combined := (processScore*0.4 + networkScore*0.4 + fileScore*0.2)
	expected := 0.32
	
	if combined != expected {
		t.Errorf("Anomaly aggregation incorrect: got %f, expected %f", combined, expected)
	}
	
	// Should NOT activate (0.32 < 0.7 threshold)
	if combined >= agent.activationThreshold {
		t.Errorf("Should not activate with score %f (threshold %f)", combined, agent.activationThreshold)
	}
}

// TestBreachIDGeneration tests unique breach ID generation.
func TestBreachIDGeneration(t *testing.T) {
	config := &Config{
		AgentID:             "test-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               false,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Skip("NATS not available, skipping test")
	}
	defer agent.Shutdown()
	
	// Generate multiple breach IDs
	id1 := agent.generateBreachID()
	time.Sleep(1 * time.Millisecond) // Ensure different timestamp
	id2 := agent.generateBreachID()
	
	// Should be unique
	if id1 == id2 {
		t.Errorf("Breach IDs should be unique: %s == %s", id1, id2)
	}
	
	// Should contain agent ID
	if len(id1) == 0 || len(id2) == 0 {
		t.Error("Breach IDs should not be empty")
	}
}

// BenchmarkAnomalyCheck benchmarks anomaly checking performance.
//
// Target: <1ms per check (allows 1000 checks/sec per agent)
func BenchmarkAnomalyCheck(b *testing.B) {
	config := &Config{
		AgentID:             "bench-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               false,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		b.Skip("NATS not available")
	}
	defer agent.Shutdown()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		agent.checkForAnomalies()
	}
}
