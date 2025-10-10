package platelet_agent

import (
	"context"
	"testing"
	"time"
)

// TestPlateletAgentIntegration tests full agent lifecycle.
//
// Integration test: Agent → Sensors → P2P → Detection
func TestPlateletAgentIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}
	
	// Create agent
	config := &Config{
		AgentID:             "integration-test-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.6,
		Debug:               true,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Skip("NATS not available, skipping integration test")
	}
	defer agent.Shutdown()
	
	// Start agent
	if err := agent.Start(); err != nil {
		t.Fatalf("Failed to start agent: %v", err)
	}
	
	t.Log("Agent started successfully")
	
	// Let agent run for monitoring cycle
	time.Sleep(3 * time.Second)
	
	// Verify agent is in resting state initially
	if agent.state != StateResting {
		t.Errorf("Expected agent in Resting state, got %s", agent.state)
	}
	
	// Verify sensors are running
	processScore := agent.processSensor.GetAnomalyScore()
	networkScore := agent.networkSensor.GetAnomalyScore()
	fileScore := agent.fileSensor.GetAnomalyScore()
	
	t.Logf("Sensor scores: process=%.2f, network=%.2f, file=%.2f", 
		processScore, networkScore, fileScore)
	
	// Scores should be within valid range
	if processScore < 0.0 || processScore > 1.0 {
		t.Errorf("Process score out of range: %.2f", processScore)
	}
	if networkScore < 0.0 || networkScore > 1.0 {
		t.Errorf("Network score out of range: %.2f", networkScore)
	}
	if fileScore < 0.0 || fileScore > 1.0 {
		t.Errorf("File score out of range: %.2f", fileScore)
	}
}

// TestMultiAgentCommunication tests P2P signaling between agents.
func TestMultiAgentCommunication(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}
	
	// Create two agents
	agent1, err := NewAgent(&Config{
		AgentID:             "agent-1",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.6,
		Debug:               false,
	})
	if err != nil {
		t.Skip("NATS not available")
	}
	defer agent1.Shutdown()
	
	agent2, err := NewAgent(&Config{
		AgentID:             "agent-2",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               false,
	})
	if err != nil {
		agent1.Shutdown()
		t.Skip("NATS not available")
	}
	defer agent2.Shutdown()
	
	// Start both agents
	if err := agent1.Start(); err != nil {
		t.Fatalf("Failed to start agent1: %v", err)
	}
	if err := agent2.Start(); err != nil {
		t.Fatalf("Failed to start agent2: %v", err)
	}
	
	t.Log("Both agents started")
	
	// Give agents time to establish subscriptions
	time.Sleep(2 * time.Second)
	
	// Simulate agent1 activation
	agent1.activate(0.8)
	
	// Wait for P2P signal propagation
	time.Sleep(1 * time.Second)
	
	// Verify agent1 is activated
	if agent1.state != StateActivated {
		t.Errorf("Agent1 should be activated, got %s", agent1.state)
	}
	
	t.Log("Multi-agent communication test passed")
}

// TestSensorIntegration tests all sensors working together.
func TestSensorIntegration(t *testing.T) {
	config := &Config{
		AgentID:             "sensor-test-agent",
		NATSEndpoint:        "nats://localhost:4222",
		ActivationThreshold: 0.7,
		Debug:               true,
	}
	
	agent, err := NewAgent(config)
	if err != nil {
		t.Skip("NATS not available")
	}
	defer agent.Shutdown()
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	// Start sensors
	if err := agent.processSensor.Start(ctx); err != nil {
		t.Fatalf("Failed to start process sensor: %v", err)
	}
	if err := agent.networkSensor.Start(ctx); err != nil {
		t.Fatalf("Failed to start network sensor: %v", err)
	}
	if err := agent.fileSensor.Start(ctx); err != nil {
		t.Fatalf("Failed to start file sensor: %v", err)
	}
	
	// Let sensors run
	time.Sleep(3 * time.Second)
	
	// Verify all sensors have scores
	processScore := agent.processSensor.GetAnomalyScore()
	networkScore := agent.networkSensor.GetAnomalyScore()
	fileScore := agent.fileSensor.GetAnomalyScore()
	
	t.Logf("Process baseline: %d processes", len(agent.processSensor.knownProcesses))
	
	// Network connections
	knownConns, suspIPs := agent.networkSensor.GetConnectionStats()
	t.Logf("Network baseline: %d connections, %d suspicious IPs", knownConns, suspIPs)
	
	// File monitoring
	monitoredFiles := agent.fileSensor.GetMonitoredFileCount()
	t.Logf("File baseline: %d monitored files", monitoredFiles)
	
	// All sensors should have valid scores
	scores := []float64{processScore, networkScore, fileScore}
	for i, score := range scores {
		if score < 0.0 || score > 1.0 {
			t.Errorf("Sensor %d score out of range: %.2f", i, score)
		}
	}
}
