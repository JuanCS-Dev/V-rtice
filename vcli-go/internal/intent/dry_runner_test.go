// Package intent - Dry Runner Tests
package intent

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestDryRunner_Estimate(t *testing.T) {
	runner := NewDryRunner()
	ctx := context.Background()

	tests := []struct {
		name              string
		cmd               *nlp.Command
		expectedResources int
		expectedSeverity  string
		expectedReversible bool
	}{
		{
			name: "single pod delete",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"test-pod"},
			},
			expectedResources: 1,
			expectedSeverity:  "critical",
			expectedReversible: true, // Pods are recreated by controllers
		},
		{
			name: "multiple pods delete",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
				Args: []string{"pod-1", "pod-2", "pod-3"},
			},
			expectedResources: 3,
			expectedSeverity:  "critical",
			expectedReversible: true,
		},
		{
			name: "scale operation",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "scale", "deployment"},
				Args:  []string{"webapp"},
				Flags: map[string]string{"--replicas": "5"},
			},
			expectedResources: 1,
			expectedSeverity:  "medium",
			expectedReversible: true,
		},
		{
			name: "delete in production namespace",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "delete", "deployment"},
				Args:  []string{"critical-service"},
				Flags: map[string]string{"-n": "production"},
			},
			expectedResources: 1,
			expectedSeverity:  "critical",
			expectedReversible: false,
		},
		{
			name: "get pods (low risk)",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "get", "pods"},
				Flags: map[string]string{"-n": "default"},
			},
			expectedResources: 1,
			expectedSeverity:  "low",
			expectedReversible: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			impact, err := runner.Estimate(ctx, tt.cmd)
			require.NoError(t, err)
			require.NotNil(t, impact)

			assert.Equal(t, tt.expectedSeverity, impact.Severity,
				"Severity mismatch for %s", tt.name)
			assert.Equal(t, tt.expectedReversible, impact.Reversible,
				"Reversible mismatch for %s", tt.name)
			
			// Check that description is populated
			assert.NotEmpty(t, impact.Description)
			assert.NotEmpty(t, impact.EstimatedTime)
		})
	}
}

func TestDryRunner_CountResources(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected int
	}{
		{
			name: "specific resources named",
			cmd: &nlp.Command{
				Args: []string{"pod-1", "pod-2", "pod-3"},
			},
			expected: 3,
		},
		{
			name: "--all flag",
			cmd: &nlp.Command{
				Flags: map[string]string{"--all"},
			},
			expected: 10,
		},
		{
			name: "label selector",
			cmd: &nlp.Command{
				Flags: map[string]string{"-l", "app=web"},
			},
			expected: 5,
		},
		{
			name: "no args or selectors",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get", "pods"},
			},
			expected: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.countResources(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDryRunner_ExtractNamespaces(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected []string
	}{
		{
			name: "explicit namespace",
			cmd: &nlp.Command{
				Flags: map[string]string{"-n", "kafka"},
			},
			expected: []string{"kafka"},
		},
		{
			name: "all namespaces",
			cmd: &nlp.Command{
				Flags: map[string]string{"--all-namespaces"},
			},
			expected: []string{"ALL"},
		},
		{
			name: "all namespaces short flag",
			cmd: &nlp.Command{
				Flags: map[string]string{"-A"},
			},
			expected: []string{"ALL"},
		},
		{
			name: "default namespace (implicit)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get", "pods"},
			},
			expected: []string{"default"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.extractNamespaces(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDryRunner_IsReversible(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected bool
	}{
		{
			name: "delete pod (reversible - controller recreates)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
			},
			expected: true,
		},
		{
			name: "delete deployment (not reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "deployment"},
			},
			expected: false,
		},
		{
			name: "scale (reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "scale", "deployment"},
			},
			expected: true,
		},
		{
			name: "apply (reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "apply", "-f"},
			},
			expected: true,
		},
		{
			name: "patch (reversible)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "patch", "deployment"},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.isReversible(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDryRunner_CalculateRisk(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name          string
		cmd           *nlp.Command
		resourceCount int
		minRisk       float64
		maxRisk       float64
	}{
		{
			name: "delete single resource",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
			},
			resourceCount: 1,
			minRisk:       0.7,
			maxRisk:       0.9,
		},
		{
			name: "delete multiple resources",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
			},
			resourceCount: 15,
			minRisk:       0.9,
			maxRisk:       1.0,
		},
		{
			name: "delete in production",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "delete", "deployment"},
				Flags: map[string]string{"-n", "production"},
			},
			resourceCount: 1,
			minRisk:       0.9,
			maxRisk:       1.0,
		},
		{
			name: "get pods (low risk)",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get", "pods"},
			},
			resourceCount: 1,
			minRisk:       0.0,
			maxRisk:       0.2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.calculateRisk(tt.cmd, tt.resourceCount)
			assert.GreaterOrEqual(t, result, tt.minRisk)
			assert.LessOrEqual(t, result, tt.maxRisk)
		})
	}
}

func TestDryRunner_Execute(t *testing.T) {
	runner := NewDryRunner()
	ctx := context.Background()

	cmd := &nlp.Command{
		Path: []string{"kubectl", "delete", "pod"},
		Args: []string{"test-pod-1", "test-pod-2"},
	}

	result, err := runner.Execute(ctx, cmd)
	require.NoError(t, err)
	require.NotNil(t, result)

	assert.True(t, result.Success)
	assert.NotEmpty(t, result.Output)
	assert.Equal(t, 2, len(result.ResourcesChanged))
}

func TestDryRunner_ExtractVerb(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected string
	}{
		{
			name: "kubectl command",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "delete", "pod"},
			},
			expected: "delete",
		},
		{
			name: "non-kubectl command",
			cmd: &nlp.Command{
				Path: []string{"docker", "ps"},
			},
			expected: "docker",
		},
		{
			name: "empty path",
			cmd: &nlp.Command{
				Path: []string{},
			},
			expected: "execute",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.extractVerb(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDryRunner_ExtractResource(t *testing.T) {
	runner := NewDryRunner()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		expected string
	}{
		{
			name: "kubectl with resource",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get", "pods"},
			},
			expected: "pods",
		},
		{
			name: "resource in flags",
			cmd: &nlp.Command{
				Path:  []string{"kubectl", "get"},
				Flags: map[string]string{"--resource", "deployments"},
			},
			expected: "deployments",
		},
		{
			name: "no resource specified",
			cmd: &nlp.Command{
				Path: []string{"kubectl", "get"},
			},
			expected: "resource",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := runner.extractResource(tt.cmd)
			assert.Equal(t, tt.expected, result)
		})
	}
}
