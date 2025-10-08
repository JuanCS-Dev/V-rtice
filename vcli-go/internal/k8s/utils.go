package k8s

import (
	"encoding/json"
	"fmt"
	"strings"

	"gopkg.in/yaml.v3"
)

// ParseLabels parses a label string into a map
// Input format: "key1=value1,key2=value2"
func ParseLabels(labelsStr string) (map[string]string, error) {
	if labelsStr == "" {
		return make(map[string]string), nil
	}

	labels := make(map[string]string)
	pairs := strings.Split(labelsStr, ",")

	for _, pair := range pairs {
		pair = strings.TrimSpace(pair)
		if pair == "" {
			continue
		}

		parts := strings.SplitN(pair, "=", 2)
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid label format %q (expected key=value)", pair)
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		if key == "" {
			return nil, fmt.Errorf("empty label key in %q", pair)
		}

		labels[key] = value
	}

	return labels, nil
}

// ParseLiteral parses a literal string into key and value
// Input format: "key=value"
func ParseLiteral(literal string) (string, string, error) {
	parts := strings.SplitN(literal, "=", 2)
	if len(parts) != 2 {
		return "", "", fmt.Errorf("invalid format (expected key=value)")
	}

	key := strings.TrimSpace(parts[0])
	value := strings.TrimSpace(parts[1])

	if key == "" {
		return "", "", fmt.Errorf("empty key")
	}

	return key, value, nil
}

// FormatOutput formats an object as JSON or YAML
func FormatOutput(obj interface{}, format string) (string, error) {
	switch format {
	case "json":
		data, err := json.MarshalIndent(obj, "", "  ")
		if err != nil {
			return "", fmt.Errorf("failed to marshal to JSON: %w", err)
		}
		return string(data), nil

	case "yaml":
		data, err := yaml.Marshal(obj)
		if err != nil {
			return "", fmt.Errorf("failed to marshal to YAML: %w", err)
		}
		return string(data), nil

	case "wide", "":
		// For wide format, use JSON as default
		data, err := json.MarshalIndent(obj, "", "  ")
		if err != nil {
			return "", fmt.Errorf("failed to marshal to JSON: %w", err)
		}
		return string(data), nil

	default:
		return "", fmt.Errorf("unsupported output format: %s (supported: json, yaml, wide)", format)
	}
}
