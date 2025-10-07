package k8s

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

// ========================================================================
// APPLY OPTIONS TESTS
// ========================================================================

func TestNewApplyOptions(t *testing.T) {
	opts := NewApplyOptions()

	assert.NotNil(t, opts)
	assert.Equal(t, DryRunNone, opts.DryRun)
	assert.False(t, opts.Force)
	assert.False(t, opts.ServerSide)
	assert.Equal(t, "vcli", opts.FieldManager)
	assert.True(t, opts.Validate)
	assert.Equal(t, 30*time.Second, opts.Timeout)
}

func TestApplyOptions_CustomValues(t *testing.T) {
	opts := NewApplyOptions()
	opts.DryRun = DryRunClient
	opts.Force = true
	opts.ServerSide = true
	opts.FieldManager = "custom"
	opts.Namespace = "test-ns"

	assert.Equal(t, DryRunClient, opts.DryRun)
	assert.True(t, opts.Force)
	assert.True(t, opts.ServerSide)
	assert.Equal(t, "custom", opts.FieldManager)
	assert.Equal(t, "test-ns", opts.Namespace)
}

// ========================================================================
// DELETE OPTIONS TESTS
// ========================================================================

func TestNewDeleteOptions(t *testing.T) {
	opts := NewDeleteOptions()

	assert.NotNil(t, opts)
	assert.NotNil(t, opts.GracePeriodSeconds)
	assert.Equal(t, int64(30), *opts.GracePeriodSeconds)
	assert.Equal(t, PropagationPolicyBackground, opts.PropagationPolicy)
	assert.Equal(t, DryRunNone, opts.DryRun)
	assert.False(t, opts.Force)
	assert.Equal(t, 60*time.Second, opts.Timeout)
}

func TestDeleteOptions_ForceDelete(t *testing.T) {
	opts := NewDeleteOptions()
	opts.Force = true
	gracePeriod := int64(0)
	opts.GracePeriodSeconds = &gracePeriod

	assert.True(t, opts.Force)
	assert.Equal(t, int64(0), *opts.GracePeriodSeconds)
}

func TestDeleteOptions_PropagationPolicies(t *testing.T) {
	tests := []struct {
		name   string
		policy PropagationPolicy
	}{
		{"orphan", PropagationPolicyOrphan},
		{"background", PropagationPolicyBackground},
		{"foreground", PropagationPolicyForeground},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opts := NewDeleteOptions()
			opts.PropagationPolicy = tt.policy
			assert.Equal(t, tt.policy, opts.PropagationPolicy)
		})
	}
}

// ========================================================================
// SCALE OPTIONS TESTS
// ========================================================================

func TestNewScaleOptions(t *testing.T) {
	replicas := int32(5)
	opts := NewScaleOptions(replicas)

	assert.NotNil(t, opts)
	assert.Equal(t, replicas, opts.Replicas)
	assert.Equal(t, 5*time.Minute, opts.Timeout)
	assert.False(t, opts.Wait)
	assert.Equal(t, DryRunNone, opts.DryRun)
}

func TestScaleOptions_WithWait(t *testing.T) {
	opts := NewScaleOptions(3)
	opts.Wait = true

	assert.True(t, opts.Wait)
	assert.Equal(t, int32(3), opts.Replicas)
}

// ========================================================================
// PATCH OPTIONS TESTS
// ========================================================================

func TestNewPatchOptions(t *testing.T) {
	patchData := []byte(`{"spec":{"replicas":3}}`)
	opts := NewPatchOptions(PatchTypeMerge, patchData)

	assert.NotNil(t, opts)
	assert.Equal(t, PatchTypeMerge, opts.PatchType)
	assert.Equal(t, patchData, opts.Patch)
	assert.Equal(t, DryRunNone, opts.DryRun)
	assert.False(t, opts.Force)
	assert.Equal(t, 30*time.Second, opts.Timeout)
}

func TestPatchOptions_AllPatchTypes(t *testing.T) {
	tests := []struct {
		name      string
		patchType PatchType
	}{
		{"json", PatchTypeJSON},
		{"merge", PatchTypeMerge},
		{"strategic", PatchTypeStrategic},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			opts := NewPatchOptions(tt.patchType, []byte("{}"))
			assert.Equal(t, tt.patchType, opts.PatchType)
		})
	}
}

// ========================================================================
// BATCH OPTIONS TESTS
// ========================================================================

func TestNewBatchApplyOptions(t *testing.T) {
	opts := NewBatchApplyOptions()

	assert.NotNil(t, opts)
	assert.NotNil(t, opts.ApplyOptions)
	assert.False(t, opts.ContinueOnError)
	assert.False(t, opts.Parallel)
	assert.Equal(t, 5, opts.MaxParallel)
}

func TestBatchApplyOptions_Parallel(t *testing.T) {
	opts := NewBatchApplyOptions()
	opts.Parallel = true
	opts.MaxParallel = 10

	assert.True(t, opts.Parallel)
	assert.Equal(t, 10, opts.MaxParallel)
}

// ========================================================================
// WAIT OPTIONS TESTS
// ========================================================================

func TestNewWaitOptions(t *testing.T) {
	opts := NewWaitOptions(WaitConditionReady)

	assert.NotNil(t, opts)
	assert.Equal(t, WaitConditionReady, opts.Condition)
	assert.Equal(t, 5*time.Minute, opts.Timeout)
	assert.Equal(t, 2*time.Second, opts.Interval)
}

func TestWaitOptions_AllConditions(t *testing.T) {
	conditions := []WaitCondition{
		WaitConditionReady,
		WaitConditionAvailable,
		WaitConditionDeleted,
		WaitConditionExists,
	}

	for _, cond := range conditions {
		opts := NewWaitOptions(cond)
		assert.Equal(t, cond, opts.Condition)
	}
}

// ========================================================================
// RESOURCE SELECTOR TESTS
// ========================================================================

func TestNewResourceSelector(t *testing.T) {
	selector := NewResourceSelector()

	assert.NotNil(t, selector)
	assert.NotNil(t, selector.Labels)
	assert.NotNil(t, selector.Names)
	assert.NotNil(t, selector.Kinds)
	assert.Empty(t, selector.Namespace)
}

func TestResourceSelector_Matches_Namespace(t *testing.T) {
	selector := NewResourceSelector()
	selector.Namespace = "test-ns"

	obj := &unstructured.Unstructured{}
	obj.SetNamespace("test-ns")
	obj.SetName("test-pod")
	obj.SetKind("Pod")

	assert.True(t, selector.Matches(obj))

	obj2 := &unstructured.Unstructured{}
	obj2.SetNamespace("other-ns")
	obj2.SetName("test-pod")
	obj2.SetKind("Pod")

	assert.False(t, selector.Matches(obj2))
}

func TestResourceSelector_Matches_Kind(t *testing.T) {
	selector := NewResourceSelector()
	selector.Kinds = []string{"Pod", "Service"}

	obj := &unstructured.Unstructured{}
	obj.SetKind("Pod")
	obj.SetName("test-pod")

	assert.True(t, selector.Matches(obj))

	obj2 := &unstructured.Unstructured{}
	obj2.SetKind("Deployment")
	obj2.SetName("test-deploy")

	assert.False(t, selector.Matches(obj2))
}

func TestResourceSelector_Matches_Name(t *testing.T) {
	selector := NewResourceSelector()
	selector.Names = []string{"pod1", "pod2"}

	obj := &unstructured.Unstructured{}
	obj.SetName("pod1")
	obj.SetKind("Pod")

	assert.True(t, selector.Matches(obj))

	obj2 := &unstructured.Unstructured{}
	obj2.SetName("pod3")
	obj2.SetKind("Pod")

	assert.False(t, selector.Matches(obj2))
}

func TestResourceSelector_Matches_Labels(t *testing.T) {
	selector := NewResourceSelector()
	selector.Labels = map[string]string{
		"app":  "test",
		"tier": "frontend",
	}

	obj := &unstructured.Unstructured{}
	obj.SetName("test-pod")
	obj.SetKind("Pod")
	obj.SetLabels(map[string]string{
		"app":  "test",
		"tier": "frontend",
	})

	assert.True(t, selector.Matches(obj))

	obj2 := &unstructured.Unstructured{}
	obj2.SetName("test-pod2")
	obj2.SetKind("Pod")
	obj2.SetLabels(map[string]string{
		"app": "test",
		// missing tier label
	})

	assert.False(t, selector.Matches(obj2))
}

func TestResourceSelector_Matches_MultipleFilters(t *testing.T) {
	selector := NewResourceSelector()
	selector.Namespace = "test-ns"
	selector.Kinds = []string{"Pod"}
	selector.Labels = map[string]string{"app": "test"}

	obj := &unstructured.Unstructured{}
	obj.SetNamespace("test-ns")
	obj.SetKind("Pod")
	obj.SetName("test-pod")
	obj.SetLabels(map[string]string{"app": "test"})

	assert.True(t, selector.Matches(obj))
}

func TestResourceSelector_Matches_NilObject(t *testing.T) {
	selector := NewResourceSelector()
	assert.False(t, selector.Matches(nil))
}

// ========================================================================
// MUTATION CONTEXT TESTS
// ========================================================================

func TestNewMutationContext(t *testing.T) {
	ctx := NewMutationContext("test-ns", false)

	assert.NotNil(t, ctx)
	assert.NotEmpty(t, ctx.UID)
	assert.False(t, ctx.StartTime.IsZero())
	assert.Equal(t, "test-ns", ctx.Namespace)
	assert.False(t, ctx.DryRun)
	assert.Equal(t, "vcli", ctx.Source)
}

func TestMutationContext_Duration(t *testing.T) {
	ctx := NewMutationContext("test-ns", false)
	time.Sleep(10 * time.Millisecond)

	duration := ctx.Duration()
	assert.True(t, duration >= 10*time.Millisecond)
}

func TestMutationContext_DryRun(t *testing.T) {
	ctx := NewMutationContext("test-ns", true)
	assert.True(t, ctx.DryRun)
}

// ========================================================================
// VALIDATION RESULT TESTS
// ========================================================================

func TestNewValidationResult(t *testing.T) {
	result := NewValidationResult()

	assert.NotNil(t, result)
	assert.True(t, result.Valid)
	assert.Empty(t, result.Errors)
	assert.Empty(t, result.Warnings)
}

func TestValidationResult_AddError(t *testing.T) {
	result := NewValidationResult()

	result.AddError("spec.replicas", "must be positive", ValidationErrorTypeInvalid)

	assert.False(t, result.Valid)
	assert.Len(t, result.Errors, 1)
	assert.Equal(t, "spec.replicas", result.Errors[0].Field)
	assert.Equal(t, "must be positive", result.Errors[0].Message)
	assert.Equal(t, ValidationErrorTypeInvalid, result.Errors[0].Type)
}

func TestValidationResult_AddMultipleErrors(t *testing.T) {
	result := NewValidationResult()

	result.AddError("field1", "error1", ValidationErrorTypeRequired)
	result.AddError("field2", "error2", ValidationErrorTypeInvalid)

	assert.False(t, result.Valid)
	assert.Len(t, result.Errors, 2)
}

func TestValidationResult_AddWarning(t *testing.T) {
	result := NewValidationResult()

	result.AddWarning("deprecated field used")

	assert.True(t, result.Valid) // Warnings don't invalidate
	assert.Len(t, result.Warnings, 1)
	assert.Equal(t, "deprecated field used", result.Warnings[0])
}

func TestValidationResult_ErrorTypes(t *testing.T) {
	types := []ValidationErrorType{
		ValidationErrorTypeRequired,
		ValidationErrorTypeInvalid,
		ValidationErrorTypeNotSupported,
		ValidationErrorTypeForbidden,
	}

	for _, errType := range types {
		result := NewValidationResult()
		result.AddError("field", "message", errType)
		assert.Equal(t, errType, result.Errors[0].Type)
	}
}

// ========================================================================
// RESULT MODELS TESTS
// ========================================================================

func TestApplyResult(t *testing.T) {
	obj := &unstructured.Unstructured{}
	obj.SetName("test-pod")
	obj.SetKind("Pod")

	result := &ApplyResult{
		Object:   obj,
		Action:   ApplyActionCreated,
		Warnings: []string{"warning1"},
		DryRun:   false,
	}

	assert.NotNil(t, result.Object)
	assert.Equal(t, ApplyActionCreated, result.Action)
	assert.Len(t, result.Warnings, 1)
	assert.False(t, result.DryRun)
}

func TestDeleteResult(t *testing.T) {
	result := &DeleteResult{
		ResourceIdentifier: "Pod/test-pod",
		Success:            true,
		Message:            "deleted successfully",
		DryRun:             false,
	}

	assert.Equal(t, "Pod/test-pod", result.ResourceIdentifier)
	assert.True(t, result.Success)
	assert.NotEmpty(t, result.Message)
}

func TestScaleResult(t *testing.T) {
	result := &ScaleResult{
		ResourceIdentifier: "Deployment/nginx",
		PreviousReplicas:   2,
		DesiredReplicas:    5,
		CurrentReplicas:    5,
		ReadyReplicas:      5,
		Success:            true,
		Message:            "scaled successfully",
	}

	assert.Equal(t, "Deployment/nginx", result.ResourceIdentifier)
	assert.Equal(t, int32(2), result.PreviousReplicas)
	assert.Equal(t, int32(5), result.DesiredReplicas)
	assert.True(t, result.Success)
}

func TestPatchResult(t *testing.T) {
	obj := &unstructured.Unstructured{}
	obj.SetName("test-pod")

	result := &PatchResult{
		Object:             obj,
		ResourceIdentifier: "Pod/test-pod",
		Success:            true,
		Message:            "patched successfully",
		DryRun:             false,
	}

	assert.NotNil(t, result.Object)
	assert.True(t, result.Success)
	assert.Equal(t, "Pod/test-pod", result.ResourceIdentifier)
}

func TestBatchResult(t *testing.T) {
	result := &BatchResult{
		Total:      10,
		Successful: 8,
		Failed:     2,
		Skipped:    0,
		Results:    make([]interface{}, 0),
		Errors:     make([]error, 0),
		Duration:   5 * time.Second,
	}

	assert.Equal(t, 10, result.Total)
	assert.Equal(t, 8, result.Successful)
	assert.Equal(t, 2, result.Failed)
	assert.Equal(t, 5*time.Second, result.Duration)
}

func TestWaitResult(t *testing.T) {
	result := &WaitResult{
		Success:   true,
		Condition: WaitConditionReady,
		Message:   "resource is ready",
		TimedOut:  false,
		Duration:  30 * time.Second,
	}

	assert.True(t, result.Success)
	assert.Equal(t, WaitConditionReady, result.Condition)
	assert.False(t, result.TimedOut)
	assert.Equal(t, 30*time.Second, result.Duration)
}

// ========================================================================
// DRY RUN STRATEGY TESTS
// ========================================================================

func TestDryRunStrategies(t *testing.T) {
	assert.Equal(t, DryRunStrategy(""), DryRunNone)
	assert.Equal(t, DryRunStrategy("client"), DryRunClient)
	assert.Equal(t, DryRunStrategy("server"), DryRunServer)
}

// ========================================================================
// APPLY ACTION TESTS
// ========================================================================

func TestApplyActions(t *testing.T) {
	actions := []ApplyAction{
		ApplyActionCreated,
		ApplyActionConfigured,
		ApplyActionUnchanged,
		ApplyActionServerSideApplied,
	}

	for _, action := range actions {
		assert.NotEmpty(t, string(action))
	}
}
