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

func TestNewVulnClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewVulnClient("http://localhost:8000", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewVulnClient("http://localhost:8000", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// QUERY VULNERABILITY TESTS
// ============================================================================

func TestVulnClientQueryVulnerability(t *testing.T) {
	t.Run("successful vulnerability query by CVE", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/query_vulnerability", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			var req VulnQuery
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "CVE-2024-1234", req.CVE)
			assert.Empty(t, req.Product)
			assert.Empty(t, req.Version)

			resp := VulnResponse{
				CVE:         "CVE-2024-1234",
				Severity:    "CRITICAL",
				Score:       9.8,
				Description: "Remote code execution vulnerability in OpenSSL",
				Affected:    []string{"OpenSSL 1.1.1", "OpenSSL 3.0.0"},
				References: []string{
					"https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
					"https://www.openssl.org/news/secadv/20240101.txt",
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.QueryVulnerability("CVE-2024-1234", "", "", nil)

		require.NoError(t, err)
		assert.Equal(t, "CVE-2024-1234", result.CVE)
		assert.Equal(t, "CRITICAL", result.Severity)
		assert.Equal(t, 9.8, result.Score)
		assert.Contains(t, result.Description, "OpenSSL")
		assert.Len(t, result.Affected, 2)
		assert.Contains(t, result.Affected, "OpenSSL 1.1.1")
		assert.Len(t, result.References, 2)
	})

	t.Run("successful vulnerability query by product and version", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var req VulnQuery
			json.NewDecoder(r.Body).Decode(&req)
			assert.Empty(t, req.CVE)
			assert.Equal(t, "apache", req.Product)
			assert.Equal(t, "2.4.49", req.Version)

			resp := VulnResponse{
				CVE:         "CVE-2021-41773",
				Severity:    "HIGH",
				Score:       7.5,
				Description: "Path traversal vulnerability in Apache HTTP Server",
				Affected:    []string{"Apache 2.4.49", "Apache 2.4.50"},
				References:  []string{"https://httpd.apache.org/security/vulnerabilities_24.html"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.QueryVulnerability("", "apache", "2.4.49", nil)

		require.NoError(t, err)
		assert.Equal(t, "CVE-2021-41773", result.CVE)
		assert.Equal(t, "HIGH", result.Severity)
		assert.Equal(t, 7.5, result.Score)
		assert.Contains(t, result.Description, "Apache")
	})

	t.Run("successful query with context", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var req VulnQuery
			json.NewDecoder(r.Body).Decode(&req)
			assert.NotNil(t, req.Context)
			assert.Equal(t, "production", req.Context["environment"])

			resp := VulnResponse{
				CVE:         "CVE-2023-9999",
				Severity:    "MEDIUM",
				Score:       5.5,
				Description: "Information disclosure vulnerability",
				Affected:    []string{"nginx 1.20.0"},
				References:  []string{"https://nginx.org/security_advisories"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		context := map[string]interface{}{
			"environment": "production",
			"priority":    "high",
		}
		result, err := client.QueryVulnerability("", "nginx", "1.20.0", context)

		require.NoError(t, err)
		assert.Equal(t, "CVE-2023-9999", result.CVE)
		assert.Equal(t, "MEDIUM", result.Severity)
	})

	t.Run("query without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := VulnResponse{
				CVE:         "CVE-2020-1234",
				Severity:    "LOW",
				Score:       3.1,
				Description: "Minor vulnerability",
				Affected:    []string{"test 1.0"},
				References:  []string{"https://example.com"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "")
		result, err := client.QueryVulnerability("CVE-2020-1234", "", "", nil)

		require.NoError(t, err)
		assert.Equal(t, "CVE-2020-1234", result.CVE)
		assert.Equal(t, "LOW", result.Severity)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("CVE not found"))
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.QueryVulnerability("CVE-9999-9999", "", "", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
		assert.Contains(t, err.Error(), "CVE not found")
	})

	t.Run("error on unauthorized", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("invalid token"))
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "bad-token")
		result, err := client.QueryVulnerability("CVE-2024-1234", "", "", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "401")
	})

	t.Run("error on server error", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("database connection failed"))
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.QueryVulnerability("CVE-2024-1234", "", "", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewVulnClient("http://localhost:99999", "test-token")
		result, err := client.QueryVulnerability("CVE-2024-1234", "", "", nil)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestVulnClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := map[string]string{
				"status":        "healthy",
				"service":       "vulnerability-scanner",
				"version":       "2.1.0",
				"database_size": "1.2M CVEs",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result["status"])
		assert.Equal(t, "vulnerability-scanner", result["service"])
		assert.Equal(t, "2.1.0", result["version"])
		assert.Equal(t, "1.2M CVEs", result["database_size"])
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid json"))
		}))
		defer server.Close()

		client := NewVulnClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on network failure", func(t *testing.T) {
		client := NewVulnClient("http://localhost:99999", "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
