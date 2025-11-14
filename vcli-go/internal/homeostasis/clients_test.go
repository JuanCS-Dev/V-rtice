package homeostasis

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewHomeostasisClient(t *testing.T) {
	client := NewHomeostasisClient("http://test-homeostasis:5555")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-homeostasis:5555", client.endpoint)
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:  "balanced",
			Balance: 0.95,
			Parameters: []Parameter{
				{Name: "cpu_threshold", Value: 0.75, Status: "optimal"},
				{Name: "memory_threshold", Value: 0.80, Status: "optimal"},
				{Name: "request_rate", Value: 1000.0, Status: "normal"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "balanced", result.Status)
	assert.Greater(t, result.Balance, 0.9)
	assert.Len(t, result.Parameters, 3)
	assert.Equal(t, "cpu_threshold", result.Parameters[0].Name)
	assert.Equal(t, "optimal", result.Parameters[0].Status)
}

func TestGetStatus_Imbalanced(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:  "imbalanced",
			Balance: 0.45,
			Parameters: []Parameter{
				{Name: "cpu_threshold", Value: 0.95, Status: "critical"},
				{Name: "memory_threshold", Value: 0.90, Status: "warning"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "imbalanced", result.Status)
	assert.Less(t, result.Balance, 0.5)
	assert.Equal(t, "critical", result.Parameters[0].Status)
}

func TestAdjust_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/adjust", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := AdjustResult{
			Parameter: "cpu_threshold",
			Value:     "0.85",
			Status:    "adjusted",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)
	result, err := client.Adjust(&AdjustRequest{
		Parameter: "cpu_threshold",
		Value:     "0.85",
	})

	require.NoError(t, err)
	assert.Equal(t, "cpu_threshold", result.Parameter)
	assert.Equal(t, "0.85", result.Value)
	assert.Equal(t, "adjusted", result.Status)
}

func TestAdjust_Pending(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AdjustResult{
			Parameter: "memory_threshold",
			Value:     "0.75",
			Status:    "pending",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)
	result, err := client.Adjust(&AdjustRequest{
		Parameter: "memory_threshold",
		Value:     "0.75",
	})

	require.NoError(t, err)
	assert.Equal(t, "pending", result.Status)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})

	t.Run("Adjust", func(t *testing.T) {
		_, err := client.Adjust(&AdjustRequest{})
		assert.Error(t, err)
	})
}

func BenchmarkGetStatus(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(StatusResult{Status: "balanced", Balance: 0.95})
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetStatus()
	}
}

func BenchmarkAdjust(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(AdjustResult{Parameter: "test", Status: "adjusted"})
	}))
	defer server.Close()

	client := NewHomeostasisClient(server.URL)
	req := &AdjustRequest{Parameter: "test", Value: "1.0"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Adjust(req)
	}
}
