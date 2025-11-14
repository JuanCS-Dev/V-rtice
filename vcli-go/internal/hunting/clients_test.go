package hunting

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewHuntingClient(t *testing.T) {
	client := NewHuntingClient("http://test-hunting:9300")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-hunting:9300", client.endpoint)
}

func TestPredictAPT_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := APTPredictResult{Target: "test.com", OverallRisk: "high"}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.PredictAPT(&APTPredictRequest{Target: "test.com"})

	require.NoError(t, err)
	assert.Equal(t, "high", result.OverallRisk)
}

func TestProfileAPT_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := APTProfileResult{Actor: "APT29"}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.ProfileAPT(&APTProfileRequest{Actor: "APT29"})

	require.NoError(t, err)
	assert.Equal(t, "APT29", result.Actor)
}

func TestStartHunt_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := HuntStartResult{HuntID: "hunt-123", Status: "running"}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.StartHunt(&HuntStartRequest{})

	require.NoError(t, err)
	assert.Equal(t, "running", result.Status)
}

func TestGetHuntResults_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := HuntResultsResult{HuntID: "hunt-123", Status: "completed"}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.GetHuntResults("hunt-123")

	require.NoError(t, err)
	assert.Equal(t, "completed", result.Status)
}

func TestPredictAnomaly_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AnomalyPredictResult{
			Target:            "example.com",
			PredictionHorizon: "24h",
			ModelConfidence:   0.92,
			Predictions: []AnomalyPrediction{
				{TimeWindow: "12:00-13:00", Type: "exfiltration", Probability: 0.85},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.PredictAnomaly(&AnomalyPredictRequest{})

	require.NoError(t, err)
	assert.Equal(t, "example.com", result.Target)
	assert.Greater(t, result.ModelConfidence, 0.9)
	assert.Len(t, result.Predictions, 1)
}

func TestAnalyzeSurface_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SurfaceAnalyzeResult{
			Target:          "example.com",
			Scope:           "external",
			TotalAssets:     25,
			ExposedServices: 5,
			RiskScore:       7.5,
			Recommendations: []string{"Close port 23", "Update TLS"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.AnalyzeSurface(&SurfaceAnalyzeRequest{Target: "example.com"})

	require.NoError(t, err)
	assert.Equal(t, "example.com", result.Target)
	assert.Equal(t, 25, result.TotalAssets)
	assert.Greater(t, result.RiskScore, 5.0)
}

func TestMapSurface_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SurfaceMapResult{
			MapID:            "map-456",
			Nodes:            150,
			Edges:            420,
			CriticalPaths:    8,
			VisualizationURL: "https://viz.example.com/map-456",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)
	result, err := client.MapSurface(&SurfaceMapRequest{})

	require.NoError(t, err)
	assert.Equal(t, "map-456", result.MapID)
	assert.Equal(t, 150, result.Nodes)
	assert.Greater(t, result.CriticalPaths, 0)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewHuntingClient(server.URL)

	_, err := client.PredictAPT(&APTPredictRequest{})
	assert.Error(t, err)
}
