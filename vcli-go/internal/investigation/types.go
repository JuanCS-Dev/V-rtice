package investigation

// ============================================================================
// SHARED TYPES FOR INVESTIGATION SERVICES
// Consolidated to avoid duplications across clients
// ============================================================================

// AttributionResponse from attribution endpoint
type AttributionResponse struct {
	Success  bool              `json:"success"`
	Message  string            `json:"message,omitempty"`
	Data     map[string]interface{} `json:"data,omitempty"`
	Error    string            `json:"error,omitempty"`
}

// CampaignResponse from campaign analysis endpoint
type CampaignResponse struct {
	Success  bool              `json:"success"`
	Message  string            `json:"message,omitempty"`
	Data     map[string]interface{} `json:"data,omitempty"`
	Error    string            `json:"error,omitempty"`
}

// InvestigationResponse from investigation endpoint
type InvestigationResponse struct {
	Success  bool              `json:"success"`
	Message  string            `json:"message,omitempty"`
	Data     map[string]interface{} `json:"data,omitempty"`
	Error    string            `json:"error,omitempty"`
}

// StatusResponse from status check endpoint
type StatusResponse struct {
	Success  bool              `json:"success"`
	Status   string            `json:"status"`
	Message  string            `json:"message,omitempty"`
	Data     map[string]interface{} `json:"data,omitempty"`
}

// Helper methods for type-safe access to flexible schema

// GetIncidentID extracts incident ID from attribution response
func (r *AttributionResponse) GetIncidentID() string {
	if r.Data == nil {
		return ""
	}
	if id, ok := r.Data["incident_id"].(string); ok {
		return id
	}
	return ""
}

// GetAttributedActorID extracts actor ID from attribution response
func (r *AttributionResponse) GetAttributedActorID() string {
	if r.Data == nil {
		return ""
	}
	if id, ok := r.Data["attributed_actor_id"].(string); ok {
		return id
	}
	return ""
}

// GetAttributedActorName extracts actor name from attribution response
func (r *AttributionResponse) GetAttributedActorName() string {
	if r.Data == nil {
		return "Unknown"
	}
	if name, ok := r.Data["attributed_actor_name"].(string); ok {
		return name
	}
	return "Unknown"
}

// GetConfidenceScore extracts confidence score from attribution response
func (r *AttributionResponse) GetConfidenceScore() float64 {
	if r.Data == nil {
		return 0.0
	}
	if score, ok := r.Data["confidence_score"].(float64); ok {
		return score
	}
	return 0.0
}
