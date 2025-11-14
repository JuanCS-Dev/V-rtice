package architect

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewArchitectClient(t *testing.T) {
	client := NewArchitectClient("http://test-architect:7777")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-architect:7777", client.endpoint)
}

func TestAnalyze_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/analyze", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := AnalyzeResult{
			TotalServices: 25,
			GapsFound:     3,
			Redundancies:  2,
			HealthScore:   0.85,
			Recommendations: []string{
				"Add monitoring to service X",
				"Remove redundant service Y",
				"Scale service Z horizontally",
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.Analyze()

	require.NoError(t, err)
	assert.Equal(t, 25, result.TotalServices)
	assert.Equal(t, 3, result.GapsFound)
	assert.Greater(t, result.HealthScore, 0.8)
	assert.Len(t, result.Recommendations, 3)
}

func TestAnalyze_Perfect(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AnalyzeResult{
			TotalServices:   15,
			GapsFound:       0,
			Redundancies:    0,
			HealthScore:     1.0,
			Recommendations: []string{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.Analyze()

	require.NoError(t, err)
	assert.Equal(t, 1.0, result.HealthScore)
	assert.Equal(t, 0, result.GapsFound)
	assert.Empty(t, result.Recommendations)
}

func TestBlueprint_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/blueprint", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := BlueprintResult{
			ServiceName: "maximus-core",
			Blueprint:   "digraph G { maximus -> postgres; maximus -> redis; }",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.Blueprint(&BlueprintRequest{
		ServiceName: "maximus-core",
		Format:      "dot",
	})

	require.NoError(t, err)
	assert.Equal(t, "maximus-core", result.ServiceName)
	assert.Contains(t, result.Blueprint, "digraph")
	assert.Contains(t, result.Blueprint, "postgres")
}

func TestBlueprint_JSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := BlueprintResult{
			ServiceName: "api-gateway",
			Blueprint:   `{"nodes": ["gateway", "auth", "db"], "edges": [["gateway", "auth"], ["auth", "db"]]}`,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.Blueprint(&BlueprintRequest{
		ServiceName: "api-gateway",
		Format:      "json",
	})

	require.NoError(t, err)
	assert.Contains(t, result.Blueprint, "nodes")
	assert.Contains(t, result.Blueprint, "edges")
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:            "operational",
			AnalysesCompleted: 142,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Greater(t, result.AnalysesCompleted, 100)
}

func TestGetStatus_Idle(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:            "idle",
			AnalysesCompleted: 0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.AnalysesCompleted)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)

	t.Run("Analyze", func(t *testing.T) {
		_, err := client.Analyze()
		assert.Error(t, err)
	})

	t.Run("Blueprint", func(t *testing.T) {
		_, err := client.Blueprint(&BlueprintRequest{})
		assert.Error(t, err)
	})

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})
}

func BenchmarkAnalyze(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(AnalyzeResult{TotalServices: 10, HealthScore: 0.9})
	}))
	defer server.Close()

	client := NewArchitectClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Analyze()
	}
}
