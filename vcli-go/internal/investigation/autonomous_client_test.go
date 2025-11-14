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
// AUTONOMOUS CLIENT TESTS
// ============================================================================

func TestNewAutonomousClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewAutonomousClient("http://localhost:8080", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8080", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without auth token", func(t *testing.T) {
		client := NewAutonomousClient("http://localhost:8080", "")

		require.NotNil(t, client)
		assert.Equal(t, "", client.authToken)
	})
}

// ============================================================================
// REGISTER ACTOR TESTS
// ============================================================================

func TestRegisterActor(t *testing.T) {
	t.Run("successful actor registration", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor/register", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req ThreatActorProfile
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "APT-001", req.ActorID)
			assert.Equal(t, "Test Actor", req.ActorName)

			resp := ThreatActorProfile{
				ActorID:             "APT-001",
				ActorName:           "Test Actor",
				KnownTTPs:           []string{"T1566", "T1027"},
				SophisticationScore: 0.8,
				ObservedIncidents:   10,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")
		profile := ThreatActorProfile{
			ActorID:   "APT-001",
			ActorName: "Test Actor",
		}

		result, err := client.RegisterActor(profile)

		require.NoError(t, err)
		assert.Equal(t, "APT-001", result.ActorID)
		assert.Equal(t, "Test Actor", result.ActorName)
		assert.Len(t, result.KnownTTPs, 2)
		assert.Equal(t, 0.8, result.SophisticationScore)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ThreatActorProfile{
				ActorID:   "APT-002",
				ActorName: "Another Actor",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")
		profile := ThreatActorProfile{
			ActorID:   "APT-002",
			ActorName: "Another Actor",
		}

		result, err := client.RegisterActor(profile)

		require.NoError(t, err)
		assert.Equal(t, "APT-002", result.ActorID)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid actor profile"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")
		profile := ThreatActorProfile{}

		result, err := client.RegisterActor(profile)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
		assert.Contains(t, err.Error(), "invalid actor profile")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")
		profile := ThreatActorProfile{}

		result, err := client.RegisterActor(profile)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")
		profile := ThreatActorProfile{}

		result, err := client.RegisterActor(profile)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET ACTOR TESTS
// ============================================================================

func TestGetActor(t *testing.T) {
	t.Run("successful actor retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor/APT-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ThreatActorProfile{
				ActorID:             "APT-001",
				ActorName:           "Advanced Threat",
				KnownTTPs:           []string{"T1566", "T1027", "T1059"},
				SophisticationScore: 0.85,
				ObservedIncidents:   15,
				FirstSeen:           "2020-01-01",
				LastSeen:            "2024-01-01",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetActor("APT-001")

		require.NoError(t, err)
		assert.Equal(t, "APT-001", result.ActorID)
		assert.Equal(t, "Advanced Threat", result.ActorName)
		assert.Len(t, result.KnownTTPs, 3)
		assert.Equal(t, 0.85, result.SophisticationScore)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ThreatActorProfile{
				ActorID: "APT-002",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.GetActor("APT-002")

		require.NoError(t, err)
		assert.Equal(t, "APT-002", result.ActorID)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("actor not found"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetActor("APT-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
		assert.Contains(t, err.Error(), "actor not found")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.GetActor("APT-001")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// LIST ACTORS TESTS
// ============================================================================

func TestListActors(t *testing.T) {
	t.Run("successful actors listing", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/actor", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := []ThreatActorProfile{
				{
					ActorID:             "APT-001",
					ActorName:           "Actor One",
					SophisticationScore: 0.8,
				},
				{
					ActorID:             "APT-002",
					ActorName:           "Actor Two",
					SophisticationScore: 0.7,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.ListActors()

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.Equal(t, "APT-001", result[0].ActorID)
		assert.Equal(t, "APT-002", result[1].ActorID)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := []ThreatActorProfile{}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.ListActors()

		require.NoError(t, err)
		assert.Len(t, result, 0)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.ListActors()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.ListActors()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// INGEST INCIDENT TESTS
// ============================================================================

func TestAutonomousIngestIncident(t *testing.T) {
	t.Run("successful incident ingestion", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/incident/ingest", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req map[string]interface{}
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "INC-001", req["incident_id"])

			resp := map[string]interface{}{
				"incident_id": "INC-001",
				"status":      "ingested",
				"timestamp":   "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")
		incident := map[string]interface{}{
			"incident_id": "INC-001",
			"severity":    "high",
		}

		result, err := client.IngestIncident(incident)

		require.NoError(t, err)
		assert.Equal(t, "INC-001", result["incident_id"])
		assert.Equal(t, "ingested", result["status"])
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := map[string]interface{}{
				"incident_id": "INC-002",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")
		incident := map[string]interface{}{"incident_id": "INC-002"}

		result, err := client.IngestIncident(incident)

		require.NoError(t, err)
		assert.Equal(t, "INC-002", result["incident_id"])
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid incident"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")
		incident := map[string]interface{}{}

		result, err := client.IngestIncident(incident)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")
		incident := map[string]interface{}{}

		result, err := client.IngestIncident(incident)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// ATTRIBUTE INCIDENT TESTS
// ============================================================================

func TestAutonomousAttributeIncident(t *testing.T) {
	t.Run("successful attribution", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/incident/attribute", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req map[string]string
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "INC-001", req["incident_id"])

			resp := AttributionResponse{
				Success: true,
				Data: map[string]interface{}{
					"attributed_actor_id": "APT-001",
					"confidence_score":    0.9,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.AttributeIncident("INC-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "APT-001", result.GetAttributedActorID())
		assert.Equal(t, 0.9, result.GetConfidenceScore())
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := AttributionResponse{
				Success: true,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.AttributeIncident("INC-002")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("incident not found"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.AttributeIncident("INC-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.AttributeIncident("INC-001")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// CORRELATE CAMPAIGNS TESTS
// ============================================================================

func TestAutonomousCorrelateCampaigns(t *testing.T) {
	t.Run("successful campaign correlation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign/correlate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := []CampaignResponse{
				{
					Success: true,
					Data: map[string]interface{}{
						"campaign_id": "CAMP-001",
						"incidents":   []interface{}{"INC-001", "INC-002"},
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.CorrelateCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 1)
		assert.True(t, result[0].Success)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := []CampaignResponse{}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.CorrelateCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 0)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("correlation failed"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.CorrelateCampaigns()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.CorrelateCampaigns()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET CAMPAIGN TESTS
// ============================================================================

func TestAutonomousGetCampaign(t *testing.T) {
	t.Run("successful campaign retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign/CAMP-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := CampaignResponse{
				Success: true,
				Data: map[string]interface{}{
					"campaign_id": "CAMP-001",
					"actor_id":    "APT-001",
					"incidents":   []interface{}{"INC-001", "INC-002", "INC-003"},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetCampaign("CAMP-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.Data)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := CampaignResponse{
				Success: true,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.GetCampaign("CAMP-002")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("campaign not found"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetCampaign("CAMP-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.GetCampaign("CAMP-001")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// LIST CAMPAIGNS TESTS
// ============================================================================

func TestAutonomousListCampaigns(t *testing.T) {
	t.Run("successful campaigns listing", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/campaign", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := []CampaignResponse{
				{
					Success: true,
					Data: map[string]interface{}{
						"campaign_id": "CAMP-001",
					},
				},
				{
					Success: true,
					Data: map[string]interface{}{
						"campaign_id": "CAMP-002",
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.ListCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.True(t, result[0].Success)
		assert.True(t, result[1].Success)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := []CampaignResponse{}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.ListCampaigns()

		require.NoError(t, err)
		assert.Len(t, result, 0)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("access denied"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.ListCampaigns()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.ListCampaigns()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// INITIATE INVESTIGATION TESTS
// ============================================================================

func TestAutonomousInitiateInvestigation(t *testing.T) {
	t.Run("successful investigation initiation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/initiate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req map[string]string
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "example.com", req["target"])
			assert.Equal(t, "full", req["scope"])

			resp := InvestigationResponse{
				Success: true,
				Data: map[string]interface{}{
					"investigation_id": "INV-001",
					"status":           "initiated",
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.InitiateInvestigation("example.com", "full")

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.Data)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := InvestigationResponse{
				Success: true,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.InitiateInvestigation("target", "scope")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid parameters"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.InitiateInvestigation("", "")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.InitiateInvestigation("target", "scope")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET INVESTIGATION TESTS
// ============================================================================

func TestAutonomousGetInvestigation(t *testing.T) {
	t.Run("successful investigation retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/INV-001", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := InvestigationResponse{
				Success: true,
				Data: map[string]interface{}{
					"investigation_id": "INV-001",
					"status":           "in_progress",
					"progress":         0.6,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetInvestigation("INV-001")

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.NotNil(t, result.Data)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := InvestigationResponse{
				Success: true,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.GetInvestigation("INV-002")

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("investigation not found"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetInvestigation("INV-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.GetInvestigation("INV-001")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET STATUS TESTS
// ============================================================================

func TestAutonomousGetStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := StatusResponse{
				Success: true,
				Status:  "operational",
				Message: "All systems running",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "operational", result.Status)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := StatusResponse{
				Success: true,
				Status:  "operational",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.True(t, result.Success)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestAutonomousHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := HealthResponse{
				Status:    "healthy",
				Timestamp: "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.NotEmpty(t, result.Timestamp)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := HealthResponse{
				Status: "healthy",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
	})

	t.Run("error on unhealthy service", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewAutonomousClient(server.URL, "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewAutonomousClient("://invalid-url", "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
