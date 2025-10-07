package load

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

const (
	grpcServerURL = "localhost:50051"
	operatorID    = "load_test_operator"
)

// LoadTestResult holds metrics from a load test
type LoadTestResult struct {
	TotalRequests      int64
	SuccessfulRequests int64
	FailedRequests     int64
	TotalDuration      time.Duration
	MinLatency         time.Duration
	MaxLatency         time.Duration
	AvgLatency         time.Duration
	P50Latency         time.Duration
	P95Latency         time.Duration
	P99Latency         time.Duration
	P999Latency        time.Duration
	RequestsPerSecond  float64
	ErrorRate          float64
}

// LatencyTracker tracks individual request latencies
type LatencyTracker struct {
	latencies []time.Duration
	mu        sync.Mutex
}

func (lt *LatencyTracker) Record(latency time.Duration) {
	lt.mu.Lock()
	defer lt.mu.Unlock()
	lt.latencies = append(lt.latencies, latency)
}

func (lt *LatencyTracker) Calculate() (min, max, avg, p50, p95, p99, p999 time.Duration) {
	lt.mu.Lock()
	defer lt.mu.Unlock()

	if len(lt.latencies) == 0 {
		return 0, 0, 0, 0, 0, 0, 0
	}

	// Sort latencies for percentile calculation
	sorted := make([]time.Duration, len(lt.latencies))
	copy(sorted, lt.latencies)
	sortDurations(sorted)

	min = sorted[0]
	max = sorted[len(sorted)-1]

	var total time.Duration
	for _, l := range sorted {
		total += l
	}
	avg = total / time.Duration(len(sorted))

	p50 = sorted[int(float64(len(sorted))*0.50)]
	p95 = sorted[int(float64(len(sorted))*0.95)]
	p99 = sorted[int(float64(len(sorted))*0.99)]
	p999 = sorted[int(float64(len(sorted))*0.999)]

	return min, max, avg, p50, p95, p99, p999
}

// sortDurations sorts slice of durations in place
func sortDurations(durations []time.Duration) {
	// Simple bubble sort (sufficient for test data)
	for i := 0; i < len(durations); i++ {
		for j := i + 1; j < len(durations); j++ {
			if durations[i] > durations[j] {
				durations[i], durations[j] = durations[j], durations[i]
			}
		}
	}
}

// runLoadTest executes a load test with specified parameters
func runLoadTest(t *testing.T, concurrency int, totalRequests int, operationFunc func(context.Context, *grpcclient.GovernanceClient) error) *LoadTestResult {
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping load test")
		return nil
	}
	defer client.Close()

	result := &LoadTestResult{}
	tracker := &LatencyTracker{latencies: make([]time.Duration, 0, totalRequests)}

	var successful atomic.Int64
	var failed atomic.Int64

	requestsPerWorker := totalRequests / concurrency
	var wg sync.WaitGroup

	startTime := time.Now()

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			for j := 0; j < requestsPerWorker; j++ {
				ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
				requestStart := time.Now()

				err := operationFunc(ctx, client)
				latency := time.Since(requestStart)

				cancel()

				tracker.Record(latency)

				if err != nil {
					failed.Add(1)
				} else {
					successful.Add(1)
				}
			}
		}(i)
	}

	wg.Wait()
	totalDuration := time.Since(startTime)

	result.TotalRequests = int64(totalRequests)
	result.SuccessfulRequests = successful.Load()
	result.FailedRequests = failed.Load()
	result.TotalDuration = totalDuration
	result.RequestsPerSecond = float64(totalRequests) / totalDuration.Seconds()
	result.ErrorRate = float64(failed.Load()) / float64(totalRequests) * 100

	result.MinLatency, result.MaxLatency, result.AvgLatency,
		result.P50Latency, result.P95Latency, result.P99Latency, result.P999Latency = tracker.Calculate()

	return result
}

// Helper to repeat string (Go doesn't have built-in)
func repeatString(s string, n int) string {
	result := ""
	for i := 0; i < n; i++ {
		result += s
	}
	return result
}

// printLoadTestResult prints formatted load test results
func printLoadTestResult(t *testing.T, testName string, result *LoadTestResult) {
	separator := repeatString("=", 80)
	t.Logf("\n%s", separator)
	t.Logf("Load Test: %s", testName)
	t.Logf("%s", separator)
	t.Logf("Total Requests:      %d", result.TotalRequests)
	t.Logf("Successful:          %d (%.2f%%)", result.SuccessfulRequests, float64(result.SuccessfulRequests)/float64(result.TotalRequests)*100)
	t.Logf("Failed:              %d (%.2f%%)", result.FailedRequests, result.ErrorRate)
	t.Logf("Total Duration:      %v", result.TotalDuration)
	t.Logf("Throughput:          %.2f req/s", result.RequestsPerSecond)
	t.Logf("\nLatency Metrics:")
	t.Logf("  Min:     %v", result.MinLatency)
	t.Logf("  Max:     %v", result.MaxLatency)
	t.Logf("  Average: %v", result.AvgLatency)
	t.Logf("  P50:     %v", result.P50Latency)
	t.Logf("  P95:     %v", result.P95Latency)
	t.Logf("  P99:     %v", result.P99Latency)
	t.Logf("  P999:    %v", result.P999Latency)
	t.Logf("%s\n", separator)
}

// TestLoad_HealthCheck_1K tests health check with 1,000 requests
func TestLoad_HealthCheck_1K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		_, err := client.HealthCheck(ctx)
		return err
	}

	result := runLoadTest(t, 10, 1000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "Health Check - 1K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(950), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 10*time.Millisecond, "P99 latency should be < 10ms")
	assert.Greater(t, result.RequestsPerSecond, 100.0, "Should handle > 100 req/s")
}

// TestLoad_HealthCheck_5K tests health check with 5,000 requests
func TestLoad_HealthCheck_5K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		_, err := client.HealthCheck(ctx)
		return err
	}

	result := runLoadTest(t, 50, 5000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "Health Check - 5K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(4750), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 15*time.Millisecond, "P99 latency should be < 15ms")
	assert.Greater(t, result.RequestsPerSecond, 500.0, "Should handle > 500 req/s")
}

// TestLoad_HealthCheck_10K tests health check with 10,000 requests
func TestLoad_HealthCheck_10K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		_, err := client.HealthCheck(ctx)
		return err
	}

	result := runLoadTest(t, 100, 10000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "Health Check - 10K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(9500), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 40*time.Millisecond, "P99 latency should be < 40ms")
	assert.Greater(t, result.RequestsPerSecond, 1000.0, "Should handle > 1000 req/s")
}

// TestLoad_CreateSession_1K tests session creation under load
func TestLoad_CreateSession_1K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	sessionCounter := atomic.Int64{}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		operatorName := fmt.Sprintf("%s_%d", operatorID, sessionCounter.Add(1))
		_, err := client.CreateSession(ctx, operatorName)
		return err
	}

	result := runLoadTest(t, 10, 1000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "Create Session - 1K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(950), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 50*time.Millisecond, "P99 latency should be < 50ms")
}

// TestLoad_ListDecisions_5K tests list operations under load
func TestLoad_ListDecisions_5K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		_, err := client.ListPendingDecisions(ctx, 10, "PENDING", "")
		return err
	}

	result := runLoadTest(t, 50, 5000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "List Decisions - 5K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(4750), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 100*time.Millisecond, "P99 latency should be < 100ms")
}

// TestLoad_GetMetrics_10K tests metrics endpoint under heavy load
func TestLoad_GetMetrics_10K(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping load test in short mode")
	}

	operationFunc := func(ctx context.Context, client *grpcclient.GovernanceClient) error {
		_, err := client.GetMetrics(ctx)
		return err
	}

	result := runLoadTest(t, 100, 10000, operationFunc)
	if result == nil {
		return
	}

	printLoadTestResult(t, "Get Metrics - 10K requests", result)

	// Assertions
	assert.Greater(t, result.SuccessfulRequests, int64(9500), "Success rate should be > 95%")
	assert.Less(t, result.P99Latency, 20*time.Millisecond, "P99 latency should be < 20ms")
	assert.Greater(t, result.RequestsPerSecond, 2000.0, "Should handle > 2000 req/s")
}

// TestLoad_SustainedLoad tests sustained load over time
func TestLoad_SustainedLoad(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping sustained load test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping load test")
		return
	}
	defer client.Close()

	duration := 30 * time.Second
	targetRPS := 1000
	concurrency := 10

	t.Logf("Running sustained load test: %d req/s for %v...", targetRPS, duration)

	var successful atomic.Int64
	var failed atomic.Int64
	tracker := &LatencyTracker{latencies: make([]time.Duration, 0, targetRPS*int(duration.Seconds()))}

	ctx, cancel := context.WithTimeout(context.Background(), duration)
	defer cancel()

	var wg sync.WaitGroup
	startTime := time.Now()

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			ticker := time.NewTicker(time.Second / time.Duration(targetRPS/concurrency))
			defer ticker.Stop()

			for {
				select {
				case <-ctx.Done():
					return
				case <-ticker.C:
					reqStart := time.Now()
					_, err := client.HealthCheck(ctx)
					latency := time.Since(reqStart)

					tracker.Record(latency)

					if err != nil {
						failed.Add(1)
					} else {
						successful.Add(1)
					}
				}
			}
		}()
	}

	wg.Wait()
	totalDuration := time.Since(startTime)

	totalRequests := successful.Load() + failed.Load()
	min, max, avg, p50, p95, p99, p999 := tracker.Calculate()

	separator := repeatString("=", 80)
	t.Logf("\n%s", separator)
	t.Logf("Sustained Load Test Results")
	t.Logf("%s", separator)
	t.Logf("Duration:            %v", totalDuration)
	t.Logf("Total Requests:      %d", totalRequests)
	t.Logf("Successful:          %d (%.2f%%)", successful.Load(), float64(successful.Load())/float64(totalRequests)*100)
	t.Logf("Failed:              %d (%.2f%%)", failed.Load(), float64(failed.Load())/float64(totalRequests)*100)
	t.Logf("Actual RPS:          %.2f", float64(totalRequests)/totalDuration.Seconds())
	t.Logf("\nLatency Metrics:")
	t.Logf("  Min:     %v", min)
	t.Logf("  Max:     %v", max)
	t.Logf("  Average: %v", avg)
	t.Logf("  P50:     %v", p50)
	t.Logf("  P95:     %v", p95)
	t.Logf("  P99:     %v", p99)
	t.Logf("  P999:    %v", p999)
	t.Logf("%s\n", separator)

	// Assertions
	assert.Greater(t, successful.Load(), int64(float64(totalRequests)*0.95), "Success rate should be > 95%")
	assert.Less(t, p99, 20*time.Millisecond, "P99 latency should remain < 20ms under sustained load")
	assert.Less(t, avg, 5*time.Millisecond, "Average latency should remain < 5ms")

	// Verify no significant degradation over time
	require.Less(t, max, 100*time.Millisecond, "Max latency should not spike > 100ms")
}

// TestLoad_MixedOperations tests realistic mixed workload
func TestLoad_MixedOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping mixed operations load test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping load test")
		return
	}
	defer client.Close()

	totalRequests := 5000
	concurrency := 50

	var successful atomic.Int64
	var failed atomic.Int64
	tracker := &LatencyTracker{latencies: make([]time.Duration, 0, totalRequests)}

	var wg sync.WaitGroup
	startTime := time.Now()

	requestsPerWorker := totalRequests / concurrency

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			for j := 0; j < requestsPerWorker; j++ {
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				requestStart := time.Now()

				var err error
				// Mix of operations (weighted by typical usage)
				operation := j % 5
				switch operation {
				case 0, 1, 2: // 60% health checks
					_, err = client.HealthCheck(ctx)
				case 3: // 20% list decisions
					_, err = client.ListPendingDecisions(ctx, 10, "PENDING", "")
				case 4: // 20% get metrics
					_, err = client.GetMetrics(ctx)
				}

				latency := time.Since(requestStart)
				cancel()

				tracker.Record(latency)

				if err != nil {
					failed.Add(1)
				} else {
					successful.Add(1)
				}
			}
		}(i)
	}

	wg.Wait()
	totalDuration := time.Since(startTime)

	min, max, avg, p50, p95, p99, p999 := tracker.Calculate()

	separator := repeatString("=", 80)
	t.Logf("\n%s", separator)
	t.Logf("Mixed Operations Load Test")
	t.Logf("%s", separator)
	t.Logf("Total Requests:      %d", totalRequests)
	t.Logf("Successful:          %d (%.2f%%)", successful.Load(), float64(successful.Load())/float64(totalRequests)*100)
	t.Logf("Failed:              %d (%.2f%%)", failed.Load(), float64(failed.Load())/float64(totalRequests)*100)
	t.Logf("Total Duration:      %v", totalDuration)
	t.Logf("Throughput:          %.2f req/s", float64(totalRequests)/totalDuration.Seconds())
	t.Logf("\nLatency Metrics:")
	t.Logf("  Min:     %v", min)
	t.Logf("  Max:     %v", max)
	t.Logf("  Average: %v", avg)
	t.Logf("  P50:     %v", p50)
	t.Logf("  P95:     %v", p95)
	t.Logf("  P99:     %v", p99)
	t.Logf("  P999:    %v", p999)
	t.Logf("%s\n", separator)

	// Assertions
	assert.Greater(t, successful.Load(), int64(4750), "Success rate should be > 95%")
	assert.Less(t, p99, 50*time.Millisecond, "P99 latency should be < 50ms")
	assert.Greater(t, float64(totalRequests)/totalDuration.Seconds(), 500.0, "Should handle > 500 req/s mixed workload")
}
