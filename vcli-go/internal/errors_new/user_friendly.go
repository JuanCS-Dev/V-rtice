package errors

import (
	"fmt"
	"strings"
)

// WrapConnectionError wraps a connection error with user-friendly troubleshooting information
func WrapConnectionError(err error, service, endpoint string) error {
	if err == nil {
		return nil
	}

	// If endpoint is empty, try to extract from error message
	if endpoint == "" {
		endpoint = "(not specified - check config)"
	}

	errMsg := err.Error()

	// Connection refused - service not running
	if strings.Contains(errMsg, "connection refused") {
		return fmt.Errorf(`Failed to connect to %s service at %s

Possible causes:
  1. Service is not running
  2. Wrong endpoint (check with VCLI_DEBUG=true)
  3. Network/firewall issue

To fix:
  - Verify service is running: docker ps | grep %s
  - Set correct endpoint: export VCLI_%s_ENDPOINT=<your-endpoint>
  - Or use flag: --server <endpoint> or --endpoint <endpoint>
  - Check config file: cat ~/.vcli/config.yaml

💡 Tip: Run with VCLI_DEBUG=true for detailed connection logs

Original error: %v`,
			service, endpoint, strings.ToLower(service), strings.ToUpper(strings.ReplaceAll(service, " ", "_")), err)
	}

	// Context deadline exceeded - timeout
	if strings.Contains(errMsg, "context deadline exceeded") ||
		strings.Contains(errMsg, "timeout") {
		return fmt.Errorf(`Connection to %s service at %s timed out

Possible causes:
  1. Service is overloaded or slow to respond
  2. Network latency issues
  3. Timeout too short for this operation

To fix:
  - Increase timeout: --timeout 60s
  - Check service health: curl %s/health
  - Check network: ping %s
  - Enable debug logging: VCLI_DEBUG=true

Original error: %v`,
			service, endpoint, endpoint, extractHost(endpoint), err)
	}

	// Certificate/TLS errors
	if strings.Contains(errMsg, "certificate") ||
		strings.Contains(errMsg, "tls") ||
		strings.Contains(errMsg, "x509") {
		return fmt.Errorf(`TLS/Certificate error connecting to %s at %s

Possible causes:
  1. Service requires TLS but client is using insecure connection
  2. Certificate expired or invalid
  3. Certificate not trusted

To fix:
  - If testing locally, service may not require TLS
  - Check service TLS configuration
  - Verify certificate validity: openssl s_client -connect %s

Original error: %v`,
			service, endpoint, extractHost(endpoint), err)
	}

	// DNS/Name resolution errors
	if strings.Contains(errMsg, "no such host") ||
		strings.Contains(errMsg, "dns") {
		return fmt.Errorf(`DNS resolution failed for %s service at %s

Possible causes:
  1. Hostname is misspelled
  2. DNS server cannot resolve hostname
  3. Host does not exist

To fix:
  - Verify hostname: nslookup %s
  - Use IP address instead: --server <ip>:<port>
  - Check /etc/hosts for local resolution

Original error: %v`,
			service, endpoint, extractHost(endpoint), err)
	}

	// Permission denied
	if strings.Contains(errMsg, "permission denied") {
		return fmt.Errorf(`Permission denied connecting to %s at %s

Possible causes:
  1. Insufficient permissions to access service
  2. Authentication required but not provided
  3. Firewall blocking connection

To fix:
  - Check authentication: ensure valid token/credentials
  - Verify firewall rules
  - Check service access control lists

Original error: %v`,
			service, endpoint, err)
	}

	// Network unreachable
	if strings.Contains(errMsg, "network is unreachable") ||
		strings.Contains(errMsg, "no route to host") {
		return fmt.Errorf(`Network unreachable to %s service at %s

Possible causes:
  1. Network interface is down
  2. Routing configuration issue
  3. Service is on different network segment

To fix:
  - Check network status: ip addr
  - Verify routing: ip route
  - Check VPN connection if applicable

Original error: %v`,
			service, endpoint, err)
	}

	// Generic connection error with basic help
	return fmt.Errorf(`Failed to connect to %s service at %s

💡 Tip: Enable debug logging for more details:
  export VCLI_DEBUG=true
  vcli [command]

Original error: %v`,
		service, endpoint, err)
}

// WrapHTTPError wraps an HTTP error with user-friendly information
func WrapHTTPError(err error, service string, statusCode int, endpoint string) error {
	if err == nil {
		return nil
	}

	switch statusCode {
	case 400:
		return fmt.Errorf(`Bad Request to %s service at %s

The request was malformed or invalid.

To fix:
  - Check command syntax: vcli [command] --help
  - Verify all required parameters are provided
  - Check data format (JSON, etc.)

Original error: %v`,
			service, endpoint, err)

	case 401:
		return fmt.Errorf(`Authentication required for %s service at %s

You are not authenticated or your credentials are invalid.

To fix:
  - Login: vcli hitl login
  - Check token: cat ~/.vcli/tokens/hitl.json
  - Provide auth token: --token <token>

Original error: %v`,
			service, endpoint, err)

	case 403:
		return fmt.Errorf(`Access forbidden to %s service at %s

You are authenticated but do not have permission for this operation.

To fix:
  - Check your user permissions
  - Contact administrator for access
  - Verify you are using the correct account

Original error: %v`,
			service, endpoint, err)

	case 404:
		return fmt.Errorf(`Resource not found on %s service at %s

The requested resource does not exist.

To fix:
  - Verify resource ID/name is correct
  - List available resources: vcli [service] list
  - Check service endpoint is correct

Original error: %v`,
			service, endpoint, err)

	case 500, 502, 503, 504:
		return fmt.Errorf(`Server error from %s service at %s (status %d)

The service encountered an internal error.

To fix:
  - Retry the operation
  - Check service logs: docker logs <container>
  - Contact administrator if problem persists

Original error: %v`,
			service, endpoint, statusCode, err)

	default:
		return fmt.Errorf(`HTTP error %d from %s service at %s

To fix:
  - Check service health: curl %s/health
  - Enable debug mode: VCLI_DEBUG=true
  - See service documentation

Original error: %v`,
			statusCode, service, endpoint, endpoint, err)
	}
}

// extractHost extracts hostname from endpoint URL
func extractHost(endpoint string) string {
	// Remove protocol
	host := strings.TrimPrefix(endpoint, "http://")
	host = strings.TrimPrefix(host, "https://")
	host = strings.TrimPrefix(host, "grpc://")

	// Remove path
	if idx := strings.Index(host, "/"); idx != -1 {
		host = host[:idx]
	}

	return host
}

// SuggestConfigFix provides suggestions for configuration issues
func SuggestConfigFix(service, param string) string {
	return fmt.Sprintf(`Missing or invalid configuration for %s: %s

To fix:
  1. Set via environment variable:
     export VCLI_%s_%s=<value>

  2. Set via configuration file:
     vcli configure set %s.%s <value>

  3. Set via command flag:
     vcli [command] --%s <value>

To see current configuration:
  vcli configure show
`,
		service, param,
		strings.ToUpper(service), strings.ToUpper(param),
		strings.ToLower(service), strings.ToLower(param),
		strings.ToLower(param))
}
