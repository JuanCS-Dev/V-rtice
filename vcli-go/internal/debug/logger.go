package debug

import (
	"fmt"
	"os"
	"strings"
)

// IsEnabled returns true if debug mode is enabled via VCLI_DEBUG env var
func IsEnabled() bool {
	debug := strings.ToLower(os.Getenv("VCLI_DEBUG"))
	return debug == "true" || debug == "1" || debug == "yes"
}

// Log prints a debug message to stderr if debug mode is enabled
func Log(format string, args ...interface{}) {
	if IsEnabled() {
		msg := fmt.Sprintf(format, args...)
		fmt.Fprintf(os.Stderr, "[DEBUG] %s\n", msg)
	}
}

// LogConnection logs connection attempts with endpoint source information
func LogConnection(service, endpoint, source string) {
	if IsEnabled() {
		fmt.Fprintf(os.Stderr, "[DEBUG] Connecting to %s at %s (source: %s)\n",
			service, endpoint, source)
	}
}

// LogSuccess logs successful connection
func LogSuccess(service, endpoint string) {
	if IsEnabled() {
		fmt.Fprintf(os.Stderr, "[DEBUG] ✓ Connected successfully to %s at %s\n",
			service, endpoint)
	}
}

// LogError logs error details
func LogError(service, endpoint string, err error) {
	if IsEnabled() {
		fmt.Fprintf(os.Stderr, "[DEBUG] ✗ Failed to connect to %s at %s: %v\n",
			service, endpoint, err)
	}
}

// LogConfigSource logs where a configuration value came from
func LogConfigSource(key, value, source string) {
	if IsEnabled() {
		fmt.Fprintf(os.Stderr, "[DEBUG] Config: %s = %s (from %s)\n",
			key, value, source)
	}
}

// LogRequest logs an outgoing request
func LogRequest(service, operation string, details ...string) {
	if IsEnabled() {
		extra := ""
		if len(details) > 0 {
			extra = fmt.Sprintf(" | %s", strings.Join(details, " | "))
		}
		fmt.Fprintf(os.Stderr, "[DEBUG] → %s.%s%s\n", service, operation, extra)
	}
}

// LogResponse logs a response
func LogResponse(service, operation string, status string) {
	if IsEnabled() {
		fmt.Fprintf(os.Stderr, "[DEBUG] ← %s.%s: %s\n", service, operation, status)
	}
}
