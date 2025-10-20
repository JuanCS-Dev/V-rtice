// +build integration

package benchmark

import (
	"context"
	"fmt"
	"testing"
	"time"

	gov "github.com/verticedev/vcli-go/internal/governance"
	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

const (
	httpServerURL = "http://localhost:8000"
	grpcServerURL = "localhost:50051"
	operatorID    = "benchmark_operator"
)

// BenchmarkHTTPClient_HealthCheck benchmarks HTTP health check
func BenchmarkHTTPClient_HealthCheck(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.HealthCheck(ctx)
		if err != nil {
			b.Logf("Health check failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_HealthCheck benchmarks gRPC health check
func BenchmarkGRPCClient_HealthCheck(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.HealthCheck(ctx)
		if err != nil {
			b.Logf("Health check failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_CreateSession benchmarks HTTP session creation
func BenchmarkHTTPClient_CreateSession(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
		if err != nil {
			b.Logf("Session creation failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_CreateSession benchmarks gRPC session creation
func BenchmarkGRPCClient_CreateSession(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.CreateSession(ctx, fmt.Sprintf("%s_%d", operatorID, i))
		if err != nil {
			b.Logf("Session creation failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_ListDecisions benchmarks HTTP decision listing
func BenchmarkHTTPClient_ListDecisions(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	session, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("Failed to create session")
		return
	}
	client.SetSessionID(session.SessionID)

	filter := &gov.DecisionFilter{
		Status: []gov.DecisionStatus{gov.DecisionStatusPending},
		Limit:  10,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.ListDecisions(ctx, filter)
		if err != nil {
			b.Logf("List decisions failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_ListDecisions benchmarks gRPC decision listing
func BenchmarkGRPCClient_ListDecisions(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Failed to create session")
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.ListPendingDecisions(ctx, 10, "PENDING", "")
		if err != nil {
			b.Logf("List decisions failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_GetMetrics benchmarks HTTP metrics retrieval
func BenchmarkHTTPClient_GetMetrics(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	session, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("Failed to create session")
		return
	}
	client.SetSessionID(session.SessionID)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetMetrics(ctx)
		if err != nil {
			b.Logf("Get metrics failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_GetMetrics benchmarks gRPC metrics retrieval
func BenchmarkGRPCClient_GetMetrics(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Failed to create session")
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetMetrics(ctx)
		if err != nil {
			b.Logf("Get metrics failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_ApproveDecision benchmarks HTTP decision approval
func BenchmarkHTTPClient_ApproveDecision(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	session, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("Failed to create session")
		return
	}
	client.SetSessionID(session.SessionID)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Use a mock decision ID (will fail but we're measuring overhead)
		_ = client.ApproveDecision(ctx, fmt.Sprintf("dec-bench-%d", i), "Benchmark approval")
	}
}

// BenchmarkGRPCClient_ApproveDecision benchmarks gRPC decision approval
func BenchmarkGRPCClient_ApproveDecision(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Failed to create session")
		return
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Approve known decision
		_ = client.ApproveDecision(ctx, "dec-001", "Benchmark approval", "Performance test")
	}
}

// BenchmarkClientFactory benchmarks the factory pattern overhead
func BenchmarkClientFactory_HTTP(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client, err := gov.NewClient(gov.ClientConfig{
			BackendType: gov.BackendHTTP,
			ServerURL:   httpServerURL,
			OperatorID:  operatorID,
		})
		if err != nil {
			b.Fatal(err)
		}
		_ = client.Close()
	}
}

// BenchmarkClientFactory_gRPC benchmarks the factory pattern overhead for gRPC
func BenchmarkClientFactory_gRPC(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client, err := gov.NewClient(gov.ClientConfig{
			BackendType: gov.BackendGRPC,
			ServerURL:   grpcServerURL,
			OperatorID:  operatorID,
		})
		if err != nil {
			b.Logf("Failed to create client: %v", err)
			continue
		}
		_ = client.Close()
	}
}

// BenchmarkRoundTrip_Parallel benchmarks concurrent requests
func BenchmarkHTTPClient_Parallel(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	session, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("Failed to create session")
		return
	}
	client.SetSessionID(session.SessionID)

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			_, _ = client.HealthCheck(ctx)
		}
	})
}

// BenchmarkGRPCClient_Parallel benchmarks concurrent gRPC requests
func BenchmarkGRPCClient_Parallel(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Failed to create session")
		return
	}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			_, _ = client.HealthCheck(ctx)
		}
	})
}

// LatencyTest measures actual latency distribution
func BenchmarkHTTPClient_Latency(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	latencies := make([]time.Duration, b.N)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		start := time.Now()
		_, _ = client.HealthCheck(ctx)
		latencies[i] = time.Since(start)
	}
	b.StopTimer()

	// Calculate percentiles
	if b.N > 0 {
		b.Logf("Latency stats: min=%v, max=%v",
			minDuration(latencies), maxDuration(latencies))
	}
}

// BenchmarkGRPCClient_Latency measures gRPC latency distribution
func BenchmarkGRPCClient_Latency(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()
	latencies := make([]time.Duration, b.N)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		start := time.Now()
		_, _ = client.HealthCheck(ctx)
		latencies[i] = time.Since(start)
	}
	b.StopTimer()

	// Calculate percentiles
	if b.N > 0 {
		b.Logf("Latency stats: min=%v, max=%v",
			minDuration(latencies), maxDuration(latencies))
	}
}

// Helper functions
func minDuration(d []time.Duration) time.Duration {
	if len(d) == 0 {
		return 0
	}
	min := d[0]
	for _, v := range d[1:] {
		if v < min {
			min = v
		}
	}
	return min
}

func maxDuration(d []time.Duration) time.Duration {
	if len(d) == 0 {
		return 0
	}
	max := d[0]
	for _, v := range d[1:] {
		if v > max {
			max = v
		}
	}
	return max
}

// BenchmarkHTTPClient_RejectDecision benchmarks HTTP reject decision
func BenchmarkHTTPClient_RejectDecision(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("HTTP server not available or session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		decisionID := fmt.Sprintf("bench-reject-%d", i)
		err := client.RejectDecision(ctx, decisionID, "Benchmark test", "Performance testing")
		if err != nil {
			b.Logf("Reject failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_RejectDecision benchmarks gRPC reject decision
func BenchmarkGRPCClient_RejectDecision(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		decisionID := fmt.Sprintf("bench-reject-%d", i)
		err := client.RejectDecision(ctx, decisionID, "Benchmark test", "Performance testing")
		if err != nil {
			b.Logf("Reject failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_GetDecision benchmarks HTTP get decision
func BenchmarkHTTPClient_GetDecision(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("HTTP server not available or session creation failed")
		return
	}
	// Session cleanup handled by server

	// Use a known decision ID (from POC data)
	decisionID := "dec-001"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetDecision(ctx, decisionID)
		if err != nil {
			b.Logf("Get decision failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_GetDecision benchmarks gRPC get decision
func BenchmarkGRPCClient_GetDecision(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Session creation failed")
		return
	}
	// Session cleanup handled by server

	// Use a known decision ID (from POC data)
	decisionID := "dec-001"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetDecision(ctx, decisionID)
		if err != nil {
			b.Logf("Get decision failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_EscalateDecision benchmarks HTTP escalate decision
func BenchmarkHTTPClient_EscalateDecision(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("HTTP server not available or session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		decisionID := fmt.Sprintf("bench-escalate-%d", i)
		err := client.EscalateDecision(ctx, decisionID, "Benchmark test", "soc_lead")
		if err != nil {
			b.Logf("Escalate failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_EscalateDecision benchmarks gRPC escalate decision
func BenchmarkGRPCClient_EscalateDecision(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		decisionID := fmt.Sprintf("bench-escalate-%d", i)
		err := client.EscalateDecision(ctx, decisionID, "Benchmark test", "soc_lead")
		if err != nil {
			b.Logf("Escalate failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_GetSessionStats benchmarks HTTP get session stats
func BenchmarkHTTPClient_GetSessionStats(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	// Create session first
	_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
	if err != nil {
		b.Skip("HTTP server not available or session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetSessionStats(ctx)
		if err != nil {
			b.Logf("Get session stats failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_GetSessionStats benchmarks gRPC get session stats
func BenchmarkGRPCClient_GetSessionStats(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session first
	_, err = client.CreateSession(ctx, operatorID)
	if err != nil {
		b.Skip("Session creation failed")
		return
	}
	// Session cleanup handled by server

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := client.GetSessionStats(ctx)
		if err != nil {
			b.Logf("Get session stats failed: %v", err)
		}
	}
}

// BenchmarkHTTPClient_CloseSession benchmarks HTTP close session
func BenchmarkHTTPClient_CloseSession(b *testing.B) {
	client := gov.NewHTTPClient(httpServerURL, operatorID)
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		b.StopTimer()
		// Create session
		_, err := client.CreateSession(ctx, operatorID, "benchmark_role")
		if err != nil {
			b.Skip("HTTP server not available or session creation failed")
			return
		}
		b.StartTimer()

		// Close session
		err = client.CloseSession(ctx)
		if err != nil {
			b.Logf("Close session failed: %v", err)
		}
	}
}

// BenchmarkGRPCClient_CloseSession benchmarks gRPC close session
func BenchmarkGRPCClient_CloseSession(b *testing.B) {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		b.Skip("gRPC server not available")
		return
	}
	defer client.Close()

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		b.StopTimer()
		// Create session
		_, err = client.CreateSession(ctx, fmt.Sprintf("%s_%d", operatorID, i))
		if err != nil {
			b.Skip("Session creation failed")
			return
		}
		b.StartTimer()

		// Close session
		err = client.CloseSession(ctx)
		if err != nil {
			b.Logf("Close session failed: %v", err)
		}
	}
}
