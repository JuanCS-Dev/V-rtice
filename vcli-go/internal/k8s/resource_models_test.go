package k8s

import (
	"testing"
	"time"
)

// TestNewConfigMapOptions tests the NewConfigMapOptions constructor
func TestNewConfigMapOptions(t *testing.T) {
	opts := NewConfigMapOptions()

	if opts == nil {
		t.Fatal("NewConfigMapOptions() returned nil")
	}

	if opts.Data == nil {
		t.Error("Data map should not be nil")
	}
	if len(opts.Data) != 0 {
		t.Errorf("Data length = %d, want 0", len(opts.Data))
	}

	if opts.BinaryData == nil {
		t.Error("BinaryData map should not be nil")
	}
	if len(opts.BinaryData) != 0 {
		t.Errorf("BinaryData length = %d, want 0", len(opts.BinaryData))
	}

	if opts.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(opts.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(opts.Labels))
	}

	if opts.DryRun != DryRunNone {
		t.Errorf("DryRun = %v, want %v", opts.DryRun, DryRunNone)
	}

	if opts.Timeout != 30*time.Second {
		t.Errorf("Timeout = %v, want 30s", opts.Timeout)
	}
}

// TestNewConfigMapListOptions tests the NewConfigMapListOptions constructor
func TestNewConfigMapListOptions(t *testing.T) {
	opts := NewConfigMapListOptions()

	if opts == nil {
		t.Fatal("NewConfigMapListOptions() returned nil")
	}

	if opts.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(opts.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(opts.Labels))
	}

	if opts.FieldSelector != "" {
		t.Errorf("FieldSelector = %q, want empty string", opts.FieldSelector)
	}
}

// TestNewSecretOptions tests the NewSecretOptions constructor
func TestNewSecretOptions(t *testing.T) {
	opts := NewSecretOptions()

	if opts == nil {
		t.Fatal("NewSecretOptions() returned nil")
	}

	if opts.Type != "Opaque" {
		t.Errorf("Type = %q, want 'Opaque'", opts.Type)
	}

	if opts.Data == nil {
		t.Error("Data map should not be nil")
	}
	if len(opts.Data) != 0 {
		t.Errorf("Data length = %d, want 0", len(opts.Data))
	}

	if opts.BinaryData == nil {
		t.Error("BinaryData map should not be nil")
	}
	if len(opts.BinaryData) != 0 {
		t.Errorf("BinaryData length = %d, want 0", len(opts.BinaryData))
	}

	if opts.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(opts.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(opts.Labels))
	}

	if opts.DryRun != DryRunNone {
		t.Errorf("DryRun = %v, want %v", opts.DryRun, DryRunNone)
	}

	if opts.Timeout != 30*time.Second {
		t.Errorf("Timeout = %v, want 30s", opts.Timeout)
	}
}

// TestNewSecretListOptions tests the NewSecretListOptions constructor
func TestNewSecretListOptions(t *testing.T) {
	opts := NewSecretListOptions()

	if opts == nil {
		t.Fatal("NewSecretListOptions() returned nil")
	}

	if opts.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(opts.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(opts.Labels))
	}

	if opts.FieldSelector != "" {
		t.Errorf("FieldSelector = %q, want empty string", opts.FieldSelector)
	}

	if opts.Type != "" {
		t.Errorf("Type = %q, want empty string", opts.Type)
	}
}

// TestNewRolloutOptions tests the NewRolloutOptions constructor
func TestNewRolloutOptions(t *testing.T) {
	opts := NewRolloutOptions()

	if opts == nil {
		t.Fatal("NewRolloutOptions() returned nil")
	}

	if opts.Revision != 0 {
		t.Errorf("Revision = %d, want 0", opts.Revision)
	}

	if opts.Timeout != 5*time.Minute {
		t.Errorf("Timeout = %v, want 5m", opts.Timeout)
	}
}

// TestSecretTypeConstants tests secret type constants
func TestSecretTypeConstants(t *testing.T) {
	tests := []struct {
		name  string
		value string
		want  string
	}{
		{"Opaque", SecretTypeOpaque, "Opaque"},
		{"ServiceAccountToken", SecretTypeServiceAccountToken, "kubernetes.io/service-account-token"},
		{"Dockercfg", SecretTypeDockercfg, "kubernetes.io/dockercfg"},
		{"DockerConfigJson", SecretTypeDockerConfigJson, "kubernetes.io/dockerconfigjson"},
		{"BasicAuth", SecretTypeBasicAuth, "kubernetes.io/basic-auth"},
		{"SSHAuth", SecretTypeSSHAuth, "kubernetes.io/ssh-auth"},
		{"TLS", SecretTypeTLS, "kubernetes.io/tls"},
		{"BootstrapToken", SecretTypeBootstrapToken, "bootstrap.kubernetes.io/token"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.value != tt.want {
				t.Errorf("%s = %q, want %q", tt.name, tt.value, tt.want)
			}
		})
	}
}

// TestConfigMapOptions_Modification tests modifying ConfigMap options
func TestConfigMapOptions_Modification(t *testing.T) {
	opts := NewConfigMapOptions()

	// Add data
	opts.Data["key1"] = "value1"
	opts.Data["key2"] = "value2"

	// Add binary data
	opts.BinaryData["binary1"] = []byte("data")

	// Add labels
	opts.Labels["app"] = "test"

	// Modify settings
	opts.DryRun = DryRunClient
	opts.Timeout = 60 * time.Second

	// Verify modifications
	if len(opts.Data) != 2 {
		t.Errorf("Data length = %d, want 2", len(opts.Data))
	}
	if opts.Data["key1"] != "value1" {
		t.Errorf("Data[key1] = %q, want 'value1'", opts.Data["key1"])
	}

	if len(opts.BinaryData) != 1 {
		t.Errorf("BinaryData length = %d, want 1", len(opts.BinaryData))
	}

	if len(opts.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(opts.Labels))
	}

	if opts.DryRun != DryRunClient {
		t.Errorf("DryRun = %v, want %v", opts.DryRun, DryRunClient)
	}

	if opts.Timeout != 60*time.Second {
		t.Errorf("Timeout = %v, want 60s", opts.Timeout)
	}
}

// TestSecretOptions_Modification tests modifying Secret options
func TestSecretOptions_Modification(t *testing.T) {
	opts := NewSecretOptions()

	// Change type
	opts.Type = SecretTypeTLS

	// Add data
	opts.Data["username"] = "admin"
	opts.Data["password"] = "secret"

	// Add binary data
	opts.BinaryData["cert"] = []byte("certificate-data")

	// Add labels
	opts.Labels["env"] = "production"

	// Verify modifications
	if opts.Type != SecretTypeTLS {
		t.Errorf("Type = %q, want %q", opts.Type, SecretTypeTLS)
	}

	if len(opts.Data) != 2 {
		t.Errorf("Data length = %d, want 2", len(opts.Data))
	}

	if len(opts.BinaryData) != 1 {
		t.Errorf("BinaryData length = %d, want 1", len(opts.BinaryData))
	}

	if len(opts.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(opts.Labels))
	}
}

// TestConfigMapListOptions_Modification tests modifying ConfigMap list options
func TestConfigMapListOptions_Modification(t *testing.T) {
	opts := NewConfigMapListOptions()

	opts.Labels["app"] = "nginx"
	opts.Labels["version"] = "1.0"
	opts.FieldSelector = "metadata.name=my-config"

	if len(opts.Labels) != 2 {
		t.Errorf("Labels length = %d, want 2", len(opts.Labels))
	}

	if opts.FieldSelector != "metadata.name=my-config" {
		t.Errorf("FieldSelector = %q", opts.FieldSelector)
	}
}

// TestSecretListOptions_Modification tests modifying Secret list options
func TestSecretListOptions_Modification(t *testing.T) {
	opts := NewSecretListOptions()

	opts.Labels["tier"] = "backend"
	opts.FieldSelector = "type=Opaque"
	opts.Type = SecretTypeOpaque

	if len(opts.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(opts.Labels))
	}

	if opts.FieldSelector != "type=Opaque" {
		t.Errorf("FieldSelector = %q", opts.FieldSelector)
	}

	if opts.Type != SecretTypeOpaque {
		t.Errorf("Type = %q, want %q", opts.Type, SecretTypeOpaque)
	}
}

// TestRolloutOptions_Modification tests modifying rollout options
func TestRolloutOptions_Modification(t *testing.T) {
	opts := NewRolloutOptions()

	opts.Revision = 3
	opts.Timeout = 10 * time.Minute

	if opts.Revision != 3 {
		t.Errorf("Revision = %d, want 3", opts.Revision)
	}

	if opts.Timeout != 10*time.Minute {
		t.Errorf("Timeout = %v, want 10m", opts.Timeout)
	}
}

// TestRolloutStatusStruct tests the RolloutStatus struct
func TestRolloutStatusStruct(t *testing.T) {
	status := RolloutStatus{
		Kind:              "Deployment",
		Name:              "my-app",
		Namespace:         "default",
		CurrentRevision:   5,
		UpdatedReplicas:   3,
		ReadyReplicas:     3,
		AvailableReplicas: 3,
		Conditions:        []string{"Available", "Progressing"},
		Complete:          true,
	}

	if status.Kind != "Deployment" {
		t.Errorf("Kind = %q, want 'Deployment'", status.Kind)
	}
	if status.CurrentRevision != 5 {
		t.Errorf("CurrentRevision = %d, want 5", status.CurrentRevision)
	}
	if !status.Complete {
		t.Error("Complete should be true")
	}
	if len(status.Conditions) != 2 {
		t.Errorf("Conditions length = %d, want 2", len(status.Conditions))
	}
}

// TestRolloutStatusResultStruct tests the RolloutStatusResult struct
func TestRolloutStatusResultStruct(t *testing.T) {
	result := RolloutStatusResult{
		Kind:              "Deployment",
		Name:              "web-app",
		Namespace:         "production",
		CurrentRevision:   10,
		Replicas:          5,
		UpdatedReplicas:   5,
		ReadyReplicas:     5,
		AvailableReplicas: 5,
		Conditions:        []string{"Available"},
		Complete:          true,
		Message:           "Deployment successfully rolled out",
	}

	if result.Kind != "Deployment" {
		t.Errorf("Kind = %q", result.Kind)
	}
	if result.Replicas != 5 {
		t.Errorf("Replicas = %d, want 5", result.Replicas)
	}
	if result.Message != "Deployment successfully rolled out" {
		t.Errorf("Message = %q", result.Message)
	}
}

// TestRolloutHistoryResultStruct tests the RolloutHistoryResult struct
func TestRolloutHistoryResultStruct(t *testing.T) {
	now := time.Now()
	result := RolloutHistoryResult{
		Kind:      "Deployment",
		Name:      "api-server",
		Namespace: "default",
		Revisions: []RevisionInfo{
			{
				Revision:    1,
				ChangeCause: "Initial deployment",
				CreatedAt:   now.Add(-2 * time.Hour),
			},
			{
				Revision:    2,
				ChangeCause: "Update image to v2.0",
				CreatedAt:   now.Add(-1 * time.Hour),
			},
			{
				Revision:    3,
				ChangeCause: "Scale to 5 replicas",
				CreatedAt:   now,
			},
		},
	}

	if len(result.Revisions) != 3 {
		t.Errorf("Revisions length = %d, want 3", len(result.Revisions))
	}

	if result.Revisions[0].Revision != 1 {
		t.Errorf("Revision 0 = %d, want 1", result.Revisions[0].Revision)
	}

	if result.Revisions[2].ChangeCause != "Scale to 5 replicas" {
		t.Errorf("Revision 2 ChangeCause = %q", result.Revisions[2].ChangeCause)
	}
}

// TestRolloutUndoResultStruct tests the RolloutUndoResult struct
func TestRolloutUndoResultStruct(t *testing.T) {
	result := RolloutUndoResult{
		Kind:         "Deployment",
		Name:         "frontend",
		Namespace:    "default",
		FromRevision: 5,
		ToRevision:   3,
		Success:      true,
		Message:      "Rolled back to revision 3",
	}

	if result.FromRevision != 5 {
		t.Errorf("FromRevision = %d, want 5", result.FromRevision)
	}

	if result.ToRevision != 3 {
		t.Errorf("ToRevision = %d, want 3", result.ToRevision)
	}

	if !result.Success {
		t.Error("Success should be true")
	}

	if result.Message != "Rolled back to revision 3" {
		t.Errorf("Message = %q", result.Message)
	}
}

// TestRevisionInfoStruct tests the RevisionInfo struct
func TestRevisionInfoStruct(t *testing.T) {
	now := time.Now()
	info := RevisionInfo{
		Revision:    7,
		ChangeCause: "Updated environment variables",
		CreatedAt:   now,
	}

	if info.Revision != 7 {
		t.Errorf("Revision = %d, want 7", info.Revision)
	}

	if info.ChangeCause != "Updated environment variables" {
		t.Errorf("ChangeCause = %q", info.ChangeCause)
	}

	if !info.CreatedAt.Equal(now) {
		t.Error("CreatedAt not set correctly")
	}
}

// TestConfigMapOptions_EmptyMaps tests that maps are properly initialized
func TestConfigMapOptions_EmptyMaps(t *testing.T) {
	opts := NewConfigMapOptions()

	// Should be able to add to maps without nil pointer errors
	opts.Data["test"] = "value"
	opts.BinaryData["binary"] = []byte("data")
	opts.Labels["label"] = "value"

	if opts.Data["test"] != "value" {
		t.Error("Failed to add to Data map")
	}
	if string(opts.BinaryData["binary"]) != "data" {
		t.Error("Failed to add to BinaryData map")
	}
	if opts.Labels["label"] != "value" {
		t.Error("Failed to add to Labels map")
	}
}

// TestSecretOptions_EmptyMaps tests that maps are properly initialized
func TestSecretOptions_EmptyMaps(t *testing.T) {
	opts := NewSecretOptions()

	// Should be able to add to maps without nil pointer errors
	opts.Data["username"] = "admin"
	opts.BinaryData["key"] = []byte("private-key")
	opts.Labels["env"] = "prod"

	if opts.Data["username"] != "admin" {
		t.Error("Failed to add to Data map")
	}
	if string(opts.BinaryData["key"]) != "private-key" {
		t.Error("Failed to add to BinaryData map")
	}
	if opts.Labels["env"] != "prod" {
		t.Error("Failed to add to Labels map")
	}
}

// TestSecretOptions_TypeVariations tests different secret types
func TestSecretOptions_TypeVariations(t *testing.T) {
	types := []string{
		SecretTypeOpaque,
		SecretTypeServiceAccountToken,
		SecretTypeDockercfg,
		SecretTypeDockerConfigJson,
		SecretTypeBasicAuth,
		SecretTypeSSHAuth,
		SecretTypeTLS,
		SecretTypeBootstrapToken,
	}

	for _, secretType := range types {
		t.Run(secretType, func(t *testing.T) {
			opts := NewSecretOptions()
			opts.Type = secretType

			if opts.Type != secretType {
				t.Errorf("Type = %q, want %q", opts.Type, secretType)
			}
		})
	}
}
