package threat

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewIntelClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewIntelClient("http://localhost:8000", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewIntelClient("http://localhost:8000", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// QUERY THREAT INTEL TESTS
// ============================================================================

func TestIntelClientQueryThreatIntel(t *testing.T) {
	t.Run("successful threat intel query with IP indicator", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/query_threat_intel", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			var req ThreatIntelQuery
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "192.168.1.100", req.Indicator)
			assert.Equal(t, "ip", req.IndicatorType)

			resp := ThreatIntelResponse{
				Indicator:      "192.168.1.100",
				ThreatScore:    0.85,
				Classification: "malicious",
				Sources:        []string{"virustotal", "alienvault", "abuse.ch"},
				TTPs:           []string{"T1071", "T1095"},
				AdditionalInfo: map[string]interface{}{
					"first_seen": "2024-01-01",
					"country":    "CN",
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.QueryThreatIntel("192.168.1.100", "ip", nil)

		require.NoError(t, err)
		assert.Equal(t, "192.168.1.100", result.Indicator)
		assert.Equal(t, 0.85, result.ThreatScore)
		assert.Equal(t, "malicious", result.Classification)
		assert.Len(t, result.Sources, 3)
		assert.Contains(t, result.Sources, "virustotal")
		assert.Len(t, result.TTPs, 2)
		assert.Equal(t, "T1071", result.TTPs[0])
		assert.Equal(t, "CN", result.AdditionalInfo["country"])
	})

	t.Run("successful threat intel query with hash indicator", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var req ThreatIntelQuery
			json.NewDecoder(r.Body).Decode(&req)
			assert.Equal(t, "md5", req.IndicatorType)
			assert.Equal(t, "abc123def456", req.Indicator)

			resp := ThreatIntelResponse{
				Indicator:      "abc123def456",
				ThreatScore:    0.95,
				Classification: "ransomware",
				Sources:        []string{"hybrid-analysis"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.QueryThreatIntel("abc123def456", "md5", nil)

		require.NoError(t, err)
		assert.Equal(t, "abc123def456", result.Indicator)
		assert.Equal(t, "ransomware", result.Classification)
	})

	t.Run("successful query with context", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var req ThreatIntelQuery
			json.NewDecoder(r.Body).Decode(&req)
			assert.NotNil(t, req.Context)
			assert.Equal(t, "Brazil", req.Context["country"])

			resp := ThreatIntelResponse{
				Indicator:      "example.com",
				ThreatScore:    0.65,
				Classification: "suspicious",
				Sources:        []string{"urlhaus"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		context := map[string]interface{}{"country": "Brazil", "priority": "high"}
		result, err := client.QueryThreatIntel("example.com", "domain", context)

		require.NoError(t, err)
		assert.Equal(t, "example.com", result.Indicator)
		assert.Equal(t, "suspicious", result.Classification)
	})

	t.Run("query without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ThreatIntelResponse{
				Indicator:      "8.8.8.8",
				ThreatScore:    0.1,
				Classification: "benign",
				Sources:        []string{"public"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "")
		result, err := client.QueryThreatIntel("8.8.8.8", "ip", nil)

		require.NoError(t, err)
		assert.Equal(t, "8.8.8.8", result.Indicator)
		assert.Equal(t, "benign", result.Classification)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("indicator not found"))
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.QueryThreatIntel("unknown", "ip", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
		assert.Contains(t, err.Error(), "indicator not found")
	})

	t.Run("error on server unavailable", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("threat intel service offline"))
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.QueryThreatIntel("192.168.1.1", "ip", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewIntelClient("http://localhost:99999", "test-token")
		result, err := client.QueryThreatIntel("test", "ip", nil)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET STATUS TESTS
// ============================================================================

func TestIntelClientGetStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/threat_intel_status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := map[string]interface{}{
				"status":            "healthy",
				"sources_available": []string{"virustotal", "alienvault", "abuse.ch"},
				"queries_today":     1250,
				"cache_hit_rate":    0.78,
				"avg_latency_ms":    125.5,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result["status"])
		assert.Equal(t, 1250.0, result["queries_today"])
		assert.Equal(t, 0.78, result["cache_hit_rate"])
	})

	t.Run("status without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := map[string]interface{}{
				"status": "limited",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "")
		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.Equal(t, "limited", result["status"])
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewIntelClient("http://localhost:99999", "test-token")
		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestIntelClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := map[string]string{
				"status":  "healthy",
				"service": "threat-intel",
				"version": "1.0.0",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result["status"])
		assert.Equal(t, "threat-intel", result["service"])
		assert.Equal(t, "1.0.0", result["version"])
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewIntelClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewIntelClient("http://localhost:99999", "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
