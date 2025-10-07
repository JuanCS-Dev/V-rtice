package k8s

import (
	"fmt"
	"time"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
)

// ========================================================================
// APPLY MODELS
// ========================================================================

// ApplyOptions configures apply operations
type ApplyOptions struct {
	// DryRun enables dry-run mode (client or server)
	DryRun DryRunStrategy
	// Force forces apply even if resource exists
	Force bool
	// ServerSide enables server-side apply
	ServerSide bool
	// FieldManager identifies the manager for server-side apply
	FieldManager string
	// Namespace overrides the namespace in resources
	Namespace string
	// Validate enables schema validation
	Validate bool
	// Timeout for apply operation
	Timeout time.Duration
}

// DryRunStrategy defines dry-run behavior
type DryRunStrategy string

const (
	// DryRunNone disables dry-run (default)
	DryRunNone DryRunStrategy = ""
	// DryRunClient performs client-side dry-run
	DryRunClient DryRunStrategy = "client"
	// DryRunServer performs server-side dry-run
	DryRunServer DryRunStrategy = "server"
)

// NewApplyOptions creates default apply options
func NewApplyOptions() *ApplyOptions {
	return &ApplyOptions{
		DryRun:       DryRunNone,
		Force:        false,
		ServerSide:   false,
		FieldManager: "vcli",
		Validate:     true,
		Timeout:      30 * time.Second,
	}
}

// ApplyResult represents the result of an apply operation
type ApplyResult struct {
	// Object is the resulting resource
	Object *unstructured.Unstructured
	// Action indicates what action was taken
	Action ApplyAction
	// Warnings are non-fatal warnings
	Warnings []string
	// DryRun indicates if this was a dry-run
	DryRun bool
}

// ApplyAction indicates what action was taken during apply
type ApplyAction string

const (
	// ApplyActionCreated indicates resource was created
	ApplyActionCreated ApplyAction = "created"
	// ApplyActionConfigured indicates resource was updated
	ApplyActionConfigured ApplyAction = "configured"
	// ApplyActionUnchanged indicates resource was unchanged
	ApplyActionUnchanged ApplyAction = "unchanged"
	// ApplyActionServerSideApplied indicates server-side apply was used
	ApplyActionServerSideApplied ApplyAction = "server-side-applied"
)

// ========================================================================
// DELETE MODELS
// ========================================================================

// DeleteOptions configures delete operations
type DeleteOptions struct {
	// GracePeriodSeconds is time to wait before force deletion
	GracePeriodSeconds *int64
	// PropagationPolicy controls cascade deletion
	PropagationPolicy PropagationPolicy
	// DryRun enables dry-run mode
	DryRun DryRunStrategy
	// Force enables immediate deletion (sets grace period to 0)
	Force bool
	// Timeout for delete operation
	Timeout time.Duration
	// Wait waits for deletion to complete
	Wait bool
	// WaitTimeout is the timeout for waiting
	WaitTimeout time.Duration
}

// PropagationPolicy defines how dependent objects are deleted
type PropagationPolicy string

const (
	// PropagationPolicyOrphan orphans dependents
	PropagationPolicyOrphan PropagationPolicy = "Orphan"
	// PropagationPolicyBackground deletes in background
	PropagationPolicyBackground PropagationPolicy = "Background"
	// PropagationPolicyForeground blocks until dependents deleted
	PropagationPolicyForeground PropagationPolicy = "Foreground"
)

// NewDeleteOptions creates default delete options
func NewDeleteOptions() *DeleteOptions {
	gracePeriod := int64(30)
	return &DeleteOptions{
		GracePeriodSeconds: &gracePeriod,
		PropagationPolicy:  PropagationPolicyBackground,
		DryRun:             DryRunNone,
		Force:              false,
		Timeout:            60 * time.Second,
		Wait:               false,
		WaitTimeout:        60 * time.Second,
	}
}

// DeleteResult represents the result of a delete operation
type DeleteResult struct {
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// Kind is the resource kind
	Kind string
	// Status is the deletion status
	Status DeleteStatus
	// Message provides additional information
	Message string
	// Duration is how long the operation took
	Duration time.Duration
	// DryRun indicates if this was a dry-run
	DryRun bool
}

// DeleteStatus represents deletion status
type DeleteStatus string

const (
	// DeleteStatusDeleted indicates resource was deleted
	DeleteStatusDeleted DeleteStatus = "deleted"
	// DeleteStatusNotFound indicates resource was not found
	DeleteStatusNotFound DeleteStatus = "not_found"
	// DeleteStatusFailed indicates deletion failed
	DeleteStatusFailed DeleteStatus = "failed"
)

// BatchDeleteOptions provides options for batch delete operations
type BatchDeleteOptions struct {
	// DeleteOptions are the delete options to use
	DeleteOptions *DeleteOptions
	// ContinueOnError if true, continue deleting even if errors occur
	ContinueOnError bool
	// Parallel if true, delete resources in parallel
	Parallel bool
}

// NewBatchDeleteOptions creates default batch delete options
func NewBatchDeleteOptions() *BatchDeleteOptions {
	return &BatchDeleteOptions{
		DeleteOptions:   NewDeleteOptions(),
		ContinueOnError: false,
		Parallel:        false,
	}
}

// ========================================================================
// SCALE MODELS
// ========================================================================

// ScaleOptions configures scale operations
type ScaleOptions struct {
	// Replicas is the desired replica count
	Replicas int32
	// Timeout for scale operation
	Timeout time.Duration
	// Wait waits for scale to complete
	Wait bool
	// WaitTimeout is the timeout for waiting
	WaitTimeout time.Duration
	// DryRun enables dry-run mode
	DryRun DryRunStrategy
}

// NewScaleOptions creates default scale options
func NewScaleOptions() *ScaleOptions {
	return &ScaleOptions{
		Replicas:    0,
		Timeout:     5 * time.Minute,
		WaitTimeout: 5 * time.Minute,
		Wait:        false,
		DryRun:      DryRunNone,
	}
}

// ScaleResult represents the result of a scale operation
type ScaleResult struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// PreviousReplicas is the replica count before scaling
	PreviousReplicas int32
	// DesiredReplicas is the target replica count
	DesiredReplicas int32
	// CurrentReplicas is the current replica count
	CurrentReplicas int32
	// Status is the scaling status
	Status ScaleStatus
	// Message provides additional information
	Message string
	// Duration is how long the operation took
	Duration time.Duration
	// DryRun indicates if this was a dry-run
	DryRun bool
}

// ScaleStatus represents scaling status
type ScaleStatus string

const (
	// ScaleStatusScaling indicates scaling is in progress
	ScaleStatusScaling ScaleStatus = "scaling"
	// ScaleStatusScaled indicates scaling completed successfully
	ScaleStatusScaled ScaleStatus = "scaled"
	// ScaleStatusFailed indicates scaling failed
	ScaleStatusFailed ScaleStatus = "failed"
)

// ScaleInfo provides information about a resource's scale
type ScaleInfo struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// DesiredReplicas is the desired replica count
	DesiredReplicas int32
	// CurrentReplicas is the current replica count
	CurrentReplicas int32
	// Selector is the label selector for the scaled pods
	Selector string
}

// ScaleTarget represents a resource to scale
type ScaleTarget struct {
	// Kind is the resource kind (Deployment, StatefulSet, ReplicaSet)
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// Replicas is the target replica count
	Replicas int32
}

// ========================================================================
// PATCH MODELS
// ========================================================================

// PatchOptions configures patch operations
type PatchOptions struct {
	// PatchType defines the patch strategy
	PatchType PatchType
	// Patch is the patch content
	Patch []byte
	// DryRun enables dry-run mode
	DryRun DryRunStrategy
	// Force enables force patching
	Force bool
	// FieldManager is the manager name for server-side apply
	FieldManager string
	// Timeout for patch operation
	Timeout time.Duration
}

// PatchType defines the patch strategy
type PatchType string

const (
	// PatchTypeJSON uses JSON Patch (RFC 6902)
	PatchTypeJSON PatchType = "json"
	// PatchTypeMerge uses JSON Merge Patch (RFC 7386)
	PatchTypeMerge PatchType = "merge"
	// PatchTypeStrategic uses Strategic Merge Patch (K8s-specific)
	PatchTypeStrategic PatchType = "strategic"
	// PatchTypeApply uses Server-Side Apply
	PatchTypeApply PatchType = "apply"
)

// NewPatchOptions creates default patch options
func NewPatchOptions() *PatchOptions {
	return &PatchOptions{
		PatchType:    PatchTypeStrategic,
		Patch:        nil,
		DryRun:       DryRunNone,
		Force:        false,
		FieldManager: "vcli",
		Timeout:      30 * time.Second,
	}
}

// PatchResult represents the result of a patch operation
type PatchResult struct {
	// Object is the resulting resource after patch
	Object *unstructured.Unstructured
	// PatchType is the type of patch that was applied
	PatchType PatchType
	// Applied indicates if patch was applied successfully
	Applied bool
	// Message provides additional information
	Message string
	// Duration is how long the operation took
	Duration time.Duration
	// DryRun indicates if this was a dry-run
	DryRun bool
}

// ========================================================================
// BATCH OPERATION MODELS
// ========================================================================

// BatchApplyOptions configures batch apply operations
type BatchApplyOptions struct {
	// ApplyOptions is the base apply options
	*ApplyOptions
	// ContinueOnError continues applying even if errors occur
	ContinueOnError bool
	// Parallel enables parallel applies
	Parallel bool
	// MaxParallel limits number of parallel operations
	MaxParallel int
}

// NewBatchApplyOptions creates default batch apply options
func NewBatchApplyOptions() *BatchApplyOptions {
	return &BatchApplyOptions{
		ApplyOptions:    NewApplyOptions(),
		ContinueOnError: false,
		Parallel:        false,
		MaxParallel:     5,
	}
}

// BatchResult represents results of batch operations
type BatchResult struct {
	// Total is the total number of resources processed
	Total int
	// Successful is the number of successful operations
	Successful int
	// Failed is the number of failed operations
	Failed int
	// Skipped is the number of skipped operations
	Skipped int
	// Results contains individual operation results
	Results []interface{}
	// Errors contains errors that occurred
	Errors []error
	// Duration is the total time taken
	Duration time.Duration
}

// ========================================================================
// WAIT & WATCH MODELS
// ========================================================================

// WaitOptions configures wait operations
type WaitOptions struct {
	// Condition is the condition to wait for
	Condition WaitCondition
	// Timeout is maximum time to wait
	Timeout time.Duration
	// Interval is polling interval
	Interval time.Duration
}

// WaitCondition defines what condition to wait for
type WaitCondition string

const (
	// WaitConditionReady waits for resource to be ready
	WaitConditionReady WaitCondition = "ready"
	// WaitConditionAvailable waits for resource to be available
	WaitConditionAvailable WaitCondition = "available"
	// WaitConditionDeleted waits for resource to be deleted
	WaitConditionDeleted WaitCondition = "deleted"
	// WaitConditionExists waits for resource to exist
	WaitConditionExists WaitCondition = "exists"
)

// NewWaitOptions creates default wait options
func NewWaitOptions(condition WaitCondition) *WaitOptions {
	return &WaitOptions{
		Condition: condition,
		Timeout:   5 * time.Minute,
		Interval:  2 * time.Second,
	}
}

// WaitResult represents the result of a wait operation
type WaitResult struct {
	// Success indicates if condition was met
	Success bool
	// Condition is the condition that was waited for
	Condition WaitCondition
	// Message provides additional information
	Message string
	// TimedOut indicates if operation timed out
	TimedOut bool
	// Duration is how long we waited
	Duration time.Duration
}

// ========================================================================
// RESOURCE SELECTOR MODELS
// ========================================================================

// ResourceSelector selects resources for operations
type ResourceSelector struct {
	// Namespace filters by namespace
	Namespace string
	// Labels filters by labels
	Labels map[string]string
	// FieldSelector filters by fields
	FieldSelector string
	// Names filters by specific names
	Names []string
	// Kinds filters by resource kinds
	Kinds []string
}

// NewResourceSelector creates a new resource selector
func NewResourceSelector() *ResourceSelector {
	return &ResourceSelector{
		Labels: make(map[string]string),
		Names:  []string{},
		Kinds:  []string{},
	}
}

// Matches checks if a resource matches the selector
func (rs *ResourceSelector) Matches(obj *unstructured.Unstructured) bool {
	if obj == nil {
		return false
	}

	// Check namespace
	if rs.Namespace != "" && obj.GetNamespace() != rs.Namespace {
		return false
	}

	// Check kind
	if len(rs.Kinds) > 0 {
		kindMatches := false
		for _, kind := range rs.Kinds {
			if obj.GetKind() == kind {
				kindMatches = true
				break
			}
		}
		if !kindMatches {
			return false
		}
	}

	// Check name
	if len(rs.Names) > 0 {
		nameMatches := false
		for _, name := range rs.Names {
			if obj.GetName() == name {
				nameMatches = true
				break
			}
		}
		if !nameMatches {
			return false
		}
	}

	// Check labels
	if len(rs.Labels) > 0 {
		objLabels := obj.GetLabels()
		for key, value := range rs.Labels {
			if objLabels[key] != value {
				return false
			}
		}
	}

	return true
}

// ========================================================================
// MUTATION OPERATION CONTEXT
// ========================================================================

// MutationContext provides context for mutation operations
type MutationContext struct {
	// UID is unique identifier for this mutation operation
	UID types.UID
	// StartTime is when the operation started
	StartTime time.Time
	// Namespace is the target namespace
	Namespace string
	// DryRun indicates if this is a dry-run
	DryRun bool
	// User is the user performing the operation
	User string
	// Source identifies the source of the mutation (e.g., "vcli", "api")
	Source string
}

// NewMutationContext creates a new mutation context
func NewMutationContext(namespace string, dryRun bool) *MutationContext {
	return &MutationContext{
		UID:       types.UID(fmt.Sprintf("vcli-%d", time.Now().UnixNano())),
		StartTime: time.Now(),
		Namespace: namespace,
		DryRun:    dryRun,
		Source:    "vcli",
	}
}

// Duration returns how long the operation has been running
func (mc *MutationContext) Duration() time.Duration {
	return time.Since(mc.StartTime)
}

// ========================================================================
// VALIDATION MODELS
// ========================================================================

// ValidationResult represents resource validation result
type ValidationResult struct {
	// Valid indicates if resource is valid
	Valid bool
	// Errors contains validation errors
	Errors []ValidationError
	// Warnings contains non-fatal warnings
	Warnings []string
}

// ValidationError represents a validation error
type ValidationError struct {
	// Field is the field that failed validation
	Field string
	// Message describes the error
	Message string
	// Type is the error type
	Type ValidationErrorType
}

// ValidationErrorType categorizes validation errors
type ValidationErrorType string

const (
	// ValidationErrorTypeRequired indicates required field missing
	ValidationErrorTypeRequired ValidationErrorType = "required"
	// ValidationErrorTypeInvalid indicates invalid value
	ValidationErrorTypeInvalid ValidationErrorType = "invalid"
	// ValidationErrorTypeNotSupported indicates unsupported value
	ValidationErrorTypeNotSupported ValidationErrorType = "not_supported"
	// ValidationErrorTypeForbidden indicates forbidden operation
	ValidationErrorTypeForbidden ValidationErrorType = "forbidden"
)

// NewValidationResult creates a new validation result
func NewValidationResult() *ValidationResult {
	return &ValidationResult{
		Valid:    true,
		Errors:   []ValidationError{},
		Warnings: []string{},
	}
}

// AddError adds a validation error
func (vr *ValidationResult) AddError(field, message string, errorType ValidationErrorType) {
	vr.Valid = false
	vr.Errors = append(vr.Errors, ValidationError{
		Field:   field,
		Message: message,
		Type:    errorType,
	})
}

// AddWarning adds a validation warning
func (vr *ValidationResult) AddWarning(message string) {
	vr.Warnings = append(vr.Warnings, message)
}
