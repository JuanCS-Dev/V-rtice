package specialized

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewSpecializedClient(t *testing.T) {
	client := NewSpecializedClient("http://test-specialized:9800")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-specialized:9800", client.endpoint)
}

// ============================================================================
// AETHER - Distributed Consciousness Tests
// ============================================================================

func TestQueryAether_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/aether/query", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := AetherQueryResult{
			Query:     "security consensus",
			Consensus: 0.95,
			Nodes:     50,
			Insights: []AetherInsight{
				{Content: "High security posture", Confidence: 0.92},
				{Content: "No critical threats", Confidence: 0.88},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.QueryAether(&AetherQueryRequest{Query: "security consensus"})

	require.NoError(t, err)
	assert.Equal(t, 0.95, result.Consensus)
	assert.Equal(t, 50, result.Nodes)
	assert.Len(t, result.Insights, 2)
	assert.Greater(t, result.Insights[0].Confidence, 0.9)
}

// ============================================================================
// BABEL - Multi-language NLP Tests
// ============================================================================

func TestTranslateBabel_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/babel/translate", r.URL.Path)

		response := BabelTranslateResult{
			SourceText:     "security alert",
			SourceLang:     "en",
			TranslatedText: "alerta de segurança",
			TargetLang:     "pt",
			Confidence:     0.98,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.TranslateBabel(&BabelTranslateRequest{
		Text:       "security alert",
		TargetLang: "pt",
	})

	require.NoError(t, err)
	assert.Equal(t, "alerta de segurança", result.TranslatedText)
	assert.Equal(t, "pt", result.TargetLang)
	assert.Greater(t, result.Confidence, 0.95)
}

// ============================================================================
// CERBERUS - Multi-head Authentication Tests
// ============================================================================

func TestAuthenticateCerberus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CerberusAuthResult{
			Tenant:        "acme-corp",
			Status:        "authenticated",
			HeadsVerified: 3,
			VerificationMethods: []VerificationMethod{
				{Method: "password", Status: "verified"},
				{Method: "mfa", Status: "verified"},
				{Method: "biometric", Status: "verified"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AuthenticateCerberus(&CerberusAuthRequest{Tenant: "acme-corp"})

	require.NoError(t, err)
	assert.Equal(t, "authenticated", result.Status)
	assert.Equal(t, 3, result.HeadsVerified)
	assert.Len(t, result.VerificationMethods, 3)
}

func TestAuthenticateCerberus_PartialAuth(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CerberusAuthResult{
			Tenant:        "test-corp",
			Status:        "partial",
			HeadsVerified: 1,
			VerificationMethods: []VerificationMethod{
				{Method: "password", Status: "verified"},
				{Method: "mfa", Status: "pending"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AuthenticateCerberus(&CerberusAuthRequest{Tenant: "test-corp"})

	require.NoError(t, err)
	assert.Equal(t, "partial", result.Status)
	assert.Less(t, result.HeadsVerified, 3)
}

// ============================================================================
// CHIMERA - Hybrid Threat Detection Tests
// ============================================================================

func TestDetectChimera_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ChimeraDetectResult{
			HybridScore: 0.87,
			Threats: []ChimeraThreat{
				{Type: "malware", Model: "ml-based", Score: 0.9, Confidence: 0.95},
				{Type: "phishing", Model: "rule-based", Score: 0.85, Confidence: 0.88},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.DetectChimera(&ChimeraDetectRequest{Query: "suspicious activity"})

	require.NoError(t, err)
	assert.Greater(t, result.HybridScore, 0.8)
	assert.Len(t, result.Threats, 2)
	assert.Equal(t, "malware", result.Threats[0].Type)
}

// ============================================================================
// CHRONOS - Time-series Analysis Tests
// ============================================================================

func TestAnalyzeChronos_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ChronosAnalyzeResult{
			Metric:       "cpu_usage",
			Start:        "2025-01-01T00:00:00Z",
			End:          "2025-01-07T23:59:59Z",
			DataPoints:   672,
			Trend:        "increasing",
			ForecastNext: 78.5,
			Anomalies: []ChronosAnomaly{
				{Timestamp: "2025-01-05T14:30:00Z", Value: 95.2, Deviation: 2.5},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AnalyzeChronos(&ChronosAnalyzeRequest{
		Metric: "cpu_usage",
		Start:  "2025-01-01T00:00:00Z",
		End:    "2025-01-07T23:59:59Z",
	})

	require.NoError(t, err)
	assert.Equal(t, "cpu_usage", result.Metric)
	assert.Equal(t, "increasing", result.Trend)
	assert.Greater(t, result.DataPoints, 600)
	assert.Len(t, result.Anomalies, 1)
}

func TestAnalyzeChronos_NoAnomalies(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ChronosAnalyzeResult{
			Metric:       "memory_usage",
			Trend:        "stable",
			DataPoints:   100,
			ForecastNext: 45.0,
			Anomalies:    []ChronosAnomaly{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AnalyzeChronos(&ChronosAnalyzeRequest{Metric: "memory_usage"})

	require.NoError(t, err)
	assert.Equal(t, "stable", result.Trend)
	assert.Empty(t, result.Anomalies)
}

// ============================================================================
// ECHO - Event Replay Tests
// ============================================================================

func TestReplayEcho_Success(t *testing.T) {
	now := time.Now()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := EchoReplayResult{
			Event:          "security-incident-123",
			OriginalTime:   now.Add(-24 * time.Hour),
			ReplayTime:     now,
			EventsReplayed: 157,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.ReplayEcho(&EchoReplayRequest{Event: "security-incident-123"})

	require.NoError(t, err)
	assert.Equal(t, "security-incident-123", result.Event)
	assert.Equal(t, 157, result.EventsReplayed)
	assert.True(t, result.ReplayTime.After(result.OriginalTime))
}

// ============================================================================
// HYDRA - Multi-tenancy Tests
// ============================================================================

func TestGetHydraStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := HydraStatusResult{
			Tenant:         "tenant-alpha",
			IsolationLevel: "strict",
			ActiveHeads:    5,
			ResourceUsage:  67.3,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.GetHydraStatus(&HydraStatusRequest{Tenant: "tenant-alpha"})

	require.NoError(t, err)
	assert.Equal(t, "tenant-alpha", result.Tenant)
	assert.Equal(t, "strict", result.IsolationLevel)
	assert.Equal(t, 5, result.ActiveHeads)
	assert.Greater(t, result.ResourceUsage, 60.0)
}

// ============================================================================
// IRIS - Visual Recognition Tests
// ============================================================================

func TestAnalyzeIris_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IrisAnalyzeResult{
			Image:       "network-diagram.png",
			ThreatLevel: "low",
			Objects: []IrisObject{
				{Label: "firewall", Confidence: 0.95, IsThreat: "false"},
				{Label: "server", Confidence: 0.92, IsThreat: "false"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AnalyzeIris(&IrisAnalyzeRequest{Image: "network-diagram.png"})

	require.NoError(t, err)
	assert.Equal(t, "low", result.ThreatLevel)
	assert.Len(t, result.Objects, 2)
	assert.Equal(t, "firewall", result.Objects[0].Label)
}

func TestAnalyzeIris_ThreatDetected(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IrisAnalyzeResult{
			Image:       "suspicious-screenshot.png",
			ThreatLevel: "high",
			Objects: []IrisObject{
				{Label: "phishing-page", Confidence: 0.88, IsThreat: "true"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.AnalyzeIris(&IrisAnalyzeRequest{Image: "suspicious-screenshot.png"})

	require.NoError(t, err)
	assert.Equal(t, "high", result.ThreatLevel)
	assert.Equal(t, "true", result.Objects[0].IsThreat)
}

// ============================================================================
// JANUS - Bidirectional Sync Tests
// ============================================================================

func TestSyncJanus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := JanusSyncResult{
			SyncID:        "sync-789",
			Direction:     "bidirectional",
			RecordsSynced: 2450,
			Status:        "completed",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.SyncJanus(&JanusSyncRequest{Query: "sync all"})

	require.NoError(t, err)
	assert.Equal(t, "sync-789", result.SyncID)
	assert.Equal(t, "bidirectional", result.Direction)
	assert.Equal(t, "completed", result.Status)
	assert.Greater(t, result.RecordsSynced, 2000)
}

func TestSyncJanus_InProgress(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := JanusSyncResult{
			SyncID:        "sync-790",
			Direction:     "inbound",
			RecordsSynced: 150,
			Status:        "in_progress",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.SyncJanus(&JanusSyncRequest{Query: "sync partial"})

	require.NoError(t, err)
	assert.Equal(t, "in_progress", result.Status)
}

// ============================================================================
// PHOENIX - Self-healing Tests
// ============================================================================

func TestGetPhoenixStatus_Success(t *testing.T) {
	now := time.Now()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/phoenix/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := PhoenixStatusResult{
			Status:          "healing",
			Health:          0.92,
			RecoveriesCount: 15,
			LastRecovery:    now.Add(-10 * time.Minute),
			ActiveHealing: []PhoenixHealing{
				{Component: "database", Action: "reconnecting"},
				{Component: "cache", Action: "clearing"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.GetPhoenixStatus()

	require.NoError(t, err)
	assert.Equal(t, "healing", result.Status)
	assert.Greater(t, result.Health, 0.9)
	assert.Equal(t, 15, result.RecoveriesCount)
	assert.Len(t, result.ActiveHealing, 2)
}

func TestGetPhoenixStatus_Healthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := PhoenixStatusResult{
			Status:          "healthy",
			Health:          1.0,
			RecoveriesCount: 0,
			ActiveHealing:   []PhoenixHealing{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	result, err := client.GetPhoenixStatus()

	require.NoError(t, err)
	assert.Equal(t, "healthy", result.Status)
	assert.Equal(t, 1.0, result.Health)
	assert.Empty(t, result.ActiveHealing)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)

	t.Run("QueryAether", func(t *testing.T) {
		_, err := client.QueryAether(&AetherQueryRequest{})
		assert.Error(t, err)
	})

	t.Run("TranslateBabel", func(t *testing.T) {
		_, err := client.TranslateBabel(&BabelTranslateRequest{})
		assert.Error(t, err)
	})

	t.Run("AuthenticateCerberus", func(t *testing.T) {
		_, err := client.AuthenticateCerberus(&CerberusAuthRequest{})
		assert.Error(t, err)
	})

	t.Run("DetectChimera", func(t *testing.T) {
		_, err := client.DetectChimera(&ChimeraDetectRequest{})
		assert.Error(t, err)
	})

	t.Run("AnalyzeChronos", func(t *testing.T) {
		_, err := client.AnalyzeChronos(&ChronosAnalyzeRequest{})
		assert.Error(t, err)
	})

	t.Run("ReplayEcho", func(t *testing.T) {
		_, err := client.ReplayEcho(&EchoReplayRequest{})
		assert.Error(t, err)
	})

	t.Run("GetHydraStatus", func(t *testing.T) {
		_, err := client.GetHydraStatus(&HydraStatusRequest{})
		assert.Error(t, err)
	})

	t.Run("AnalyzeIris", func(t *testing.T) {
		_, err := client.AnalyzeIris(&IrisAnalyzeRequest{})
		assert.Error(t, err)
	})

	t.Run("SyncJanus", func(t *testing.T) {
		_, err := client.SyncJanus(&JanusSyncRequest{})
		assert.Error(t, err)
	})

	t.Run("GetPhoenixStatus", func(t *testing.T) {
		_, err := client.GetPhoenixStatus()
		assert.Error(t, err)
	})
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkQueryAether(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(AetherQueryResult{Query: "test", Consensus: 0.9})
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)
	req := &AetherQueryRequest{Query: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.QueryAether(req)
	}
}

func BenchmarkGetPhoenixStatus(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(PhoenixStatusResult{Status: "healthy", Health: 1.0})
	}))
	defer server.Close()

	client := NewSpecializedClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetPhoenixStatus()
	}
}
