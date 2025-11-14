package maximus

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

func TestNewConsciousnessClient(t *testing.T) {
	t.Run("creates client with provided URL", func(t *testing.T) {
		client := NewConsciousnessClient("http://localhost:8022")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8022", client.baseURL)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("trims trailing slash from URL", func(t *testing.T) {
		client := NewConsciousnessClient("http://localhost:8022/")

		assert.Equal(t, "http://localhost:8022", client.baseURL)
	})

	t.Run("uses default localhost when empty", func(t *testing.T) {
		client := NewConsciousnessClient("")

		require.NotNil(t, client)
		assert.Contains(t, client.baseURL, "localhost")
	})
}

func TestConsciousnessClientWithStreamURL(t *testing.T) {
	t.Run("sets stream URL", func(t *testing.T) {
		client := NewConsciousnessClient("http://localhost:8022")

		client.WithStreamURL("ws://localhost:9000")

		assert.Equal(t, "ws://localhost:9000", client.streamURL)
	})

	t.Run("trims trailing slash from stream URL", func(t *testing.T) {
		client := NewConsciousnessClient("http://localhost:8022")

		client.WithStreamURL("ws://localhost:9000/")

		assert.Equal(t, "ws://localhost:9000", client.streamURL)
	})
}

// ============================================================================
// GET STATE TESTS
// ============================================================================

func TestConsciousnessClientGetState(t *testing.T) {
	t.Run("successful state retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/state", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ConsciousnessState{
				Timestamp:             "2024-01-01T10:00:00Z",
				ESGTActive:            true,
				ArousalLevel:          0.75,
				ArousalClassification: ArousalAlert,
				RecentEventsCount:     5,
				Coherence:             0.85,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetState()

		require.NoError(t, err)
		assert.Equal(t, "2024-01-01T10:00:00Z", result.Timestamp)
		assert.True(t, result.ESGTActive)
		assert.Equal(t, 0.75, result.ArousalLevel)
		assert.Equal(t, 5, result.RecentEventsCount)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetState()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetState()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on connection failure", func(t *testing.T) {
		client := NewConsciousnessClient("http://invalid-host:99999")

		result, err := client.GetState()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET ESGT EVENTS TESTS
// ============================================================================

func TestConsciousnessClientGetESGTEvents(t *testing.T) {
	t.Run("successful events retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/esgt/events", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "10", r.URL.Query().Get("limit"))

			resp := []ESGTEvent{
				{
					EventID:            "event-1",
					Timestamp:          "2024-01-01T10:00:00Z",
					Success:            true,
					NodesParticipating: 50,
					DurationMs:         125.5,
				},
				{
					EventID:            "event-2",
					Timestamp:          "2024-01-01T10:01:00Z",
					Success:            false,
					NodesParticipating: 30,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetESGTEvents(10)

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.Equal(t, "event-1", result[0].EventID)
		assert.True(t, result[0].Success)
		assert.False(t, result[1].Success)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid limit"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetESGTEvents(10)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetESGTEvents(10)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET AROUSAL TESTS
// ============================================================================

func TestConsciousnessClientGetArousal(t *testing.T) {
	t.Run("successful arousal retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/arousal", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ArousalState{
				Arousal:            0.65,
				Level:              ArousalAwake,
				Baseline:           0.50,
				NeedContribution:   0.15,
				StressContribution: 0.10,
				Timestamp:          "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetArousal()

		require.NoError(t, err)
		assert.Equal(t, 0.65, result.Arousal)
		assert.Equal(t, ArousalAwake, result.Level)
		assert.Equal(t, 0.50, result.Baseline)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("internal error"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetArousal()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetArousal()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET METRICS TESTS
// ============================================================================

func TestConsciousnessClientGetMetrics(t *testing.T) {
	t.Run("successful metrics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/metrics", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ConsciousnessMetrics{
				TIGMetrics: TIGMetrics{
					NodesActive:  10,
					Connectivity: 0.85,
					Integration:  0.75,
					PhiProxy:     0.68,
				},
				ESGTStats: ESGTStats{
					TotalIgnitions: 100,
					SuccessRate:    0.85,
					AvgCoherence:   0.80,
					AvgDurationMs:  125.5,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetMetrics()

		require.NoError(t, err)
		assert.Equal(t, 10, result.TIGMetrics.NodesActive)
		assert.Equal(t, 0.85, result.TIGMetrics.Connectivity)
		assert.Equal(t, 100, result.ESGTStats.TotalIgnitions)
		assert.Equal(t, 0.85, result.ESGTStats.SuccessRate)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("forbidden"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		result, err := client.GetMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// TRIGGER ESGT TESTS
// ============================================================================

func TestConsciousnessClientTriggerESGT(t *testing.T) {
	t.Run("successful ESGT trigger", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/esgt/trigger", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req SalienceInput
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, 0.8, req.Novelty)
			assert.Equal(t, 0.9, req.Relevance)
			assert.Equal(t, 0.7, req.Urgency)

			resp := ESGTEvent{
				EventID:            "event-triggered",
				Timestamp:          "2024-01-01T10:00:00Z",
				Success:            true,
				NodesParticipating: 60,
				DurationMs:         150.0,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		salience := SalienceInput{
			Novelty:   0.8,
			Relevance: 0.9,
			Urgency:   0.7,
		}

		result, err := client.TriggerESGT(salience)

		require.NoError(t, err)
		assert.Equal(t, "event-triggered", result.EventID)
		assert.True(t, result.Success)
		assert.Equal(t, 60, result.NodesParticipating)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid salience"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		salience := SalienceInput{Novelty: 0.8, Relevance: 0.9, Urgency: 0.7}

		result, err := client.TriggerESGT(salience)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		salience := SalienceInput{Novelty: 0.8, Relevance: 0.9, Urgency: 0.7}

		result, err := client.TriggerESGT(salience)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// ADJUST AROUSAL TESTS
// ============================================================================

func TestConsciousnessClientAdjustArousal(t *testing.T) {
	t.Run("successful arousal adjustment", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/consciousness/arousal/adjust", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req ArousalAdjustment
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, 0.15, req.Delta)
			assert.Equal(t, 30.0, req.DurationSeconds)
			assert.Equal(t, "manual", req.Source)

			resp := ArousalState{
				Arousal:   0.80,
				Level:     ArousalAlert,
				Baseline:  0.50,
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		adjustment := ArousalAdjustment{
			Delta:           0.15,
			DurationSeconds: 30.0,
			Source:          "manual",
		}

		result, err := client.AdjustArousal(adjustment)

		require.NoError(t, err)
		assert.Equal(t, 0.80, result.Arousal)
		assert.Equal(t, ArousalAlert, result.Level)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid adjustment"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		adjustment := ArousalAdjustment{Delta: 0.15, DurationSeconds: 30.0, Source: "manual"}

		result, err := client.AdjustArousal(adjustment)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		adjustment := ArousalAdjustment{Delta: 0.15, DurationSeconds: 30.0, Source: "manual"}

		result, err := client.AdjustArousal(adjustment)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestConsciousnessClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		err := client.Health()

		require.NoError(t, err)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewConsciousnessClient(server.URL)

		err := client.Health()

		require.Error(t, err)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on connection failure", func(t *testing.T) {
		client := NewConsciousnessClient("http://invalid-host:99999")

		err := client.Health()

		require.Error(t, err)
	})
}
