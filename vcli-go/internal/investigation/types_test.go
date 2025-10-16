package investigation

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

// ============================================================================
// INVESTIGATION TYPES - 100% COVERAGE
// ============================================================================
// PHASE 3: WEAK TIER → 90%+
// Target: 0% → 100% (types.go)

func TestAttributionResponse_GetIncidentID(t *testing.T) {
	tests := []struct {
		name     string
		response *AttributionResponse
		want     string
	}{
		{
			name: "valid incident ID",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"incident_id": "INC-123456",
				},
			},
			want: "INC-123456",
		},
		{
			name:     "nil data",
			response: &AttributionResponse{Data: nil},
			want:     "",
		},
		{
			name: "missing incident_id key",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"other_key": "value",
				},
			},
			want: "",
		},
		{
			name: "incident_id wrong type",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"incident_id": 12345, // int instead of string
				},
			},
			want: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.response.GetIncidentID()
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestAttributionResponse_GetAttributedActorID(t *testing.T) {
	tests := []struct {
		name     string
		response *AttributionResponse
		want     string
	}{
		{
			name: "valid actor ID",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"attributed_actor_id": "ACTOR-APT29",
				},
			},
			want: "ACTOR-APT29",
		},
		{
			name:     "nil data",
			response: &AttributionResponse{Data: nil},
			want:     "",
		},
		{
			name: "missing attributed_actor_id key",
			response: &AttributionResponse{
				Data: map[string]interface{}{},
			},
			want: "",
		},
		{
			name: "attributed_actor_id wrong type",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"attributed_actor_id": 999,
				},
			},
			want: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.response.GetAttributedActorID()
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestAttributionResponse_GetAttributedActorName(t *testing.T) {
	tests := []struct {
		name     string
		response *AttributionResponse
		want     string
	}{
		{
			name: "valid actor name",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"attributed_actor_name": "Cozy Bear",
				},
			},
			want: "Cozy Bear",
		},
		{
			name:     "nil data returns Unknown",
			response: &AttributionResponse{Data: nil},
			want:     "Unknown",
		},
		{
			name: "missing attributed_actor_name key returns Unknown",
			response: &AttributionResponse{
				Data: map[string]interface{}{},
			},
			want: "Unknown",
		},
		{
			name: "attributed_actor_name wrong type returns Unknown",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"attributed_actor_name": []string{"APT29"},
				},
			},
			want: "Unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.response.GetAttributedActorName()
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestAttributionResponse_GetConfidenceScore(t *testing.T) {
	tests := []struct {
		name     string
		response *AttributionResponse
		want     float64
	}{
		{
			name: "valid confidence score",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"confidence_score": 0.95,
				},
			},
			want: 0.95,
		},
		{
			name:     "nil data returns 0.0",
			response: &AttributionResponse{Data: nil},
			want:     0.0,
		},
		{
			name: "missing confidence_score key returns 0.0",
			response: &AttributionResponse{
				Data: map[string]interface{}{},
			},
			want: 0.0,
		},
		{
			name: "confidence_score wrong type returns 0.0",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"confidence_score": "95%", // string instead of float64
				},
			},
			want: 0.0,
		},
		{
			name: "confidence_score zero",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"confidence_score": 0.0,
				},
			},
			want: 0.0,
		},
		{
			name: "confidence_score high",
			response: &AttributionResponse{
				Data: map[string]interface{}{
					"confidence_score": 0.999,
				},
			},
			want: 0.999,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.response.GetConfidenceScore()
			assert.Equal(t, tt.want, got)
		})
	}
}

// Integration test: full attribution response
func TestAttributionResponse_FullResponse(t *testing.T) {
	response := &AttributionResponse{
		Success: true,
		Message: "Attribution complete",
		Data: map[string]interface{}{
			"incident_id":           "INC-2024-001",
			"attributed_actor_id":   "ACTOR-APT29",
			"attributed_actor_name": "Cozy Bear",
			"confidence_score":      0.87,
		},
	}

	assert.True(t, response.Success)
	assert.Equal(t, "Attribution complete", response.Message)
	assert.Equal(t, "INC-2024-001", response.GetIncidentID())
	assert.Equal(t, "ACTOR-APT29", response.GetAttributedActorID())
	assert.Equal(t, "Cozy Bear", response.GetAttributedActorName())
	assert.Equal(t, 0.87, response.GetConfidenceScore())
}

// Edge case: completely empty response
func TestAttributionResponse_EmptyResponse(t *testing.T) {
	response := &AttributionResponse{}

	assert.False(t, response.Success)
	assert.Empty(t, response.Message)
	assert.Empty(t, response.GetIncidentID())
	assert.Empty(t, response.GetAttributedActorID())
	assert.Equal(t, "Unknown", response.GetAttributedActorName())
	assert.Equal(t, 0.0, response.GetConfidenceScore())
}

// Edge case: error response
func TestAttributionResponse_ErrorResponse(t *testing.T) {
	response := &AttributionResponse{
		Success: false,
		Error:   "Failed to attribute incident",
		Data:    nil,
	}

	assert.False(t, response.Success)
	assert.Equal(t, "Failed to attribute incident", response.Error)
	assert.Empty(t, response.GetIncidentID())
	assert.Equal(t, "Unknown", response.GetAttributedActorName())
}

// Test other response types to ensure they're instantiable
func TestCampaignResponse_Instantiation(t *testing.T) {
	response := &CampaignResponse{
		Success: true,
		Message: "Campaign analyzed",
		Data: map[string]interface{}{
			"campaign_id": "CAMP-123",
		},
	}

	assert.True(t, response.Success)
	assert.Equal(t, "Campaign analyzed", response.Message)
	assert.NotNil(t, response.Data)
}

func TestInvestigationResponse_Instantiation(t *testing.T) {
	response := &InvestigationResponse{
		Success: true,
		Message: "Investigation complete",
		Data: map[string]interface{}{
			"findings": []string{"indicator1", "indicator2"},
		},
	}

	assert.True(t, response.Success)
	assert.Equal(t, "Investigation complete", response.Message)
	assert.NotNil(t, response.Data)
}

func TestStatusResponse_Instantiation(t *testing.T) {
	response := &StatusResponse{
		Success: true,
		Status:  "running",
		Message: "Investigation in progress",
		Data: map[string]interface{}{
			"progress": 45,
		},
	}

	assert.True(t, response.Success)
	assert.Equal(t, "running", response.Status)
	assert.Equal(t, "Investigation in progress", response.Message)
	assert.NotNil(t, response.Data)
}
