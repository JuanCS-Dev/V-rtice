package k8s

import "time"

// ========================================================================
// CONFIGMAP OPERATION MODELS
// ========================================================================

// ConfigMapOptions configures ConfigMap operations
type ConfigMapOptions struct {
	// Data contains string key-value pairs
	Data map[string]string
	// BinaryData contains binary key-value pairs
	BinaryData map[string][]byte
	// Labels for the ConfigMap
	Labels map[string]string
	// DryRun enables dry-run mode
	DryRun DryRunStrategy
	// Timeout for operation
	Timeout time.Duration
}

// NewConfigMapOptions creates default ConfigMap options
func NewConfigMapOptions() *ConfigMapOptions {
	return &ConfigMapOptions{
		Data:       make(map[string]string),
		BinaryData: make(map[string][]byte),
		Labels:     make(map[string]string),
		DryRun:     DryRunNone,
		Timeout:    30 * time.Second,
	}
}

// ConfigMapListOptions configures ConfigMap list operations
type ConfigMapListOptions struct {
	// Labels filters by labels
	Labels map[string]string
	// FieldSelector filters by fields
	FieldSelector string
}

// NewConfigMapListOptions creates default ConfigMap list options
func NewConfigMapListOptions() *ConfigMapListOptions {
	return &ConfigMapListOptions{
		Labels:        make(map[string]string),
		FieldSelector: "",
	}
}

// ========================================================================
// SECRET OPERATION MODELS
// ========================================================================

// SecretOptions configures Secret operations
type SecretOptions struct {
	// Type is the secret type
	Type string
	// Data contains string key-value pairs (will be base64 encoded)
	Data map[string]string
	// BinaryData contains binary key-value pairs
	BinaryData map[string][]byte
	// Labels for the Secret
	Labels map[string]string
	// DryRun enables dry-run mode
	DryRun DryRunStrategy
	// Timeout for operation
	Timeout time.Duration
}

// NewSecretOptions creates default Secret options
func NewSecretOptions() *SecretOptions {
	return &SecretOptions{
		Type:       "Opaque",
		Data:       make(map[string]string),
		BinaryData: make(map[string][]byte),
		Labels:     make(map[string]string),
		DryRun:     DryRunNone,
		Timeout:    30 * time.Second,
	}
}

// SecretListOptions configures Secret list operations
type SecretListOptions struct {
	// Labels filters by labels
	Labels map[string]string
	// FieldSelector filters by fields
	FieldSelector string
	// Type filters by secret type
	Type string
}

// NewSecretListOptions creates default Secret list options
func NewSecretListOptions() *SecretListOptions {
	return &SecretListOptions{
		Labels:        make(map[string]string),
		FieldSelector: "",
		Type:          "",
	}
}

// Common secret types
const (
	SecretTypeOpaque                 = "Opaque"
	SecretTypeServiceAccountToken    = "kubernetes.io/service-account-token"
	SecretTypeDockercfg              = "kubernetes.io/dockercfg"
	SecretTypeDockerConfigJson       = "kubernetes.io/dockerconfigjson"
	SecretTypeBasicAuth              = "kubernetes.io/basic-auth"
	SecretTypeSSHAuth                = "kubernetes.io/ssh-auth"
	SecretTypeTLS                    = "kubernetes.io/tls"
	SecretTypeBootstrapToken         = "bootstrap.kubernetes.io/token"
)

// ========================================================================
// ROLLOUT OPERATION MODELS
// ========================================================================

// RolloutOptions configures rollout operations
type RolloutOptions struct {
	// Revision to rollback to (0 = previous)
	Revision int64
	// Timeout for rollout operation
	Timeout time.Duration
}

// NewRolloutOptions creates default rollout options
func NewRolloutOptions() *RolloutOptions {
	return &RolloutOptions{
		Revision: 0,
		Timeout:  5 * time.Minute,
	}
}

// RolloutStatus represents rollout status (legacy)
type RolloutStatus struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// CurrentRevision is the current revision
	CurrentRevision int64
	// UpdatedReplicas is the number of updated replicas
	UpdatedReplicas int32
	// ReadyReplicas is the number of ready replicas
	ReadyReplicas int32
	// AvailableReplicas is the number of available replicas
	AvailableReplicas int32
	// Conditions are the rollout conditions
	Conditions []string
	// Complete indicates if rollout is complete
	Complete bool
}

// RolloutStatusResult represents the result of a rollout status operation
type RolloutStatusResult struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// CurrentRevision is the current revision
	CurrentRevision int64
	// Replicas is the desired number of replicas
	Replicas int32
	// UpdatedReplicas is the number of updated replicas
	UpdatedReplicas int32
	// ReadyReplicas is the number of ready replicas
	ReadyReplicas int32
	// AvailableReplicas is the number of available replicas
	AvailableReplicas int32
	// Conditions are the rollout conditions
	Conditions []string
	// Complete indicates if rollout is complete
	Complete bool
	// Message is a status message
	Message string
}

// RolloutHistoryResult represents the result of a rollout history operation
type RolloutHistoryResult struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// Revisions is the list of revisions
	Revisions []RevisionInfo
}

// RevisionInfo represents information about a single revision
type RevisionInfo struct {
	// Revision is the revision number
	Revision int64
	// ChangeCause is the change-cause annotation
	ChangeCause string
	// CreatedAt is when the revision was created
	CreatedAt time.Time
}

// RolloutUndoResult represents the result of a rollout undo operation
type RolloutUndoResult struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// FromRevision is the revision being rolled back from
	FromRevision int64
	// ToRevision is the revision being rolled back to
	ToRevision int64
	// Success indicates if the undo was successful
	Success bool
	// Message is a status message
	Message string
}
