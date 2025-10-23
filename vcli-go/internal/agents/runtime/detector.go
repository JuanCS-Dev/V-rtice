package runtime

import (
	"os"
	"strings"
)

// RuntimeEnvironment represents where the agents are running
type RuntimeEnvironment string

const (
	// RuntimeClaudeCode means agents are running inside Claude Code (web UI)
	RuntimeClaudeCode RuntimeEnvironment = "claude-code"

	// RuntimeVCLI means agents are running in vcli-go CLI
	RuntimeVCLI RuntimeEnvironment = "vcli-go"
)

// DetectRuntime detects the current runtime environment
func DetectRuntime() RuntimeEnvironment {
	// Strategy 1: Check VCLI_RUNTIME environment variable (explicit)
	if runtime := os.Getenv("VCLI_RUNTIME"); runtime != "" {
		if strings.ToLower(runtime) == "claude-code" {
			return RuntimeClaudeCode
		}
		return RuntimeVCLI
	}

	// Strategy 2: Check if running in Claude Code context
	// Claude Code sets CLAUDE_CODE=true when executing commands
	if os.Getenv("CLAUDE_CODE") == "true" {
		return RuntimeClaudeCode
	}

	// Strategy 3: Check for typical vcli-go indicators
	// If binary name contains "vcli", assume CLI
	if len(os.Args) > 0 && strings.Contains(os.Args[0], "vcli") {
		return RuntimeVCLI
	}

	// Default: assume vcli-go (backward compatibility)
	return RuntimeVCLI
}

// IsClaudeCode returns true if running in Claude Code environment
func IsClaudeCode() bool {
	return DetectRuntime() == RuntimeClaudeCode
}

// IsVCLI returns true if running in vcli-go CLI
func IsVCLI() bool {
	return DetectRuntime() == RuntimeVCLI
}

// GetRuntimeString returns human-readable runtime name
func GetRuntimeString() string {
	return string(DetectRuntime())
}
