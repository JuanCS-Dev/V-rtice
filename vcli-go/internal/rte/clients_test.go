package rte

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewRTEClient verifies client creation
func TestNewRTEClient(t *testing.T) {
	client := NewRTEClient("http://test-rte:9900")
	assert.NotNil(t, client)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, "http://test-rte:9900", client.endpoint)
}

// TestNewRTEClient_DefaultEndpoint verifies default endpoint from config
func TestNewRTEClient_DefaultEndpoint(t *testing.T) {
	client := NewRTEClient("")
	assert.NotNil(t, client)
	assert.NotEmpty(t, client.endpoint, "Should use config default endpoint")
}

// TestTriage_Success verifies successful alert triage
func TestTriage_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/triage", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req TriageRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "alert-12345", req.AlertID)
		assert.Equal(t, "malware-triage", req.Playbook)
		assert.True(t, req.Auto)

		response := TriageResult{
			AlertID:       "alert-12345",
			Verdict:       "malicious",
			Confidence:    0.95,
			ExecutionTime: 150,
			PlaybookUsed:  "malware-triage",
			Actions: []ActionResult{
				{Action: "isolate_host", Status: "completed"},
				{Action: "collect_forensics", Status: "completed"},
			},
			Reasoning: "Multiple malware indicators detected with high confidence",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Triage(&TriageRequest{
		AlertID:  "alert-12345",
		Playbook: "malware-triage",
		Auto:     true,
	})

	require.NoError(t, err)
	assert.Equal(t, "alert-12345", result.AlertID)
	assert.Equal(t, "malicious", result.Verdict)
	assert.Equal(t, 0.95, result.Confidence)
	assert.Equal(t, 150, result.ExecutionTime)
	assert.Len(t, result.Actions, 2)
	assert.Equal(t, "isolate_host", result.Actions[0].Action)
	assert.Equal(t, "completed", result.Actions[0].Status)
	assert.Contains(t, result.Reasoning, "high confidence")
}

// TestTriage_BenignVerdict verifies benign triage result
func TestTriage_BenignVerdict(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TriageResult{
			AlertID:       "alert-67890",
			Verdict:       "benign",
			Confidence:    0.88,
			ExecutionTime: 80,
			PlaybookUsed:  "false-positive-check",
			Actions:       []ActionResult{},
			Reasoning:     "No malicious indicators found",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Triage(&TriageRequest{
		AlertID:  "alert-67890",
		Playbook: "false-positive-check",
	})

	require.NoError(t, err)
	assert.Equal(t, "benign", result.Verdict)
	assert.Empty(t, result.Actions, "Benign verdict should have no actions")
}

// TestTriage_ServerError verifies error handling
func TestTriage_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Triage(&TriageRequest{AlertID: "test"})

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "triage failed")
}

// TestCorrelate_Success verifies event correlation
func TestCorrelate_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/fusion/correlate", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req FusionRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "event-abc123", req.EventID)

		response := FusionResult{
			EventID: "event-abc123",
			CorrelatedSources: []CorrelatedSource{
				{Name: "firewall", EventCount: 15, Relevance: 0.92},
				{Name: "ids", EventCount: 8, Relevance: 0.85},
				{Name: "endpoint", EventCount: 5, Relevance: 0.78},
			},
			CorrelationScore: 0.88,
			Insights: []string{
				"Multiple sources detected similar patterns",
				"Coordinated attack across network segments",
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Correlate(&FusionRequest{EventID: "event-abc123"})

	require.NoError(t, err)
	assert.Equal(t, "event-abc123", result.EventID)
	assert.Equal(t, 0.88, result.CorrelationScore)
	assert.Len(t, result.CorrelatedSources, 3)
	assert.Equal(t, "firewall", result.CorrelatedSources[0].Name)
	assert.Equal(t, 15, result.CorrelatedSources[0].EventCount)
	assert.Len(t, result.Insights, 2)
}

// TestCorrelate_NoCorrelation verifies no correlation found
func TestCorrelate_NoCorrelation(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := FusionResult{
			EventID:           "event-xyz789",
			CorrelatedSources: []CorrelatedSource{},
			CorrelationScore:  0.0,
			Insights:          []string{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Correlate(&FusionRequest{EventID: "event-xyz789"})

	require.NoError(t, err)
	assert.Empty(t, result.CorrelatedSources)
	assert.Equal(t, 0.0, result.CorrelationScore)
}

// TestPredict_Success verifies ML prediction
func TestPredict_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/predict", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req PredictRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.NotEmpty(t, req.Data)

		response := PredictResult{
			Prediction:    "malware",
			Confidence:    0.94,
			InferenceTime: 25,
			Features: []FeatureImportance{
				{Name: "entropy", Importance: 0.85},
				{Name: "api_calls", Importance: 0.72},
				{Name: "network_behavior", Importance: 0.68},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Predict(&PredictRequest{Data: "base64_encoded_sample"})

	require.NoError(t, err)
	assert.Equal(t, "malware", result.Prediction)
	assert.Equal(t, 0.94, result.Confidence)
	assert.Equal(t, 25, result.InferenceTime)
	assert.Len(t, result.Features, 3)
	assert.Equal(t, "entropy", result.Features[0].Name)
	assert.Equal(t, 0.85, result.Features[0].Importance)
}

// TestPredict_BenignPrediction verifies benign prediction
func TestPredict_BenignPrediction(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := PredictResult{
			Prediction:    "benign",
			Confidence:    0.91,
			InferenceTime: 20,
			Features: []FeatureImportance{
				{Name: "signature_match", Importance: 0.95},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Predict(&PredictRequest{Data: "clean_file"})

	require.NoError(t, err)
	assert.Equal(t, "benign", result.Prediction)
	assert.Greater(t, result.Confidence, 0.9)
}

// TestMatch_Success verifies pattern matching with hyperscan
func TestMatch_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/match", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req MatchRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "malicious_pattern", req.Pattern)

		response := MatchResult{
			Pattern:  "malicious_pattern",
			ScanTime: 5,
			Matches: []PatternMatch{
				{Position: 100, Context: "...malicious code..."},
				{Position: 500, Context: "...malicious call..."},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Match(&MatchRequest{Pattern: "malicious_pattern"})

	require.NoError(t, err)
	assert.Equal(t, "malicious_pattern", result.Pattern)
	assert.Equal(t, 5, result.ScanTime)
	assert.Len(t, result.Matches, 2)
	assert.Equal(t, 100, result.Matches[0].Position)
	assert.Contains(t, result.Matches[0].Context, "malicious code")
}

// TestMatch_NoMatches verifies no pattern matches found
func TestMatch_NoMatches(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MatchResult{
			Pattern:  "unknown_pattern",
			ScanTime: 3,
			Matches:  []PatternMatch{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.Match(&MatchRequest{Pattern: "unknown_pattern"})

	require.NoError(t, err)
	assert.Empty(t, result.Matches)
	assert.Greater(t, result.ScanTime, 0, "Should have scan time even with no matches")
}

// TestListPlaybooks_Success verifies playbook listing
func TestListPlaybooks_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/playbooks", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := PlaybooksResult{
			Playbooks: []Playbook{
				{
					Name:        "malware-triage",
					Description: "Automated malware analysis and containment",
					AvgExecTime: 150,
					UsageCount:  250,
				},
				{
					Name:        "phishing-response",
					Description: "Phishing email investigation and remediation",
					AvgExecTime: 120,
					UsageCount:  180,
				},
				{
					Name:        "ransomware-mitigation",
					Description: "Ransomware detection and response",
					AvgExecTime: 200,
					UsageCount:  45,
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.ListPlaybooks()

	require.NoError(t, err)
	assert.Len(t, result.Playbooks, 3)
	assert.Equal(t, "malware-triage", result.Playbooks[0].Name)
	assert.Equal(t, 150, result.Playbooks[0].AvgExecTime)
	assert.Equal(t, 250, result.Playbooks[0].UsageCount)
}

// TestListPlaybooks_Empty verifies empty playbook list
func TestListPlaybooks_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := PlaybooksResult{
			Playbooks: []Playbook{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.ListPlaybooks()

	require.NoError(t, err)
	assert.Empty(t, result.Playbooks)
}

// TestGetStatus_Success verifies status retrieval
func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:          "healthy",
			AvgResponseTime: 45.5,
			TriagesExecuted: 1250,
			ActivePlaybooks: 8,
			ComponentHealth: []ComponentHealth{
				{Name: "triage-engine", Status: "healthy"},
				{Name: "fusion-engine", Status: "healthy"},
				{Name: "ml-predictor", Status: "healthy"},
				{Name: "hyperscan", Status: "healthy"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "healthy", result.Status)
	assert.Equal(t, 45.5, result.AvgResponseTime)
	assert.Equal(t, 1250, result.TriagesExecuted)
	assert.Equal(t, 8, result.ActivePlaybooks)
	assert.Len(t, result.ComponentHealth, 4)
	assert.Equal(t, "triage-engine", result.ComponentHealth[0].Name)
	assert.Equal(t, "healthy", result.ComponentHealth[0].Status)
}

// TestGetStatus_Degraded verifies degraded status
func TestGetStatus_Degraded(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:          "degraded",
			AvgResponseTime: 150.0,
			TriagesExecuted: 850,
			ActivePlaybooks: 3,
			ComponentHealth: []ComponentHealth{
				{Name: "triage-engine", Status: "healthy"},
				{Name: "fusion-engine", Status: "degraded"},
				{Name: "ml-predictor", Status: "healthy"},
				{Name: "hyperscan", Status: "degraded"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result.Status)
	assert.Greater(t, result.AvgResponseTime, 100.0, "Degraded should have higher response time")

	// Count degraded components
	degradedCount := 0
	for _, comp := range result.ComponentHealth {
		if comp.Status == "degraded" {
			degradedCount++
		}
	}
	assert.Greater(t, degradedCount, 0, "Should have at least one degraded component")
}

// TestGetStatus_ServerError verifies error handling
func TestGetStatus_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	result, err := client.GetStatus()

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "get status failed")
}

// BenchmarkTriage measures triage performance
func BenchmarkTriage(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TriageResult{
			AlertID:    "test",
			Verdict:    "benign",
			Confidence: 0.9,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	req := &TriageRequest{AlertID: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Triage(req)
	}
}

// BenchmarkPredict measures ML prediction performance
func BenchmarkPredict(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := PredictResult{
			Prediction:    "benign",
			Confidence:    0.9,
			InferenceTime: 20,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	req := &PredictRequest{Data: "sample"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Predict(req)
	}
}

// BenchmarkMatch measures pattern matching performance
func BenchmarkMatch(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MatchResult{
			Pattern:  "test",
			ScanTime: 5,
			Matches:  []PatternMatch{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRTEClient(server.URL)
	req := &MatchRequest{Pattern: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Match(req)
	}
}
