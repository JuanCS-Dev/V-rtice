package registry

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewRegistryClient(t *testing.T) {
	client := NewRegistryClient("http://test-registry:8500")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-registry:8500", client.endpoint)
}

func TestList_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/services", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := ListResult{
			Services: []ServiceInfo{
				{Name: "maximus-core", Endpoint: "http://maximus:8080", Status: "healthy", Health: 0.99},
				{Name: "atlas-service", Endpoint: "http://atlas:9000", Status: "healthy", Health: 0.95},
				{Name: "penelope-service", Endpoint: "http://penelope:7000", Status: "degraded", Health: 0.70},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Len(t, result.Services, 3)
	assert.Equal(t, "maximus-core", result.Services[0].Name)
	assert.Equal(t, "healthy", result.Services[0].Status)
	assert.Greater(t, result.Services[0].Health, 0.9)
}

func TestList_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ListResult{Services: []ServiceInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Empty(t, result.Services)
}

func TestHealth_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/services/health", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := HealthResult{
			Service:      "maximus-core",
			Status:       "healthy",
			Health:       0.98,
			ResponseTime: 45,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.Health(&HealthRequest{Service: "maximus-core"})

	require.NoError(t, err)
	assert.Equal(t, "maximus-core", result.Service)
	assert.Equal(t, "healthy", result.Status)
	assert.Greater(t, result.Health, 0.9)
	assert.Less(t, result.ResponseTime, 100)
}

func TestHealth_Unhealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := HealthResult{
			Service:      "failing-service",
			Status:       "unhealthy",
			Health:       0.25,
			ResponseTime: 3000,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.Health(&HealthRequest{Service: "failing-service"})

	require.NoError(t, err)
	assert.Equal(t, "unhealthy", result.Status)
	assert.Less(t, result.Health, 0.5)
	assert.Greater(t, result.ResponseTime, 2000)
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:             "operational",
			RegisteredServices: 15,
			ActiveSidecars:     12,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Greater(t, result.RegisteredServices, 10)
	assert.Greater(t, result.ActiveSidecars, 10)
}

func TestGetStatus_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:             "idle",
			RegisteredServices: 0,
			ActiveSidecars:     0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.RegisteredServices)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)

	t.Run("List", func(t *testing.T) {
		_, err := client.List()
		assert.Error(t, err)
	})

	t.Run("Health", func(t *testing.T) {
		_, err := client.Health(&HealthRequest{})
		assert.Error(t, err)
	})

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})
}

func BenchmarkList(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ListResult{Services: []ServiceInfo{}})
	}))
	defer server.Close()

	client := NewRegistryClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.List()
	}
}
