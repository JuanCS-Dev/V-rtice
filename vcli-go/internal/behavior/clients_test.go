package behavior

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// AnalysisClient Tests
// ============================================================================

func TestNewAnalysisClient(t *testing.T) {
	client := NewAnalysisClient("http://test-analysis:5000")
	assert.NotNil(t, client)
	assert.NotNil(t, client.BaseClient)
	assert.Equal(t, "http://test-analysis:5000", client.endpoint)
}

func TestAnalyze_MediumRisk(t *testing.T) {
	client := NewAnalysisClient("http://test-analysis:5000")
	result, err := client.Analyze(&AnalyzeRequest{
		User:      "john.doe",
		Timerange: "7d",
		Threshold: 0.5,
	})

	require.NoError(t, err)
	assert.Equal(t, "john.doe", result.User)
	assert.Equal(t, "7d", result.Timerange)
	assert.Equal(t, 0.65, result.AnomalyScore)
	assert.Equal(t, "medium", result.RiskLevel)
	assert.Len(t, result.Anomalies, 2)

	// Validate anomalies
	assert.Contains(t, result.Anomalies[0].Description, "login time")
	assert.Equal(t, 5, result.Anomalies[0].Severity)
	assert.Greater(t, result.Anomalies[0].Confidence, 0.7)

	assert.Contains(t, result.Anomalies[1].Description, "new location")
	assert.Equal(t, 6, result.Anomalies[1].Severity)
	assert.Greater(t, result.Anomalies[1].Confidence, 0.8)
}

func TestAnalyze_DifferentTimerange(t *testing.T) {
	client := NewAnalysisClient("http://test-analysis:5000")
	result, err := client.Analyze(&AnalyzeRequest{
		User:      "admin",
		Timerange: "30d",
		Threshold: 0.8,
	})

	require.NoError(t, err)
	assert.Equal(t, "admin", result.User)
	assert.Equal(t, "30d", result.Timerange)
	assert.NotEmpty(t, result.Anomalies)
}

// ============================================================================
// BASClient Tests
// ============================================================================

func TestNewBASClient(t *testing.T) {
	client := NewBASClient("http://test-bas:6000")
	assert.NotNil(t, client)
	assert.NotNil(t, client.BaseClient)
	assert.Equal(t, "http://test-bas:6000", client.endpoint)
}

func TestDetectAnomaly_AnomaliesDetected(t *testing.T) {
	client := NewBASClient("http://test-bas:6000")
	result, err := client.DetectAnomaly(&BASDetectRequest{
		Entity: "server-prod-01",
		Mode:   "realtime",
	})

	require.NoError(t, err)
	assert.Equal(t, "server-prod-01", result.Entity)
	assert.Equal(t, "anomalies_detected", result.Status)
	assert.Len(t, result.Anomalies, 2)

	// Validate CPU anomaly
	assert.Contains(t, result.Anomalies[0].Type, "CPU")
	assert.Equal(t, 7, result.Anomalies[0].Severity)
	assert.Greater(t, result.Anomalies[0].Confidence, 0.9)

	// Validate network anomaly
	assert.Contains(t, result.Anomalies[1].Type, "network")
	assert.Equal(t, 6, result.Anomalies[1].Severity)
	assert.Greater(t, result.Anomalies[1].Confidence, 0.8)
}

func TestDetectAnomaly_DifferentEntity(t *testing.T) {
	client := NewBASClient("http://test-bas:6000")
	result, err := client.DetectAnomaly(&BASDetectRequest{
		Entity: "database-cluster",
		Mode:   "batch",
	})

	require.NoError(t, err)
	assert.Equal(t, "database-cluster", result.Entity)
	assert.NotEmpty(t, result.Anomalies)
}

// ============================================================================
// MAVClient Tests
// ============================================================================

func TestNewMAVClient(t *testing.T) {
	client := NewMAVClient("http://test-mav:7000")
	assert.NotNil(t, client)
	assert.NotNil(t, client.BaseClient)
	assert.Equal(t, "http://test-mav:7000", client.endpoint)
}

func TestScan_NetworkVectors(t *testing.T) {
	client := NewMAVClient("http://test-mav:7000")
	result, err := client.Scan(&MAVScanRequest{
		Network: "10.0.0.0/24",
		Mode:    "aggressive",
	})

	require.NoError(t, err)
	assert.Equal(t, "10.0.0.0/24", result.Network)
	assert.Equal(t, 254, result.HostsScanned)
	assert.Len(t, result.Vectors, 2)

	// Validate port scanning vector
	assert.Contains(t, result.Vectors[0].Type, "Port scanning")
	assert.Equal(t, "10.0.0.15", result.Vectors[0].Source)
	assert.Equal(t, 6, result.Vectors[0].Severity)

	// Validate brute force vector
	assert.Contains(t, result.Vectors[1].Type, "Brute force")
	assert.Equal(t, "10.0.0.42", result.Vectors[1].Source)
	assert.Equal(t, 8, result.Vectors[1].Severity)
}

func TestScan_DifferentNetwork(t *testing.T) {
	client := NewMAVClient("http://test-mav:7000")
	result, err := client.Scan(&MAVScanRequest{
		Network: "192.168.1.0/24",
		Mode:    "stealth",
	})

	require.NoError(t, err)
	assert.Equal(t, "192.168.1.0/24", result.Network)
	assert.Greater(t, result.HostsScanned, 0)
	assert.NotEmpty(t, result.Vectors)
}

// ============================================================================
// TrafficClient Tests
// ============================================================================

func TestNewTrafficClient(t *testing.T) {
	client := NewTrafficClient("http://test-traffic:8000")
	assert.NotNil(t, client)
	assert.NotNil(t, client.BaseClient)
	assert.Equal(t, "http://test-traffic:8000", client.endpoint)
}

func TestTrafficAnalyze_AnomalousFlows(t *testing.T) {
	client := NewTrafficClient("http://test-traffic:8000")
	result, err := client.Analyze(&TrafficAnalyzeRequest{
		PCAPPath: "/captures/traffic-2024.pcap",
		Mode:     "deep",
	})

	require.NoError(t, err)
	assert.Equal(t, 125430, result.PacketsAnalyzed)
	assert.Equal(t, 1247, result.FlowsIdentified)
	assert.Len(t, result.AnomalousFlows, 2)

	// Validate DNS tunneling detection
	dnsFlow := result.AnomalousFlows[0]
	assert.Equal(t, "192.168.1.50", dnsFlow.Source)
	assert.Equal(t, "8.8.8.8", dnsFlow.Destination)
	assert.Equal(t, "DNS", dnsFlow.Protocol)
	assert.Contains(t, dnsFlow.AnomalyType, "DNS tunneling")
	assert.Equal(t, 8, dnsFlow.Severity)

	// Validate C2 communication detection
	c2Flow := result.AnomalousFlows[1]
	assert.Equal(t, "192.168.1.100", c2Flow.Source)
	assert.Contains(t, c2Flow.Destination, "external-c2.com")
	assert.Equal(t, "HTTPS", c2Flow.Protocol)
	assert.Contains(t, c2Flow.AnomalyType, "C2 communication")
	assert.Equal(t, 9, c2Flow.Severity)
}

func TestTrafficAnalyze_DifferentPCAP(t *testing.T) {
	client := NewTrafficClient("http://test-traffic:8000")
	result, err := client.Analyze(&TrafficAnalyzeRequest{
		PCAPPath: "/captures/suspicious-traffic.pcap",
		Mode:     "fast",
	})

	require.NoError(t, err)
	assert.Greater(t, result.PacketsAnalyzed, 100000)
	assert.Greater(t, result.FlowsIdentified, 1000)
	assert.NotEmpty(t, result.AnomalousFlows)
}

// ============================================================================
// FabricClient Tests
// ============================================================================

func TestNewFabricClient(t *testing.T) {
	client := NewFabricClient("http://test-fabric:9000")
	assert.NotNil(t, client)
	assert.NotNil(t, client.BaseClient)
	assert.Equal(t, "http://test-fabric:9000", client.endpoint)
}

func TestGetStatus_AllComponentsActive(t *testing.T) {
	client := NewFabricClient("http://test-fabric:9000")
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Len(t, result.Components, 3)

	// Validate Fabric Core
	core := result.Components[0]
	assert.Equal(t, "Fabric Core", core.Name)
	assert.Equal(t, "active", core.Status)
	assert.Equal(t, 342, core.ActiveRules)
	assert.Equal(t, 1250, core.EventsPerSecond)

	// Validate Fabric Analysis
	analysis := result.Components[1]
	assert.Equal(t, "Fabric Analysis", analysis.Name)
	assert.Equal(t, "active", analysis.Status)
	assert.Equal(t, 128, analysis.ActiveRules)
	assert.Equal(t, 850, analysis.EventsPerSecond)

	// Validate Fabric Response
	response := result.Components[2]
	assert.Equal(t, "Fabric Response", response.Name)
	assert.Equal(t, "active", response.Status)
	assert.Equal(t, 67, response.ActiveRules)
	assert.Equal(t, 420, response.EventsPerSecond)
}

func TestGetStatus_ComponentCounts(t *testing.T) {
	client := NewFabricClient("http://test-fabric:9000")
	result, err := client.GetStatus()

	require.NoError(t, err)

	totalRules := 0
	totalEPS := 0
	for _, comp := range result.Components {
		totalRules += comp.ActiveRules
		totalEPS += comp.EventsPerSecond
		assert.Equal(t, "active", comp.Status)
	}

	assert.Equal(t, 537, totalRules)    // 342 + 128 + 67
	assert.Equal(t, 2520, totalEPS)     // 1250 + 850 + 420
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkAnalyze(b *testing.B) {
	client := NewAnalysisClient("http://test-analysis:5000")
	req := &AnalyzeRequest{User: "test", Timerange: "7d", Threshold: 0.5}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Analyze(req)
	}
}

func BenchmarkDetectAnomaly(b *testing.B) {
	client := NewBASClient("http://test-bas:6000")
	req := &BASDetectRequest{Entity: "server-01", Mode: "realtime"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.DetectAnomaly(req)
	}
}

func BenchmarkMAVScan(b *testing.B) {
	client := NewMAVClient("http://test-mav:7000")
	req := &MAVScanRequest{Network: "10.0.0.0/24", Mode: "aggressive"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Scan(req)
	}
}

func BenchmarkTrafficAnalyze(b *testing.B) {
	client := NewTrafficClient("http://test-traffic:8000")
	req := &TrafficAnalyzeRequest{PCAPPath: "/test.pcap", Mode: "deep"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Analyze(req)
	}
}

func BenchmarkFabricGetStatus(b *testing.B) {
	client := NewFabricClient("http://test-fabric:9000")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetStatus()
	}
}
