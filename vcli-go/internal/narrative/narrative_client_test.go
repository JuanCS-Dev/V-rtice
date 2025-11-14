package narrative

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

func TestNewNarrativeClient(t *testing.T) {
	t.Run("creates client with custom base URL", func(t *testing.T) {
		client := NewNarrativeClient("http://custom:9000")

		require.NotNil(t, client)
		assert.Equal(t, "http://custom:9000", client.baseURL)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("uses default URL when empty string provided", func(t *testing.T) {
		client := NewNarrativeClient("")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8030", client.baseURL)
	})
}

// ============================================================================
// ANALYZE TESTS
// ============================================================================

func TestNarrativeClientAnalyze(t *testing.T) {
	t.Run("successful narrative analysis without source URL", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/analyze", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req AnalysisRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "This is a test narrative", req.Text)
			assert.Nil(t, req.SourceURL)

			resp := AnalysisResponse{
				Success: true,
				Report: &CognitiveDefenseReport{
					AnalysisID:        "analysis-123",
					Timestamp:         "2024-01-01T10:00:00Z",
					Version:           "1.0.0",
					Text:              "This is a test narrative",
					ThreatScore:       0.75,
					Severity:          "HIGH",
					RecommendedAction: "WARN",
					Confidence:        0.85,
					Reasoning:         "Emotional manipulation detected",
					Evidence:          []string{"loaded language", "fear appeals"},
					ProcessingTimeMs:  125.5,
					ModelsUsed:        []string{"credibility", "emotional", "logical"},
					CredibilityResult: map[string]interface{}{
						"credibility_score": 0.4,
						"rating":            "QUESTIONABLE",
					},
					EmotionalResult: map[string]interface{}{
						"fear_level": 0.8,
						"anger_level": 0.6,
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("This is a test narrative", nil)

		require.NoError(t, err)
		assert.Equal(t, "analysis-123", report.AnalysisID)
		assert.Equal(t, 0.75, report.ThreatScore)
		assert.Equal(t, "HIGH", report.Severity)
		assert.Equal(t, "WARN", report.RecommendedAction)
		assert.Equal(t, 0.85, report.Confidence)
		assert.Contains(t, report.Reasoning, "manipulation")
		assert.Len(t, report.Evidence, 2)
		assert.Contains(t, report.Evidence, "loaded language")
		assert.Len(t, report.ModelsUsed, 3)
	})

	t.Run("successful analysis with source URL", func(t *testing.T) {
		sourceURL := "https://example.com/article"

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var req AnalysisRequest
			json.NewDecoder(r.Body).Decode(&req)
			assert.NotNil(t, req.SourceURL)
			assert.Equal(t, sourceURL, *req.SourceURL)

			resp := AnalysisResponse{
				Success: true,
				Report: &CognitiveDefenseReport{
					AnalysisID:        "analysis-456",
					Text:              "Test",
					SourceURL:         &sourceURL,
					ThreatScore:       0.2,
					Severity:          "LOW",
					RecommendedAction: "ALLOW",
					Confidence:        0.9,
					Reasoning:         "Content appears credible",
					Evidence:          []string{},
					ModelsUsed:        []string{"credibility"},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("Test", &sourceURL)

		require.NoError(t, err)
		assert.Equal(t, "analysis-456", report.AnalysisID)
		assert.NotNil(t, report.SourceURL)
		assert.Equal(t, sourceURL, *report.SourceURL)
		assert.Equal(t, "LOW", report.Severity)
	})

	t.Run("error when API returns non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid request"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("test", nil)

		require.Error(t, err)
		assert.Nil(t, report)
		assert.Contains(t, err.Error(), "400")
		assert.Contains(t, err.Error(), "invalid request")
	})

	t.Run("error when API returns success=false", func(t *testing.T) {
		errorMsg := "analysis model unavailable"
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			resp := AnalysisResponse{
				Success: false,
				Error:   &errorMsg,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("test", nil)

		require.Error(t, err)
		assert.Nil(t, report)
		assert.Contains(t, err.Error(), "analysis model unavailable")
	})

	t.Run("error when response has no report", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			resp := AnalysisResponse{
				Success: true,
				Report:  nil,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("test", nil)

		require.Error(t, err)
		assert.Nil(t, report)
		assert.Contains(t, err.Error(), "no report")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		report, err := client.Analyze("test", nil)

		require.Error(t, err)
		assert.Nil(t, report)
		assert.Contains(t, err.Error(), "failed to decode")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeClient("http://localhost:99999")
		report, err := client.Analyze("test", nil)

		require.Error(t, err)
		assert.Nil(t, report)
		assert.Contains(t, err.Error(), "failed to connect")
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestNarrativeClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := HealthCheckResponse{
				Status:    "healthy",
				Version:   "1.2.3",
				Timestamp: "2024-01-01T10:00:00Z",
				Services: map[string]bool{
					"database": true,
					"redis":    true,
					"llm":      true,
				},
				ModelsLoaded: []string{"credibility-v2", "emotional-v1", "logical-v1"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		health, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", health.Status)
		assert.Equal(t, "1.2.3", health.Version)
		assert.Len(t, health.Services, 3)
		assert.True(t, health.Services["database"])
		assert.Len(t, health.ModelsLoaded, 3)
		assert.Contains(t, health.ModelsLoaded, "credibility-v2")
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		health, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, health)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		health, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, health)
		assert.Contains(t, err.Error(), "failed to decode")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeClient("http://localhost:99999")
		health, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, health)
		assert.Contains(t, err.Error(), "unreachable")
	})
}

// ============================================================================
// GET CACHE STATS TESTS
// ============================================================================

func TestNarrativeClientGetCacheStats(t *testing.T) {
	t.Run("successful cache stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats/cache", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := CacheStats{
				Success: true,
				Stats: map[string]interface{}{
					"hit_rate":      0.85,
					"total_entries": 1250.0,
					"memory_mb":     45.2,
					"evictions":     12.0,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetCacheStats()

		require.NoError(t, err)
		assert.True(t, stats.Success)
		assert.Equal(t, 0.85, stats.Stats["hit_rate"])
		assert.Equal(t, 1250.0, stats.Stats["total_entries"])
		assert.Equal(t, 45.2, stats.Stats["memory_mb"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("stats unavailable"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, stats)
		assert.Contains(t, err.Error(), "404")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("bad json"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, stats)
		assert.Contains(t, err.Error(), "failed to decode")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeClient("http://localhost:99999")
		stats, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, stats)
	})
}

// ============================================================================
// GET DATABASE STATS TESTS
// ============================================================================

func TestNarrativeClientGetDatabaseStats(t *testing.T) {
	t.Run("successful database stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats/database", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := DatabaseStats{
				Success: true,
				TableCounts: map[string]int{
					"analyses":  1500,
					"reports":   1500,
					"artifacts": 3200,
					"cache":     5000,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetDatabaseStats()

		require.NoError(t, err)
		assert.True(t, stats.Success)
		assert.Equal(t, 1500, stats.TableCounts["analyses"])
		assert.Equal(t, 3200, stats.TableCounts["artifacts"])
		assert.Len(t, stats.TableCounts, 4)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("database query failed"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, stats)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("{invalid}"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		stats, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, stats)
		assert.Contains(t, err.Error(), "failed to decode")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeClient("http://localhost:99999")
		stats, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, stats)
	})
}

// ============================================================================
// GET SERVICE INFO TESTS
// ============================================================================

func TestNarrativeClientGetServiceInfo(t *testing.T) {
	t.Run("successful service info retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/info", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ServiceInfo{
				Service:     "narrative-filter",
				Version:     "2.1.0",
				Environment: "production",
				Config: map[string]interface{}{
					"max_text_length": 10000.0,
					"cache_enabled":   true,
					"tier2_enabled":   false,
					"models": []interface{}{
						"credibility-v2",
						"emotional-v1",
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		info, err := client.GetServiceInfo()

		require.NoError(t, err)
		assert.Equal(t, "narrative-filter", info.Service)
		assert.Equal(t, "2.1.0", info.Version)
		assert.Equal(t, "production", info.Environment)
		assert.Equal(t, 10000.0, info.Config["max_text_length"])
		assert.Equal(t, true, info.Config["cache_enabled"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		info, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, info)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not valid json"))
		}))
		defer server.Close()

		client := NewNarrativeClient(server.URL)
		info, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, info)
		assert.Contains(t, err.Error(), "failed to decode")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeClient("http://localhost:99999")
		info, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, info)
	})
}
