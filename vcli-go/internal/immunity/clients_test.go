package immunity

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewImmunityClient(t *testing.T) {
	client := NewImmunityClient("http://test-immunity:9400")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-immunity:9400", client.endpoint)
}

// ============================================================================
// Core Status Tests
// ============================================================================

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/core/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := CoreStatusResult{
			Zone:             "production",
			Status:           "protected",
			Health:           0.95,
			ActiveThreats:    2,
			DeployedVaccines: 15,
			ActiveAntibodies: 8,
			Subsystems: []Subsystem{
				{Name: "scanner", Status: "active", Health: 0.98},
				{Name: "vaccine-manager", Status: "active", Health: 0.92},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "production", result.Zone)
	assert.Equal(t, "protected", result.Status)
	assert.Greater(t, result.Health, 0.9)
	assert.Equal(t, 15, result.DeployedVaccines)
	assert.Len(t, result.Subsystems, 2)
}

func TestGetStatus_Degraded(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CoreStatusResult{
			Zone:             "staging",
			Status:           "degraded",
			Health:           0.65,
			ActiveThreats:    10,
			DeployedVaccines: 5,
			ActiveAntibodies: 3,
			Subsystems: []Subsystem{
				{Name: "scanner", Status: "degraded", Health: 0.60},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result.Status)
	assert.Less(t, result.Health, 0.8)
	assert.Greater(t, result.ActiveThreats, 5)
}

// ============================================================================
// Core Activation Tests
// ============================================================================

func TestActivateResponse_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/core/activate", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := CoreActivateResult{
			ActivationID:        "act-123",
			Zone:                "production",
			Policy:              "aggressive",
			Status:              "activated",
			ActivatedSubsystems: []string{"scanner", "vaccine-manager", "antibody-generator"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ActivateResponse(&CoreActivateRequest{
		Zone:   "production",
		Policy: "aggressive",
	})

	require.NoError(t, err)
	assert.Equal(t, "act-123", result.ActivationID)
	assert.Equal(t, "activated", result.Status)
	assert.Len(t, result.ActivatedSubsystems, 3)
	assert.Contains(t, result.ActivatedSubsystems, "scanner")
}

func TestActivateResponse_Conservative(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CoreActivateResult{
			ActivationID:        "act-124",
			Zone:                "development",
			Policy:              "conservative",
			Status:              "activated",
			ActivatedSubsystems: []string{"scanner"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ActivateResponse(&CoreActivateRequest{
		Zone:   "development",
		Policy: "conservative",
	})

	require.NoError(t, err)
	assert.Equal(t, "conservative", result.Policy)
	assert.Len(t, result.ActivatedSubsystems, 1)
}

// ============================================================================
// Immunis Scanner Tests
// ============================================================================

func TestScan_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/immunis/scan", r.URL.Path)

		response := ImmunisScanResult{
			Target:       "web-app-v2",
			ScanID:       "scan-789",
			Duration:     45.3,
			ItemsScanned: 1250,
			Vulnerabilities: []Vulnerability{
				{CVE: "CVE-2024-1234", SeverityScore: 8, Component: "nginx", Status: "detected", Description: "Remote code execution"},
				{CVE: "CVE-2024-5678", SeverityScore: 6, Component: "nodejs", Status: "detected", Description: "Path traversal"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.Scan(&ImmunisScanRequest{
		Target: "web-app-v2",
		Mode:   "deep",
	})

	require.NoError(t, err)
	assert.Equal(t, "scan-789", result.ScanID)
	assert.Equal(t, 1250, result.ItemsScanned)
	assert.Len(t, result.Vulnerabilities, 2)
	assert.Equal(t, "CVE-2024-1234", result.Vulnerabilities[0].CVE)
	assert.Equal(t, 8, result.Vulnerabilities[0].SeverityScore)
}

func TestScan_Clean(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ImmunisScanResult{
			Target:          "api-service",
			ScanID:          "scan-790",
			Duration:        15.8,
			ItemsScanned:    450,
			Vulnerabilities: []Vulnerability{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.Scan(&ImmunisScanRequest{
		Target: "api-service",
		Mode:   "quick",
	})

	require.NoError(t, err)
	assert.Empty(t, result.Vulnerabilities)
	assert.Less(t, result.Duration, 20.0)
}

// ============================================================================
// Vaccine Management Tests
// ============================================================================

func TestDeployVaccine_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/vaccine/deploy", r.URL.Path)

		response := VaccineDeployResult{
			Vaccine:        "log4shell-patch",
			DeploymentID:   "deploy-456",
			Zone:           "production",
			Status:         "deployed",
			HostsProtected: 127,
			ProtectedComponents: []string{
				"apache-log4j",
				"elasticsearch",
				"kafka",
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.DeployVaccine(&VaccineDeployRequest{
		Vaccine: "log4shell-patch",
		Zone:    "production",
	})

	require.NoError(t, err)
	assert.Equal(t, "deploy-456", result.DeploymentID)
	assert.Equal(t, "deployed", result.Status)
	assert.Equal(t, 127, result.HostsProtected)
	assert.Len(t, result.ProtectedComponents, 3)
}

func TestDeployVaccine_Pending(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := VaccineDeployResult{
			Vaccine:             "heartbleed-fix",
			DeploymentID:        "deploy-457",
			Zone:                "staging",
			Status:              "pending",
			HostsProtected:      0,
			ProtectedComponents: []string{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.DeployVaccine(&VaccineDeployRequest{
		Vaccine: "heartbleed-fix",
		Zone:    "staging",
	})

	require.NoError(t, err)
	assert.Equal(t, "pending", result.Status)
	assert.Equal(t, 0, result.HostsProtected)
}

func TestListVaccines_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/vaccine/list", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := VaccineListResult{
			Vaccines: []VaccineInfo{
				{Name: "log4shell-patch", Type: "critical", Severity: "critical", DeploymentStatus: "deployed"},
				{Name: "xss-filter", Type: "preventive", Severity: "medium", DeploymentStatus: "deployed"},
				{Name: "sql-injection-guard", Type: "preventive", Severity: "high", DeploymentStatus: "pending"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ListVaccines()

	require.NoError(t, err)
	assert.Len(t, result.Vaccines, 3)
	assert.Equal(t, "log4shell-patch", result.Vaccines[0].Name)
	assert.Equal(t, "critical", result.Vaccines[0].Severity)
	assert.Equal(t, "deployed", result.Vaccines[0].DeploymentStatus)
}

func TestListVaccines_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := VaccineListResult{Vaccines: []VaccineInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ListVaccines()

	require.NoError(t, err)
	assert.Empty(t, result.Vaccines)
}

// ============================================================================
// Antibody Generation Tests
// ============================================================================

func TestGenerateAntibody_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/antibody/generate", r.URL.Path)

		response := AntibodyGenerateResult{
			AntibodyID: "ab-999",
			Threat:     "ransomware-attack",
			Type:       "neutralization",
			Efficacy:   0.93,
			Status:     "active",
			Countermeasures: []Countermeasure{
				{Type: "block-execution", Description: "Block ransomware binaries"},
				{Type: "isolate-host", Description: "Quarantine infected systems"},
				{Type: "restore-backup", Description: "Restore from clean backup"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.GenerateAntibody(&AntibodyGenerateRequest{
		Threat:   "ransomware-attack",
		Severity: "critical",
	})

	require.NoError(t, err)
	assert.Equal(t, "ab-999", result.AntibodyID)
	assert.Equal(t, "neutralization", result.Type)
	assert.Greater(t, result.Efficacy, 0.9)
	assert.Len(t, result.Countermeasures, 3)
	assert.Equal(t, "block-execution", result.Countermeasures[0].Type)
}

func TestGenerateAntibody_LowEfficacy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AntibodyGenerateResult{
			AntibodyID: "ab-1000",
			Threat:     "zero-day-exploit",
			Type:       "experimental",
			Efficacy:   0.45,
			Status:     "testing",
			Countermeasures: []Countermeasure{
				{Type: "monitor", Description: "Enhanced monitoring"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.GenerateAntibody(&AntibodyGenerateRequest{
		Threat:   "zero-day-exploit",
		Severity: "high",
	})

	require.NoError(t, err)
	assert.Equal(t, "experimental", result.Type)
	assert.Less(t, result.Efficacy, 0.5)
	assert.Equal(t, "testing", result.Status)
}

func TestListAntibodies_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/antibody/list", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := AntibodyListResult{
			Antibodies: []AntibodyInfo{
				{ID: "ab-101", Threat: "ddos-attack", Type: "mitigation", Efficacy: 0.88, Status: "active"},
				{ID: "ab-102", Threat: "phishing", Type: "detection", Efficacy: 0.95, Status: "active"},
				{ID: "ab-103", Threat: "malware-c2", Type: "blocking", Efficacy: 0.91, Status: "active"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ListAntibodies()

	require.NoError(t, err)
	assert.Len(t, result.Antibodies, 3)
	assert.Equal(t, "ab-101", result.Antibodies[0].ID)
	assert.Equal(t, "active", result.Antibodies[0].Status)
	assert.Greater(t, result.Antibodies[1].Efficacy, 0.9)
}

func TestListAntibodies_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AntibodyListResult{Antibodies: []AntibodyInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	result, err := client.ListAntibodies()

	require.NoError(t, err)
	assert.Empty(t, result.Antibodies)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})

	t.Run("ActivateResponse", func(t *testing.T) {
		_, err := client.ActivateResponse(&CoreActivateRequest{})
		assert.Error(t, err)
	})

	t.Run("Scan", func(t *testing.T) {
		_, err := client.Scan(&ImmunisScanRequest{})
		assert.Error(t, err)
	})

	t.Run("DeployVaccine", func(t *testing.T) {
		_, err := client.DeployVaccine(&VaccineDeployRequest{})
		assert.Error(t, err)
	})

	t.Run("ListVaccines", func(t *testing.T) {
		_, err := client.ListVaccines()
		assert.Error(t, err)
	})

	t.Run("GenerateAntibody", func(t *testing.T) {
		_, err := client.GenerateAntibody(&AntibodyGenerateRequest{})
		assert.Error(t, err)
	})

	t.Run("ListAntibodies", func(t *testing.T) {
		_, err := client.ListAntibodies()
		assert.Error(t, err)
	})
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkGetStatus(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(CoreStatusResult{Status: "protected", Health: 0.95})
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetStatus()
	}
}

func BenchmarkScan(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ImmunisScanResult{ScanID: "test", ItemsScanned: 100})
	}))
	defer server.Close()

	client := NewImmunityClient(server.URL)
	req := &ImmunisScanRequest{Target: "test", Mode: "quick"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Scan(req)
	}
}
