package neuro

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewNeuroClient verifies client creation
func TestNewNeuroClient(t *testing.T) {
	client := NewNeuroClient("http://test-neuro:9600")
	assert.NotNil(t, client)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, "http://test-neuro:9600", client.endpoint)
}

// TestNewNeuroClient_DefaultEndpoint verifies default endpoint from config
func TestNewNeuroClient_DefaultEndpoint(t *testing.T) {
	client := NewNeuroClient("")
	assert.NotNil(t, client)
	assert.NotEmpty(t, client.endpoint, "Should use config default endpoint")
}

// TestListenAuditory_Success verifies auditory cortex listening
func TestListenAuditory_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/auditory/listen", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req AuditoryListenRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "kafka", req.Source)
		assert.Equal(t, "security.alerts", req.Topic)

		response := []AuditoryEvent{
			{
				Timestamp:   time.Now(),
				EventType:   "security.threat",
				Severity:    8,
				Description: "Suspicious network activity detected",
				Source:      "firewall",
				Metadata:    map[string]interface{}{"src_ip": "192.168.1.100"},
			},
			{
				Timestamp:   time.Now(),
				EventType:   "security.anomaly",
				Severity:    6,
				Description: "Unusual login pattern",
				Source:      "auth",
				Metadata:    map[string]interface{}{"user": "admin"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	events, err := client.ListenAuditory(&AuditoryListenRequest{
		Source: "kafka",
		Topic:  "security.alerts",
		Follow: true,
	})

	require.NoError(t, err)
	assert.Len(t, events, 2)
	assert.Equal(t, "security.threat", events[0].EventType)
	assert.Equal(t, 8, events[0].Severity)
	assert.Equal(t, "firewall", events[0].Source)
}

// TestListenAuditory_Empty verifies empty event stream
func TestListenAuditory_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := []AuditoryEvent{}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	events, err := client.ListenAuditory(&AuditoryListenRequest{Source: "test"})

	require.NoError(t, err)
	assert.Empty(t, events)
}

// TestRouteThalamus_Success verifies thalamus routing
func TestRouteThalamus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/thalamus/route", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req ThalamusRouteRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "security_alert", req.InputType)

		response := ThalamusRouteResult{
			Routes: []ThalamusRoute{
				{
					InputType:    "security_alert",
					TargetCortex: "prefrontal",
					Priority:     "high",
					Status:       "active",
				},
				{
					InputType:    "security_alert",
					TargetCortex: "visual",
					Priority:     "medium",
					Status:       "active",
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.RouteThalamus(&ThalamusRouteRequest{
		Input:     "alert_data",
		InputType: "security_alert",
	})

	require.NoError(t, err)
	assert.Len(t, result.Routes, 2)
	assert.Equal(t, "prefrontal", result.Routes[0].TargetCortex)
	assert.Equal(t, "high", result.Routes[0].Priority)
}

// TestRouteThalamus_NoRoutes verifies no routing available
func TestRouteThalamus_NoRoutes(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ThalamusRouteResult{Routes: []ThalamusRoute{}}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.RouteThalamus(&ThalamusRouteRequest{InputType: "unknown"})

	require.NoError(t, err)
	assert.Empty(t, result.Routes)
}

// TestConsolidateMemory_Success verifies memory consolidation
func TestConsolidateMemory_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/memory/consolidate", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req MemoryConsolidateRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "long-term", req.Type)

		response := MemoryConsolidateResult{
			PatternsConsolidated: 1250,
			MemoryUsage:          "85%",
			Duration:             "2.5s",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.ConsolidateMemory(&MemoryConsolidateRequest{Type: "long-term"})

	require.NoError(t, err)
	assert.Equal(t, 1250, result.PatternsConsolidated)
	assert.Equal(t, "85%", result.MemoryUsage)
	assert.Equal(t, "2.5s", result.Duration)
}

// TestConsolidateMemory_Empty verifies empty consolidation
func TestConsolidateMemory_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MemoryConsolidateResult{
			PatternsConsolidated: 0,
			MemoryUsage:          "10%",
			Duration:             "0.1s",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.ConsolidateMemory(&MemoryConsolidateRequest{Type: "short-term"})

	require.NoError(t, err)
	assert.Equal(t, 0, result.PatternsConsolidated)
}

// TestPlanCortex_Success verifies prefrontal cortex planning
func TestPlanCortex_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/cortex/plan", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req CortexPlanRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "mitigate security threat", req.Objective)

		response := CortexPlan{
			Objective:     "mitigate security threat",
			TotalDuration: "5m",
			Steps: []CortexPlanStep{
				{
					Description:       "Isolate affected systems",
					EstimatedDuration: "1m",
					Priority:          "critical",
					Dependencies:      []string{},
				},
				{
					Description:       "Collect forensic data",
					EstimatedDuration: "2m",
					Priority:          "high",
					Dependencies:      []string{"Isolate affected systems"},
				},
				{
					Description:       "Analyze threat patterns",
					EstimatedDuration: "2m",
					Priority:          "medium",
					Dependencies:      []string{"Collect forensic data"},
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.PlanCortex(&CortexPlanRequest{Objective: "mitigate security threat"})

	require.NoError(t, err)
	assert.Equal(t, "mitigate security threat", result.Objective)
	assert.Equal(t, "5m", result.TotalDuration)
	assert.Len(t, result.Steps, 3)
	assert.Equal(t, "Isolate affected systems", result.Steps[0].Description)
	assert.Equal(t, "critical", result.Steps[0].Priority)
}

// TestPlanCortex_SimpleObjective verifies simple plan
func TestPlanCortex_SimpleObjective(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CortexPlan{
			Objective:     "monitor system",
			TotalDuration: "1m",
			Steps: []CortexPlanStep{
				{Description: "Check metrics", EstimatedDuration: "1m", Priority: "low"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.PlanCortex(&CortexPlanRequest{Objective: "monitor system"})

	require.NoError(t, err)
	assert.Len(t, result.Steps, 1)
}

// TestAnalyzeVisual_Success verifies visual cortex analysis
func TestAnalyzeVisual_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/visual/analyze", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req VisualAnalyzeRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "camera-feed-1", req.ImageFeed)

		response := VisualAnalyzeResult{
			FeedID:      "camera-feed-1",
			ThreatLevel: "high",
			Analysis:    "Suspicious activity detected: unauthorized access attempt",
			DetectedObjects: []DetectedObject{
				{
					Label:       "person",
					Confidence:  0.98,
					BoundingBox: map[string]int{"x": 100, "y": 200, "w": 50, "h": 100},
				},
				{
					Label:       "weapon",
					Confidence:  0.85,
					BoundingBox: map[string]int{"x": 120, "y": 250, "w": 20, "h": 30},
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.AnalyzeVisual(&VisualAnalyzeRequest{ImageFeed: "camera-feed-1"})

	require.NoError(t, err)
	assert.Equal(t, "camera-feed-1", result.FeedID)
	assert.Equal(t, "high", result.ThreatLevel)
	assert.Len(t, result.DetectedObjects, 2)
	assert.Equal(t, "person", result.DetectedObjects[0].Label)
	assert.Equal(t, 0.98, result.DetectedObjects[0].Confidence)
}

// TestAnalyzeVisual_NoThreats verifies benign visual analysis
func TestAnalyzeVisual_NoThreats(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := VisualAnalyzeResult{
			FeedID:          "camera-feed-2",
			ThreatLevel:     "none",
			Analysis:        "Normal activity",
			DetectedObjects: []DetectedObject{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.AnalyzeVisual(&VisualAnalyzeRequest{ImageFeed: "camera-feed-2"})

	require.NoError(t, err)
	assert.Equal(t, "none", result.ThreatLevel)
	assert.Empty(t, result.DetectedObjects)
}

// TestGetSomatosensoryStatus_Success verifies somatosensory status
func TestGetSomatosensoryStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/somatosensory/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := SomatosensoryStatus{
			Sensors: []SomatosensorySensor{
				{Name: "cpu_temp", Status: "normal", Value: "65", Threshold: "80", Unit: "celsius"},
				{Name: "memory_usage", Status: "normal", Value: "72", Threshold: "85", Unit: "percent"},
				{Name: "disk_io", Status: "warning", Value: "850", Threshold: "1000", Unit: "ops/s"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.GetSomatosensoryStatus()

	require.NoError(t, err)
	assert.Len(t, result.Sensors, 3)
	assert.Equal(t, "cpu_temp", result.Sensors[0].Name)
	assert.Equal(t, "normal", result.Sensors[0].Status)
	assert.Equal(t, "warning", result.Sensors[2].Status)
}

// TestGetSomatosensoryStatus_AllHealthy verifies all sensors healthy
func TestGetSomatosensoryStatus_AllHealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SomatosensoryStatus{
			Sensors: []SomatosensorySensor{
				{Name: "sensor1", Status: "normal", Value: "50", Threshold: "100"},
				{Name: "sensor2", Status: "normal", Value: "30", Threshold: "100"},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.GetSomatosensoryStatus()

	require.NoError(t, err)
	for _, sensor := range result.Sensors {
		assert.Equal(t, "normal", sensor.Status)
	}
}

// TestActivateTegumentar_Success verifies tegumentar shield activation
func TestActivateTegumentar_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/tegumentar/shield", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req TegumentarShieldRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "perimeter", req.Zone)

		response := TegumentarShieldResult{
			ProtectionLevel: "high",
			ActiveBarriers:  5,
			Zone:            "perimeter",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.ActivateTegumentar(&TegumentarShieldRequest{Zone: "perimeter"})

	require.NoError(t, err)
	assert.Equal(t, "high", result.ProtectionLevel)
	assert.Equal(t, 5, result.ActiveBarriers)
	assert.Equal(t, "perimeter", result.Zone)
}

// TestActivateTegumentar_LowProtection verifies low protection level
func TestActivateTegumentar_LowProtection(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TegumentarShieldResult{
			ProtectionLevel: "low",
			ActiveBarriers:  1,
			Zone:            "internal",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.ActivateTegumentar(&TegumentarShieldRequest{Zone: "internal"})

	require.NoError(t, err)
	assert.Equal(t, "low", result.ProtectionLevel)
	assert.LessOrEqual(t, result.ActiveBarriers, 2)
}

// TestBalanceVestibular_Success verifies vestibular load balancing
func TestBalanceVestibular_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/vestibular/balance", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req VestibularBalanceRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "redistribute", req.Action)

		response := VestibularBalanceResult{
			BalanceScore:       0.92,
			TasksRedistributed: 35,
			Status:             "balanced",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.BalanceVestibular(&VestibularBalanceRequest{Action: "redistribute"})

	require.NoError(t, err)
	assert.Equal(t, 0.92, result.BalanceScore)
	assert.Equal(t, 35, result.TasksRedistributed)
	assert.Equal(t, "balanced", result.Status)
}

// TestBalanceVestibular_Imbalanced verifies imbalanced state
func TestBalanceVestibular_Imbalanced(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := VestibularBalanceResult{
			BalanceScore:       0.45,
			TasksRedistributed: 0,
			Status:             "imbalanced",
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.BalanceVestibular(&VestibularBalanceRequest{Action: "check"})

	require.NoError(t, err)
	assert.Less(t, result.BalanceScore, 0.5)
	assert.Equal(t, "imbalanced", result.Status)
}

// TestSenseChemical_Success verifies chemical sensing
func TestSenseChemical_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/chemical/sense", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req ChemicalSenseRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "network_traffic", req.Indicators)

		response := ChemicalSenseResult{
			Threats: []ChemicalThreat{
				{
					Type:     "malware",
					Severity: 9,
					Location: "192.168.1.100",
					Details:  map[string]interface{}{"variant": "ransomware"},
				},
				{
					Type:     "phishing",
					Severity: 6,
					Location: "email_gateway",
					Details:  map[string]interface{}{"target": "finance_team"},
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.SenseChemical(&ChemicalSenseRequest{Indicators: "network_traffic"})

	require.NoError(t, err)
	assert.Len(t, result.Threats, 2)
	assert.Equal(t, "malware", result.Threats[0].Type)
	assert.Equal(t, 9, result.Threats[0].Severity)
	assert.Equal(t, "192.168.1.100", result.Threats[0].Location)
}

// TestSenseChemical_NoThreats verifies no chemical threats
func TestSenseChemical_NoThreats(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ChemicalSenseResult{
			Threats: []ChemicalThreat{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	result, err := client.SenseChemical(&ChemicalSenseRequest{Indicators: "clean_traffic"})

	require.NoError(t, err)
	assert.Empty(t, result.Threats)
}

// BenchmarkListenAuditory measures auditory listening performance
func BenchmarkListenAuditory(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := []AuditoryEvent{}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	req := &AuditoryListenRequest{Source: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.ListenAuditory(req)
	}
}

// BenchmarkPlanCortex measures planning performance
func BenchmarkPlanCortex(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CortexPlan{Objective: "test", Steps: []CortexPlanStep{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	req := &CortexPlanRequest{Objective: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.PlanCortex(req)
	}
}

// BenchmarkAnalyzeVisual measures visual analysis performance
func BenchmarkAnalyzeVisual(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := VisualAnalyzeResult{
			FeedID:          "test",
			ThreatLevel:     "none",
			DetectedObjects: []DetectedObject{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewNeuroClient(server.URL)
	req := &VisualAnalyzeRequest{ImageFeed: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.AnalyzeVisual(req)
	}
}
