package integration

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewIntegrationClient(t *testing.T) {
	client := NewIntegrationClient("http://test-integration:6666")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-integration:6666", client.endpoint)
}

func TestList_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/integrations", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := ListResult{
			Integrations: []IntegrationInfo{
				{Name: "slack", Type: "notification", Status: "active", Health: 0.98},
				{Name: "jira", Type: "ticketing", Status: "active", Health: 0.95},
				{Name: "splunk", Type: "siem", Status: "degraded", Health: 0.75},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Len(t, result.Integrations, 3)
	assert.Equal(t, "slack", result.Integrations[0].Name)
	assert.Equal(t, "active", result.Integrations[0].Status)
	assert.Greater(t, result.Integrations[0].Health, 0.9)
}

func TestList_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ListResult{Integrations: []IntegrationInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Empty(t, result.Integrations)
}

func TestTest_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/integrations/test", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := TestResult{
			Integration:  "slack",
			Status:       "success",
			ResponseTime: 145,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.Test(&TestRequest{Integration: "slack"})

	require.NoError(t, err)
	assert.Equal(t, "slack", result.Integration)
	assert.Equal(t, "success", result.Status)
	assert.Less(t, result.ResponseTime, 200)
}

func TestTest_Failed(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TestResult{
			Integration:  "legacy-system",
			Status:       "failed",
			ResponseTime: 5000,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.Test(&TestRequest{Integration: "legacy-system"})

	require.NoError(t, err)
	assert.Equal(t, "failed", result.Status)
	assert.Greater(t, result.ResponseTime, 3000)
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:             "operational",
			ActiveIntegrations: 12,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Greater(t, result.ActiveIntegrations, 10)
}

func TestGetStatus_NoIntegrations(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:             "idle",
			ActiveIntegrations: 0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.ActiveIntegrations)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)

	t.Run("List", func(t *testing.T) {
		_, err := client.List()
		assert.Error(t, err)
	})

	t.Run("Test", func(t *testing.T) {
		_, err := client.Test(&TestRequest{})
		assert.Error(t, err)
	})

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})
}

func BenchmarkList(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ListResult{Integrations: []IntegrationInfo{}})
	}))
	defer server.Close()

	client := NewIntegrationClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.List()
	}
}
