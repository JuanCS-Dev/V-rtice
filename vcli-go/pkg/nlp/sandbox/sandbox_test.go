package sandbox

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func setupSandbox(t *testing.T) *Sandbox {
config := &SandboxConfig{
AllowedNamespaces:   []string{"default", "dev", "staging"},
ForbiddenNamespaces: []string{"kube-system", "kube-public"},
AllowedPaths:        []string{"/tmp", "/var/tmp"},
ForbiddenPaths:      []string{"/etc", "/root", "/var/secrets"},
MaxCPU:              "200m",
MaxMemory:           "256Mi",
Timeout:             30 * time.Second,
}

sandbox, err := NewSandbox(config)
require.NoError(t, err)
return sandbox
}

func TestNewSandbox(t *testing.T) {
config := &SandboxConfig{}
sandbox, err := NewSandbox(config)

require.NoError(t, err)
assert.NotNil(t, sandbox)
assert.Equal(t, "default", sandbox.config.DefaultNamespace)
assert.Equal(t, 30*time.Second, sandbox.config.Timeout)
}

func TestValidateNamespace_Allowed(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidateNamespace("default")
assert.True(t, result.Valid)
assert.True(t, result.Allowed)

result = sandbox.ValidateNamespace("dev")
assert.True(t, result.Valid)
}

func TestValidateNamespace_Forbidden(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidateNamespace("kube-system")
assert.False(t, result.Valid)
assert.False(t, result.Allowed)
assert.Contains(t, result.Reason, "forbidden")
}

func TestValidateNamespace_NotInWhitelist(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidateNamespace("production")
assert.False(t, result.Valid)
assert.Contains(t, result.Reason, "not in whitelist")
}

func TestValidatePath_Allowed(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidatePath("/tmp/file.txt")
assert.True(t, result.Valid)
assert.True(t, result.Allowed)
}

func TestValidatePath_Forbidden(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidatePath("/etc/passwd")
assert.False(t, result.Valid)
assert.False(t, result.Allowed)
assert.Contains(t, result.Reason, "forbidden")

result = sandbox.ValidatePath("/var/secrets/token")
assert.False(t, result.Valid)
}

func TestValidatePath_NotInWhitelist(t *testing.T) {
sandbox := setupSandbox(t)

result := sandbox.ValidatePath("/home/user/file")
assert.False(t, result.Valid)
assert.Contains(t, result.Reason, "not in whitelist")
}

func TestExecute_Success(t *testing.T) {
sandbox := setupSandbox(t)

execCtx := &ExecutionContext{
CommandString: "kubectl get pods",
Namespace:     "default",
WorkDir:       "/tmp",
Timeout:       10 * time.Second,
}

result, err := sandbox.Execute(execCtx)
require.NoError(t, err)
assert.True(t, result.Success)
assert.Empty(t, result.Violations)
}

func TestExecute_NamespaceViolation(t *testing.T) {
sandbox := setupSandbox(t)

execCtx := &ExecutionContext{
CommandString: "kubectl get pods",
Namespace:     "kube-system",
Timeout:       10 * time.Second,
}

result, err := sandbox.Execute(execCtx)
require.NoError(t, err)
assert.False(t, result.Success)
assert.NotEmpty(t, result.Violations)
assert.Contains(t, result.Violations[0], "forbidden")
}

func TestExecute_PathViolation(t *testing.T) {
sandbox := setupSandbox(t)

execCtx := &ExecutionContext{
CommandString: "ls",
Namespace:     "default",
WorkDir:       "/etc",
Timeout:       10 * time.Second,
}

result, err := sandbox.Execute(execCtx)
require.NoError(t, err)
assert.False(t, result.Success)
assert.NotEmpty(t, result.Violations)
}

func TestExecute_TimeoutViolation(t *testing.T) {
sandbox := setupSandbox(t)

execCtx := &ExecutionContext{
CommandString: "sleep 100",
Namespace:     "default",
Timeout:       60 * time.Second, // Exceeds 30s limit
}

result, err := sandbox.Execute(execCtx)
require.NoError(t, err)
assert.False(t, result.Success)
assert.NotEmpty(t, result.Violations)
}

func TestDryRun(t *testing.T) {
sandbox := setupSandbox(t)

execCtx := &ExecutionContext{
CommandString: "kubectl get pods",
Namespace:     "default",
}

result, err := sandbox.DryRun(execCtx)
require.NoError(t, err)
assert.True(t, result.DryRun)
}

func TestIsNamespaceAllowed(t *testing.T) {
sandbox := setupSandbox(t)

assert.True(t, sandbox.IsNamespaceAllowed("default"))
assert.False(t, sandbox.IsNamespaceAllowed("kube-system"))
}

func TestIsPathAllowed(t *testing.T) {
sandbox := setupSandbox(t)

assert.True(t, sandbox.IsPathAllowed("/tmp/file"))
assert.False(t, sandbox.IsPathAllowed("/etc/passwd"))
}

func TestResourceLimiter(t *testing.T) {
config := &SandboxConfig{
MaxCPU:    "100m",
MaxMemory: "128Mi",
Timeout:   30 * time.Second,
}

limiter := NewResourceLimiter(config)

t.Run("Valid limits", func(t *testing.T) {
execCtx := &ExecutionContext{
Timeout: 10 * time.Second,
}
err := limiter.Validate(execCtx)
assert.NoError(t, err)
})

t.Run("Timeout exceeded", func(t *testing.T) {
execCtx := &ExecutionContext{
Timeout: 60 * time.Second,
}
err := limiter.Validate(execCtx)
assert.Error(t, err)
assert.Contains(t, err.Error(), "timeout")
})
}

func TestPathValidator(t *testing.T) {
config := &SandboxConfig{
AllowedPaths:   []string{"/app", "/tmp"},
ForbiddenPaths: []string{"/etc", "/root"},
}

validator := NewPathValidator(config)

t.Run("Allowed path", func(t *testing.T) {
result := validator.Validate("/app/config.yaml")
assert.True(t, result.Valid)
})

t.Run("Forbidden path", func(t *testing.T) {
result := validator.Validate("/etc/passwd")
assert.False(t, result.Valid)
})

t.Run("Not in whitelist", func(t *testing.T) {
result := validator.Validate("/home/user")
assert.False(t, result.Valid)
})
}
