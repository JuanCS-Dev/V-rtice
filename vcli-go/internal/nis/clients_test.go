package nis

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewNISClient verifies client creation
func TestNewNISClient(t *testing.T) {
	client := NewNISClient("http://test-nis:9800")
	assert.NotNil(t, client)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, "http://test-nis:9800", client.endpoint)
}

// TestNewNISClient_DefaultEndpoint verifies default endpoint from config
func TestNewNISClient_DefaultEndpoint(t *testing.T) {
	client := NewNISClient("")
	assert.NotNil(t, client)
	assert.NotEmpty(t, client.endpoint, "Should use config default endpoint")
}

// TestGenerateNarrative_Success verifies narrative generation
func TestGenerateNarrative_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/narrative/generate", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req NarrativeRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "maximus", req.Service)
		assert.Equal(t, "operational", req.Type)

		response := NarrativeResult{
			Service:   "maximus",
			Type:      "operational",
			Narrative: "System is operating normally with 98% uptime.",
			KeyInsights: []string{
				"High availability maintained",
				"No critical incidents",
			},
			Recommendations: []string{
				"Continue monitoring",
			},
			Cost:           0.05,
			GenerationTime: 1250,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GenerateNarrative(&NarrativeRequest{
		Service: "maximus",
		Type:    "operational",
		Focus:   "uptime",
	})

	require.NoError(t, err)
	assert.Equal(t, "maximus", result.Service)
	assert.Equal(t, "operational", result.Type)
	assert.Contains(t, result.Narrative, "operating normally")
	assert.Len(t, result.KeyInsights, 2)
	assert.Len(t, result.Recommendations, 1)
	assert.Equal(t, 0.05, result.Cost)
	assert.Equal(t, 1250, result.GenerationTime)
}

// TestGenerateNarrative_ServerError verifies error handling
func TestGenerateNarrative_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GenerateNarrative(&NarrativeRequest{Service: "test"})

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "generate narrative failed")
}

// TestListNarratives_Success verifies narrative listing
func TestListNarratives_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/narrative/list", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := NarrativeListResult{
			Narratives: []NarrativeSummary{
				{
					Service:   "maximus",
					Type:      "operational",
					Timestamp: "2025-11-14T10:00:00Z",
					Cost:      0.05,
					Preview:   "System is operating normally...",
				},
				{
					Service:   "immune",
					Type:      "security",
					Timestamp: "2025-11-14T09:30:00Z",
					Cost:      0.08,
					Preview:   "Security posture is strong...",
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.ListNarratives()

	require.NoError(t, err)
	assert.Len(t, result.Narratives, 2)
	assert.Equal(t, "maximus", result.Narratives[0].Service)
	assert.Equal(t, "operational", result.Narratives[0].Type)
	assert.Equal(t, 0.05, result.Narratives[0].Cost)
}

// TestListNarratives_Empty verifies empty narrative list
func TestListNarratives_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NarrativeListResult{
			Narratives: []NarrativeSummary{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.ListNarratives()

	require.NoError(t, err)
	assert.Empty(t, result.Narratives)
}

// TestDetectAnomalies_Success verifies anomaly detection
func TestDetectAnomalies_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/anomaly/detect", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req AnomalyRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "maximus", req.Service)
		assert.Equal(t, "response_time", req.Metric)

		response := AnomalyResult{
			Service:  "maximus",
			Baseline: 125.5,
			StdDev:   15.2,
			Anomalies: []Anomaly{
				{
					Timestamp: "2025-11-14T10:15:00Z",
					Metric:    "response_time",
					Value:     250.0,
					ZScore:    8.22,
					Severity:  "high",
				},
				{
					Timestamp: "2025-11-14T10:20:00Z",
					Metric:    "response_time",
					Value:     180.0,
					ZScore:    3.58,
					Severity:  "medium",
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.DetectAnomalies(&AnomalyRequest{
		Service:   "maximus",
		Metric:    "response_time",
		Threshold: 3.0,
	})

	require.NoError(t, err)
	assert.Equal(t, "maximus", result.Service)
	assert.Equal(t, 125.5, result.Baseline)
	assert.Equal(t, 15.2, result.StdDev)
	assert.Len(t, result.Anomalies, 2)
	assert.Equal(t, "high", result.Anomalies[0].Severity)
	assert.Equal(t, 8.22, result.Anomalies[0].ZScore)
}

// TestDetectAnomalies_NoAnomalies verifies no anomalies detected
func TestDetectAnomalies_NoAnomalies(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AnomalyResult{
			Service:   "maximus",
			Baseline:  100.0,
			StdDev:    10.0,
			Anomalies: []Anomaly{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.DetectAnomalies(&AnomalyRequest{
		Service: "maximus",
		Metric:  "response_time",
	})

	require.NoError(t, err)
	assert.Empty(t, result.Anomalies)
}

// TestGetBaseline_Success verifies baseline retrieval
func TestGetBaseline_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/anomaly/baseline", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req BaselineRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "maximus", req.Service)

		response := BaselineResult{
			Service: "maximus",
			Baselines: []BaselineStats{
				{
					Metric:     "response_time",
					Mean:       125.5,
					StdDev:     15.2,
					WindowSize: 1000,
					LastUpdate: "2025-11-14T10:00:00Z",
				},
				{
					Metric:     "cpu_usage",
					Mean:       45.0,
					StdDev:     8.5,
					WindowSize: 1000,
					LastUpdate: "2025-11-14T10:00:00Z",
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetBaseline(&BaselineRequest{
		Service: "maximus",
		Metric:  "all",
	})

	require.NoError(t, err)
	assert.Equal(t, "maximus", result.Service)
	assert.Len(t, result.Baselines, 2)
	assert.Equal(t, "response_time", result.Baselines[0].Metric)
	assert.Equal(t, 125.5, result.Baselines[0].Mean)
	assert.Equal(t, 1000, result.Baselines[0].WindowSize)
}

// TestGetBaseline_Empty verifies empty baseline
func TestGetBaseline_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := BaselineResult{
			Service:   "new-service",
			Baselines: []BaselineStats{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetBaseline(&BaselineRequest{Service: "new-service"})

	require.NoError(t, err)
	assert.Empty(t, result.Baselines)
}

// TestGetCostStatus_Success verifies cost status retrieval
func TestGetCostStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/cost/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := CostStatusResult{
			DailySpent:    2.45,
			DailyLimit:    10.0,
			MonthlySpent:  68.50,
			MonthlyLimit:  300.0,
			TotalRequests: 490,
			AvgCost:       0.14,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetCostStatus()

	require.NoError(t, err)
	assert.Equal(t, 2.45, result.DailySpent)
	assert.Equal(t, 10.0, result.DailyLimit)
	assert.Equal(t, 68.50, result.MonthlySpent)
	assert.Equal(t, 300.0, result.MonthlyLimit)
	assert.Equal(t, 490, result.TotalRequests)
	assert.Equal(t, 0.14, result.AvgCost)
}

// TestGetCostStatus_NearLimit verifies near limit warning
func TestGetCostStatus_NearLimit(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CostStatusResult{
			DailySpent:    9.50,
			DailyLimit:    10.0,
			MonthlySpent:  285.0,
			MonthlyLimit:  300.0,
			TotalRequests: 1950,
			AvgCost:       0.15,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetCostStatus()

	require.NoError(t, err)
	// Verify near limit (95% of daily, 95% of monthly)
	assert.InDelta(t, result.DailyLimit, result.DailySpent, result.DailyLimit*0.1)
	assert.InDelta(t, result.MonthlyLimit, result.MonthlySpent, result.MonthlyLimit*0.1)
}

// TestGetCostHistory_Success verifies cost history retrieval
func TestGetCostHistory_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/cost/history", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := CostHistoryResult{
			History: []CostEntry{
				{
					Date:      "2025-11-14",
					Requests:  150,
					TotalCost: 2.45,
					AvgCost:   0.016,
				},
				{
					Date:      "2025-11-13",
					Requests:  200,
					TotalCost: 3.20,
					AvgCost:   0.016,
				},
				{
					Date:      "2025-11-12",
					Requests:  180,
					TotalCost: 2.88,
					AvgCost:   0.016,
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetCostHistory()

	require.NoError(t, err)
	assert.Len(t, result.History, 3)
	assert.Equal(t, "2025-11-14", result.History[0].Date)
	assert.Equal(t, 150, result.History[0].Requests)
	assert.Equal(t, 2.45, result.History[0].TotalCost)
}

// TestGetCostHistory_Empty verifies empty history
func TestGetCostHistory_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CostHistoryResult{
			History: []CostEntry{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetCostHistory()

	require.NoError(t, err)
	assert.Empty(t, result.History)
}

// TestGetRateLimit_Success verifies rate limit retrieval
func TestGetRateLimit_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/ratelimit", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := RateLimitResult{
			HourlyUsed:    15,
			HourlyLimit:   100,
			DailyUsed:     350,
			DailyLimit:    1000,
			MinInterval:   1000,
			NextAvailable: 0,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetRateLimit()

	require.NoError(t, err)
	assert.Equal(t, 15, result.HourlyUsed)
	assert.Equal(t, 100, result.HourlyLimit)
	assert.Equal(t, 350, result.DailyUsed)
	assert.Equal(t, 1000, result.DailyLimit)
	assert.Equal(t, 1000, result.MinInterval)
	assert.Equal(t, 0, result.NextAvailable)
}

// TestGetRateLimit_NearLimit verifies rate limit near exhaustion
func TestGetRateLimit_NearLimit(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := RateLimitResult{
			HourlyUsed:    98,
			HourlyLimit:   100,
			DailyUsed:     950,
			DailyLimit:    1000,
			MinInterval:   1000,
			NextAvailable: 500,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetRateLimit()

	require.NoError(t, err)
	assert.Greater(t, result.NextAvailable, 0, "Should have wait time when near limit")
	// Verify near limit (within 5%)
	hourlyRemaining := result.HourlyLimit - result.HourlyUsed
	assert.LessOrEqual(t, hourlyRemaining, 5)
}

// TestGetStatus_Success verifies status retrieval
func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:              "healthy",
			Health:              98.5,
			NarrativesGenerated: 1250,
			AnomaliesDetected:   45,
			TotalCost:           125.50,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "healthy", result.Status)
	assert.Equal(t, 98.5, result.Health)
	assert.Equal(t, 1250, result.NarrativesGenerated)
	assert.Equal(t, 45, result.AnomaliesDetected)
	assert.Equal(t, 125.50, result.TotalCost)
}

// TestGetStatus_Degraded verifies degraded status
func TestGetStatus_Degraded(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:              "degraded",
			Health:              65.0,
			NarrativesGenerated: 850,
			AnomaliesDetected:   150,
			TotalCost:           85.25,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result.Status)
	assert.Less(t, result.Health, 70.0, "Health should indicate degradation")
	assert.Greater(t, result.AnomaliesDetected, 100, "High anomaly count")
}

// TestGetStatus_ServerError verifies error handling
func TestGetStatus_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	result, err := client.GetStatus()

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "get status failed")
}

// BenchmarkGenerateNarrative measures narrative generation performance
func BenchmarkGenerateNarrative(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NarrativeResult{
			Service:   "test",
			Narrative: "Test narrative",
			Cost:      0.05,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	req := &NarrativeRequest{Service: "test", Type: "operational"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GenerateNarrative(req)
	}
}

// BenchmarkDetectAnomalies measures anomaly detection performance
func BenchmarkDetectAnomalies(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AnomalyResult{
			Service:   "test",
			Baseline:  100.0,
			Anomalies: []Anomaly{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNISClient(server.URL)
	req := &AnomalyRequest{Service: "test", Metric: "cpu"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.DetectAnomalies(req)
	}
}
