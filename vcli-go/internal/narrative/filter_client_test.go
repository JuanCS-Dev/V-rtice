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

func TestNewNarrativeFilterClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:8030", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8030", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:8030", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8030", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// ANALYZE CONTENT TESTS
// ============================================================================

func TestNarrativeFilterClientAnalyzeContent(t *testing.T) {
	t.Run("successful content analysis with auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/analyze", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			var req AnalysisRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "Test content for analysis", req.Text)

			resp := AnalysisResponse{
				Success: true,
				Report: &CognitiveDefenseReport{
					AnalysisID:        "filter-analysis-789",
					Timestamp:         "2024-01-01T12:00:00Z",
					Version:           "2.0.0",
					Text:              "Test content for analysis",
					ThreatScore:       0.65,
					Severity:          "MEDIUM",
					RecommendedAction: "FLAG",
					Confidence:        0.88,
					Reasoning:         "Some manipulation indicators detected",
					Evidence:          []string{"emotional language", "unverified claims"},
					ProcessingTimeMs:  95.3,
					ModelsUsed:        []string{"filter-v2", "credibility-v2"},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.AnalyzeContent(AnalysisRequest{
			Text: "Test content for analysis",
		})

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.Report)
		assert.Equal(t, "filter-analysis-789", result.Report.AnalysisID)
		assert.Equal(t, 0.65, result.Report.ThreatScore)
		assert.Equal(t, "MEDIUM", result.Report.Severity)
		assert.Equal(t, "FLAG", result.Report.RecommendedAction)
		assert.Len(t, result.Report.Evidence, 2)
	})

	t.Run("successful analysis without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := AnalysisResponse{
				Success: true,
				Report: &CognitiveDefenseReport{
					AnalysisID:        "public-123",
					ThreatScore:       0.1,
					Severity:          "LOW",
					RecommendedAction: "ALLOW",
					Confidence:        0.95,
					Reasoning:         "Content appears benign",
					Evidence:          []string{},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "")
		result, err := client.AnalyzeContent(AnalysisRequest{
			Text: "Normal content",
		})

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "public-123", result.Report.AnalysisID)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid content format"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.AnalyzeContent(AnalysisRequest{
			Text: "",
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
		assert.Contains(t, err.Error(), "invalid content format")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not valid json"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.AnalyzeContent(AnalysisRequest{
			Text: "test",
		})

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.AnalyzeContent(AnalysisRequest{
			Text: "test",
		})

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestNarrativeFilterClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := HealthCheckResponse{
				Status:    "healthy",
				Version:   "2.0.1",
				Timestamp: "2024-01-01T12:00:00Z",
				Services: map[string]bool{
					"filter":   true,
					"database": true,
					"cache":    true,
				},
				ModelsLoaded: []string{"filter-v2", "credibility-v2", "emotional-v1"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "2.0.1", result.Version)
		assert.Len(t, result.Services, 3)
		assert.True(t, result.Services["filter"])
		assert.Len(t, result.ModelsLoaded, 3)
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// SIMPLE HEALTH CHECK TESTS
// ============================================================================

func TestNarrativeFilterClientSimpleHealth(t *testing.T) {
	t.Run("successful simple health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health/simple", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := SimpleHealthResponse{
				Status: "ok",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.SimpleHealth()

		require.NoError(t, err)
		assert.Equal(t, "ok", result.Status)
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("plain text"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.SimpleHealth()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.SimpleHealth()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET CACHE STATS TESTS
// ============================================================================

func TestNarrativeFilterClientGetCacheStats(t *testing.T) {
	t.Run("successful cache stats retrieval with auth", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats/cache", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := CacheStatsResponse{
				Success: true,
				Stats: map[string]interface{}{
					"hit_rate":      0.92,
					"total_entries": 2400.0,
					"memory_mb":     58.7,
					"evictions":     8.0,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetCacheStats()

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, 0.92, result.Stats["hit_rate"])
		assert.Equal(t, 2400.0, result.Stats["total_entries"])
	})

	t.Run("successful retrieval without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := CacheStatsResponse{
				Success: true,
				Stats: map[string]interface{}{
					"hit_rate": 0.5,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "")
		result, err := client.GetCacheStats()

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "bad-token")
		result, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "401")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.GetCacheStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET DATABASE STATS TESTS
// ============================================================================

func TestNarrativeFilterClientGetDatabaseStats(t *testing.T) {
	t.Run("successful database stats retrieval with auth", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats/database", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := DatabaseStatsResponse{
				Success: true,
				TableCounts: map[string]int{
					"analyses":    2100,
					"reports":     2100,
					"filters":     450,
					"flagged":     89,
					"blocked":     12,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetDatabaseStats()

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, 2100, result.TableCounts["analyses"])
		assert.Equal(t, 450, result.TableCounts["filters"])
		assert.Len(t, result.TableCounts, 5)
	})

	t.Run("successful retrieval without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := DatabaseStatsResponse{
				Success: true,
				TableCounts: map[string]int{
					"public": 100,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "")
		result, err := client.GetDatabaseStats()

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, 100, result.TableCounts["public"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("database error"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("bad json"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.GetDatabaseStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET SERVICE INFO TESTS
// ============================================================================

func TestNarrativeFilterClientGetServiceInfo(t *testing.T) {
	t.Run("successful service info retrieval with auth", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/info", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ServiceInfoResponse{
				Service:     "narrative-filter-v2",
				Version:     "2.0.1",
				Environment: "production",
				Config: map[string]interface{}{
					"max_text_length":  15000.0,
					"cache_enabled":    true,
					"filter_threshold": 0.7,
					"models": []interface{}{
						"filter-v2",
						"credibility-v2",
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetServiceInfo()

		require.NoError(t, err)
		assert.Equal(t, "narrative-filter-v2", result.Service)
		assert.Equal(t, "2.0.1", result.Version)
		assert.Equal(t, "production", result.Environment)
		assert.Equal(t, 15000.0, result.Config["max_text_length"])
		assert.Equal(t, true, result.Config["cache_enabled"])
	})

	t.Run("successful retrieval without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ServiceInfoResponse{
				Service: "narrative-filter-public",
				Version: "1.0.0",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "")
		result, err := client.GetServiceInfo()

		require.NoError(t, err)
		assert.Equal(t, "narrative-filter-public", result.Service)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("forbidden"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on invalid JSON", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewNarrativeFilterClient(server.URL, "test-token")
		result, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewNarrativeFilterClient("http://localhost:99999", "test-token")
		result, err := client.GetServiceInfo()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
