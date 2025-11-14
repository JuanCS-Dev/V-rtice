package investigation

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// INVESTIGATION CLIENT TESTS
// ============================================================================

func TestNewInvestigationClient(t *testing.T) {
	t.Run("creates client with custom endpoint", func(t *testing.T) {
		client := NewInvestigationClient("http://custom:8080")

		require.NotNil(t, client)
		assert.Equal(t, "http://custom:8080", client.baseURL)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("uses default endpoint when empty", func(t *testing.T) {
		client := NewInvestigationClient("")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8042", client.baseURL)
	})
}

// ============================================================================
// REGISTER THREAT ACTOR TESTS
// ============================================================================

func TestRegisterThreatActor(t *testing.T) {
	t.Run("successful actor registration", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor/register", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req ThreatActorRegistrationRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "APT-001", req.ActorID)
			assert.Equal(t, "Advanced Threat", req.ActorName)

			resp := map[string]interface{}{
				"success": true,
				"message": "Actor registered",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)
		req := ThreatActorRegistrationRequest{
			ActorID:             "APT-001",
			ActorName:           "Advanced Threat",
			KnownTTPs:           []string{"T1566", "T1059"},
			SophisticationScore: 0.85,
		}

		result, err := client.RegisterThreatActor(req)

		require.NoError(t, err)
		assert.True(t, result["success"].(bool))
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid actor data"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)
		req := ThreatActorRegistrationRequest{ActorID: "test"}

		result, err := client.RegisterThreatActor(req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})
}

// ============================================================================
// GET ACTOR PROFILE TESTS
// ============================================================================

func TestGetActorProfile(t *testing.T) {
	t.Run("successful profile retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor/APT-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ThreatActorProfileResponse{
				ActorID:              "APT-001",
				ActorName:            "Advanced Threat",
				TTPs:                 []string{"T1566", "T1059"},
				SophisticationScore:  0.85,
				ActivityCount:        42,
				AttributionConfidence: 0.9,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetActorProfile("APT-001")

		require.NoError(t, err)
		assert.Equal(t, "APT-001", result.ActorID)
		assert.Equal(t, "Advanced Threat", result.ActorName)
		assert.Equal(t, 0.85, result.SophisticationScore)
		assert.Equal(t, 42, result.ActivityCount)
	})

	t.Run("error on not found", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("actor not found"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetActorProfile("APT-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "APT-999")
	})
}

// ============================================================================
// LIST THREAT ACTORS TESTS
// ============================================================================

func TestListThreatActors(t *testing.T) {
	t.Run("successful list retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := []ThreatActorProfileResponse{
				{ActorID: "APT-001", ActorName: "Threat 1"},
				{ActorID: "APT-002", ActorName: "Threat 2"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.ListThreatActors()

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.Equal(t, "APT-001", result[0].ActorID)
		assert.Equal(t, "APT-002", result[1].ActorID)
	})

	t.Run("error on server failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("server error"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.ListThreatActors()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})
}

// ============================================================================
// INGEST INCIDENT TESTS
// ============================================================================

func TestIngestIncident(t *testing.T) {
	t.Run("successful incident ingestion", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/incident/ingest", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			var req SecurityIncidentRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "INC-001", req.IncidentID)
			assert.Equal(t, 8.5, req.Severity)

			resp := map[string]interface{}{
				"success": true,
				"incident_id": "INC-001",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)
		req := SecurityIncidentRequest{
			IncidentID:     "INC-001",
			IncidentType:   "malware",
			AffectedAssets: []string{"server-1"},
			IOCs:           []string{"192.168.1.100"},
			TTPsObserved:   []string{"T1566"},
			Severity:       8.5,
		}

		result, err := client.IngestIncident(req)

		require.NoError(t, err)
		assert.True(t, result["success"].(bool))
	})

	t.Run("error on validation failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("missing required fields"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)
		req := SecurityIncidentRequest{IncidentID: "test"}

		result, err := client.IngestIncident(req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})
}

// ============================================================================
// ATTRIBUTE INCIDENT TESTS
// ============================================================================

func TestAttributeIncident(t *testing.T) {
	t.Run("successful attribution", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/incident/attribute", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			resp := AttributionResponse{
				Success: true,
				Message: "Attribution complete",
				Data: map[string]interface{}{
					"attributed_actor_id": "APT-001",
					"confidence_score":    0.85,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.AttributeIncident("INC-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "APT-001", result.GetAttributedActorID())
	})

	t.Run("error on attribution failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("incident not found"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.AttributeIncident("INC-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})
}

// ============================================================================
// CORRELATE CAMPAIGNS TESTS
// ============================================================================

func TestCorrelateCampaigns(t *testing.T) {
	t.Run("successful campaign correlation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign/correlate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			resp := []CampaignResponse{
				{Success: true, Message: "Campaign 1"},
				{Success: true, Message: "Campaign 2"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.CorrelateCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 2)
	})

	t.Run("error on server failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.CorrelateCampaigns()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET CAMPAIGN TESTS
// ============================================================================

func TestGetCampaign(t *testing.T) {
	t.Run("successful campaign retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign/CAMP-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := CampaignResponse{
				Success: true,
				Message: "Campaign details",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetCampaign("CAMP-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on not found", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetCampaign("CAMP-999")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// LIST CAMPAIGNS TESTS
// ============================================================================

func TestListCampaigns(t *testing.T) {
	t.Run("successful list retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := []CampaignResponse{
				{Success: true},
				{Success: true},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.ListCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 2)
	})
}

// ============================================================================
// INITIATE INVESTIGATION TESTS
// ============================================================================

func TestInitiateInvestigation(t *testing.T) {
	t.Run("successful investigation initiation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/initiate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			resp := InvestigationResponse{
				Success: true,
				Message: "Investigation started",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.InitiateInvestigation("INC-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on initiation failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.InitiateInvestigation("INC-001")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET INVESTIGATION TESTS
// ============================================================================

func TestGetInvestigation(t *testing.T) {
	t.Run("successful investigation retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/INV-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := InvestigationResponse{
				Success: true,
				Message: "Investigation details",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetInvestigation("INV-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on not found", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetInvestigation("INV-999")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestInvestigationHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		err := client.Health()

		assert.NoError(t, err)
	})

	t.Run("error on unhealthy service", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		err := client.Health()

		require.Error(t, err)
		assert.Contains(t, err.Error(), "503")
	})
}

// ============================================================================
// GET STATUS TESTS
// ============================================================================

func TestInvestigationGetStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := StatusResponse{
				Success: true,
				Status:  "operational",
				Message: "All systems green",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "operational", result.Status)
	})

	t.Run("error on status failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET STATS TESTS
// ============================================================================

func TestInvestigationGetStats(t *testing.T) {
	t.Run("successful stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := map[string]interface{}{
				"total_incidents":     100,
				"total_actors":        25,
				"active_investigations": 5,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetStats()

		require.NoError(t, err)
		assert.Equal(t, float64(100), result["total_incidents"])
		assert.Equal(t, float64(25), result["total_actors"])
	})

	t.Run("error on stats failure", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
		}))
		defer server.Close()

		client := NewInvestigationClient(server.URL)

		result, err := client.GetStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
